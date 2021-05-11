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
        self.unit_to_um = kwds["unit_to_um"]
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0
        self.stage_id = kwds["stage_id"]
        self.limits = kwds["limits_dict"]

        # We need to remove the keywords not needed for the RS232 super class initialization
        del kwds["stage_id"]
        del kwds["unit_to_um"]
        del kwds["limits_dict"]

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
        # Coerce values to stage limits
        coerced_value = False
        if x<self.limits["x_min"]:
            x=self.limits["x_min"]
            coerced_value = True
        if y<self.limits["y_min"]:
            y=self.limits["y_min"]
            coerced_value = True
        if x>self.limits["x_max"]:
            x=self.limits["x_max"]
            coerced_value = True
        if y>self.limits["y_max"]:
            y=self.limits["y_max"]
            coerced_value = True
        if coerced_value:
            print("Stage warning: Requested a move outside of programmed limits")
    
        # Convert um units to the stage step units and round to an integer
        x = int(round(x * self.um_to_unit))
        y = int(round(y * self.um_to_unit))
       
        
        # Send a command for each axis
        for axis, pos in enumerate([x,y]):
            self.writeline("/" + str(self.stage_id)+ " " + str(axis+1) + " move abs " + str(pos))
        
    def goRelative(self, x, y):
        # Convert um units to the stage step units and round to an integer
        x = int(round(x * self.um_to_unit))
        y = int(round(y * self.um_to_unit))
        
        # Send a command for each axis
        for axis, pos in enumerate([x,y]):
            self.writeline("/" + str(self.stage_id)+ " " + str(axis+1) + " move rel " + str(pos))

    def jog(self, x_speed, y_speed):
        # Convert um units to the stage step units and round to an integer
        vx = int(round(x_speed * self.um_to_unit * 1.6384))
        vy = int(round(y_speed * self.um_to_unit * 1.6384))
        
        # Send a command for each axis
        for axis, vel in enumerate([x,y]):
            self.writeline("/" + str(self.stage_id)+ " " + str(axis+1) + " move vel " + str(vel))
        
    def joystickOnOff(self, on):
        print("Joystick cannot be inactivated")
        #if on:
        #    self.writeline("!joy 2")
        #else:
        #    self.writeline("!joy 0")

    def position(self):
        ### UNUSED?!?!
        self.writeline("?pos")

    def getPosition(self):
        response = self.commWithResp("/" + str(self.stage_id) + " get pos")
        #print("Position response: " + response)
        
        response = response.strip()
        response_parts = response.split(" ")
        try:
            [sx, sy] = map(float, response_parts[5:])
        except ValueError:
            return [None, None]
        return [sx*self.unit_to_um,sy*self.unit_to_um]

    def isStageMoving(self):
        response = self.commWithResp("/" + str(self.stage_id))
        #print("isMoving response: " + response)
        
        # Parse the response
        response_parts = response.split(" ")

        # Handle an error response, or an empty response
        if not (response_parts[2] == "OK") or len(response_parts) < 2:
            print("STAGE ERROR: " + response)
            return "ERROR"        
        # Parse IDLE/BUSY
        if response_parts[3] == "IDLE":
            return "IDLE"
        else: # BUSY Case
            return "MOVING"

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
        self.writeline("/" + str(self.stage_id)+ " " + "set maxspeed " + str(vx))
    
    def setAcceleration(self, x_accel, y_accel):
        ## NOTE THAT THERE IS ONLY ONE MAXIMUM VELOCITY (x_vel)

        # Convert to stage units
        ax = int(round(x_accel * self.um_to_unit * 1.6384 / 10000))
        
        if ax > 2147483647:
            print("ERROR: Invalid acceleration requested: " + str(ax))
            return

        # Write the command
        self.writeline("/" + str(self.stage_id)+ " " + "set accel " + str(ax))

    def zero(self):
        print("The Zaber stage cannot be zeroed!")
        #self.writeline("!pos 0 0")


#
# Testing
#
if (__name__ == "__main__"):
    import time

    stage = ZaberXYRS232(port = "COM1", baudrate = 1156200)
    
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
