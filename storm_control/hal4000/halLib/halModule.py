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
    Use this if you can guarantee that your processLXMessage() function(s) 
    will execute on the millisecond time frame. If this is not the case 
    then use the HalModuleBuffered class instead.

    Conventions:
       1. self.view is the GUI view, if any that is associated with this module.

    """
    newMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = "", **kwds):
        super().__init__(**kwds)
        self.module_name = module_name

    def cleanUp(self, qt_settings):
        pass

    def handleError(self, m_error):
        """
        Override this with class specific error handling.
        """
        return False
    
    def handleErrors(self, message):
        for m_error in message.getErrors():
            data = m_error.source + ": " + m_error.message
            if m_error.hasException():
                if not self.handleError(m_error):
                    halMessageBox.halMessageBoxInfo(message.data, is_error = True)
                    raise m_error.getException()
            else:
                if not self.handleWarning(m_warning):
                    halMessageBox.halMessageBoxInfo(message.data)    
    
    def handleFrame(self, new_frame):
        pass

    def handleMessage(self, message):
        if (message.level == 1):
            self.processL1Message(message)
        elif (message.level == 2):
            self.processL2Message(message)
        elif (message.level == 3):
            self.processL3Message(message)
        else:
            raise halException.HalException("Unknown message level", message.level)
        message.decRefCount()

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

        
class HalModuleBuffered(HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.idle_counts = 0

        self.queued_messages = deque()
        self.queued_messages_mutex = QtCore.QMutex()

        self.time_to_stop = False

    def cleanUp(self, qt_settings):
        """
        Wait for the thread to stop before exiting.
        """
        self.time_to_stop = True
        self.wait()
        
    def handleMessage(self, message):
        
        # Add the message to the queue.
        self.queued_messages_mutex.lock()
        self.queued_messages.append(message)
        self.queued_messages_mutex.unlock()

        # Start message processing, if it is not already running.
        if not self.isRunning():
            self.start(QtCore.QThread.NormalPriority)
        
    def run(self):
        while (len(self.queued_messages) > 0) and (self.idle_counts < 20):

            if self.time_to_stop:
                break
            
            self.queued_messages_mutex.lock()
            message = self.queued_messages.popleft()
            self.queued_messages_mutex.unlock()

            if (message.level == 1):
                self.processL1Message(message)
            elif (message.level == 2):
                self.processL2Message(message)
            elif (message.level == 3):
                self.processL3Message(message)
            else:
                raise halException.HalException("Unknown message level", message.level)        
            message.decRefCount()

            #
            # The idea is that we don't want the thread to immediately stop if
            # there are no new messages. Instead we'd like it to stay alive for
            # a few hundred milli-seconds, then stop. Though with a camera
            # running at a normal speed the thread is not likely to ever actually
            # stop.
            #
            if (len(self.queued_messages) == 0):
                self.idle_counts += 1
                self.msleep(10)
            else:
                self.idle_counts = 0

            
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
