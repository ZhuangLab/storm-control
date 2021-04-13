#!/usr/bin/env python
"""
RS232 interface to a Zaber XY stage.

Hazen 04/17
Jeff 04/21
"""
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232
import storm_control.sc_library.hdebug as hdebug


class ZaberXYRS232(RS232.RS232):
    """
    ZaberXY stage RS232 interface class.
    """
    def __init__(self, **kwds):
        """
        Connect to the Zaber stage at the specified port.
        """
        self.live = True
        if kwds.has_key("unit_to_um"):
            self.unit_to_um = kwds["unit_to_um"]
        else:
            self.unit_to_um = 1000.0
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0

        # RS232 stuff
        try:
            super().__init__(**kwds)
            test = self.commWithResp("/")
            if not test:
                self.live = False

        except (AttributeError, AssertionError):
            print(traceback.format_exc())
            self.live = False
            print("Zaber XY Stage is not connected? Stage is not on?")
            print("Failed to connect to the Zaber XY stage at port", kwds["port"])

    def goAbsolute(self, x, y):
        # Convert um units to the stage step units and round to an integer
        x = int(round(x * self.um_to_unit))
        y = int(round(y * self.um_to_unit))
        
        # Send a command for each axis
        for axis, pos in enumerate([x,y]):
            self.writeline("/1 " + str(axis+1) + " move abs " + str(pos))
        
    def goRelative(self, x, y):
        # Convert um units to the stage step units and round to an integer
        x = int(round(x * self.um_to_unit))
        y = int(round(y * self.um_to_unit))
        
        # Send a command for each axis
        for axis, pos in enumerate([x,y]):
            self.writeline("/1 " + str(axis+1) + " move rel " + str(pos))

    def jog(self, x_speed, y_speed):
        # Convert um units to the stage step units and round to an integer
        vx = int(round(x_speed * self.um_to_unit * 1.6384))
        vy = int(round(y_speed * self.um_to_unit * 1.6384))
        
        # Send a command for each axis
        for axis, vel in enumerate([x,y]):
            self.writeline("/1 " + str(axis+1) + " move vel " + str(vel))
        
    def joystickOnOff(self, on):
        if on:
            self.writeline("!joy 2")
        else:
            self.writeline("!joy 0")

    def position(self):
        ### UNUSED?!?!
        self.writeline("?pos")

    def serialNumber(self):
        """
        Return the stages serial number.
        """
        return self.writeline("?readsn")

    def setVelocity(self, x_vel, y_vel):
        ## NOTE THAT THERE IS ONLY ONE MAXIMUM VELOCITY (x_vel)
    
        # Convert um units to the stage step units and round to an integer
        vx = int(round(x_vel * self.um_to_unit * 1.6384))

        # Write the command
        self.writeline("/1 set maxspeed " + str(vx))
    
    def setAcceleration(self, x_accel, y_accel):
        ## NOTE THAT THERE IS ONLY ONE MAXIMUM VELOCITY (x_vel)

        # Convert to stage units
        ax = int(round(x_accel * self.um_to_unit * 1.6384 / 10000))
        
        if ax > 2147483647:
            print("ERROR: Invalid acceleration requested: " + str(ax))
            return

        # Write the command
        self.writeline("/1 set accel " + str(ax))

    def zero(self):
        self.writeline("!pos 0 0")


#
# Testing
#
if (__name__ == "__main__"):
    import time

    stage = ZaberXYRS232(port = "COM1", baudrate = 57600)
    
    def comm(cmd, timeout):
        cmd()
        time.sleep(timeout)
        return stage.readline()
    
    if stage.getStatus():

        # Test communication.
        if False:
            print("SN:", comm(stage.serialNumber, 0.1))
            print("zero:", comm(stage.zero, 0.1))
            print("position:", comm(stage.position, 0.1))
            print("goAbsolute:", comm(lambda: stage.goAbsolute(100,100), 0.5))
            print("position:", comm(stage.position, 0.1))
            print("goRelative:", len(comm(lambda: stage.goRelative(100,100), 0.5)))
            print("position:", comm(stage.position, 0.1))

        # Test whether we can jam up stage communication.
        if True:
            reps = 20
            for i in range(reps):
                print(i)
                stage.position()
                stage.goAbsolute(i*10,0)
                stage.position()
                time.sleep(0.1)

            for i in range(3*reps + 4):
                responses = stage.readline()
                for resp in responses.split("\r"):
                    print(i, resp, len(resp))
            
        stage.shutDown()


#
# The MIT License
#
# Copyright (c) 2021 Moffitt Lab, Boston Children's Hospital
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
