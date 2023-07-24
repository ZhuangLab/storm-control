#!/usr/bin/env python
"""
Interface to Point Grey's PySpin Python module.

Tested with "Spinnaker 1.19 for Python 2 and 3 - Windows (64-bit)".
Updated to handle Spinnaker 2.0

Note: As currently written this is designed to work with 12 bit cameras. See
      onImageEvent() in SpinImageEventHandler class.

Hazen 01/19
Jeff 08/20
"""

import numpy
import os
import PySpin


# Global variables.
camera_list = None
n_active_cameras = 0
system = None

# Capture the PySpin version
try:
    SpinImageEventClass = PySpin.ImageEventHandler
    pyspin_version = 2
except:
    SpinImageEventClass = PySpin.ImageEvent
    pyspin_version = 1
try:
    temp_value = PySpin.NO_COLOR_PROCESSING
except:
    pyspin_version = 3

print("Initializing FLIR spinnaker library")
print("...detected version: " + str(pyspin_version))

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
    global n_active_cameras

    assert camera_list is not None, "pySpinInitialize() was not called?"
        
    if isinstance(cam_id, int):
        n_active_cameras += 1
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
                n_active_cameras += 1
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
    global camera_list
    global system
    
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
    global camera_list
    global n_active_cameras
    global system

    if (n_active_cameras > 0):
        n_active_cameras -= 1
        
    if (system is not None) and (n_active_cameras == 0):
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
    def __init__(self, np_array = None, **kwds):
        super().__init__(**kwds)
        self.np_array = np_array

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
    
    
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

        self.frames = []
        self.frame_size = None
        self.h_camera = h_camera
        self.image_event_handler = None

        # Initialize camera.
        self.h_camera.Init()
        
        # Get interface.
        self.nodemap_applayer = self.h_camera.GetNodeMap()

        # Register for image events.
        self.image_event_handler = SpinImageEventHandler(frame_buffer = self.frames)
        if pyspin_version >=2:
            self.h_camera.RegisterEventHandler(self.image_event_handler)
        else:
            self.h_camera.RegisterEvent(self.image_event_handler)
                
        # Cached properties, these are called 'nodes' in Spinakker.
        self.properties = {}

    def getFrames(self):
        """
        Get all frames that are currently available. 

        The SpinImageEventHandler appends images to self.frames() each time
        there is a new image. Here we make a copy of the current list and
        reset the original.
        """
        # Make a copy of the current list of frames.
        tmp = self.frames.copy()

        # Need to use clear() because if we create a new list the SpinImageEventHandler
        # will still be working with the old list.
        #
        self.frames.clear()
        return [tmp, self.frame_size]

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
            raise SpinnakerExceptionNotFound("Node '" + p_name + "' does not exist.")

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

    def setProperty(self, pname, pvalue):
        """
        Set a camera property. Loading it if we don't already have it cached.
        """
        spin_node = self.getProperty(pname)
        spin_node.setValue(pvalue)

    def shutdown(self, finalize = True):
        """
        Call this only when you are done with this class instance and camera.
        """
        if pyspin_version >= 2:
            self.h_camera.UnregisterEventHandler(self.image_event_handler)
        else:
            self.h_camera.UnregisterEvent(self.image_event_handler)

        self.h_camera.DeInit()
        self.h_camera = None

        # If requested, release cameras and the system.
        if finalize:
            pySpinFinalize()
            
    def startAcquisition(self):
        self.image_event_handler.resetNImages()
        self.frame_size = (self.getProperty("Width").getValue(),
                           self.getProperty("Height").getValue())
        self.frames.clear()
        self.image_event_handler.setAcquiring(True)
        self.h_camera.BeginAcquisition()

    def stopAcquisition(self):
        self.h_camera.EndAcquisition()
        self.image_event_handler.setAcquiring(False)
        self.frames.clear()


class SpinImageEventHandler(SpinImageEventClass):
    """
    This handles a new image from the camera. It converts it to a SCamData
    object and adds the object to the cameras list of frames.
    """
    def __init__(self, frame_buffer = None, **kwds):
        super().__init__(**kwds)

        self.acquiring = False
        self.frame_buffer = frame_buffer
        self.n_images = 0

        if pyspin_version >=3:
            self.processor = PySpin.ImageProcessor()
            self.processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_NONE)


    def getNImages(self):
        return self.n_images
    
    def OnImageEvent(self, image):

        # Does this happen? It was in the ImageEvents example..
        if image.IsIncomplete():
            raise SpinnakerException("Incomplete image detected.")

        # Ignore image events when we are not acquiring.
        if not self.acquiring:
            image.Release()
            return
                
        # Convert to Mono16 as HAL works with numpy.uint16 arrays for images. This might
        # not work well with color cameras, but neither does HAL..
        #
        # Values are in Spinnaker/include/SpinnakerDefs.h
        #
        if pyspin_version>= 3:
            image_converted = self.processor.Convert(image, PySpin.PixelFormat_Mono16)
        else:
            image_converted = image.Convert(PySpin.PixelFormat_Mono16, PySpin.NO_COLOR_PROCESSING)

        # Release original image from camera.
        image.Release()
                
        # Print some stuff for debugging.
        if False:
            print("Bits per pixel", image_converted.GetBitsPerPixel())
            print("Size in bytes", image_converted.GetImageSize())
            print("Dimensions", image_converted.GetHeight(), image.GetWidth())
            print("Pixel format", image_converted.GetPixelFormat())
            print()

        # Get a numpy version of the image.
        #
        # FIXME:
        #
        # 1. Does this make a copy? Or will the numpy array be invalid when
        #    the image is garbage collected? Is the image garbage collected?
        #    This doesn't matter if we are also right shifting the array.
        #
        np_array = image_converted.GetNDArray().flatten()

        # Spinnaker will return the image in the highest 16 bits. We shift
        # bits to the right under the assumption that we are dealing with a
        # 12 bit camera.
        #
        np_array = numpy.right_shift(np_array, 4)

        # Add to cameras list of images.
        self.frame_buffer.append(SCamData(np_array = np_array))

        self.n_images += 1

    def resetNImages(self):
        self.n_images = 0

    def setAcquiring(self, acquiring):
        self.acquiring = acquiring
    

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
                tmp = "Value for " + self.name + " of " + str(p_value)
                raise SpinnakerExceptionValue(tmp + " is less than minumum of " + str(v_min))
            if (p_value > v_max):
                tmp = "Value for " + self.name + " of " + str(p_value)
                raise SpinnakerExceptionValue(tmp + " is greater than maximum of " + str(v_max))
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
        print()

    # Take a short movie.
    if True:
        
        # Set some properties of the camera.
        cam.setProperty("VideoMode", "Mode7")
        cam.setProperty("AcquisitionMode", "Continuous")
        cam.setProperty("TriggerMode", "Off")
        cam.setProperty("PixelFormat", "Mono12p")
        cam.setProperty("AcquisitionFrameRateAuto", "Off")
        cam.setProperty("AcquisitionFrameRate", 10.0)
        #cam.setProperty("ExposureTime", 99000.0)
        #cam.setProperty("BlackLevel", 5.0)
        #cam.setProperty("Gain", 20.0)

        # Capture a few frames.
        frames = []
        cam.startAcquisition()
        for i in range(2):
            time.sleep(0.2)
            frames.extend(cam.getFrames()[0])
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
