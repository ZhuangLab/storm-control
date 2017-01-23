#!/usr/bin/python
#
## @file
#
# Communicates with the Newport SMC100 motor controller.
#
# Hazen 2/11
#

import time

import storm_control.sc_hardware.serial.RS232 as RS232

## SMC100
#
# Encapsulates control of Newport SMC100 motor controller using RS-232.
#
class SMC100(RS232.RS232):

    ## __init__
    #
    # @param id (Optional) The id of the motor controller (integer), defaults to 1.
    # @param port (Optional) The RS-232 port to use, defaults to "COM5".
    # @param timeout (Optional) The time to wait for a response, defaults to None.
    # @param baudrate (Optional) The baud rate of the port, defaults to 57600.
    #
    def __init__(self, id = 1, port = "COM5", timeout = None, baudrate = 57600):
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r\n", 0.1)
        self.id = str(id)
        try:
            # check if we are referenced
            if self.amNotReferenced():
                print "SMC100 homing."
                # reference
                self.commWithResp(self.id + "OR")
                # wait until homed
                while self.amHoming():
                    time.sleep(1)
        except:
            print "SMC100 controller is not responding."
            print "Perhaps it is not turned on, or the Keyspan COM ports have been scrambled."
            self.live = 0

    ## _compose
    #
    # Combines the command with the id of the motor controller.
    #
    # @param command A command (as a string).
    #
    def _compose(self, command):
        return self.id + command

    ## _command
    #
    # Send the command, return the response.
    #
    # @param command A command (as a string)
    #
    # @return The response from the controller.
    #
    def _command(self, command):
        if self.live:
            self.sendCommand(self._compose(command))
            return self.waitResponse()[:-2]

    ## amHoming
    #
    # @return 1/0 If the stage is currently homing.
    #
    def amHoming(self):
        self.state = self._command("TS")
        if self.state == (self.id + "TS00001E"):
            return 1
        else:
            return 0

    ## amMoving
    #
    # @return 1/0 If the stage is moving.
    #
    def amMoving(self):
        self.state = self._command("TS")
        if self.state == (self.id + "TS000028"):
            return 1
        else:
            return 0

    ## amNotReferenced
    #
    # @return 1/0 The stage has not been homed.
    #
    def amNotReferenced(self):
        self.state = self._command("TS")
        assert len(self.state) == len(self.id + "TS00000A"), "SMC100 controller not responding."
        if self.state == (self.id + "TS00000A"):
            return 1
        else:
            return 0

    ## getPosition
    #
    # @return The current stage position.
    #
    def getPosition(self):
        try:
            return float(self._command("TP")[3:])
        except:
            return -1.0

    ## moveTo
    #
    # @param position The position to move to.
    #
    def moveTo(self, position):
        self.position = position
        self.commWithResp(self.id + "PA"+str(self.position))
        error = self._command("TE")
        if not (error == (self.id + "TE@")):
            print "SMC100 motion error:", error
        self.position = float(self._command("TP")[3:])

    ## stopMove
    #
    # Tell the stage to stop motion.
    #
    def stopMove(self):
        if self.amMoving():
            self.sendCommand("ST")

#
# Testing
# 

if __name__ == "__main__":
    smc100 = SMC100(id = 3)
    pos = smc100.getPosition()
    print pos
    print smc100._command("TE")
    print smc100._command("TS")
    smc100.moveTo(0.0)
    smc100.shutDown()

#
#    Copyright (C) 2011  Hazen Babcock
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
