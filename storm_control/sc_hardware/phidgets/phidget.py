#!/usr/bin/python
#
## @file
#
# ctypes interace to a phidgets control library.
#
# Hazen 12/10
#

import time
from ctypes import *

#class ProductInformation(Structure):
#    _fields_ = [("axis_bitmap", c_ubyte),
#                ("ADC_resolution", c_short),
#                ("DAC_resolution", c_short),
#                ("Product_id", c_short),
#                ("FirmwareVersion", c_short),
#                ("FirmwareProfile", c_short)]

# Handles loading the library (only once)

phlib = False
def loadPhidgetsDLL(phlib_path):
    global phlib
    if (not phlib):
        phlib = windll.LoadLibrary(phlib_path + "phidget21")


## Phidget
#
# The phidget control class. This is (was ?) used to control a RC
# type servo actuator that moved a mirror.
#
class Phidget:

    ## __init__
    #
    # @param phlib_path The path to the phidgets DLL.
    #
    def __init__(self, phlib_path):

        # load the phidgets DLL library.
        loadPhidgetsDLL(phlib_path)

        # initialize the device.
        self.min_pos = 115.0
        self.max_pos = 136.0
        self.motor_index = c_int(0)
        self.ph_handle = c_int(0)
        self.position = -1.0
        phlib.CPhidgetAdvancedServo_create(byref(self.ph_handle))
        phlib.CPhidget_open(self.ph_handle, -1)
        phlib.CPhidget_waitForAttachment(self.ph_handle, 5000)
        phlib.CPhidgetAdvancedServo_setAcceleration(self.ph_handle, self.motor_index, c_double(100.0))
        phlib.CPhidgetAdvancedServo_setVelocityLimit(self.ph_handle, self.motor_index, c_double(4.0))
        phlib.CPhidgetAdvancedServo_setSpeedRampingOn(self.ph_handle, self.motor_index, c_int(1))
        phlib.CPhidgetAdvancedServo_setPositionMax(self.ph_handle, self.motor_index, c_double(self.max_pos))
        phlib.CPhidgetAdvancedServo_setPositionMin(self.ph_handle, self.motor_index, c_double(self.min_pos))
        phlib.CPhidgetAdvancedServo_setEngaged(self.ph_handle, self.motor_index, c_int(1))

    ## amMoving
    #
    # @return True/False if the servo is moving.
    #
    def amMoving(self):
        c_stopped = c_int(-1)
        phlib.CPhidgetAdvancedServo_getStopped(self.ph_handle, self.motor_index, byref(c_stopped))
        if c_stopped.value == 0:
            return True
        else:
            return False

    ## atMinimum
    #
    # @return True/False the servo is at it's minimum position.
    #
    def atMinimum(self):
        if (self.getPosition() == self.min_pos):
            return True
        else:
            return False

    ## getPosition
    #
    # @return The position of the servo.
    #
    def getPosition(self):
        c_pos = c_double(-1.0)
        phlib.CPhidgetAdvancedServo_getPosition(self.ph_handle, self.motor_index, byref(c_pos))
        self.position = c_pos.value
        return self.position

    ## goToMax
    #
    # Tell the servo to go to it's maximum position.
    #
    def goToMax(self):
        self.setPosition(self.max_pos)

    ## goToMin
    #
    # Tell the servo to go to it's minimum position.
    #
    def goToMin(self):
        self.setPosition(self.min_pos)

    ## setPosition
    #
    # Tell the servo to go position.
    #
    # @param position The position to go to.
    #
    def setPosition(self, position):
        self.position = position
        c_pos = c_double(self.position)
        phlib.CPhidgetAdvancedServo_setPosition(self.ph_handle, self.motor_index, c_pos)

    ## shutDown
    #
    # Close the connection to the servo.
    #
    def shutDown(self):
        phlib.CPhidgetAdvancedServo_setEngaged(self.ph_handle, self.motor_index, c_int(0))
        phlib.CPhidget_close(self.ph_handle)
        phlib.CPhidget_delete(self.ph_handle)

#
# Testing section.
#

if __name__ == "__main__":
    print "Initializing Servo"
    servo = Phidget("c:/Program Files/Phidgets/")
    time.sleep(0.1)
    print "Start:", servo.getPosition()

    servo.goToMin()
    while servo.amMoving():
        time.sleep(0.1)
    print "Move1:", servo.getPosition()

    servo.goToMax()
    while servo.amMoving():
        time.sleep(0.1)
    print "Move2:", servo.getPosition()
    servo.shutDown()

#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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
