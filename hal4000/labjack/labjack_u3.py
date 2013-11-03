#!/usr/bin/python
#
## @file
#
# Labjack U3 Interface.
# Everything happens on the FIO4 pin.
#
# Hazen 5/12
#

import u3
import time

## PWM
#
# This class encapsulates using a Labjack for PWM modulation on the FIO4 pin.
#
class PWM():

    ## __init__
    #
    # Try to connect to the Labjack & configure the FIO4 pin.
    #
    def __init__(self):
        self.live = True
        try:
            self.device = u3.U3()
        except:
            self.live = False
        if not self.live:
            print "Could not connect to Labjack, reset by unplugging / plugging the USB connection"
        else:
            self.device.writeRegister(6004,0) # set FIO4 state to low.
            self.device.configTimerClock(TimerClockBase = 5, TimerClockDivisor = 1)

    ## shutDown
    #
    # Close the connection to the Labjack when the program exits.
    #
    def shutDown(self):
        if self.live:
            self.device.close()

    ## startPWM
    #
    # Start PWM modulation of pin FIO4.
    #
    # @param duty_cycle The PWM duty cycle (0 - 100).
    #
    def startPWM(self, duty_cycle):
        if self.live:
            temp = 65535 - 256*duty_cycle
            self.device.configIO(NumberOfTimersEnabled = 1)
            self.device.getFeedback(u3.Timer0Config(TimerMode = 1, Value = 65535))
            self.device.getFeedback(u3.Timer0(Value = temp, UpdateReset = True))
        else:
            print "duty cycle:", duty_cycle

    ## stopPWM
    #
    # Stop PWM modulation of pin FIO4.
    #
    def stopPWM(self):
        if self.live:
            #self.device.getFeedback(u3.Timer0(Value = 65535, UpdateReset = True))
            self.device.configIO(NumberOfTimersEnabled = 0)

#
# Testing
#

if __name__ == "__main__":
    dev = PWM()
    for i in range(10):
        print i
        dev.startPWM(i)
        time.sleep(2)
    print "stopping"
    dev.stopPWM()
    time.sleep(5)
    print "shutdown"
    dev.shutDown()


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

