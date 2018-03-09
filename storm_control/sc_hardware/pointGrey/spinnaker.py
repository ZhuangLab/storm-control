#!/usr/bin/env python
"""
Interface to Point Grey's Spinnaker C library. This uses a
helper C library (spinshim.dll) that provides a callback
for the Spinnaker ImageEvent. This is done in order to try
capture every frame from the camera, which spinCameraGetNextImage()
does not seem to gaurantee.

You will need the folder where the library is located in your
windows path. For me this is:

C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2013\

FIXME: Fixed length film support?

Hazen 05/17
"""

import ctypes
import numpy
import os

import storm_control.c_libraries.loadclib as loadclib

# Spinnaker error codes.
SPINNAKER_ERR_SUCCESS = 0

# Spin shim library error codes.
SPINSHIM_ERR_SUCCESS = 0
SPINSHIM_ERR_NO_NEW_IMAGES = -2005

# Pixel formats.
pixel_formats = {"Mono8" : 3,
                 "Mono12Packed" : 214,
                 "Mono12p" : 8,
                 "Mono16" : 10}

# Global variables.
h_system = None
spindll = None
spinshimdll = None

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
def checkErrorCode(error_code, fn_name = "Unknown"):
    if (error_code != SPINNAKER_ERR_SUCCESS):
        print("Error " + str(error_code) + " in call to " + fn_name)

        
def loadSpinnakerDLL(dll_name):
    """
    Load the Spinnaker C library.
    """
    global spindll
    global spinshimdll
    if spindll is None:
        spindll = ctypes.windll.LoadLibrary(dll_name)
        spinshimdll = loadclib.loadCLibrary("spinshim")


def spinGetCamera(cam_id):
    [h_camera_list, n_cameras] = spinGetCameras()
    h_camera = ctypes.c_void_p(0)
    if isinstance(cam_id, int):
        c_index = ctypes.c_size_t(cam_id)
        checkErrorCode(spindll.spinCameraListGet(h_camera_list, c_index, ctypes.byref(h_camera)),
                       "spinCameraListGet")
        spinReleaseCameras(h_camera_list)        
        return SpinCamera(h_camera)
        
    
def spinGetCameras():
    """
    Returns a pointer to a list of cameras and the number of cameras. This
    combines the following into a single call:

    spinCameraListCreateEmpty()
    spinSystemGetCameras()
    spinCameraListGetSize()
    """
    global h_system
    h_camera_list = ctypes.c_void_p(0)
    checkErrorCode(spindll.spinCameraListCreateEmpty(ctypes.byref(h_camera_list)), "spinCameraListCreateEmpty")
    checkErrorCode(spindll.spinSystemGetCameras(h_system, h_camera_list), "spinSystemGetCameras")
    num_cameras = ctypes.c_long(0)
    checkErrorCode(spindll.spinCameraListGetSize(h_camera_list, ctypes.byref(num_cameras)), "spinCameraListGetSize")
    return [h_camera_list, num_cameras.value]

        
def spinGetInterfaces():
    """
    Returns a pointer to a list of interfaces and the number of interfaces. This
    combines the following into a single call:

    spinInterfaceListCreateEmpty()
    spinSystemGetInterfaces()
    spinInterfaceListGetSize()
    """
    global h_system
    h_interface_list = ctypes.c_void_p(0)
    checkErrorCode(spindll.spinInterfaceListCreateEmpty(ctypes.byref(h_interface_list)), "spinInterfaceListCreateEmpty")
    checkErrorCode(spindll.spinSystemGetInterfaces(h_system, h_interface_list), "spinSystemGetInterfaces")
    num_interfaces = ctypes.c_long(0)
    checkErrorCode(spindll.spinInterfaceListGetSize(h_interface_list, ctypes.byref(num_interfaces)), "spinInterfaceListGetSize")
    return [h_interface_list, num_interfaces.value]


def spinReleaseCameras(h_camera_list):
    checkErrorCode(spindll.spinCameraListClear(h_camera_list), "spinCameraListClear")
    checkErrorCode(spindll.spinCameraListDestroy(h_camera_list), "spinCameraListDestroy")


def spinReleaseInterfaces(h_interface_list):
    checkErrorCode(spindll.spinInterfaceListClear(h_interface_list), "spinInterfaceListClear")
    checkErrorCode(spindll.spinInterfaceListDestroy(h_interface_list), "spinInterfaceListDestroy")


def spinSystemGetInstance():
    """
    Get singleton reference to the system object.
    """
    global h_system
    if h_system is None:
        h_system = ctypes.c_void_p(0)
        checkErrorCode(spindll.spinSystemGetInstance(ctypes.byref(h_system)), "spinSystemGetInstance")

        
def spinSystemReleaseInstance():
    global h_system
    if h_system is not None:
        checkErrorCode(spindll.spinSystemReleaseInstance(h_system), "spinSystemReleaseInstance")
        h_system = None


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
    
    
class ShimImage(ctypes.Structure):
    _fields_ = [("pixel_format", ctypes.c_int),
                ("height", ctypes.c_size_t),
                ("im_size", ctypes.c_size_t),
                ("width", ctypes.c_size_t),
                ("data", ctypes.c_void_p)]

    
class SpinCamera(object):
    """
    The interface to a single camera.

    Note: Currently this only works with Mono8, Mono12p, Mono12Packed and Mono16.
    """
    def __init__(self, h_camera = None, **kwds):
        super().__init__(**kwds)
        self.aoi_width = None
        self.aoi_height = None
        self.buffer_len = 50
        self.encoding = 'utf-8'
        self.h_camera = h_camera
        self.im_event = None
        self.pixel_format = None
        self.properties = {}
        self.verbose = True

        # Initialize.
        checkErrorCode(spindll.spinCameraInit(self.h_camera), "spinCameraInit")

        # Get handle to camera properties.
        self.h_node_map = ctypes.c_void_p(0)
        checkErrorCode(spindll.spinCameraGetNodeMap(self.h_camera, ctypes.byref(self.h_node_map)),
                       "spinCameraGetNodeMap")

        # Get handle to TL device properties.
        self.h_tl_device_node_map = ctypes.c_void_p(0)
        checkErrorCode(spindll.spinCameraGetTLDeviceNodeMap(self.h_camera, ctypes.byref(self.h_tl_device_node_map)),
                       "spinCameraGetTLDeviceNodeMap")
        
        # Get handle to TL stream properties.
        self.h_tl_stream_node_map = ctypes.c_void_p(0)
        checkErrorCode(spindll.spinCameraGetTLStreamNodeMap(self.h_camera, ctypes.byref(self.h_tl_stream_node_map)),
                       "spinCameraGetTLStreamNodeMap")

        self.node_maps = [self.h_node_map, self.h_tl_device_node_map, self.h_tl_stream_node_map]
        
        # Get stream buffer count property.
        self.stream_buffer_count = self.getProperty("StreamDefaultBufferCount")

    def getFrames(self):
        frames = []
        
        # Get all the images that are currently available.
        while True:

            #
            # Create an image, possibly wasteful as if we don't get an
            # image we'll immediately throw this object away.
            #
            image_size = self.aoi_width * self.aoi_height
            s_cam_data = SCamData(size = image_size)
            image = ShimImage(ctypes.c_int(self.pixel_format),
                              ctypes.c_size_t(self.aoi_height),
                              ctypes.c_size_t(image_size),
                              ctypes.c_size_t(self.aoi_width),
                              ctypes.c_void_p(s_cam_data.getDataPtr()))

            # Get the image.
            err_code = spinshimdll.getNextImage(self.im_event, ctypes.byref(image))

            # Check if we actually got an image.
            if (err_code != SPINSHIM_ERR_SUCCESS):
                break

            # Add to the list of images if we did.
            frames.append(s_cam_data)

        if (err_code != SPINSHIM_ERR_NO_NEW_IMAGES):
            raise SpinnakerException("Image acquisition error!", err_code)

        return [frames, [self.aoi_width, self.aoi_height]]

    def getProperty(self, p_name):
        """
        Get a camera property, loading it if we don't already have it cached.
        """
        if self.h_camera is None:
            return
        
        if not p_name in self.properties:
            
            # Get node by searching the node maps to see if we can find it.
            c_p_name = ctypes.c_char_p(p_name.encode(self.encoding))
            h_node = ctypes.c_void_p(0)
            for node_map in self.node_maps:
                checkErrorCode(spindll.spinNodeMapGetNode(node_map, c_p_name, ctypes.byref(h_node)),
                               "spinNodeMapGetNode")
                if h_node.value is not None:
                    break

            if h_node.value is None:
                raise SpinnakerException("Property " + p_name + " not found")
            
            # Get node type.
            p_type = ctypes.c_int(0)
            checkErrorCode(spindll.spinNodeGetType(h_node, ctypes.byref(p_type)),
                           "spinNodeGetType")
            p_type = p_type.value

            # Value (basically integer?) type.
            if (p_type == 0):
                self.properties[p_name] = SpinNodeValue(h_node = h_node)

            # Integer type.
            elif (p_type == 2):
                self.properties[p_name] = SpinNodeInteger(h_node = h_node)

            # Boolean type.
            elif (p_type == 3):
                self.properties[p_name] = SpinNodeBoolean(h_node = h_node)
            
            # Float type.
            elif (p_type == 4):
                self.properties[p_name] = SpinNodeFloat(h_node = h_node)

            # String type.
            elif (p_type == 6):
                self.properties[p_name] = SpinNodeString(h_node = h_node)

            # Enumeration type.
            elif (p_type == 8):
                self.properties[p_name] = SpinNodeEnumeration(h_node = h_node)
                
            else:
                print("Unknown node type", p_type)
                return None
                    
        return self.properties[p_name]

    def listAllProperties(self):
        """
        This is strictly informational, calling it will print out all the 
        available properties of the camera, of which there are a lot..
        """
        for i, node_map in enumerate(self.node_maps):

            # Get the number of nodes in the node map.
            p_value = ctypes.c_size_t(0)
            checkErrorCode(spindll.spinNodeMapGetNumNodes(node_map, ctypes.byref(p_value)),
                           "spinNodeMapGetNumNodes")
            p_value = p_value.value

            print("Node " + str(i) + " has " + str(p_value) + " properties.")
            
            # List all of the node names.
            for j in range(p_value):
                c_index = ctypes.c_size_t(j)
                h_node = ctypes.c_void_p(0)
                error_code = spindll.spinNodeMapGetNodeByIndex(node_map, c_index, ctypes.byref(h_node))

                if (error_code == SPINNAKER_ERR_SUCCESS):
                    spin_node = SpinNode(h_node)
                    print("  " + spin_node.name + " / " + spin_node.description)
            print("")
    
    def release(self):
        """
        Release the camera when finished.
        """
        if self.h_camera is None:
            return
        
        # Should we also de-initialize?
        checkErrorCode(spindll.spinCameraRelease(self.h_camera), "spinCameraRelease")
        self.h_camera = None

    def setProperty(self, pname, pvalue):
        """
        Set a camera property. The property must already exist in the cache in order to be set.
        """
        if self.h_camera is None:
            return

        if not pname in self.properties:
            raise SpinnakerExceptionNotFound("Property " + pname + " not in cache, cannot be set.")

        if self.verbose:
            print(">spinnaker setProperty", pname)
        self.properties[pname].spinNodeSetValue(pvalue)

    def shutdown(self):
        self.release()
        spinSystemReleaseInstance()

    def startAcquisition(self):
        if self.h_camera is None:
            return

        self.aoi_height = self.getProperty("Height").spinNodeGetValue()
        self.aoi_width = self.getProperty("Width").spinNodeGetValue()
        self.pixel_format = pixel_formats[self.getProperty("PixelFormat").spinNodeGetValue()]
        
        # Configure number of stream buffers to match what we want.
        #
        # FIXME: Should depend on the exposure time. Maybe need enough buffer for up to 1 second?
        #
        self.stream_buffer_count.spinNodeSetValue(self.buffer_len)
        
        # Configure C shim library that handles camera ImageEvent.
        self.im_event = ctypes.c_void_p(0)
        c_buffer_len = ctypes.c_int(self.buffer_len)
        checkErrorCode(spinshimdll.configureImageEvent(self.h_camera, ctypes.byref(self.im_event), c_buffer_len),
                       "configureImageEvent")

        # Start acquisition.
        checkErrorCode(spindll.spinCameraBeginAcquisition(self.h_camera), "spinCameraBeginAcquisition")

    def stopAcquisition(self):
        if self.h_camera is None:
            return
        
        checkErrorCode(spindll.spinCameraEndAcquisition(self.h_camera), "spinCameraEndAcquisition")

        # Release C shim library.
        checkErrorCode(spinshimdll.releaseImageEvent(self.h_camera, self.im_event),
                       "releaseImageEvent")


class SpinNode(object):
    """
    Base class for accessing and configuring camera properties.
    """
    def __init__(self, h_node = None, **kwds):
        super().__init__(**kwds)
        self.encoding = 'utf-8'
        self.h_node = h_node
        self.value = None
        
        self.description = self.spinNodeGetDescription()
        self.name = self.spinNodeGetName()

    def spinNodeGetDescription(self):
        max_len = ctypes.c_size_t(1000)
        p_buf = ctypes.create_string_buffer(max_len.value)
        checkErrorCode(spindll.spinNodeGetDescription(self.h_node, p_buf, ctypes.byref(max_len)),
                       "spinNodeGetDescription")
        return p_buf.value.decode(self.encoding)

    def spinNodeGetName(self):
        max_len = ctypes.c_size_t(100)
        p_buf = ctypes.create_string_buffer(max_len.value)
        checkErrorCode(spindll.spinNodeGetName(self.h_node, p_buf, ctypes.byref(max_len)),
                       "spinNodeGetName")
        return p_buf.value.decode(self.encoding)

    def spinNodeGetValue(self):
        """
        Sub-classes should all implement this in order to work with Parameters.
        """
        pass
        
    def spinNodeIsReadable(self, warn = True):
        pb_result = ctypes.c_int8(0)
        checkErrorCode(spindll.spinNodeIsReadable(self.h_node, ctypes.byref(pb_result)),
                       "spinNodeIsReadable")
        readable = (pb_result.value == 1)
        if warn and not readable:
            print("Property " + self.name + " is not readable.")
        return readable

    def spinNodeIsWritable(self, warn = True):
        pb_result = ctypes.c_int8(0)
        checkErrorCode(spindll.spinNodeIsWritable(self.h_node, ctypes.byref(pb_result)),
                       "spinNodeIsWritable")
        writeable = (pb_result.value == 1)
        if warn and not writeable:
            print("Property " + self.name + " is not writeable.")
        return writeable

    def spinNodeSetValue(self):
        """
        Sub-classes should all implement this in order to work with Parameters.
        """
        pass


class SpinNodeBoolean(SpinNode):
    """
    Boolean values.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.value = self.spinNodeGetValue()

    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            b_value = ctypes.c_int8(0)
            checkErrorCode(spindll.spinBooleanGetValue(self.h_node, ctypes.byref(b_value)),
                           "spinBooleanGetValue")
            self.value = (b_value.value == 1)
            return self.value

    def spinNodeSetValue(self, new_value):
        if (new_value != self.value):
            if not isinstance(new_value, bool):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not a boolean.")
            b_value = ctypes.c_int8(new_value)
            checkErrorCode(spindll.spinBooleanSetValue(self.h_node, b_value),
                           "spinBooleanSetValue")
            self.value = new_value
            return self.value
            
        
class SpinNodeEnumeration(SpinNode):
    """
    Enumerated values.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Get a list of all the possible value.
        p_value = ctypes.c_size_t(0)
        checkErrorCode(spindll.spinEnumerationGetNumEntries(self.h_node, ctypes.byref(p_value)),
                       "spinEnumerationGetNumEntries")
        n_entries = p_value.value

        self.values = []
        for i in range(n_entries):
            index = ctypes.c_size_t(i)
            h_entry = ctypes.c_void_p(0)
            checkErrorCode(spindll.spinEnumerationGetEntryByIndex(self.h_node, index, ctypes.byref(h_entry)),
                           "spinEnumerationEntryByIndex")
            self.values.append(self.spinEnumerationEntryGetSymbolic(h_entry))

        self.value = self.spinNodeGetValue()

    def spinEnumerationEntryGetSymbolic(self, h_entry):
        max_len = ctypes.c_size_t(100)
        p_buf = ctypes.create_string_buffer(max_len.value)
        checkErrorCode(spindll.spinEnumerationEntryGetSymbolic(h_entry, p_buf, ctypes.byref(max_len)),
                       "spinEnumerationEntryGetSymbolic")
        return p_buf.value.decode(self.encoding)
            
    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            h_entry = ctypes.c_void_p(0)
            checkErrorCode(spindll.spinEnumerationGetCurrentEntry(self.h_node, ctypes.byref(h_entry)),
                           "spinEnumerationGetCurrentEntry")
            self.value = self.spinEnumerationEntryGetSymbolic(h_entry)
            return self.value

    def spinNodeSetValue(self, new_value):
        if (new_value != self.value):
            if not isinstance(new_value, str):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not a string")
            if not new_value in self.values:
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + new_value + " is not in " + str(self.values))

            if self.spinNodeIsWritable():
                h_choice = ctypes.c_void_p(0)
                c_value = ctypes.c_char_p(new_value.encode(self.encoding))
                checkErrorCode(spindll.spinEnumerationGetEntryByName(self.h_node, c_value, ctypes.byref(h_choice)),
                               "spinEnumerationGetEntryByName")
                choice = ctypes.c_uint64(0)
                checkErrorCode(spindll.spinEnumerationEntryGetIntValue(h_choice, ctypes.byref(choice)),
                               "spinEnumerationEntryGetEnumValue")
                checkErrorCode(spindll.spinEnumerationSetIntValue(self.h_node, choice),
                               "spinEnumerationEntrySetIntValue")

                self.value = new_value
                return self.value

        
class SpinNodeFloat(SpinNode):
    """
    Float camera property.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Get unit.
        max_len = ctypes.c_size_t(20)
        p_buf = ctypes.create_string_buffer(max_len.value)
        checkErrorCode(spindll.spinFloatGetUnit(self.h_node, p_buf, ctypes.byref(max_len)),
                       "spinFloatGetUnit")
        self.v_unit = p_buf.value.decode(self.encoding)

        self.value = self.spinNodeGetValue()

    def spinNodeGetMaximum(self):
        p_value = ctypes.c_double(0)
        checkErrorCode(spindll.spinFloatGetMax(self.h_node, ctypes.byref(p_value)),
                       "spinFloatGetMax")
        return p_value.value

    def spinNodeGetMinimum(self):
        p_value = ctypes.c_double(0)
        checkErrorCode(spindll.spinFloatGetMin(self.h_node, ctypes.byref(p_value)),
                       "spinFloatGetMin")
        return p_value.value
        
    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            p_value = ctypes.c_double(0.0)
            checkErrorCode(spindll.spinFloatGetValue(self.h_node, ctypes.byref(p_value)),
                           "spinFloatGetValue")
            self.value = p_value.value
            return self.value

    def spinNodeSetValue(self, new_value):
        if (new_value != self.value):
            if not isinstance(new_value, float):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not a float")
            if self.spinNodeIsWritable():
                v_max = self.spinNodeGetMaximum()
                v_min = self.spinNodeGetMinimum()
                if (new_value < v_min):
                    raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is less than minumum of " + str(v_min))
                if (new_value > v_max):
                    raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is greater than maximum of " + str(v_max))
                
                value = ctypes.c_double(new_value)
                checkErrorCode(spindll.spinFloatSetValue(self.h_node, value),
                               "spinFloatSetValue")
                self.value = value.value
                return self.value


class SpinNodeInteger(SpinNode):
    """
    Integer camera property.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Get the current value.
        self.value = self.spinNodeGetValue()

    def spinNodeGetIncrement(self):
        p_value = ctypes.c_uint64(0)
        checkErrorCode(spindll.spinIntegerGetInc(self.h_node, ctypes.byref(p_value)),
                       "spinIntegerGetInc")
        return int(p_value.value)        
        
    def spinNodeGetMaximum(self):
        p_value = ctypes.c_uint64(0)
        checkErrorCode(spindll.spinIntegerGetMax(self.h_node, ctypes.byref(p_value)),
                       "spinIntegerGetMax")
        return int(p_value.value)

    def spinNodeGetMinimum(self):
        p_value = ctypes.c_uint64(0)
        checkErrorCode(spindll.spinIntegerGetMin(self.h_node, ctypes.byref(p_value)),
                       "spinIntegerGetMin")
        return int(p_value.value)

    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            p_value = ctypes.c_uint64(0)
            checkErrorCode(spindll.spinIntegerGetValue(self.h_node, ctypes.byref(p_value)),
                           "spinIntegerGetValue")
            self.value = int(p_value.value)
            return self.value

    def spinNodeSetValue(self, new_value):
        if (new_value != self.value):
            if not isinstance(new_value, int):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not an integer")
            if self.spinNodeIsWritable():
                v_inc = self.spinNodeGetIncrement()
                v_max = self.spinNodeGetMaximum()
                v_min = self.spinNodeGetMinimum()
                if (new_value < v_min):
                    raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is less than minumum of " + str(v_min))
                if (new_value > v_max):
                    raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is greater than maximum of " + str(v_max))
                if ((new_value % v_inc) != 0):
                    raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not divisible by " + str(v_inc))

                value = ctypes.c_uint64(new_value)
                checkErrorCode(spindll.spinIntegerSetValue(self.h_node, value),
                               "spinIntegerSetValue")
                self.value = value.value
                return self.value
            
        
class SpinNodeString(SpinNode):
    """
    String camera property.
    """
    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            max_len = ctypes.c_uint64(0)
            checkErrorCode(spindll.spinStringGetMaxLength(self.h_node, ctypes.byref(max_len)),
                           "spinStringGetMaxLength")
            max_len = ctypes.c_size_t(max_len.value + 1)
            p_buf = ctypes.create_string_buffer(max_len.value)
            checkErrorCode(spindll.spinStringGetValue(self.h_node, p_buf, ctypes.byref(max_len)),
                           "spinStringGetValue")
            self.value = p_buf.value.decode(self.encoding)
            return self.value


class SpinNodeValue(SpinNode):
    """
    ValueNode / spinEnumeration camera property.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.value = self.spinNodeGetValue()

    def spinNodeGetValue(self):
        if self.spinNodeIsReadable():
            p_value = ctypes.c_uint64(0)
            checkErrorCode(spindll.spinEnumerationEntryGetIntValue(self.h_node, ctypes.byref(p_value)),
                           "spinEnumerationEntryGetIntValue")
            self.value = p_value.value
            return self.value

    def spinNodeSetValue(self, new_value):
        if (new_value != self.value):
            if not isinstance(new_value, int):
                raise SpinnakerExceptionValue("Value for " + self.name + " of " + str(new_value) + " is not an integer")
            if self.spinNodeIsWritable():
                value = ctypes.c_uint64(new_value)
                checkErrorCode(spindll.spinEnumerationSetIntValue(self.h_node, value),
                               "spinEnumerationSetIntValue")
                self.value = value.value
                return self.value
            

if (__name__ == "__main__"):
    import os
    import time

    # Load the Spinnaker C library.
    dll_name = r'C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2013\SpinnakerC_v120.dll'
    if os.path.exists(dll_name):
        loadSpinnakerDLL(dll_name)
    else:
        print(dll_name + " not found")
        exit()

    # Initialize.
    spinSystemGetInstance()

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

    if False:
        # Set some properties of the camera.
        cam.setProperty("AcquisitionFrameRate", 2.0)
        cam.setProperty("ExposureTime", 100000.0)
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
