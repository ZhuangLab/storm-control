#!/usr/bin/env python
"""
The core functionality for a HAL module.

Hazen 01/17
"""

from collections import deque

from PyQt5 import QtCore


class HalModule(QtCore.QThread):
    """
    Use this if you can guarantee that your processMessage() function 
    will execute on the millisecond time frame. If this is not the
    case then use the HalModuleBuffered class instead.
    """
    new_frame = QtCore.pyqtSignal(object)
    new_message = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def cleanup(self):
        pass

    def handleFrame(self, new_frame):
        pass

    def handleMessage(self, message):
        self.processMessage(message)

    def processMessage(self, message):
        message.ref_count -= 1


class HalModuleBuffered(HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.queued_messages = deque()
        self.queue_mutex = QtCore.QMutex()

    def addMessageToQueue(self, message):
        # Add the message to the queue.
        self.queue_mutex.lock()
        self.queued_messages.append(message)
        self.queue_mutex.unlock()

        # Start message processing, if it is not already running.
        if not self.isRunning():
            self.start(QtCore.QThread.NormalPriority)
        
    def run(self):
        while (len(self.queued_message) > 0):
            self.queue_mutex.lock()
            next_message = self.queued_messages.popleft()
            self.queue_mutex.unlock()
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
