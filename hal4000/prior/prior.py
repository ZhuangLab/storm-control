#!/usr/bin/python
#
# Communicates with the Prior stages, typically on com2.
#
# Hazen 5/11
#

import halLib.RS232 as RS232
import time


#
# XY Prior stage, possibly with piezo Z control & a filter wheel.
#
class Prior(RS232.RS232):
    def __init__(self, port = "COM2", timeout = None, baudrate = 9600):
        self.unit_to_um = 1.0
        self.um_to_unit = 1.0/self.unit_to_um

        # RS232 stuff
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r", 0.0001)
        try:
            test = self.commWithResp("?")
        except:
            self.live = False
        if not self.live:
            print "Prior Stage is not connected? Stage is not on?"
        else:   # this turns off "drift correction".
            self.setServo(False)

    def _command(self, command):
        response = self.commWithResp(command)
        if response:
            return response.split("\r")

    def active(self):
        state = self.state()
        try:
            state.index("busy")
            return 1
        except:
            return 0
        
    def backlashOnOff(self, on):
        if on:
            self._command("BLSH 1")
        else:
            self._command("BLSH 0")

    def changeFilter(self, filter):
        if not (filter == self.getFilter()):
            self.sendCommand("7,1," + str(filter))
            self.waitResponse()

    def getFilter(self):
        return int(self._command("7,1,F")[0])

    def getServo(self):
        return [self._command("SERVO,X"), self._command("SERVO,Y")]

    def goAbsolute(self, x, y):
        self.sendCommand("G " + str(x * self.um_to_unit) + "," + str(y * self.um_to_unit))
        self.waitResponse()

    def goRelative(self, dx, dy):
        self.sendCommand("GR " + str(dx * self.um_to_unit) + "," + str(dy * self.um_to_unit))
        self.waitResponse()

    def info(self):
        return self._command("?")

    def jog(self, x_speed, y_speed):
        #print "VS {0:.1f},{1:.1f}".format(x_speed,y_speed)
        self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    def joystickOnOff(self, on):
        if on:
            self._command("J")
        else:
            self._command("H")
        
    def position(self):
        try:
            response = self._command("P")[0]
            [self.x, self.y, self.z] = map(int, response.split(","))
        except:
            print "  Bad position from Prior stage."
        return [self.x * self.unit_to_um, 
                self.y * self.unit_to_um, 
                self.z * self.unit_to_um]

    def setEncoderWindow(self, axis, window):
        assert window >= 0, "setEncoderWindow window is too smale " + str(window)
        assert window <= 4, "setEncoderWindow window is too large " + str(window)
        if axis == "X":
            self._command("ENCW X," + str(window))
        if axis == "Y":
            self._command("ENCW Y," + str(window))

    def setServo(self, servo):
        if servo:
            self._command("SERVO,1")
        else:
            self._command("SERVO,0")

    def state(self):
        response = self._command("#")[0]
        state = []
        for i in range(len(response)):
            if response[i] == "1":
                state.append("busy")
            else:
                state.append("idle")
        return state
        
    def zero(self):
        self._command("P 0,0,0")

    def zMoveTo(self, z):
        self._command("<V " + str(z))

    def zPosition(self):
        zpos = self._command("<PZ")
        return zpos[1:]


#
# Focus drive only.
#
class PriorFocus(Prior):
    def __init__(self, port = "COM1", timeout = None, baudrate = 9600):
        Prior.__init__(self, port = port, timeout = timeout, baudrate = baudrate)
        if not self.live:
            print "Failed to connect to Prior focus motor controller."

    def zMoveRelative(self, dz):
        self._command("U " + str(10.0 * dz))

    def zMoveTo(self, z):
        self._command("V " + str(10.0 * z))

    def zPosition(self):
        zpos = self._command("PZ")[0]
        return float(zpos) * 0.1

#
# Testing
# 

if __name__ == "__main__":
    if 1:
        stage = Prior(port = "COM9", baudrate = 115200)
        for info in stage.info():
            print info

        if 1:
            print stage.getServo()
            stage.setServo(True)
            print stage.getServo()

        if 0:
            stage.changeFilter(1)
            stage.getFilter()

        if 0:
            stage.zero()
            print stage.position()
            stage.goAbsolute(500, 500)
            print stage.position()
            stage.goAbsolute(0, 0)
            print stage.position()
            stage.goRelative(-500, -5000)
            print stage.position()
            stage.goAbsolute(0, 0)
            print stage.position()
        if 0:
            stage.zMoveTo(51.2)
            print stage.zPosition()
            stage.zMoveTo(50.0)
            print stage.zPosition()
    if 0:
        stage = PriorFocus(port = "COM1")
        for info in stage.info():
            print info

        stage.zMoveRelative(5.0)
        print stage.zPosition()
        stage.zMoveRelative(-5.0)
        print stage.zPosition()

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
