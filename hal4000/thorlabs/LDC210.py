#!/usr/bin/python
#
# LDC210 diode laser driver on/off control
#
# Hazen 04/12
#

import sys
import time

try:
    import nationalInstruments.nicontrol as nicontrol
except:
    sys.path.append("..")
    import nationalInstruments.nicontrol as nicontrol

#
# Turn on/off with a digital line connected to the
# TTL input of the laser diode controller.
#
class LDC210():
    def __init__(self, board, line):
        self.board = board
        self.line = line

    def havePowerControl(self):
        return False

    def on(self, dummy):
        nicontrol.setDigitalLine(self.board, self.line, True)

    def off(self):
        nicontrol.setDigitalLine(self.board, self.line, False)

#
# Turn on/off with a counter connected to the analog
# modulation input. This also lets you control the power.
#
# National Instruments version
#
class LDC210PWMNI():
    def __init__(self, board, line, frequency = 50000):

        self.am_on = False
        self.board = board
        self.ct_task = None
        self.frequency = frequency
        self.line = line

    def havePowerControl(self):
        return True

    # power is an integer between 0 and 100
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

    def off(self):
        if self.am_on:
            self.ct_task.stopTask()
            self.ct_task.clearTask()
            self.am_on = False


#
# Turn on/off with a counter connected to the analog
# modulation input. This also lets you control the power.
#
# Labjack U3 version.
#
class LDC210PWMLJ():
    def __init__(self):

        try:
            import labjack.labjack_u3 as labjack_u3
        except:
            sys.path.append("..")
            import labjack.labjack_u3 as labjack_u3

        self.am_on = False
        self.dev = labjack_u3.PWM()

    def havePowerControl(self):
        return True

    # power is an integer between 0 and 100
    def on(self, power):
        self.dev.startPWM(power)
        self.am_on = True

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
