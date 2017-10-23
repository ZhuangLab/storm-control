#!/usr/bin/env python
"""
RS232 interface to a Marzhauser stage.

Hazen 04/17
"""
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232
import storm_control.sc_library.hdebug as hdebug


class MarzhauserRS232(RS232.RS232):
    """
    Marzhauser RS232 interface class.
    """
    def __init__(self, **kwds):
        """
        Connect to the Marzhauser stage at the specified port.
        """
        self.live = True
        self.unit_to_um = 1000.0
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0

        # RS232 stuff
        try:
            super().__init__(**kwds)
            test = self.commWithResp("?version")
            if not test:
                self.live = False

        # FIXME: This should not catch everything!                
        except Exception:
            print(traceback.format_exc())
            self.live = False
            print("Marzhauser Stage is not connected? Stage is not on?")
            
    def goAbsolute(self, x, y):
        x = x * self.um_to_unit
        y = y * self.um_to_unit
        # FIXME: Too many digits here? Use format() instead? int()?"
        self.writeline(" ".join(["!moa", str(x), str(y)]))

    def goRelative(self, x, y):
        x = x * self.um_to_unit
        y = y * self.um_to_unit
        self.writeline(" ".join(["!mor", str(x), str(y)]))

    def jog(self, x_speed, y_speed):
        vx = x_speed * self.um_to_unit
        vy = y_speed * self.um_to_unit
        self.writeline(" ".join(["!speed ", str(vx), str(vy)]))
        
    def joystickOnOff(self, on):
        if on:
            self.writeline("!joy 2")
        else:
            self.writeline("!joy 0")

    def position(self):
        self.writeline("?pos")

    def serialNumber(self):
        """
        Return the stages serial number.
        """
        return self.writeline("?readsn")

    def setVelocity(self, x_vel, y_vel):
        self.writeline(" ".join(["!vel",str(x_vel),str(y_vel)]))

    def zero(self):
        self.writeline("!pos 0 0")


#
# Testing
#
if (__name__ == "__main__"):
    import time

    stage = MarzhauserRS232(port = "COM5", baudrate = 57600)
    
    def comm(cmd, timeout):
        cmd()
        time.sleep(timeout)
        return stage.readline()
    
    if stage.getStatus():
        print("SN:", comm(stage.serialNumber, 0.1))
        print("zero:", comm(stage.zero, 0.1))
        print("position:", comm(stage.position, 0.1))
        print("goAbsolute:", comm(lambda: stage.goAbsolute(100,100), 0.5))
        print("position:", comm(stage.position, 0.1))
        print("goRelative:", len(comm(lambda: stage.goRelative(100,100), 0.5)))
        print("position:", comm(stage.position, 0.1))
        stage.shutDown()


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
