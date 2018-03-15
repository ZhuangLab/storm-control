#!/usr/bin/env python
"""
The core functionality for a HAL module. All modules should be
a sub-class of this module.

Hazen 01/17
"""

import traceback

from collections import deque

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox


threadpool = QtCore.QThreadPool.globalInstance()


def runWorkerTask(module, message, task):
    """
    Use this to handle long running (non-GUI) tasks. See
    camera.camera.py for examples.

    This will also handle errors in manner that HAL expects.

    Note: Only one of these can be run at a time (per module) in order 
          to gaurantee that messages are handled serially. This assumes 
          that the threadpool starts the tasks in the order they are 
          received.
    """
    
    # Increment the count because once this message is handed off
    # HalModule will automatically decrement the count.
    message.incRefCount()
    ct_task = HalWorker(message = message,
                        mutex = module.worker_mutex,
                        task = task)
    ct_task.hwsignaler.workerDone.connect(module.handleWorkerDone)
    ct_task.hwsignaler.workerError.connect(module.handleWorkerError)

    # We need to manage the tasks ourselves because otherwise we'll
    # experience strange/sporadic errors like the GUI freezing.
    ct_task.setAutoDelete(False)
    module.workers[id(ct_task)] = ct_task

    # This had better start tasks in the order they are received or
    # there could be all kinds of issues..
    threadpool.start(ct_task)


class HalWorkerSignaler(QtCore.QObject):
    """
    A signaler class for HalWorker.
    """
    workerDone = QtCore.pyqtSignal(object, object)
    workerError = QtCore.pyqtSignal(object, object, object, str)


class HalWorker(QtCore.QRunnable):
    """
    For running long non-GUI tasks in a separate thread. 

    Note that the message will remain in HAL's sent messages queue
    until this (and all other processing) are complete.
    """
    def __init__(self, message = None, mutex = None, task = None, **kwds):
        super().__init__(**kwds)
        self.message = message
        self.mutex = mutex
        self.task = task
        self.task_complete = False

        self.hwsignaler = HalWorkerSignaler()

    def isFinished(self):
        return self.task_complete
    
    def run(self):
        try:
            self.mutex.lock()
            self.task()
            self.mutex.unlock()
        except Exception as exception:
            self.hwsignaler.workerError.emit(id(self),
                                             self.message,
                                             exception,
                                             traceback.format_exc())
        finally:
            self.task_complete = True
            
        self.hwsignaler.workerDone.emit(id(self), self.message)

        
class HalModule(QtCore.QObject):
    """
    To handle messages sub-classes should override the appropriate
    processMessage method.

    The processMessage() method should execute essentially instantly. If
    it needs to do something that will take some time, then processing
    should be handled using runWorkerTask(). This will process the message 
    in a separate thread, and hold onto the message so that HAL knows
    that message processing is not complete. This will keep the task from 
    freezing the GUI and causing other issues.

    Conventions:
       1. self.view is the GUI view, if any that is associated with this module.
       2. self.control is the controller, if any.

    """
    newMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", **kwds):
        super().__init__(**kwds)
        self.module_name = module_name

        self.queued_messages = deque()
        self.workers = {}
        self.worker_mutex = QtCore.QMutex()

        self.queued_messages_timer = QtCore.QTimer(self)
        self.queued_messages_timer.setInterval(0)
        self.queued_messages_timer.timeout.connect(self.nextMessage)
        self.queued_messages_timer.setSingleShot(True)

        self.view = None
        
    def cleanUp(self, qt_settings):
        """
        Override to provide module specific clean up and to save
        GUI settings.
        """
        pass

    def cleanUpWorker(self, worker_id):
        """
        Disconnects any workers that have finished and discard them.
        """
        worker = self.workers[worker_id]
        worker.hwsignaler.workerDone.disconnect(self.handleWorkerDone)
        worker.hwsignaler.workerError.disconnect(self.handleWorkerError)
        del self.workers[worker_id]

    def findChild(self, qt_type, name, options):
        """
        Overwrite the QT version as the 'child' could only
        be in the view, if any.
        """
        if self.view is not None:
            print("fc", self.view, self.view.objectName(), name)
            if (self.view.objectName() == name):
                return self.view
            else:
                return self.view.findChild(qt_type, name, options)

    def handleError(self, message, m_error):
        """
        Override this with class specific error handling.
        """
        return False
    
    def handleErrors(self, message):
        """
        Don't override..
        """
        for m_error in message.getErrors():
            data = m_error.source + ": " + m_error.message
            if m_error.hasException():
                if not self.handleError(message, m_error):
                    m_error.printException()
                    return False
            else:
                if not self.handleWarning(message, m_error):
                    halMessageBox.halMessageBoxInfo(data)
        return True

    def handleMessage(self, message):
        """
        Don't override..
        """
        # Use a queue and timer so that core doesn't
        # get hung up sending messages.
        self.queued_messages.append(message)        
        self.queued_messages_timer.start()
        
    def handleResponse(self, message, response):
        """
        Override this if you expect only singleton message responses.
        """
        pass

    def handleResponses(self, message):
        """
        Override this if you want to handle all the message
        responses (as a list).
        """
        if message.hasResponses():
            for response in message.getResponses():
                self.handleResponse(message, response)

    def handleWarning(self, message, m_error):
        """
        Override with class specific warning handling.
        """
        return False

    def handleWorkerDone(self, worker_id, message):
        """
        You probably don't want to override this..
        """
        message.decRefCount()

        # Log when the worker finished.
        message.logEvent("worker done")

        # Cleanup the worker.
        self.cleanUpWorker(worker_id)

    def handleWorkerError(self, worker_id, message, exception, stack_trace):
        """
        You probably don't want to override this..
        """
        message.addError(halMessage.HalMessageError(source = self.module_name,
                                                    message = str(exception),
                                                    m_exception = exception,
                                                    stack_trace = stack_trace))

        # Decrement ref count otherwise the error will hang HAL.
        message.decRefCount()

        # Log when the worker failed.
        message.logEvent("worker failed")

        # Cleanup the worker.
        self.cleanUpWorker(worker_id)

    def processMessage(self, message):
        """
        Override with class specific handling of messages.

        This needs to execute quickly, otherwise the GUI
        will appear frozen among other problems.
        """
        pass
        
    def nextMessage(self):
        """
        Don't override..
        """
        # Get the next message from the queue.
        message = self.queued_messages.popleft()

        try:
            self.processMessage(message)
        except Exception as exception:
            message.addError(halMessage.HalMessageError(source = self.module_name,
                                                        message = str(exception),
                                                        m_exception = exception,
                                                        stack_trace = traceback.format_exc()))
        message.decRefCount()

        # Start the timer if we still have messages left.
        if (len(self.queued_messages) > 0):
            self.queued_messages_timer.start()

    def sendMessage(self, message):
        """
        Use this to send a message from the module.

        FIXME: Have all modules been updated to use this?
        """
        message.source = self
        self.newMessage.emit(message)
        
            
#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
