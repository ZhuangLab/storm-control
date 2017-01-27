#!/usr/bin/env python
"""
The messages that are passed between modules.

Hazen 01/17
"""

import storm_control.sc_library.hdebug as hdebug


class HalMessage(object):

    def __init__(self, source = None, m_type = "", data = None, sync = False, level = 1, finalizer = None, **kwds):
        """
        source - HalModule object that sent the message.

        mtype - String that defines the message type.

        data - Python object containing the message data.

        sync - Boolean that indicates whether or not this message should be 
               processed by all the modules before continuing to the next message.

        level - Integer that for the message 'level'. Most messages are level 1
                but if the message is one that there will be a lot of, and that
                is only relevant to one or two other modules (such as commands
                from a USB joystick) then it should be some other level so that
                modules that are not interested can more quickly ignore it.

        finalizer - A function with no arguments to call when the message has been 
                    processed by all of the modules.
        """
        super().__init__(**kwds)

        self.data = data
        self.finalizer = finalizer
        self.level = level
        self.m_errors = []
        self.m_type = m_type
        self.source = source
        self.sync = sync

        self.ref_count = 0

        # Log when message was created.
        hdebug.logText(",".join(["created", str(id(self)), self.source.module_name, self.m_type]))

    def addError(self, hal_message_error):
        self.m_errors.append(hal_message_error)
        
    def finalize(self):

        # Log when message was destroyed. This is primarily for profiling.
        hdebug.logText(",".join(["destroyed", str(id(self)), self.m_type]))
        
        if self.finalizer is not None:
            self.finalizer()

    def getErrors(self):
        return self.m_errors

    def getSource(self):
        return self.source

    def hasErrors(self):
        return len(self.m_errors) > 0


class HalMessageError(object):
    """
    If a module has a problem with a message that it can't handle then
    it should append one of these objects to the message merrors field.
    """
    def __init__(self, source = "", message = "", m_exception = None, **kwds):
        """
        source - String identifier of the message source.
        message - The warning / error message as a String.
        m_exception - The exception for the source to raise if can't handle
                      this error.
        """
        super().__init__(**kwds)

        self.source = source
        self.message = message
        self.m_exception = m_exception

    def getException(self):
        return self.m_exception
    
    def hasException(self):
        return self.m_exception is not None

                 
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
