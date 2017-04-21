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

    def __init__(self, wait_time = 0.02, **kwds):
        """
        Connect to the Marzhuaser stage at the specified port.
        """
        # Add Marzhauser RS232 default settings.
        kwds["baudrate"] = 57600
        kwds["end_of_line"] = "\r"
        kwds["wait_time"] = wait_time
        
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
        x = y * self.um_to_unit
        print(self.commWithResp(" ".join(["!moa", str(x), str(y), "0"])))

    def goRelative(self, x, y):
        x = x * self.um_to_unit
        y = y * self.um_to_unit
        print(self.commWithResp(" ".join(["!mor", str(x), str(y), "0"])))

    def jog(self, x_speed, y_speed):
        vx = x_speed * self.um_to_unit
        vy = y_speed * self.um_to_unit
        self.commWithResp(" ".join(["!speed ", str(vx), str(vy)]))
        
    def joystickOnOff(self, on):
        if on:
            self.commWithResp("!joy 2")
        else:
            self.commWithResp("!joy 0")

    def position(self):
        try:
            [self.x, self.y] = map(lambda x: float(x)*self.unit_to_um, 
                                   self.commWithResp("?pos")[:-2].split(" "))
            return [self.x, self.y, 0.0]
        except Exception as ex:
            print(ex)
            hdebug.logText("  Warning: Bad position from Marzhauser stage.")
            return [self.x, self.y, 0.0]

    def serialNumber(self):
        """
        Return the stages serial number.
        """
        return self.commWithResp("?readsn")

    def setVelocity(self, x_vel, y_vel):
        self.commWithResp(" ".join(["!vel",str(x_vel),str(y_vel)]))

    def zero(self):
        self.commWithResp("!pos 0 0 0")


#
# Testing
#
if (__name__ == "__main__"):
    import time
    
    stage = MarzhauserRS232(port = "COM5")
    if stage.getStatus():
        print("SN:", stage.serialNumber())
        stage.zero()
        time.sleep(0.1)
        print("Position:", stage.position())
        stage.goAbsolute(100.0, 100.0)
        time.sleep(0.5)
        print("Position:", stage.position())
        stage.goRelative(100.0, 100.0)
        time.sleep(0.5)
        print("Position:", stage.position())
        time.sleep(0.1)
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
