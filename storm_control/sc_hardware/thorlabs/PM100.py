#!/usr/bin/python
#
## @file
#
# Communicates with a Thorlabs PM-100 power 
# meter attached to COM1.
#
# Hazen 2/09
#

import lib.RS232 as RS232

## powerMeter
#
# Encapsulates RS-232 based communication with a Thorlabs power meter.
#
class powerMeter(RS232.RS232):

    ## __init__
    #
    # @param port (Optional) the default is COM1.
    # @param timeout (Optional) the default is none.
    # @param baudrate (Optional) the default is 57600.
    #
    def __init__(self, port = "COM1", timeout = None, baudrate = 57600):
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r\n", 0.1)
        test = self.commWithResp("*IDN?")
        assert test, "Power meter is not connected? Not set to " + str(baudrate) + " baudrate?"

    ## id
    #
    # @return The power meter id.
    #
    def id(self):
        try:
            return self.commWithResp("*IDN?")
        except:
            print "powerMeter.id failed"
            return 0.0

    ## power
    #
    # @return The current power reading.
    #
    def power(self):
        try:
            self.sendCommand(":POWER?")
            return self.waitResponse()[:-2]
#            return float(self.commWithResp(":POWER?"))
        except:
            print "powerMeter.power failed"
            return 0.0

    ## wavelength
    #
    # @return The current power meter wavelength.
    #
    def wavelength(self):
        try:
            self.sendCommand(":WAVELENGTH?")
            return self.waitResponse()[:-2]
#            return float(self.commWithResp(":WAVELENGTH?"))
        except:
            print "powerMeter.wavelength failed"
            return 0.0


#
# Testing
# 

if __name__ == "__main__":
    pm100 = powerMeter()
    if 1:
        print pm100.id()
        print pm100.wavelength()
        for i in range(5):
            print pm100.power()

    if 0:
        import time
        fp = open("powerlog.txt", "w")
        for i in range(20*60):
            power = pm100.power()
            print i, power
            fp.write(str(i) + " " + str(power) + "\n")
            time.sleep(1)
        fp.close()

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
