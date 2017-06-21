#!/usr/bin/env python
"""
Prior XY stage communication (mostly).

Hazen 5/11
"""

import time
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232


class Prior(RS232.RS232):
    """
    Control of a XY Prior stage, possibly with piezo Z control & a 
    filter wheel. Communication via RS-232.
    """
    def __init__(self, **kwds):

        self.has_device = {"stage" : False,
                           "focus" : False,
                           "filter_1" : False,
                           "filter_2" : False}
        self.live = True
        self.unit_to_um = 1.0
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        try:
            super().__init__(**kwds)
            device_info = self._command("?")
            if not device_info:
                self.live = False
        except Exception:
            print(traceback.format_exc())
            self.live = False

        if not self.live:
            print("Prior Stage is not connected? Stage is not on?")
            
        else:
            # Query for available devices.
            for elt in device_info:
                data = elt.split(" = ")
                if (len(data) > 1) and (data[0].lower() in self.has_device):
                    if (data[1] != "NONE"):
                        self.has_device[data[0].lower()] = True
            
            # This turns off "drift correction".
            self.setServo(False)
            self.setEncoderWindow("X", 2)
            self.setEncoderWindow("Y", 2)

    def _command(self, command):
        response = self.commWithResp(command)
        if response:
            return response.split("\r")

    def active(self):
        """
        Return True/False The stage is busy doing something.
        """
        response = self._command("$")[0]
        if (response == "0"):
            return False
        else:
            return True

    def backlashOnOff(self, on):
        if on:
            self._command("BLSH 1")
        else:
            self._command("BLSH 0")

    def changeFilter(self, filter_wheel, filter_index):
        if not (filter_index == self.getFilter(filter_wheel)):
            self.sendCommand("7," + str(filter_wheel) + "," + str(filter_index))
            self.waitResponse()

    def getFilter(self, filter_wheel):
        try:
            return int(self._command("7," + str(filter_wheel) + ",F")[0])
        except Exception:
            print("Error reading filter position.")
            return -1

    def getServo(self):
        """
        Returns whether or not the stage is servoing, i.e. updating it
        position based on the encoders in the event of drift.
        """
        return [self._command("SERVO,X"), self._command("SERVO,Y")]

    def goAbsolute(self, x, y):
        self.sendCommand("G " + str(x * self.um_to_unit) + "," + str(y * self.um_to_unit))
        self.waitResponse()

    def goRelative(self, dx, dy):
        self.sendCommand("GR " + str(dx * self.um_to_unit) + "," + str(dy * self.um_to_unit))
        self.waitResponse()

    def hasDevice(self, device_name):
        return self.has_device[device_name]
    
    def info(self):
        return self._command("?")

    def jog(self, x_speed, y_speed):
        """
        x_speed - Speed the stage should be moving at in x in um/s.
        y_speed - Speed the stage should be moving at in y in um/s.
        """
        #print("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))
        self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    def joystickOnOff(self, on):
        """
        True/False enable/disable the stage joystick.
        """
        if on:
            self._command("J")
        else:
            self._command("H")
     
    def position(self):
        try:
            response = self._command("P")[0]
            [self.x, self.y, self.z] = map(int, response.split(","))
        except Exception:
            pass
        return [self.x * self.unit_to_um, 
                self.y * self.unit_to_um, 
                self.z * self.unit_to_um]

    def setEncoderWindow(self, axis, window):
        """
        Sets the amount of diplacement from the correct position that is allowed
        before the stage will attempt to correct by moving.
        """
        assert window >= 0, "setEncoderWindow window is too small " + str(window)
        #assert window <= 4, "setEncoderWindow window is too large " + str(window)
        if (axis == "X"):
            self._command("ENCW X," + str(window))
        if (axis == "Y"):
            self._command("ENCW Y," + str(window))

    def setServo(self, servo):
        """
        Set the stage to update (or not) based on the encoders 
        in the event of stage drift.
        """
        if servo:
            self._command("SERVO,1")
        else:
            self._command("SERVO,0")

    def setVelocity(self, x_vel, y_vel):
        """
        x_vel - The maximum stage velocity allowed in x.
        y_vel - The maximum stage velocity allowed in y.
        """
        # FIXME: units are 1-100, but not exactly sure what..
        speed = x_vel
        if (speed > 100.0):
            speed = 100.0
        self._command("SMS," + str(speed))

    def state(self):
        """
        FIXME: Not sure if this works anymore, I can't find this command in the
               manual for the ProScanIII stage.
        """
        response = self._command("#")[0]
        state = []
        for i in range(len(response)):
            if response[i] == "1":
                state.append("busy")
            else:
                state.append("idle")
        return state

    def zero(self):
        """
        Set the current position as the stage zero position.
        """
        self._command("P 0,0,0")

    def zMoveTo(self, z):
        """
        The z value to move to the (piezo) stage to.
        """
        self._command("<V " + str(z))

    def zPosition(self):
        """
        Return the current z position of the (piezo) stage.
        """
        zpos = self._command("<PZ")
        return zpos[1:]


class PriorZ(Prior):
    """
    Communication via RS-232 with a Prior Z piezo stage.
    """
    def __init__(self, **kwds):
        self.z_scale = 1.0

        super().__init__(**kwds)
        if not self.live:
            print("Failed to connect to Prior piezo controller.")

    def changeBaudRate(self, baudrate):
        self._command("BAUD " + str(baudrate))

    def getBaudRate(self):
        baudrate = self._command("BAUD")[0]
        return int(baudrate)

    def zMoveRelative(self, dz):
        self._command("U {0:.3f}".format(dz * self.z_scale))

    def zMoveTo(self, z):
        self._command("V {0:.3f}".format(z * self.z_scale))

    def zPosition(self):
        zpos = self._command("PZ")[0]
        return float(zpos)/self.z_scale


class PriorFocus(PriorZ):
    """
    Communication via RS-232 with a Prior focus drive motor.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.z_scale = 10.0
        if not self.live:
            print("Failed to connect to Prior focus motor controller.")



#
# Testing
# 

if (__name__ == "__main__"):
    
    stage = Prior(port = "COM7", baudrate = 115200)

    for info in stage.info():
        print(info)


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
