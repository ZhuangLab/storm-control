#!/usr/bin/env python
"""
ctypes interace to a Mad City Labs piezo stage.

Hazen 3/09
"""

import ctypes
import time

import storm_control.sc_library.halExceptions as halExceptions


class MCLException(halExceptions.HardwareException):
    pass


class ProductInformation(ctypes.Structure):
    """
    The Mad City Labs product information structure.
    """
    _fields_ = [("axis_bitmap", ctypes.c_ubyte),
                ("ADC_resolution", ctypes.c_short),
                ("DAC_resolution", ctypes.c_short),
                ("Product_id", ctypes.c_short),
                ("FirmwareVersion", ctypes.c_short),
                ("FirmwareProfile", ctypes.c_short)]

mcl = None
def loadMCLDLL(mcl_lib):
    """
    Handles loading the library (only once).
    """
    global mcl
    if mcl is None:
        mcl = ctypes.cdll.LoadLibrary(mcl_lib)


class MCLStage(object):
    """
    The Mad City Labs piezo stage control class.
    """
    dll_loaded = False
    handles_grabbed = False

    def __init__(self, mcl_lib = None, serial_number = None, **kwds):
        """
        Initializes the object by initializing the DLL, opening a connection 
        to requested stage, or the first the stage if none is specified. The 
        stage is then queried to determine its various properties.
        """
        super().__init__(**kwds)
        self.connected = True
        
        # load DLL is necessary
        if not MCLStage.dll_loaded:
            loadMCLDLL(mcl_lib)
            MCLStage.dll_loaded = True

        # stage properties storage
        self._props_ = {}

        # define the return types of some the functions
        mcl.MCL_GetCalibration.restype = ctypes.c_double
        mcl.MCL_SingleReadN.restype = ctypes.c_double

        #
        # Get a stage handle.
        #
        # If the stage serial number is not specified we assume that there
        # is only stage connected (or at least powered on).
        #
        if serial_number is None:
            self.handle = mcl.MCL_InitHandle()
        else:
            if not MCLStage.handles_grabbed:
                mcl.MCL_GrabAllHandles()
                MCLStage.handles_grabbed = True
            self.handle = mcl.MCL_GetHandleBySerial(int(serial_number))

        if (self.handle == 0):
            print("Failed to connect to the MCL stage. Perhaps it is turned off?")
            self.connected = False

        # Get the stage information.
        if self.handle:
            caps = ProductInformation(0, 0, 0, 0, 0, 0)
            if (mcl.MCL_GetProductInfo(ctypes.byref(caps), self.handle) != 0):
                raise MCLException("MCL_GetProductInfo failed.")
            self._props_ = {"axis_bitmap" = caps.axis_bitmap,
                            "ADC_resolution" = caps.ADC_resolution,
                            "DAC_resolution" = caps.DAC_resolution,
                            "Product_id" = caps.Product_id,
                            "FirmwareVersion" = caps.FirmwareVersion,
                            "FirmwareProfile" = caps.FirmwareProfile,
                            "SerialNumber" = mcl.MCL_GetSerialNumber(self.handle)}

        # Store which axises are valid.
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

    def _getCalibration(self, axis):
        """
        Gets the range of an axis by querying the controller.
        """
        if self.handle and self.valid_axises[axis]:
            return mcl.MCL_GetCalibration(ctypes.c_ulong(axis), self.handle)
        else:
            return 0

    def getAxisRange(self, axis):
        """
        Returns cached axis range.
        """
        if self.handle and self.valid_axises[axis]:
            return self.axis_range[axis]
        else:
            return 0

    def getPosition(self, axis):
        """
        Query the controller for the position of a particular axis.
        """
        if not(self.valid_axises[axis]):
            print("getPosition: invalid axis", axis)
        if self.handle:
            return mcl.MCL_SingleReadN(ctypes.c_ulong(axis), self.handle)

    def getProperties(self):
        """
        Return the dictionary of properties.
        """
        return self._props_

    def getStatus(self):
        return self.connected

    def moveTo(self, axis, position):
        """
        Move an axis to a position (in microns).
        """
        if not(self.valid_axises[axis]):
            print("moveTo: invalid axis", axis)
        if not(position >= 0.0):
            print("moveTo: position too small", position)
        if not(position <= self.axis_range[axis]):
            print("moveTo: position too large", position)
        if self.handle:
            mcl.MCL_SingleWriteN(ctypes.c_double(position), ctypes.c_ulong(axis), self.handle)

    def printDeviceInfo(self):
        """
        Print information about this device.
        """
        if self.handle:
            mcl.MCL_PrintDeviceInfo(self.handle)

    def readWaveForm(self, axis, points):
        """
        Read the (position) wave form from an axis. Reading (I think) occurs at a 500us rate.
        """
        if self.handle:
            if (points < 1000):
                # FIXME: Use numpy.
                wave_form_data_type = ctypes.c_double * points
                wave_form_data = wave_form_data_type()
                mcl.MCL_ReadWaveFormN(ctypes.c_ulong(axis),
                                      ctypes.c_ulong(points),
                                      ctypes.c_double(4.0),
                                      wave_form_data,
                                      self.handle)
                return wave_form_data
            else:
                print("MCL stage can only acquire a maximum of 999 points")

    def shutDown(self):
        """
        Move the stage axises back to their zero positions and close the connection to the stage.
        """
        for i in range(4):
            if self.valid_axises[i]:
                self.moveTo(i, 0.0)
        if self.handle:
            mcl.MCL_ReleaseHandle(self.handle)

    def zMoveTo(self, position):
        """
        Move the z axis to the specified position.
        """
        self.moveTo(3, position)


#
# Testing section.
#

if (__name__ == "__main__"):

    def printDict(dict):
        keys = dict.keys()
        keys.sort()
        for key in keys:
            print(key, '\t', dict[key])

    print("Initializing Stage")
    stage = MCLStage(mcl_lib = "c:/Program Files/Mad City Labs/NanoDrive/Madlib")
    if True:
        print("Stage Properties:")
        printDict(stage.getProperties())
        print("")

    for i in range(3):
        axis = i + 1
        print("Axis:", axis, "Range:", "%.2fum" % stage.getAxisRange(axis))

    print("")
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
