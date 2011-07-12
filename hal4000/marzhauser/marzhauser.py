#!/usr/bin/python
#
# ctypes interface to a Marzhauser stage.
#
# Hazen 7/09
#

from ctypes import *
import time

tango = 0
def loadTangoDLL():
    global tango
    if (tango == 0):
        tango = windll.LoadLibrary("C:\Program Files\SwitchBoard\Tango_DLL")

instantiated = 0
class Marzhauser():
    def __init__(self):
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
        error = tango.LSX_ConnectSimple(self.LSID, 1, "COM3", 57600, 0)
        if error:
            print "Marzhauser error", error
            self.good = 0

    def getStatus(self):
        return self.good

    def goAbsolute(self, x, y):
        if self.good:
            X = c_double(x * self.um_to_unit)
            Y = c_double(y * self.um_to_unit)
            ZA = c_double(0.0)
            tango.LSX_MoveAbs(self.LSID, X, Y, ZA, ZA, self.wait)

    def goRelative(self, dx, dy):
        if self.good:
            dX = c_double(dx * self.um_to_unit)
            dY = c_double(dy * self.um_to_unit)
            dZA = c_double(0.0)
            tango.LSX_MoveRel(self.LSID, dX, dY, dZA, dZA, self.wait)

    # FIXME: lockout the joystick here.
    def lockout(self, flag):
        if self.good:
            pass

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

    def serialNumber(self):
        # Get stage serial number
        if self.good:
            serial_number = create_string_buffer(256)
            tango.LSX_GetSerialNr(self.LSID, serial_number, 256)
            return repr(serial_number.value)
        else:
            return "NA"

    def shutDown(self):
        # Disconnect from the stage
        if self.good:
            tango.LSX_Disconnect(self.LSID)
        tango.LSX_FreeLSID(self.LSID)

        global instantiated
        instantiated = 0

    def zero(self):
        if self.good:
            x = c_double(0)
            tango.LSX_SetPos(self.LSID, x, x, x, x)


#
# Testing
# 

if __name__ == "__main__":
    stage = Marzhauser()
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
