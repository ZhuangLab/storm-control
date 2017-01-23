#!/usr/bin/python
#
## @file
#
# Compass 315M laser control. This is done via a
# National Instruments card as this laser does
# not come with any more sophisticated interface.
#
# Hazen 4/09
#

import sys
import time


import storm_control.sc_hardware.nationalInstruments.nicontrol as nicontrol

## Compass315M
#
# This class encapsulates controlling a Coherent Compass315M
# laser using a National Instruments DAQ board.
#
class Compass315M():

    ## __init__
    #
    # Set up the necessary NI tasks to control the laser.
    #
    # @param board The name of the NI board to use.
    #
    def __init__(self, board = "PCI-MIO-16E-4"):
        self.interlock = nicontrol.DigitalOutput(board, 0)
        self.laser_on_off = nicontrol.DigitalOutput(board, 1)
        self.power_on_off = nicontrol.DigitalOutput(board, 2)
        self.laser_on_off_status = nicontrol.DigitalInput(board, 4)
        self.power_on_off_status = nicontrol.DigitalInput(board, 5)
        self.enter = nicontrol.DigitalOutput(board, 3)
        self.laser_set_point = nicontrol.VoltageOutput(board, 0, min_val = 0.0, max_val = 5.0)

    ## setPower
    #
    # Set the laser power.
    #
    # @param power The laser power (0.0 - 1.0).
    #
    def setPower(self, power):
        if (power >= 0.0) and (power <= 1.0):
            self.laser_set_point.outputVoltage(5.0 * power)
            time.sleep(0.05)
            self.enter.output(0)
            time.sleep(0.01)
            self.enter.output(1)
        else:
            print power, "out of range."

    ## start
    #
    # Turn the laser on at the specified power.
    #
    # @param power The initial laser power (0.0 - 1.0)
    #
    def start(self, power):
        if self.laser_on_off_status.input():
            self.setPower(power)
        else:
            self.interlock.output(1)
            time.sleep(0.2)
            self.setPower(power)
            time.sleep(0.05)
            self.power_on_off.output(1)
            time.sleep(0.05)
            self.laser_on_off.output(1)

    ## stop
    #
    # Turn the laser off.
    #
    def stop(self):
        self.enter.output(0)
        self.laser_set_point.outputVoltage(0.0)
        self.laser_on_off.output(0)
        time.sleep(0.05)
        self.power_on_off.output(0)
        time.sleep(0.05)
        self.interlock.output(0)


#
# Testing
#

if __name__ == "__main__":
    compass = Compass315M()
    print compass.laser_on_off_status.input()
    print compass.power_on_off_status.input()
    compass.start(0.2)
    time.sleep(30)
    print compass.laser_on_off_status.input()
    print compass.power_on_off_status.input()
#    compass.stop()

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

