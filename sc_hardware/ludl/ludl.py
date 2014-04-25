#!/usr/bin/python
#
## @file
#
# Ludl stage communication.
#
# Hazen 02/14
#

import sc_hardware.serial.RS232 as RS232
import time


## Ludl
#
# Encapsulates control of a XY Ludl stage.
#
class Ludl(RS232.RS232):

    ## __init__
    #
    # @param port (Optional) The RS-232 port to use, defaults to "COM2".
    # @param timeout (Optional) The time out value for communication, defaults to None.
    # @param baudrate (Optional) The communication baud rate, defaults to 9600.
    # @param wait_time How long to wait between polling events before it is decided that there is no new data available on the port, defaults to 20ms.
    #
    def __init__(self, port, timeout = None, baudrate = 9600, wait_time = 0.02):
        self.unit_to_um = 0.2
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0

        # RS232 stuff
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r", wait_time)

        try:
            test = self.commWithResp("Ver")
        except:
            self.live = False
        if not self.live:
            print "Ludl Stage is not connected? Stage is not on?"

    ## _command
    #
    # @param command The command string to send.
    #
    # @return The response to the command.
    #
    def _command(self, command):
        response = self.commWithResp(command)
        if response:
            return response.split("\r")

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.live
        
    ## goAbsolute
    #
    # @param x X position in um.
    # @param y Y position in um.
    #
    def goAbsolute(self, x, y):
        newx = str(round(x * self.um_to_unit))
        newy = str(round(y * self.um_to_unit))
        self.sendCommand("Move x=" + newx)
        self.sendCommand("Move y=" + newy)
        self.waitResponse()

    ## goRelative
    #
    # @param dx Amount to move in x in um.
    # @param dy Amount to move in y in um.
    #
    def goRelative(self, dx, dy):
        newx = str(round(dx * self.um_to_unit))
        newy = str(round(dy * self.um_to_unit))
        self.sendCommand("Movrel x=" + newx)
        self.sendCommand("Movrel y=" + newy)
        self.waitResponse()

    ## info
    #
    # @return Some information about the stage.
    #
    def info(self):
        return self._command("Ver")

    ## jog
    #
    # @param x_speed Speed the stage should be moving at in x in um/s.
    # @param y_speed Speed the stage should be moving at in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        #print "VS {0:.1f},{1:.1f}".format(x_speed,y_speed)
        self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the stage joystick.
    #
    def joystickOnOff(self, on):
        if on:
            self._command("Joystick X+ Y+")
        else:
            self._command("Joystick X- Y-")
     
    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)].
    #
    def position(self):
#        try:
        self.x = float(self._command("Where X")[0].split(" ")[1])
        self.y = float(self._command("Where Y")[0].split(" ")[1])
#            [self.x, self.y, self.z] = map(int, response.split(","))
#        except:
#            pass
        return [self.x * self.unit_to_um,
                self.y * self.unit_to_um,
                0.0]

    ## setVelocity
    #
    # @param x_vel The maximum stage velocity allowed in x in Ludl units.
    # @param y_vel The maximum stage velocity allowed in y in Ludl units.
    #
    def setVelocity(self, x_vel, y_vel):
        self._command("Speed x=" + str(x_vel))
        self._command("Speed y=" + str(y_vel))

    ## zero
    #
    # Set the current position as the stage zero position.
    #
    def zero(self):
        self._command("Here x=0 y=0")


#
# Testing
# 

if __name__ == "__main__":
    stage = Ludl("COM1")
    print stage.position()
    stage.zero()
    time.sleep(0.1)
    print stage.position()
    stage.goRelative(100.0, 100.0)
    time.sleep(0.1)
    print stage.position()
    stage.shutDown()

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
