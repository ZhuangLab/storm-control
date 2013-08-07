#!/usr/bin/python
#
# Thorlabs FW102C control.
#
# Hazen 5/12 (Josh 6/26/2013)
#

import halLib.RS232 as RS232


class FW102C(RS232.RS232):
    def __init__(self, port = "COM14"): # changed to "COM14" (was "COM5" before), Josh 6/26/13"
        self.on = False
        try:
            # open port
            RS232.RS232.__init__(self, port, None, 115200, "\r", 0.05)

            # see if the filter wheel is connected
            assert not(self.getID() == None)

        except:
            self.live = False
            print "Failed to connect to the FW102C filter wheel at port", port
            print "Perhaps it is turned off or the COM ports have been scrambled?"

    def getID(self):
        return self.commWithResp("*idn?")

    def getPositionCount(self):
        print self.sendCommand("baud?")
        print self.waitResponse()

    def setHighSpeedMode(self, on):
        if on:
            self.sendCommand("speed=1")
        else:
            self.sendCommand("speed=0")
        print self.waitResponse()

    def setPosition(self, position):
        if (position < 1):
            position = 1
        if (position > 6):
            position = 6
        self.sendCommand("pos=" + str(position))
        self.waitResponse()

    def setSensorMode(self, on):
        if on:
            self.sendCommand("sensors=0")
        else:
            self.sendCommand("sensors=1")

    def shutDown(self):
        RS232.RS232.shutDown(self)


#
# Testing
#

if __name__ == "__main__":
    fwheel = FW102C()
    print fwheel.getID()
    print fwheel.setPosition(1)
    print fwheel.setPosition(3)
    fwheel.shutDown()


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

