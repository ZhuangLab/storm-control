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

def getCamera(cam_id):
    """
    Gets the camera specified by cam_id. This can be either an integer index
    into the list of cameras, or the camera serial number as a string.
    """
    global camera_list

    assert camera_list is not None, "pySpinInitialize() was not called?"
    
    if isinstance(cam_id, int):
        return SpinCamera(h_camera = camera_list[cam_id])
    elif isinstance(cam_id, str):
        for cam in camera_list:
            nodemap_tldevice = cam.GetTLDeviceNodeMap()
                    
            # Get serial number.
            node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
            else:
                raise SpinnakerException("Cannot access serial number of device " + str(cam))

            if (device_serial_number == cam_id):
                return SpinCamera(h_camera = cam)
        raise SpinnakerException("Cannot find camera with serial number " + cam_id)

    else:
        raise SpinnakerException("Camera ID type not understood " + str(type(cam_id)))

def listCameras():
    """
    Prints a list of available cameras. This is primarily for informational 
    purposes. You must call pySpinInitialize() first.
    """
    global camera_list

    assert camera_list is not None, "pySpinInitialize() was not called?"

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
    Initialize system and get cameras.
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

    Notes: 
    1. This only works with nodes that in the genicam nodemap. It does not
       have access to nodes in the device or tl stream nodemap.

    2. It works with the node names, not their display names.
    """
    def __init__(self, h_camera = None, **kwds):
        super().__init__(**kwds)
        
        self.h_camera = h_camera

        # Initialize camera.
        self.h_camera.Init()
        
        # Get interface.
        self.nodemap_applayer = self.h_camera.GetNodeMap()
        
        # Cached properties, these are called 'nodes' in Spinakker.
        self.properties = {}

    def getFrames(self):
        """
        Get all frames that are currently available.
        """
        pass

    def getProperty(self, p_name):
        """
        Get a camera property, loading it if we don't already have it cached.
        """
        # Return it if we have it.
        if p_name in self.properties:
            return self.properties[p_name]

        # Otherwise find it and create SpinNode class to interface with it.
        a_node = self.nodemap_applayer.GetNode(p_name)

        # It seems that 'None' means PySpin could not find the node at all.
        if a_node is None:
            raise SpinnakerException("Node '" + p_name + "' does not exist.")

        spin_node = None
        if (a_node.GetPrincipalInterfaceType() == PySpin.intfIBoolean):
            spin_node = SpinNodeBoolean(name = p_name, node = a_node)
        elif (a_node.GetPrincipalInterfaceType() == PySpin.intfIEnumeration):
            spin_node = SpinNodeEnumeration(name = p_name, node = a_node)            
        elif (a_node.GetPrincipalInterfaceType() == PySpin.intfIFloat):
            spin_node = SpinNodeFloat(name = p_name, node = a_node)
        elif (a_node.GetPrincipalInterfaceType() == PySpin.intfIInteger):
            spin_node = SpinNodeInteger(name = p_name, node = a_node)
        elif (a_node.GetPrincipalInterfaceType() == PySpin.intfIString):
            spin_node = SpinNodeString(name = p_name, node = a_node)

        if spin_node is None:
            raise SpinnakerException("Node category " + str(a_node.GetPrincipalInterfaceType()) + " is not supported.")

        self.properties[p_name] = spin_node
        return spin_node

    def hasProperty(self, p_name):
        """
        Returns True if the camera currently supports the property p_name. This 
        property may only be readable, not writeable. Also whether or not it
        exists can depend on the value of other camera properties.
        """
        a_node = PySpin.CValuePtr(self.nodemap_applayer.GetNode(p_name))
        return PySpin.IsAvailable(a_node)

    def listAllProperties(self, node = None, indent =  ""):
        """
        This is strictly informational, calling it will print out all the 
        available properties of the camera, of which there are a lot..
        """
        if node is None:
            self.listAllProperties(self.nodemap_applayer.GetNode("Root"))
            return
            
        node_category = PySpin.CCategoryPtr(node)
        print(indent + node_category.GetName())
        
        for node_feature in node_category.GetFeatures():
            if not PySpin.IsAvailable(node_feature) or not PySpin.IsReadable(node_feature):
                continue
            
            if (node_feature.GetPrincipalInterfaceType() == PySpin.intfICategory):
                self.listAllProperties(node_feature, indent = indent + "  ")

            else:
                node_value = PySpin.CValuePtr(node_feature)
                print(indent + "  " + node_value.GetName() + ": " + node_value.ToString())
                
        print()
    
    def release(self):
        """
        Release the camera when finished.
        """
        pass

    def setProperty(self, pname, pvalue):
        """
        Set a camera property. Loading it if we don't already have it cached.
        """
        spin_node = self.getProperty(pname)
        spin_node.setValue(pvalue)

    def shutdown(self):
        """
        Call this only when you are done with this class instance and camera.
        """
        self.h_camera.DeInit()
        self.h_camera = None

    def startAcquisition(self):
        pass

    def stopAcquisition(self):
        pass


class SpinNode(object):
    """
    Base class for handling nodes / properties.
    """
    def __init__(self, name = None, **kwds):
        super().__init__(**kwds)
        self.name = name
        self.node = None

    def getValue(self):
        if self.isAvailable() and self.isReadable():
            return self.node.GetValue()
        
    def isAvailable(self):
        return PySpin.IsAvailable(self.node)

    def isReadable(self):
        return PySpin.IsReadable(self.node)

    def isWritable(self):
        return PySpin.IsWritable(self.node)

    def setValue(self, p_value):
        if self.isAvailable() and self.isWritable():
            print("setValue", p_value)
            self.node.SetValue(p_value)


class SpinNodeNumber(SpinNode):
    """
    Sub-class for numbers.
    """
    def getMaximum(self):
        return self.node.GetMax()

    def getMinimum(self):
        return self.node.GetMin()

    def setValue(self, p_value):
        if self.isAvailable() and self.isWritable():
            v_max = self.getMaximum()
            v_min = self.getMinimum()
            if (p_value < v_min):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(p_value) + " is less than minumum of " + str(v_min))
            if (p_value > v_max):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(p_value) + " is greater than maximum of " + str(v_max))
            self.node.SetValue(p_value)
        

# The rest of the sub-classes in alphabetical order.
#
class SpinNodeBoolean(SpinNode):
    """
    Boolean node.
    """
    def __init__(self, node = None, **kwds):
        super().__init__(**kwds)
        self.node = PySpin.CBooleanPtr(node)

    def setValue(self, p_value):
        if not isinstance(p_value, bool):
            raise SpinnakerException(str(p_value) + " is not a boolean.")
        
        super().setValue(p_value)
        
    
class SpinNodeEnumeration(SpinNode):
    """
    Enumerated node.
    """
    def __init__(self, node = None, **kwds):
        super().__init__(**kwds)
        self.node = PySpin.CEnumerationPtr(node)

    def getValue(self):
        if self.isAvailable() and self.isReadable():
            return self.node.ToString()

    def setValue(self, p_value):
        if self.isAvailable() and self.isWritable():
                    
            if not isinstance(p_value, str):
                raise SpinnakerException(str(p_value) + " is not a string.")

            # Retrieve entry node from enumeration node.
            node_entry = self.node.GetEntryByName(p_value)
            if not PySpin.IsAvailable(node_entry) or not PySpin.IsReadable(node_entry):
                raise SpinnakerException(str(p_value) + " is not a valid enumeration setting.")

            # Retrieve integer value from entry node.
            node_entry_value = node_entry.GetValue()

            # Set integer value from entry node as new value of enumeration node.
            self.node.SetIntValue(node_entry_value)
        
    
class SpinNodeFloat(SpinNodeNumber):
    """
    Float node.
    """
    def __init__(self, node = None, **kwds):
        super().__init__(**kwds)
        self.node = PySpin.CFloatPtr(node)

    def setValue(self, p_value):
        if not isinstance(p_value, float):
            raise SpinnakerException(str(p_value) + " is not a float.")
        
        super().setValue(p_value)

        
class SpinNodeInteger(SpinNodeNumber):
    """
    Integer node.
    """
    def __init__(self, node = None, **kwds):
        super().__init__(**kwds)
        self.node = PySpin.CIntegerPtr(node)

    def setValue(self, p_value):
        if not isinstance(p_value, int):
            raise SpinnakerException(str(p_value) + " is not an integer.")
        
        super().setValue(p_value)
        
      
class SpinNodeString(SpinNode):
    """
    String node.
    """
    def __init__(self, node = None, **kwds):
        super().__init__(**kwds)
        self.node = PySpin.CStringPtr(node)

    def setValue(self, p_value):
        if not isinstance(p_value, str):
            raise SpinnakerException(str(p_value) + " is not a string.")

        super().setValue(p_value)


if (__name__ == "__main__"):
    import os
    import time

    # Initialize.
    pySpinInitialize()

    # Print list of cameras.
    listCameras()

    # Get a camera.
    cam = getCamera("17491681")

    # Print all the camera properties and their values.
    if False:
        cam.listAllProperties()
    
    # Get some properties from the camera.
    if True:
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
            print(pname, prop.getValue())

    # Take a short movie.
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
    cam.shutdown()    
    pySpinFinalize()

    
#
# The MIT License
#
# Copyright (c) 2019 Babcock Lab, Harvard University
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
