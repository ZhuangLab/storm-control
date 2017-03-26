#!/usr/bin/env python
"""
The core functionality for a HAL module. All modules should be
a sub-class of this module.

Hazen 01/17
"""

from collections import deque

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox


threadpool = QtCore.QThreadPool.globalInstance()

def runWorkerTask(module, message, task):
    message.incRefCount()
    ct_task = HalWorker(message = message,
                        task = task)
    ct_task.hwsignaler.workerDone.connect(module.handleWorkerDone)
    threadpool.start(ct_task)

    
class HalWorkerSignaler(QtCore.QObject):
    workerDone = QtCore.pyqtSignal(object)


class HalWorker(QtCore.QRunnable):

    def __init__(self, message = None, task = None, **kwds):
        super().__init__(**kwds)
        self.message = message
        self.task = task

        self.hwsignaler = HalWorkerSignaler()

    def run(self):
        self.task()
        self.hwsignaler.workerDone.emit(self.message)


class HalModule(QtCore.QObject):
    """
    To handle messages sub-classes should override the appropriate
    processLXMessage method (See halMessage.py for the meaning of
    the different message levels).

    Any processLXMessage() method should execute essentially instantly. 
    If the task they need to accomplish cannot be done immediately then
    processing should be handed off to a HalConcurrentTask to be run
    in separate. This will keep the task from freezing the GUI and 
    causing other issues.

    Conventions:
       1. self.view is the GUI view, if any that is associated with this module.

    """
    newMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", **kwds):
        super().__init__(**kwds)
        self.module_name = module_name
        
        self.queued_messages = deque()

        self.queued_messages_timer = QtCore.QTimer(self)
        self.queued_messages_timer.setInterval(0)
        self.queued_messages_timer.timeout.connect(self.processMessage)
        self.queued_messages_timer.setSingleShot(True)
        
    def cleanUp(self, qt_settings):
        """
        Override to provide module specific clean up and to save
        GUI settings.
        """
        pass
        
    def handleError(self, m_error):
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
                if not self.handleError(m_error):
                    halMessageBox.halMessageBoxInfo(message.data, is_error = True)
                    raise m_error.getException()
            else:
                if not self.handleWarning(m_warning):
                    halMessageBox.halMessageBoxInfo(message.data)    
    
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
        for response in message.getResponses():
            self.handleResponse(message, response)
    
    def handleWarning(self, m_warning):
        """
        Override with class specific warning handling.
        """
        return False

    def handleWorkerDone(self, message):
        """
        You probably don't want to override this..
        """
        message.decRefCount()
    
    def processMessage(self):
        """
        Don't override..
        """
        # Get the next message from the queue.
        message = self.queued_messages.popleft()

        # All of these need to execute quickly, otherwise the GUI
        # will appear frozen among other problems.
        if (message.level == 1):
            self.processL1Message(message)
        elif (message.level == 2):
            self.processL2Message(message)
        elif (message.level == 3):
            self.processL3Message(message)
        else:
            raise halException.HalException("Unknown message level", message.level)
        message.decRefCount()

        # Start the timer if we still have messages left.
        if (len(self.queued_messages) > 0):
            self.queued_messages_timer.start()
        
    def processL1Message(self, message):
        """
        Override with class specific handling of general messages.
        """
        pass

    def processL2Message(self, message):
        """
        Override with class specific handling of 'new frame' messages.
        """
        pass
    
    def processL3Message(self, message):
        """
        Override with class specific handling of 'other' messages.
        """
        pass

            
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
