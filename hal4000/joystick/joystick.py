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
# Joystick monitoring class.
#
class JoystickObject(QtCore.QObject):
    lock_jump = QtCore.pyqtSignal(float)
    motion = QtCore.pyqtSignal(float, float)
    step = QtCore.pyqtSignal(int, int)
    toggle_film = QtCore.pyqtSignal()

    @hdebug.debug
    def __init__(self, parameters, joystick, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.jstick = joystick
        self.parameters = parameters
        self.parameters.joystick_gain_index = 0

        self.jstick.start(self.joystickHandler)

    @hdebug.debug
    def close(self):
        self.jstick.shutDown()

    def joystickHandler(self, data):
        p = self.parameters
        event_data = self.jstick.translate(data)

        # Button
        if (event_data[0] == "Button"):
            if(event_data[1] == 5):
                self.lock_jump.emit(p.lockt_step)
            elif(event_data[1] == 6):
                self.toggle_film.emit()
            elif(event_data[1] == 7):
                self.lock_jump.emit(-p.lockt_step)
            elif(event_data[1] == 9): # hard stop hack for a drifting joystick..
                self.motion.emit(0.0, 0.0, 0.0, 0.0)
            elif(event_data[1] == 10):
                p.joystick_gain_index += 1
                if(p.joystick_gain_index == len(p.joystick_gain)):
                    p.joystick_gain_index = 0

        # Hat
        if (event_data[0] == "Hat"):
            sx = 0.0
            sy = 0.0
            if(event_data[1] == "up"):
                sy = -1.0
            elif(event_data[1] == "down"):
                sy = 1.0
            elif(event_data[1] == "left"):
                sx = -1.0
            elif(event_data[1] == "right"):
                sx = 1.0

            sx = sx*p.hat_step*p.joystick_signx
            sy = sy*p.hat_step*p.joystick_signy

            if p.xy_swap:
                tmp = sx
                sx = sy
                sy = tmp

            self.step.emit(sx,sy)

        # Joystick
        if (event_data[0] == "Joystick"):
            x_speed = event_data[1]
            y_speed = event_data[2]
            if(abs(x_speed) > p.min_offset) or (abs(y_speed) > p.min_offset):
                if (p.joystick_mode == "quadratic"):
                    x_speed = x_speed * x_speed * cmp(x_speed, 0.0)
                    y_speed = y_speed * y_speed * cmp(y_speed, 0.0)

                # x_speed and y_speed range from -1.0 to 1.0.
                # convert to units of microns per second
                gain = p.joystick_gain[p.joystick_gain_index]
                x_speed = gain*x_speed*p.joystick_signx
                y_speed = gain*y_speed*p.joystick_signy

                # The stage and the joystick might have different ideas
                # about which direction is x.
                if p.xy_swap:
                    tmp = x_speed
                    x_speed = y_speed
                    y_speed = tmp
                
                self.motion.emit(x_speed, y_speed)

            else:
                self.motion.emit(0.0, 0.0)

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
