#!/usr/bin/python
#
## @file
#
# Innova 70C laser control using RS-232.
#
# Hazen 4/09
#

import storm_control.sc_hardware.serial.RS232 as RS232

## Innova70C
#
# This controls a Innova70C laser using RS-232 communication.
#
class Innova70C(RS232.RS232):

    ## __init__
    #
    # Initiate RS-232 communication, verify that the laser is responding.
    #
    # @param port (Optional) A string that specifies the port, the default is "COM4".
    #
    def __init__(self, port = "COM4"):
        self.last_light = 0.0

        # open port
        RS232.RS232.__init__(self, port, None, 1200, "\r\n", 0.05)

        # check ID
        laser_id = self.getId()
        if laser_id != "I70":
            print "Innova I70 is not on? Is not connected?"
            print "Keyspan COM ports are scrambled?"
            self.live = False

    ## _commandWithResponse
    #
    # Sends a command & waits for a response to return. Returns 0 if the
    # laser is not responding.
    #
    # @param command The command to send.
    #
    # @return The response or 0.
    #
    def _commandWithResponse(self, command):
        if self.live:
            self.sendCommand(command)
            return self.waitResponse()[:-2]
        else:
            return 0

    ## getCurrent
    #
    # @return The laser current.
    #
    def getCurrent(self):
        try:
            return float(self._commandWithResponse("? CURRENT"))
        except:
            return 0.0

    ## getHours
    #
    # @return The laser hours
    #
    def getHours(self):
        try:
            return float(self._commandWithResponse("? HOURS"))
        except:
            return 0.0

    ## getId
    #
    # @return The laser ID.
    #
    def getId(self):
        try:
            return self._commandWithResponse("? ID")
        except:
            return 0.0

    ## getLaserOnOff
    #
    # @return True/False the laser is on/off.
    #
    def getLaserOnOff(self):
        on_off = int(self._commandWithResponse("? LASER"))
        if (on_off == 0):
            return False
        else:
            return True

    ## getLight
    #
    # @return The amount of light the laser is outputting (in Watts?).
    #
    def getLight(self):
        light = self._commandWithResponse("? LIGHT")
        if (type(light) == type("")) and (len(light) > 1):
            self.last_light = light
            return float(light)
        else:
            return self.last_light

    ## getTemperature
    #
    # @return The current water temperature of the laser.
    #
    def getTemperature(self):
        try:
            return float(self._commandWithResponse("? WATER TEMPERATURE"))
        except:
            return 0.0

    ## setLaserCurrent
    #
    # Sets the laser current to the desired value (in amps).
    #
    # @param current The desired current in amps.
    #
    def setLaserCurrent(self, current):
        if (current >= 20.0) and (current <= 40.0):
            self.sendCommand("CURRENT=" + str(current))
        else:
            print "Current out of range. Current must be between 22 and 40 Amps."

    ## setLaserOff
    #
    # Turn the laser off (i.e. make it stop lasing).
    #
    def setLaserOff(self):
        if self.getLaserOnOff():
            self.sendCommand("LASER=0")

    ## setLaserOn
    #
    # Turn the laser on (i.e. make it start lasing).
    #
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

