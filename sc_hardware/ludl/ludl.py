#!/usr/bin/python
#
## @file
#
# Ludl stage communication.
#
# Hazen 02/14
#
# Edited 5/15 to add Z piezo and TCP/IP protocol
# George Emanuel 5/15

import sc_hardware.serial.RS232 as RS232
import time

import httplib

ludlStage = None

def getLudlStage(port = "COM17"):
    global ludlStage
    if not ludlStage:
	ludlStage = Ludl(port)
    return ludlStage



## Ludl
#
# Encapsulates control of a XY Ludl stage, communicating through serial.
#
class Ludl(RS232.RS232):

    ## __init__
    #
    # @param port (Optional) The RS-232 port to use, defaults to "COM5".
    # @param timeout (Optional) The time out value for communication, defaults to None.
    # @param baudrate (Optional) The communication baud rate, defaults to 115200.
    # @param wait_time How long to wait between polling events before it is decided that there is no new data available on the port, defaults to 20ms.
    #
    def __init__(self, port="COM17", timeout = None, baudrate = 115200, wait_time = 0.02):
        self.unit_to_um = 0.2
        self.um_to_unit = 1.0/self.unit_to_um

        # RS232 stuff
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r", wait_time)

	self.live = True
        try:
            test = self.commWithResp("Ver")
        except:
            self.live = False
        if not self.live:
            print "Ludl Stage is not connected? Stage is not on?"

	#Set to analog mode?
	if (self.live):
	    self._command("CAN 3, 83, 267, 0")
	    self._command("stspeed x=500, y=500")
	    self._command("speed x=1000, y=1000")

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

    ## _commandIgnoreResponse
    # @Override
    #
    # @param command The command string to send
    #
    def _commandIgnoreResponse(self, command):
	self.sendCommand(command)

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
        newx = str(int(round(x * self.um_to_unit)))
        newy = str(int(round(y * self.um_to_unit)))
        self._commandIgnoreResponse("Move x=" + newx)
	self._commandIgnoreResponse("Move y=" + newy)

    ## goRelative
    #
    # @param dx Amount to move in x in um.
    # @param dy Amount to move in y in um.
    #
    def goRelative(self, dx, dy):
        newx = str(int(round(dx * self.um_to_unit)))
        newy = str(int(round(dy * self.um_to_unit)))
        self._commandIgnoreResponse("Movrel x=" + newx + ",y="+newy)

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
	print 'not implemented for Ludl stage'
        #print "VS {0:.1f},{1:.1f}".format(x_speed,y_speed)
        #self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the stage joystick.
    #
    def joystickOnOff(self, on):
        if on:
            self._commandIgnoreResponse("Joystick X+ Y+")
        else:
            self._commandIgnoreResponse("Joystick X- Y-")
     
    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)].
    #
    def position(self):
	response = self._command("WHERE X Y B")[0].split(" ")
	try:
	    x = int(response[1]) * self.unit_to_um
	    y = int(response[2]) * self.unit_to_um
	    z = int(response[3]) * self.unit_to_um
	except:
            x = int(response[2]) * self.unit_to_um
	    y = int(response[3]) * self.unit_to_um
	    z = int(response[4]) * self.unit_to_um

        return [x, y, z]

    ## setVelocity
    #
    # @param x_vel The maximum stage velocity allowed in x in Ludl units.
    # @param y_vel The maximum stage velocity allowed in y in Ludl units.
    #
    def setVelocity(self, x_vel, y_vel):
        self._commandIgnoreResponse("Speed x=" + str(x_vel) + ",y=str(y_vel)")

    ## zero
    #
    # Set the current position as the stage zero position.
    #
    def zero(self):
        self._commandIgnoreResponse("Here x=0 y=0 b=0")

    ## zMoveTo
    #
    # @param z The z value to move to the (piezo) stage to, in microns.
    #
    def zMoveTo(self, z):
        self._commandIgnoreResponse("Move B=" + str(int(round(z * self.um_to_unit))))

    ## zMoveRelative
    #
    # @param dz Amount to move piezo (in um).
    #
    def zMoveRelative(self, dz):
        self._commandIgnoreResponse("Moverel B=" + str(int(round(dz * self.um_to_unit))))

    ## zPosition
    #
    # @return The current z position of the (piezo) stage, in microns.
    def zPosition(self):
        return int(self._command("WHERE B")[0].split(" ")[1])*self.unit_to_um

## LudlTCP
#
# Encapsulates control of a XY Ludl stage, communicating through TCP/IP.
# Ideally this should be done through a more abstract Ludl class, not
# one that already communicates through serial, but I don't want to break
# other code.
#
class LudlTCP(Ludl):

    ## __init__
    #
    # @param ipAddress (Optional) The IP address, defaults to "192.168.100.1"
    #
    def __init__(self, ipAddress="192.168.100.1"):
        self.unit_to_um = 0.05 
        self.um_to_unit = 1.0/self.unit_to_um

	self.connection = httplib.HTTPConnection(ipAddress, timeout=1)

	self.live = True
        try:
            test = self._command("Ver")
        except:
            self.live = False
        if not self.live:
            print "Ludl Stage is not connected? Stage is not on?"

	#Set to analog mode?
	if (self.live):
	    self._commandIgnoreResponse("CAN 3, 83, 267, 0")
	    self._commandIgnoreResponse("stspeed x=50000, y=50000")

    ## _command
    # @Override
    #
    # @param command The command string to send.
    #
    # @return The response to the command.
    #
    def _command(self, command):
	formCommand = "/conajx.asp?&ECMD1=\"" + command + "\""
	self.connection.request("GET", "/conajx.asp?&ECMD1=\"" + command + "\"")
	response = self.connection.getresponse().read().split("\r")[2].strip()

	return ["A: " + response]

    ## _commandIgnoreResponse
    # @Override
    #
    # @param command The command string to send
    #
    def _commandIgnoreResponse(self, command):
	t = time.time()
	self.connection.request("GET", "/conajx.asp?&ECMD1=\"" + command+ "\"")
	self.connection.getresponse().read()


#
# Testing
# 

if __name__ == "__main__":
    stage = Ludl("COM5")
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
