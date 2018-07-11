#!/usr/bin/env python
"""
The core functionality for a HAL module. All modules should be
a sub-class of this module.

Hazen 01/17
"""

import faulthandler
import traceback

from collections import deque

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox


threadpool = QtCore.QThreadPool.globalInstance()

# Maximum time that workers can run in milliseconds. Set to -1
# for no limit. Values are restricted to integers to for the
# benefit of QT signalling.
max_job_time = -1

def runWorkerTask(module, message, task, job_time_ms = None):
    """
    Use this to handle long running (non-GUI) tasks. See
    camera/camera.py for examples.

    This will also handle errors in manner that HAL expects.

    Note: Only one of these can be run at a time (per module) in order 
          to gaurantee that messages are handled serially.
    """
    if job_time_ms is None:
        job_time_ms = max_job_time
    
    # Increment the count because once this message is handed off
    # HalModule will automatically decrement the count.
    message.incRefCount()
    ct_task = HalWorker(job_time_ms = job_time_ms,
                        message = message,
                        task = task)
    ct_task.hwsignaler.workerDone.connect(module.handleWorkerDone)
    ct_task.hwsignaler.workerError.connect(module.handleWorkerError)
    ct_task.hwsignaler.workerStarted.connect(module.handleWorkerStarted)

    # We need to manage the tasks ourselves because otherwise we'll
    # experience strange/sporadic errors like the GUI freezing.
    ct_task.setAutoDelete(False)
    module.worker = ct_task

    # Run worker.
    threadpool.start(ct_task)


class HalWorkerSignaler(QtCore.QObject):
    """
    A signaler class for HalWorker.
    """
    workerDone = QtCore.pyqtSignal(object)
    workerError = QtCore.pyqtSignal(object, object, str)
    workerStarted = QtCore.pyqtSignal(object, int)


class HalWorker(QtCore.QRunnable):
    """
    For running long non-GUI tasks in a separate thread. 

    Note that the message will remain in HAL's sent messages queue
    until this (and all other processing) are complete.

    Set a timeout for the worker by using a value for job_time_ms 
    that is greater than 0.
    """
    def __init__(self, job_time_ms = -1, message = None, task = None, **kwds):
        super().__init__(**kwds)
        self.job_time_ms = job_time_ms
        self.message = message
        self.task = task
        self.task_complete = False
            
        self.hwsignaler = HalWorkerSignaler()

    def isFinished(self):
        return self.task_complete
    
    def run(self):
        self.hwsignaler.workerStarted.emit(self.message,
                                           self.job_time_ms)
        
        try:
            self.task()
        except Exception as exception:
            self.hwsignaler.workerError.emit(self.message,
                                             exception,
                                             traceback.format_exc())
        finally:
            self.task_complete = True
            
        self.hwsignaler.workerDone.emit(self.message)

    def timeout(self, signum, frame):
        raise halExceptions.HalException("Job timed out!")        

        
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

    Incoming messages are stored in queue and passed to processMessage() in
    the order they were received. If a worker is started the next message 
    will get passed to processMessage() until the worker finishes.

    Conventions:
       1. self.view is the GUI view, if any that is associated with this module.
       2. self.control is the controller, if any.

    """
    newMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", **kwds):
        super().__init__(**kwds)
        self.module_name = module_name

        self.queued_messages = deque()
        self.worker = None

        # Timer for workers.
        self.worker_timer = QtCore.QTimer(self)
        self.worker_timer.timeout.connect(self.handleWorkerTimer)
        self.worker_timer.setSingleShot(True)

        # Timer for handling messages from HAL core.
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

    def cleanUpWorker(self):
        """
        Disconnects any workers that have finished and discard them.
        """
        self.worker.hwsignaler.workerDone.disconnect(self.handleWorkerDone)
        self.worker.hwsignaler.workerError.disconnect(self.handleWorkerError)
        self.worker.hwsignaler.workerStarted.disconnect(self.handleWorkerStarted)
        self.worker = None

        # Stop the worker timer.
        if self.worker_timer.isActive():
            self.worker_timer.stop()

        # Start the timer if we still have messages left.
        if (len(self.queued_messages) > 0):
            self.queued_messages_timer.start()

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

        # Only start the timer if we have exactly one message and
        # we don't have any workers running.
        #
        # If we have more than one message or a running worker then
        # the timer will get started when the handling of the previous
        # message completes.
        #
        if (len(self.queued_messages) == 1) and self.worker is None:
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

    def handleWorkerDone(self, message):
        """
        You probably don't want to override this..
        """
        message.decRefCount(name = self.module_name)

        # Log when the worker finished.
        message.logEvent("worker done")

        # Cleanup the worker.
        self.cleanUpWorker()
        
    def handleWorkerError(self, message, exception, stack_trace):
        """
        You probably don't want to override this..
        """
        message.addError(halMessage.HalMessageError(source = self.module_name,
                                                    message = str(exception),
                                                    m_exception = exception,
                                                    stack_trace = stack_trace))

        # Decrement ref count otherwise the error will hang HAL.
        message.decRefCount(name = self.module_name)

        # Log when the worker failed.
        message.logEvent("worker failed")

        # Cleanup the worker.
        self.cleanUpWorker()

    def handleWorkerStarted(self, message, job_time_ms):
        """
        You probably don't want to override this..
        """
        if (job_time_ms > 0):
            self.worker_timer.setInterval(job_time_ms)
            self.worker_timer.start()

    def handleWorkerTimer(self):
        """
        If this timer fires that means the worker took longer than
        expected to complete a task, so it is probably hung.

        Not sure whether we handle this or just crash, but for now 
        we're going with crash. This may be all that we can do anyway
        as there is no way to kill a QRunnable that is stuck.
        """
        # Print a complete traceback including what all the threads were doing.
        print("Full Traceback With Threads:")
        faulthandler.dump_traceback()
        print("")

        e_string = "HALWorker for '" + self.module_name + "' module timed out handling '" + self.worker.message.m_type + "'!"
        raise halExceptions.HalException(e_string)
        
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
        message.decRefCount(name = self.module_name)

        # Check if this is being handled by a worker. If it is then we
        # wait until the worker is done before moving on to process the
        # next message.
        if self.worker is not None:
            return
            
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
