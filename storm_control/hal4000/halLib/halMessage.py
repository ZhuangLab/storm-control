#!/usr/bin/env python
"""
The messages that are passed between modules.

Hazen 01/17
"""

class HalMessage(object):

    def __init__(self, source, mtype, data, sync = False, level = 1, finalizer = None, **kwds):
        """
        source - String that identifies the module where this message originated.

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
        self.mtype = mtype
        self.source = source
        self.sync = sync

        self.ref_count = 0

    def finalize(self):
        if self.finalizer is not None:
            self.finalizer()
        

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
