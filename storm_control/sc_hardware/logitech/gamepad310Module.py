#!/usr/bin/python
"""
Gamepad310 HAL module.

Hazen 04/18
"""
import storm_control.sc_hardware.baseClasses.joystickModule as joystickModule

import storm_control.sc_hardware.logitech.gamepad310 as gamepad310

class Gamepad310Module(joystickModule.JoystickModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Create joystick controller.
        self.control = joystickModule.JoystickControl(joystick = gamepad310.Gamepad310(),
                                                      joystick_gains = self.gains)

        # Connect signals.
        self.control.lock_jump.connect(self.handleLockJump)
        self.control.toggle_film.connect(self.handleToggleFilm)

#
# The MIT License
#
# Copyright (c) 2018 Babcock Lab, Harvard University
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
