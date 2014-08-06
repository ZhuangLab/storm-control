#!/usr/bin/python
#
## @file
#
# RS232 interface to a Applied Scientific Instrumentation MS2000 stage.
#
# Hazen 06/14
#

import sys
import time

import sc_library.hdebug as hdebug

import sc_hardware.serial.RS232 as RS232


## MS2000
#
# Applied Scientific Instrumentation MS2000 RS232 interface class.
#
class MS2000(RS232.RS232):

    ## __init__
    #
    # Connect to the MS2000 stage at the specified port.
    #
    # @param port The RS-232 port name (e.g. "COM1").
    # @param wait_time (Optional) How long (in seconds) for a response from the stage.
    #
    def __init__(self, port, wait_time = 0.05):

        self.live = True
        self.unit_to_um = 0.1
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0

        # RS232 stuff
        RS232.RS232.__init__(self, port, None, 115200, "\r", wait_time)
        try:
            test = self.commWithResp("INFO X")
            if not test:
                self.live = False
        except:
            self.live = False
        if not self.live:
            print "ASI Stage is not connected? Stage is not on?"

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.live

    ## goAbsolute
    #
    # @param x Stage x position in um.
    # @param y Stage y position in um.
    #
    def goAbsolute(self, x, y):
        if self.live:
            X = x * self.um_to_unit
            Y = y * self.um_to_unit
            self.commWithResp("M X=" + str(X) + " Y=" + str(Y))

    ## goRelative
    #
    # @param x Amount to move the stage in x in um.
    # @param y Amount to move the stage in y in um.
    #
    def goRelative(self, x, y):
        if self.live:
            X = x * self.um_to_unit
            Y = y * self.um_to_unit
            self.commWithResp("R X=" + str(X) + " Y=" + str(Y))

    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
#        if self.live:
#            vx = x_speed * 0.001
#            vy = y_speed * 0.001
#            self.commWithResp("S X=" + str(vx) + " Y=" + str(vy))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        pass
        #if self.live:
        #    if on:
        #        self.commWithResp("!joy 2")
        #    else:
        #        self.commWithResp("!joy 0")

    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def position(self):
        if self.live:
            try:
                [self.x, self.y] = map(lambda x: float(x)*self.unit_to_um, 
                                       self.commWithResp("W X Y").split(" ")[1:3])
            except:
                hdebug.logText("  Warning: Bad position from ASI stage.")
            return [self.x, self.y, 0.0]
        else:
            return [0.0, 0.0, 0.0]

    ## setVelocity
    #
    # @param x_vel Maximum velocity to move in x.
    # @param y_vel Maximum velocity to move in y.
    #
    def setVelocity(self, x_vel, y_vel):
        if self.live:
            vx = x_vel
            vy = y_vel
            self.commWithResp("S X=" + str(vx) + " Y=" + str(vy))

    ## zero
    #
    # Set the current stage position as the stage zero.
    #
    def zero(self):
        if self.live:
            self.commWithResp("Z")



#
# Testing
# 

if __name__ == "__main__":
    stage = MS2000("COM3")
    print stage.position()

    #print stage.commWithResp("W X Y")
    #stage.goAbsolute(100.0, 100.0)
    #time.sleep(5)
    #print stage.position()
    #stage.goAbsolute(0.0, 0.0)
    #time.sleep(5)
    #print stage.position()

    #print "SN:", stage.serialNumber()
    #stage.zero()
    #print "Position:", stage.position()
    #stage.goAbsolute(100.0, 100.0)
    #print "Position:", stage.position()
    #stage.goRelative(100.0, 100.0)
    #print "Position:", stage.position()
    stage.shutDown()

#    for info in stage.info():
#        print info
#    stage.zero()
#    print stage.position()
#    stage.goAbsolute(100000,100000)
#    print stage.position()
#    stage.goAbsolute(0,0)
#    print stage.position()
#    stage.goRelative(-100000,-100000)
#    print stage.position()
#    stage.goAbsolute(0,0)
#    print stage.position()


#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
