#!/usr/bin/python
#
# Joystick monitoring class.
#
# Hazen 09/12
#

from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

#
# Joystick monitoring thread.
#
# This is a PyQt thread for monitoring the current state of a joystick.
# The status of the various controls on the joystick are polled every
# 10 milliseconds to see if anything has changed.
#
# joystick is a class with the following methods:
#
#   getAxis(i)
#      Return the current stick position for axis i.
#
#   getButton(i)
#      Return the current state of button i.
#
#   getHat(i)
#      Return the current state of hat i.
#
#   shutDown()
#      Perform joystick related cleanup.
#
class JoystickThread(QtCore.QThread):
    @hdebug.debug
    def __init__(self, joystick, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.jstick = joystick
        self.running = True

        self.number_axes = self.jstick.getNumberAxis()
        self.number_buttons = self.jstick.getNumberButtons()
        self.number_hats = self.jstick.getNumberHats()

    @hdebug.debug
    def cleanUp(self):
        self.jstick.shutDown()

    @hdebug.debug
    def close(self):
        self.stopThread()
        self.cleanUp()

    def run(self):
        while(self.running):

            # Check joystick controls
            for i in range(self.number_axes):
                tmp = self.jstick.getAxis(i)
                if(abs(tmp) > 0.02):
                    print "Axis", i, tmp

            # Check buttons
            for i in range(self.number_buttons):
                tmp = self.jstick.getButton(i)
                if tmp:
                    print "Button", i, tmp

            # Check hats
            for i in range(self.number_hats):
                tmp = self.jstick.getHat(i)
                if (tmp[0] != 0) or (tmp[1] != 0):
                    print "Hat", i, tmp

            self.msleep(10)

    @hdebug.debug
    def stopThread(self):
        self.running = False

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
