#!/usr/bin/python
#
## @file
#
# ctypes interace to a Mad City Labs piezo stage.
#
# Hazen 3/09
#

from ctypes import *
import time


## ProductInformation
#
# The Mad City Labs product information structure.
#
class ProductInformation(Structure):
    _fields_ = [("axis_bitmap", c_ubyte),
                ("ADC_resolution", c_short),
                ("DAC_resolution", c_short),
                ("Product_id", c_short),
                ("FirmwareVersion", c_short),
                ("FirmwareProfile", c_short)]


## loadMCLDLL
#
# Handles loading the library (only once)
#
mcl = False
def loadMCLDLL(mcl_path):
    global mcl
    if(mcl == False):
        mcl = cdll.LoadLibrary(mcl_path + "Madlib")


## MCLStage
#
# The Mad City Labs piezo stage control class.
#
class MCLStage:

    # Class instance variables
    dll_loaded = False
    handles_grabbed = False

    ## __init__
    #
    # Initializes the object by initializing the DLL, opening
    # a connection to requested stage, or the first the stage
    # if none is specified. The stage is then queried to
    # determine its various properties.
    #
    # @param mcl_path The path to the Mad City Labs stage control DLL.
    # @param serial_number (Optional) The serial number of the stage to control. If False then the first available stage is chosen.
    #
    def __init__(self, mcl_path, serial_number = False):

        # load DLL is necessary
        if not MCLStage.dll_loaded:
            loadMCLDLL(mcl_path)
            MCLStage.dll_loaded = True

        # stage properties storage
        self._props_ = {}

        # define the return types of some the functions
        mcl.MCL_GetCalibration.restype = c_double
        mcl.MCL_SingleReadN.restype = c_double

        #
        # Get a stage handle.
        #
        # If the stage serial number is not specified we assume that there
        # is only stage connected (or at least powered on).
        #
        if not serial_number:
            self.handle = mcl.MCL_InitHandle()
        else:
            if not MCLStage.handles_grabbed:
                mcl.MCL_GrabAllHandles()
                MCLStage.handles_grabbed = True
            self.handle = mcl.MCL_GetHandleBySerial(int(serial_number))

        #assert not(self.handle == 0), "Cannot get a MCL stage device handle."
        if self.handle == 0:
            print "Failed to connect to the MCL stage. Perhaps it is turned off?"

        # get the stage information
        caps = ProductInformation(0, 0, 0, 0, 0, 0)
        if self.handle:
            assert mcl.MCL_GetProductInfo(byref(caps), self.handle) == 0, "MCL_GetProductInfo failed."
            self._props_['axis_bitmap'] = caps.axis_bitmap
            self._props_['ADC_resolution'] = caps.ADC_resolution
            self._props_['DAC_resolution'] = caps.DAC_resolution
            self._props_['Product_id'] = caps.Product_id
            self._props_['FirmwareVersion'] = caps.FirmwareVersion
            self._props_['FirmwareProfile'] = caps.FirmwareProfile
            self._props_['SerialNumber'] = mcl.MCL_GetSerialNumber(self.handle)

        # store which axises are valid
        #
        # Note that the axises are 1 indexed, i.e.:
        #   axis X = 1
        #   axis Y = 2
        #   axis Z = 3
        self.valid_axises = [0, caps.axis_bitmap & 1, caps.axis_bitmap & 2, caps.axis_bitmap & 4]

        # store axises ranges
        self.axis_range = [0, 
                           self._getCalibration(1),
                           self._getCalibration(2),
                           self._getCalibration(3)]

    ## _getCalibration
    #
    # (Internal)
    #
    # @param axis The axis to get the calibration from.
    #
    # @return The calibration information for the specified axis.
    #
    def _getCalibration(self, axis):
        if self.handle and self.valid_axises[axis]:
            return mcl.MCL_GetCalibration(c_ulong(axis), self.handle)
        else:
            return 0

    ## getAxisRange
    #
    # @param axis (integer) The axis to get the range of.
    #
    # @return The axis range
    #
    def getAxisRange(self, axis):
        if self.handle and self.valid_axises[axis]:
            return self.axis_range[axis]
        else:
            return 0

    ## getPosition
    #
    # @param axis (integer) The axis to get the position of.
    #
    # @return The position of the axis.
    #
    def getPosition(self, axis):
        if not(self.valid_axises[axis]):
            print "getPosition: invalid axis", axis
        if self.handle:
            return mcl.MCL_SingleReadN(c_ulong(axis), self.handle)

    ## getProperties
    #
    # @return The stage properties.
    #
    def getProperties(self):
        return self._props_

    ## moveTo
    #
    # @param axis (integer) The axis to move.
    # @param position The position to move to.
    #
    def moveTo(self, axis, position):
#        assert self.valid_axises[axis], "moveTo: invalid axis " + str(axis)
#        assert position >= 0.0, "moveTo: position too small " + str(position)
#        assert position <= self.axis_range[axis], "moveTo: position too large " + str(position)
        if not(self.valid_axises[axis]):
            print "moveTo: invalid axis", axis
        if not(position >= 0.0):
            print "moveTo: position too small", position
        if not(position <= self.axis_range[axis]):
            print "moveTo: position too large", position
        if self.handle:
            mcl.MCL_SingleWriteN(c_double(position), c_ulong(axis), self.handle)

    ## printDeviceInfo
    #
    # Print information about this device.
    #
    def printDeviceInfo(self):
        if self.handle:
            mcl.MCL_PrintDeviceInfo(self.handle)

    ## readWaveForm
    #
    # Read the (position) wave form from an axis. Reading (I think) occurs at a 500us rate.
    #
    # @param axis (integer) The axis to read.
    # @param points The number of points to acquire.
    #
    # @return The waveform data as a python array.
    #
    def readWaveForm(self, axis, points):
        if self.handle:
            if points < 1000:
                wave_form_data_type = c_double * points
                wave_form_data = wave_form_data_type()
                mcl.MCL_ReadWaveFormN(c_ulong(axis), c_ulong(points), c_double(4.0), wave_form_data, self.handle)
                return wave_form_data
            else:
                print "MCL stage can only acquire a maximum of 999 points"

    ## shutDown
    #
    # Move the stage axises back to their zero positions and close the connection to the stage.
    #
    def shutDown(self):
        for i in range(4):
            if self.valid_axises[i]:
                self.moveTo(i, 0.0)
        if self.handle:
            mcl.MCL_ReleaseHandle(self.handle)

    ## zMoveTo
    #
    # Move the z axis to the specified position.
    #
    # @param position The new stage z axis position.
    #
    def zMoveTo(self, position):
        self.moveTo(3, position)


#
# Testing section.
#

if __name__ == "__main__":

    def printDict(dict):
        keys = dict.keys()
        keys.sort()
        for key in keys:
            print key, '\t', dict[key]

    print "Initializing Stage"
    #stage = MCLStage("c:\\Program Files\\Mad City Labs\\NanoDrive\\")
    stage1 = MCLStage("c:\\Program Files\\Mad City Labs\\NanoDrive\\", serial_number = 2359)
    stage2 = MCLStage("c:\\Program Files\\Mad City Labs\\NanoDrive\\", serial_number = 2636)
    stage3 = MCLStage("c:\\Program Files\\Mad City Labs\\NanoDrive\\", serial_number = 2637)
    for stage in [stage1, stage2, stage3]:
        if 1:
            print "Stage Properties:"
            printDict(stage.getProperties())
            print ""

        for i in range(3):
            axis = i + 1
            print "Axis:", axis, "Range:", "%.2fum" % stage.getAxisRange(axis)

        print ""
        stage.shutDown()
        
    exit()

    test = -1
    if test == 0:
        count = 0
        offset = 5.0
        for j in range(10):
            stage.moveTo(1, offset)
            time.sleep(0.01)
            for i in range(400):
                print count, stage.getPosition(1)
                count += 1
                time.sleep(0.01)
                offset += 5.0
    if test == 1:
        print "start: 0"
        for i in range(20):
            print "at:", i
            stage.moveTo(2, i*5)
            time.sleep(0.5)
    if test == 2:
        print dir(mcl)
    if test == 3:
        print "Moving & Waiting"
        stage.moveTo(1, 50.0)
        stage.moveTo(2, 50.0)
        stage.moveTo(3, 50.0)
        time.sleep(10.0)
        points = 500
        data = []
        axises = [1, 2, 3]
        for axis in axises:
            print "Reading axis", axis
            data.append(stage.readWaveForm(axis, points))
        fp = open("stage_data.txt", "w")
        for i in range(points):
            for datum in data:
                fp.write(str(datum[i]) + ",")
            fp.write("\n")
        
    stage.shutDown()
    

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
