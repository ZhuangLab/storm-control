#!/usr/bin/python
#
# Innova 70C laser control.
#
# Hazen 4/09
#

import halLib.RS232 as RS232

class Innova70C(RS232.RS232):
    def __init__(self, port = "COM4"):
        self.last_light = 0.0

        # open port
        RS232.RS232.__init__(self, port, None, 1200, "\r\n", 0.05)

        # check ID
        laser_id = self.getId()
        if laser_id != "I70":
            print "Innova I70 is not on? Is not connected?"
            print "Keyspan COM ports are scrambled?"
            self.live = 0

    def _commandWithResponse(self, command):
        if self.live:
            self.sendCommand(command)
            return self.waitResponse()[:-2]
        else:
            return 0

    def getCurrent(self):
        try:
            return float(self._commandWithResponse("? CURRENT"))
        except:
            return 0.0

    def getHours(self):
        try:
            return float(self._commandWithResponse("? HOURS"))
        except:
            return 0.0

    def getId(self):
        try:
            return self._commandWithResponse("? ID")
        except:
            return 0.0

    def getLaserOnOff(self):
        on_off = int(self._commandWithResponse("? LASER"))
        if on_off == 0:
            return 0
        else:
            return 1

    def getLight(self):
        light = self._commandWithResponse("? LIGHT")
        if (type(light) == type("")) and (len(light) > 1):
            self.last_light = light
            return float(light)
        else:
            return self.last_light

    def getTemperature(self):
        try:
            return float(self._commandWithResponse("? WATER TEMPERATURE"))
        except:
            return 0.0

    def setLaserCurrent(self, current):
        if (current >= 20.0) and (current <= 40.0):
            self.sendCommand("CURRENT=" + str(current))
        else:
            print "Current out of range. Current must be between 22 and 40 Amps."

    def setLaserOff(self):
        if self.getLaserOnOff():
            self.sendCommand("LASER=0")

    def setLaserOn(self):
        if self.getLaserOnOff():
            self.sendCommand("LASER=1")



#
# Testing
#

if __name__ == "__main__":
    innova = Innova70C()
    print innova.getId()
    print innova.getLaserOnOff()
    print innova.getHours()
    print innova.getLight()
    print innova.getTemperature()

#    innova.setLaserOn()
#    innova.getLaserOnOff()
#    innova.setLaserCurrent(24.0)

#    if innova.getStatus():
#        print cube.getPowerRange()
#        print cube.getLaserOnOff()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

