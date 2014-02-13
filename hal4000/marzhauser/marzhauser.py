#!/usr/bin/python
#
## @file
#
# ctypes or RS232 interface to a Marzhauser stage.
#
# Hazen 04/12
#

from ctypes import *
import sys
import time

import sc_library.hdebug as hdebug

try:
    import halLib.RS232 as RS232
except:
    sys.path.append("..")
    import halLib.RS232 as RS232

## loadTangoDLL
#
# Load the Tango DLL. Some Marzhauser stages use this DLL instead of
# RS-232 based communication.
#
tango = 0
def loadTangoDLL():
    global tango
    if (tango == 0):
        tango = windll.LoadLibrary("C:\Program Files\SwitchBoard\Tango_DLL")

instantiated = 0

## MarzhauserRS232
#
# Marzhauser RS232 interface class.
#
class MarzhauserRS232(RS232.RS232):

    ## __init__
    #
    # Connect to the Marzhuaser stage at the specified port.
    #
    # @param port The RS-232 port name (e.g. "COM1").
    # @param wait_time (Optional) How long (in seconds) for a response from the stage.
    #
    def __init__(self, port, wait_time = 0.02):

        self.live = True
        self.unit_to_um = 1000.0
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0

        # RS232 stuff
        RS232.RS232.__init__(self, port, None, 57600, "\r", wait_time)
        try:
            test = self.commWithResp("?version")
            if not test:
                self.live = False
        except:
            self.live = False
        if not self.live:
            print "Marzhauser Stage is not connected? Stage is not on?"

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
            self.commWithResp("!moa " + str(X) + " " + str(Y) + " 0")

    ## goRelative
    #
    # @param x Amount to move the stage in x in um.
    # @param y Amount to move the stage in y in um.
    #
    def goRelative(self, x, y):
        if self.live:
            X = x * self.um_to_unit
            Y = y * self.um_to_unit
            self.commWithResp("!mor " + str(X) + " " + str(Y) + " 0")

    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        if self.live:
            vx = x_speed * self.um_to_unit
            vy = y_speed * self.um_to_unit
            self.commWithResp("!speed " + str(vx) + " " + str(vy))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        if self.live:
            if on:
                self.commWithResp("!joy 2")
            else:
                self.commWithResp("!joy 0")

    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def position(self):
        if self.live:
            try:
                [self.x, self.y] = map(lambda x: float(x)*self.unit_to_um, 
                                       self.commWithResp("?pos")[:-2].split(" "))
            except:
                hdebug.logText("  Warning: Bad position from Marzhauser stage.")
            return [self.x, self.y, 0.0]
        else:
            return [0.0, 0.0, 0.0]

    ## serialNumber
    #
    # @return The stages serial number.
    #
    def serialNumber(self):
        if self.live:
            return self.commWithResp("?readsn")
        else:
            return "NA"

    ## setVelocity
    #
    # @param x_vel Maximum velocity to move in x.
    # @param y_vel Maximum velocity to move in y.
    #
    def setVelocity(self, x_vel, y_vel):
        if self.live:
            self.commWithResp("!vel " + str(x_vel) + " " + str(y_vel))

    ## zero
    #
    # Set the current stage position as the stage zero.
    #
    def zero(self):
        if self.live:
            self.commWithResp("!pos 0 0 0")


## MarzhauserDLL
#
# Marzhauser DLL interface class.
#
class MarzhauserDLL():

    ## __init__
    #
    # Connect to the Marzhuaser stage.
    #
    # @param port A RS-232 com port name such as "COM1".
    #
    def __init__(self, port):
        self.wait = 1 # move commands wait for motion to stop
        self.unit_to_um = 1000.0
        self.um_to_unit = 1.0/self.unit_to_um

        # Load the Tango library.
        loadTangoDLL()

        # Check that this class has not already been instantiated.
        global instantiated
        assert instantiated == 0, "Attempt to instantiate two Marzhauser stage classes."
        instantiated = 1

        # Connect to the stage.
        self.good = 1
        temp = c_int(-1)
        tango.LSX_CreateLSID(byref(temp))
        self.LSID = temp.value
        error = tango.LSX_ConnectSimple(self.LSID, 1, port, 57600, 0)
        if error:
            print "Marzhauser error", error
            self.good = 0

    ## getStatus
    #
    # @return True/False if we are actually connected to the stage.
    #
    def getStatus(self):
        return self.good

    ## goAbsolute
    #
    # @param x Stage x position in um.
    # @param y Stage y position in um.
    #
    def goAbsolute(self, x, y):
        if self.good:
            # If the stage is currently moving due to a jog command
            # and then you try to do a positional move everything
            # will freeze, so we stop the stage first.
            self.jog(0.0,0.0)
            X = c_double(x * self.um_to_unit)
            Y = c_double(y * self.um_to_unit)
            ZA = c_double(0.0)
            tango.LSX_MoveAbs(self.LSID, X, Y, ZA, ZA, self.wait)

    ## goRelative
    #
    # @param dx Amount to displace the stage in x in um.
    # @param dy Amount to displace the stage in y in um.
    #
    def goRelative(self, dx, dy):
        if self.good:
            self.jog(0.0,0.0)
            dX = c_double(dx * self.um_to_unit)
            dY = c_double(dy * self.um_to_unit)
            dZA = c_double(0.0)
            tango.LSX_MoveRel(self.LSID, dX, dY, dZA, dZA, self.wait)

    ## jog
    #
    # @param x_speed Speed to jog the stage in x in um/s.
    # @param y_speed Speed to jog the stage in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        if self.good:
            c_xs = c_double(x_speed * self.um_to_unit)
            c_ys = c_double(y_speed * self.um_to_unit)
            c_zr = c_double(0.0)
            tango.LSX_SetDigJoySpeed(self.LSID, c_xs, c_ys, c_zr, c_zr)

    ## joystickOnOff
    #
    # @param on True/False enable/disable the joystick.
    #
    def joystickOnOff(self, on):
        if self.good:
            if on:
                tango.LSX_SetJoystickOn(self.LSID, 1, 1)
            else:
                tango.LSX_SetJoystickOff(self.LSID)

    ## lockout
    #
    # Calls joystickOnOff.
    #
    # @param flag True/False.
    #
    def lockout(self, flag):
        self.joystickOnOff(not flag)

    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)]
    #
    def position(self):
        if self.good:
            pdX = c_double()
            pdY = c_double()
            pdZ = c_double()
            pdA = c_double()
            tango.LSX_GetPos(self.LSID, byref(pdX), byref(pdY), byref(pdZ), byref(pdA))
            return [pdX.value * self.unit_to_um, 
                    pdY.value * self.unit_to_um,
                    pdZ.value * self.unit_to_um]
        else:
            return [0.0, 0.0, 0.0]

    ## serialNumber
    #
    # @return The stage serial number.
    #
    def serialNumber(self):
        # Get stage serial number
        if self.good:
            serial_number = create_string_buffer(256)
            tango.LSX_GetSerialNr(self.LSID, serial_number, 256)
            return repr(serial_number.value)
        else:
            return "NA"

    ## setVelocity
    #
    # FIXME: figure out how to set velocity..
    #
    def setVelocity(self, x_vel, y_vel):
        pass

    ## shutDown
    #
    # Disconnect from the stage.
    #
    def shutDown(self):
        # Disconnect from the stage
        if self.good:
            tango.LSX_Disconnect(self.LSID)
        tango.LSX_FreeLSID(self.LSID)

        global instantiated
        instantiated = 0

    ## zero
    #
    # Set the current position as the new zero position.
    #
    def zero(self):
        if self.good:
            self.jog(0.0,0.0)
            x = c_double(0)
            tango.LSX_SetPos(self.LSID, x, x, x, x)


#
# Testing
# 

if __name__ == "__main__":
    stage = MarzhauserRS232("COM6")
    print "SN:", stage.serialNumber()
    stage.zero()
    print "Position:", stage.position()
    stage.goAbsolute(100.0, 100.0)
    print "Position:", stage.position()
    stage.goRelative(100.0, 100.0)
    print "Position:", stage.position()
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
