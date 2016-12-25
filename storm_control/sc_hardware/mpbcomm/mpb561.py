#!/usr/bin/python
#
## @file
#
# MPB 561 fiber laser control.
#
# Hazen 9/10
#

import sc_hardware.serial.RS232 as RS232
import time

## MPB561
#
# RS-232 control of a MPB laser, nominally 561, but I think
# this would work with any of their lasers.
#
# This is not actually used, we usually just use the interface
# that MPB provides.
#
class MPB561(RS232.RS232):

    ## __init__
    #
    # @param port A com port name such as "COM1"
    #
    def __init__(self, port):
        try:
            # open port
            RS232.RS232.__init__(self, port, None, 9600, "\r", 0.05)        
            # check for laser problems
            assert self.getStatus()
        except:
            self.live = 0
            print "Failed to connect to the MPB 561 laser at port", port
            print "Perhaps it is turned off or the COM ports have"
            print "been scrambled?"

    ## getCurrent
    #
    # @return The laser current.
    #
    def getCurrent(self):
        resp = self.commWithResp("ldcurrent 1")
        if resp:
            curr_as_text = resp.split(self.end_of_line)[1].split(">")[1]
            return float(curr_as_text)
        return 0.0

    ## getStatus
    #
    # @return True/False the laser is powered on.
    #
    def getStatus(self):
        resp = self.commWithResp("shfault").split(self.end_of_line)
        for res in resp:
            if res.count("1"):
                print res
                return False
        return True

    ## setPower
    #
    # @param power_in_mW The desired laser power in mW.
    #
    def setPower(self, power_in_mW):
        comm = "setpower 0 " + str(round(power_in_mW))
        self.sendCommand(comm)

    ## powerOn
    #
    # Turn on the laser and set the output power.
    #
    # @param power_in_mW The desired laser power in mW.
    #
    def powerOn(self, power_in_mW):
        self.sendCommand("setldenable 1")
        self.sendCommand("powerenable 1")
        self.setPower(power_in_mW)

    ## powerOff
    #
    # Turn off the laser.
    #
    def powerOff(self):
        self.sendCommand("setldenable 0")
        # clear command buffer
        resp = self.getResponse()
        if resp:
            for res in resp.split(self.end_of_line):
                print res

#
# Testing
#

if __name__ == "__main__":
    mpb561 = MPB561("COM6")
    if mpb561.live:
        mpb561.powerOn(10)
        power = 20
        for i in range(50):
            time.sleep(0.5)
            mpb561.setPower(power)
            print power, ":", mpb561.getCurrent(), "mA"
            power += 10
        mpb561.powerOff()

#    if cube.getStatus():
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

