#!/usr/bin/env python
"""
Interface to Point Grey's PySpin Python module.

Hazen 01/19
"""

import numpy
import os
import PySpin


# Global variables.
camera_list = None
system = None


class SpinnakerException(Exception):
    """
    Use this for serious errors.
    """
    pass

class SpinnakerExceptionNotFound(SpinnakerException):
    """
    Use this for property names that are not found.
    """
    pass

class SpinnakerExceptionValue(SpinnakerException):
    """
    Use this for unacceptable node/property values.
    """
    pass


#
# Functions.
#
def listCameras():
    """
    Prints a list of available cameras. This is primarily for informational purposes.
    """
    global camera_list

    cam_data = {}
    for cam in camera_list:
        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        # Get serial number.
        node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
        else:
            raise SpinnakerException("Cannot access serial number of device " + str(cam))

        # Get model.
        node_device_model_name = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceModelName'))
        if PySpin.IsAvailable(node_device_model_name) and PySpin.IsReadable(node_device_model_name):
            device_model_name = node_device_model_name.ToString()
        else:
            raise SpinnakerException("Cannot model name of device " + str(cam))

        cam_data[device_serial_number] = device_model_name

    print("Available cameras:")
    for key in sorted(cam_data):
        print(cam_data[key] + " (" + key + ")")
    print()
            
def pySpinInitialize(verbose = True):
    """
    Initialize system get cameras.
    """
    global system
    global camera_list
    
    if system is None:
        system = PySpin.System.GetInstance()
        camera_list = system.GetCameras()
        
        if verbose:
            version = system.GetLibraryVersion()
            print("Library version: {0:d}.{1:d}.{2:d}.{3:d}".format(version.major, version.minor, version.type, version.build))
            print("Found: {0:d} cameras".format(camera_list.GetSize()))
            print()

def pySpinFinalize():
    """
    Release cameras and system.
    """
    global system
    global camera_list
    
    if system is not None:
        camera_list.Clear()
        system.ReleaseInstance()
        system = None


#
# Classes
#

class SCamData(object):
    """
    Storage of camera data.
    """
    def __init__(self, size = None, **kwds):
        super().__init__(**kwds)
        self.size = size
        self.np_array = numpy.ascontiguousarray(numpy.empty(size, dtype = numpy.uint16))

#    def copyData(self, data_ptr):
#        ctypes.memmove(self.np_array.ctypes.data, data_ptr, self.size)

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
    
    
#class ShimImage(ctypes.Structure):
#    _fields_ = [("pixel_format", ctypes.c_int),
#                ("height", ctypes.c_size_t),
#                ("im_size", ctypes.c_size_t),
#                ("width", ctypes.c_size_t),
#                ("data", ctypes.c_void_p)]

    
class SpinCamera(object):
    """
    The interface to a single camera.

    Note: Currently this only works with Mono8, Mono12p, Mono12Packed and Mono16.
    """
    def __init__(self, h_camera = None, **kwds):
        super().__init__(**kwds)
        pass

    def getFrames(self):
        """
        Get all frames that are currently available.
        """
        pass

    def getProperty(self, p_name):
        """
        Get a camera property, loading it if we don't already have it cached.
        """
        pass

    def hasProperty(self, p_name):
        """
        Returns True if the camera supports the property p_name.
        """
        pass
            
    def listAllProperties(self):
        """
        This is strictly informational, calling it will print out all the 
        available properties of the camera, of which there are a lot..
        """
        pass
    
    def release(self):
        """
        Release the camera when finished.
        """
        pass

    def setProperty(self, pname, pvalue):
        """
        Set a camera property. The property must already exist in the cache in order to be set.
        """
        pass

    def shutdown(self):
        pass

    def startAcquisition(self):
        pass

    def stopAcquisition(self):
        pass


if (__name__ == "__main__"):
    import os
    import time

    # Initialize.
    pySpinInitialize()

    # Print list of cameras.
    listCameras()

    # Clean up.
    pySpinFinalize()
    
    exit()

    
    # Query interfaces.
    [h_interface_list, num_interfaces] = spinGetInterfaces()
    print("Found " + str(num_interfaces) + " interfaces.")

    # Query cameras.
    [h_camera_list, num_cameras] = spinGetCameras()
    print("Found " + str(num_cameras) + " cameras.")

    # Get the first camera.
    cam = spinGetCamera(0)

    if False:
        # Print out all the available properties.
        cam.listAllProperties()

    if True:
        # Get some properties from the camera.
        pnames = ["DeviceModelName",
                  "AcquisitionFrameRate",
                  "AcquisitionFrameRateAuto",
                  "BlackLevel",
                  "BlackLevelClampingEnable",
                  "ExposureTime",
                  "ExposureAuto",
                  "Gain",
                  "GammaEnabled",
                  "OnBoardColorProcessEnabled",
                  "PixelFormat",
                  "pgrDefectPixelCorrectionEnable",
                  "SharpnessEnabled",
                  "VideoMode"]
        for pname in pnames:
            prop = cam.getProperty(pname)
            print(pname, prop.spinNodeGetValue())

    if True:
        # Set some properties of the camera.
        cam.setProperty("AcquisitionFrameRate",10.0)
        cam.setProperty("ExposureTime", 99000.0)
        cam.setProperty("BlackLevel", 5.0)
        cam.setProperty("Gain", 20.0)

        # Capture a few frames.
        frames = []
        cam.startAcquisition()
        for i in range(10):
            frames.extend(cam.getFrames()[0])
            time.sleep(0.2)
        cam.stopAcquisition()

        # Print frame statistics.
        for i, frame in enumerate(frames):
            np_array = frame.getData()
            print(i, np_array[0:5])
            print(i, numpy.mean(np_array), numpy.std(np_array), numpy.max(np_array))
            print("")

    # Clean up.
    cam.release()
    spinReleaseInterfaces(h_interface_list)
    spinReleaseCameras(h_camera_list)
    spinSystemReleaseInstance()

    
#
# The MIT License
#
# Copyright (c) 2016 Zhuang Lab, Harvard University
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
