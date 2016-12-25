#!/usr/bin/python
#
## @file
#
# LDC210 diode laser driver on/off control
#
# Hazen 04/12
#

import sys
import time


import sc_hardware.nationalInstruments.nicontrol as nicontrol

## LDC210
#
# Turn on/off with a digital line connected to the
# TTL input of the laser diode controller.
#
class LDC210():
    
    ## __init__
    #
    # @param board The DAQ board name.
    # @param line The DAQ board line.
    #
    def __init__(self, board, line):
        self.board = board
        self.line = line

    ## havePowerControl
    #
    # @return False
    #
    def havePowerControl(self):
        return False

    ## on
    #
    # Turn on the laser by setting the DAQ line high.
    #
    # @param dummy Not used.
    #
    def on(self, dummy):
        nicontrol.setDigitalLine(self.board, self.line, True)

    ## off
    #
    # Turn off the laser by setting the DAQ line low.
    #
    def off(self):
        nicontrol.setDigitalLine(self.board, self.line, False)

## LDC210PWMNI
#
# Turn on/off with a counter connected to the analog
# modulation input. This also lets you control the power.
#
# National Instruments version.
#
class LDC210PWMNI():

    ## __init__
    #
    # @param board The DAQ board name.
    # @param line The DAQ board line.
    # @param frequency (Optional) The pulse width modulation wave form frequency, defaults to 50kHz.
    #
    def __init__(self, board, line, frequency = 50000):

        self.am_on = False
        self.board = board
        self.ct_task = None
        self.frequency = frequency
        self.line = line

    ## havePowerControl
    #
    # @return True
    #
    def havePowerControl(self):
        return True

    ## on
    #
    # Turn on the laser by starting the counter that will generate the PWM wave form
    # and setting the duty cycle to be > 0. 
    #
    # @param power An integer between 0 and 100.
    #
    def on(self, power):
        duty_cycle = float(power)*0.01
        if (duty_cycle < 0.0):
            duty_cycle = 0.0
        if (duty_cycle > 1.0):
            duty_cycle = 1.0
        self.ct_task = nicontrol.CounterOutput(self.board,
                                               self.line,
                                               self.frequency,
                                               duty_cycle)
        self.ct_task.setCounter(-1)
        self.ct_task.startTask()
        self.am_on = True

    ## off
    #
    # Stop the counter, turning off the laser.
    #
    def off(self):
        if self.am_on:
            self.ct_task.stopTask()
            self.ct_task.clearTask()
            self.am_on = False


## LDC210PWMLJ
#
# Turn on/off with a counter connected to the analog
# modulation input. This also lets you control the power.
#
# Labjack U3 version.
#
class LDC210PWMLJ():

    ## __init__
    #
    # Connect to the labjack DAQ device.
    #
    def __init__(self):
        
        import sc_hardware.labjack.labjack_u3 as labjack_u3

        self.am_on = False
        self.dev = labjack_u3.PWM()

    ## havePowerControl
    #
    # @return True
    #
    def havePowerControl(self):
        return True

    ## on
    #
    # Start generating a pulse width modulation square wave.
    #
    # param power An integer between 0 and 100.
    #
    def on(self, power):
        self.dev.startPWM(power)
        self.am_on = True

    ## off
    #
    # Stop generating the PWM square wave.
    #
    def off(self):
        if self.am_on:
            self.dev.stopPWM()
            self.am_on = False


if __name__ == "__main__":
    if 0:
        ldc = LDC210("PCI-6733", 7)
        ldc.on()
        time.sleep(1)
        ldc.off()

    if 0:
        ct_task = nicontrol.CounterOutput("PCI-6733", 0, 100, 0.5)
        ct_task.setCounter(100)
        ct_task.setTrigger(0)
        ct_task.startTask()
        ldc = LDC210PWMNI("PCI-6733", 1)
        ldc.on(7)
        time.sleep(5)
        ldc.off()
        ct_task.stopTask()
        ct_task.clearTask()

    if 1:
        ldc = LDC210PWMLJ()
        ldc.on(10)
        time.sleep(5)
        ldc.off()

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
