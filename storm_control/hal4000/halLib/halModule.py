#!/usr/bin/env python
"""
The core functionality for a HAL module.

Hazen 01/17
"""

from collections import deque

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox


class HalModule(QtCore.QThread):
    """
    Use this if you can guarantee that your processMessage() function 
    will execute on the millisecond time frame. If this is not the
    case then use the HalModuleBuffered class instead.

    Conventions:
       1. self.view is the GUI view, if any that is associated with this module.

    """
    newFrame = QtCore.pyqtSignal(object)
    newMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", **kwds):
        super().__init__(**kwds)
        self.module_name = module_name

    def cleanUp(self, qt_settings):
        pass

    def handleError(self, m_error):
        """
        Override with class specific error handling.
        """
        return False
    
    def handleFrame(self, new_frame):
        pass

    def handleMessage(self, message):
        self.processMessage(message)

    def handleResponse(self, response):
        pass
        
    def handleWarning(self, m_warning):
        """
        Override with class specific warning handling.
        """
        return False
    
    def messageError(self, m_errors):
        """
        Implement class specific error / warning handling by
        overriding handleError and/or handleWarning.
        """
        for m_error in m_errors:
            data = m_error.source + ": " + m_error.message
            if m_error.hasException():
                if not self.handleError(m_error):
                    halMessageBox.halMessageBoxInfo(message.data, is_error = True)
                    raise m_error.getException()
            else:
                if not self.handleWarning(m_warning):
                    halMessageBox.halMessageBoxInfo(message.data)

    def messageResponse(self, responses):
        """
        Implement class specific response handling by overriding
        handleResponse().
        """
        for response in responses:
            self.handleResponse(response)
        
    def processMessage(self, message):
        message.ref_count -= 1

        
class HalModuleBuffered(HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.queued_messages = deque()
        self.queued_messages_mutex = QtCore.QMutex()

    def addMessageToQueue(self, message):
        # Add the message to the queue.
        self.queued_messages_mutex.lock()
        self.queued_messages.append(message)
        self.queued_messages_mutex.unlock()

        # Start message processing, if it is not already running.
        if not self.isRunning():
            self.start(QtCore.QThread.NormalPriority)
        
    def run(self):
        while (len(self.queued_message) > 0):
            self.queued_messages_mutex.lock()
            next_message = self.queued_messages.popleft()
            self.queued_messages_mutex.unlock()
            self.processMessage(next_message)


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
