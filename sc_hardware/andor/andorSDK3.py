#!/usr/bin/python
#
## @file
#
# A ctypes based interface to Andor SDK3.
#
# Note: In order for this to work you need the Andor SDK directory and the
#       Bitflow directories in your path. Typical these are something like:
#
#       1. C:\Program Files\Andor Solis\
#       2. C:\BitFlow SDK 5.70\Bin64\
#
# George ?/15.
# Hazen 9/15.
#

import ctypes
import numpy
import time

sdk3 = None
sdk3_utility = None


# Loading the DLL

def loadSDK3DLL(path):
    global sdk3, sdk3_utility
    if sdk3 is None:
	sdk3 = ctypes.oledll.LoadLibrary(path + "atcore.dll")
	sdk3_utility = ctypes.oledll.LoadLibrary(path + "atutility.dll")


# Wrapper functions for the DLL

def check(value, fn_name = "??"):
    if (value != 0):
        print "Error", value, "when calling function", fn_name
        return False
    else:
        return True

def getBoolean(handle, command):
    read_bool = ctypes.c_bool(False)
    check(sdk3.AT_GetBool(handle, command, ctypes.byref(read_bool)), 
          "AT_GetBool")
    return read_bool.value

def getCameraCount():
    return getInteger(1, "Device Count")

def getEnumeratedIndex(handle, command):
    read_index = ctypes.c_longlong()
    if check(sdk3.AT_GetEnumIndex(handle, ctypes.c_wchar_p(command), ctypes.byref(read_index)), "AT_GetEnumIndex"):
        return read_index.value
    else:
        return -1

def getEnumeratedString(handle, command):
    max_size = 100
    response = ctypes.c_wchar_p(' ' * max_size)
    if check(sdk3.AT_GetEnumStringByIndex(handle, ctypes.c_wchar_p(command), ctypes.c_longlong(getEnumeratedIndex(handle, command)), response, max_size), "AT_GetEnumStringByIndex"):
        return response.value
    else:
        return ''

def getFloat(handle, command):
    read_float = ctypes.c_double()
    if check(sdk3.AT_GetFloat(handle, ctypes.c_wchar_p(command), ctypes.byref(read_float)), "AT_GetFloat"):
        return read_float.value
    else:
        return -1

def getInteger(handle, command):
    read_int = ctypes.c_longlong()
    if check(sdk3.AT_GetInt(handle, ctypes.c_wchar_p(command), ctypes.byref(read_int)), "AT_GetInt"):
        return read_int.value
    else:
        return -1

def getString(handle, command):
    maxLength = ctypes.c_int()
    if not check(sdk3.AT_GetStringMaxLength(handle, ctypes.c_wchar_p(command), ctypes.byref(maxLength)), "AT_GetStringMaxLength"):
        return ''

    response = ctypes.c_wchar_p(' ' * maxLength.value)
    if check(sdk3.AT_GetString(handle, ctypes.c_wchar_p(command), response, maxLength), "AT_GetString"):
        return response.value
    else:
        return ''

def sendCommand(handle, command):
    return check(sdk3.AT_Command(handle, ctypes.c_wchar_p(command)), "AT_Command")

def setBoolean(handle, command, bool_value):
    return check(sdk3.AT_SetBool(handle, command, ctypes.c_bool(bool_value)), "AT_SetBool")

def setEnumeratedString(handle, command, string):
    return check(sdk3.AT_SetEnumString(handle, ctypes.c_wchar_p(command), ctypes.c_wchar_p(string)), "AT_SetEnumString")

def setEnumeratedIndex(handle, command, index):
    return check(sdk3.AT_SetEnumIndex(handle, ctypes.c_wchar_p(command), ctypes.c_longlong(index)), "AT_SetEnumIndex")

def setFloat(handle, command, float_value):
    return check(sdk3.AT_SetFloat(handle, ctypes.c_wchar_p(command), ctypes.c_double(float_value)), "AT_SetFloat")

def setInteger(handle, command, value):
    return check(sdk3.AT_SetInt(handle, ctypes.c_wchar_p(command), ctypes.c_longlong(value)), "AT_SetInt")

def setString(handle, command, string):
    return check(sdk3.AT_SetString(handle, ctypes.c_wchar_p(command), ctypes.c_wchar_p(string)), "AT_SetString")


## AndorRawData
#
# This class stores the raw data from the Andor camera, the "buffer".
#
class AndorRawData():

    def __init__(self, size):
        #self.np_array = numpy.require(numpy.empty(size, dtype = numpy.uint8),
        #                              dtype = numpy.uint8,
        #                              requirements = ['C_CONTIGUOUS', 'ALIGNED'])
        self.np_array = numpy.ascontiguousarray(numpy.empty(size + 100, dtype = numpy.uint8))
        self.size = size

    def getDataPtr(self):
        return self.np_array.ctypes.data


## AndorFrameData
#
# This class stores the converted data from the Andor camera.
#
class AndorFrameData():
    
    def __init__(self, size):
        self.np_array = numpy.ascontiguousarray(numpy.empty(size, dtype = numpy.uint16))
        self.size = size

    def getDataPtr(self):
        return self.np_array.ctypes.data


## SDK3Camera
#
# The interface to and Andor SDK3 controlled camera.
#
class SDK3Camera:

    def __init__(self, cameraID = 0):
        self.camera_handle = ctypes.c_long()
        self.frame_bytes = 0
        self.frame_data = []
        self.frame_data_cur = 0
        self.frame_x = 0
        self.frame_y = 0
        self.pixel_encoding = ""
        self.raw_data = []
        self.stride = 0

	check(sdk3.AT_InitialiseLibrary(), "AT_InitializeLibrary")
	check(sdk3_utility.AT_InitialiseUtilityLibrary(), "AT_InitialiseUtilityLibrary")
	check(sdk3.AT_Open(cameraID, ctypes.byref(self.camera_handle)), "AT_Open")

    def captureSetup(self):

        # Get current capture size.
        self.frame_x = self.getProperty("AOIWidth", "int")
        self.frame_y = self.getProperty("AOIHeight", "int")
        self.pixel_encoding = getEnumeratedString(self.camera_handle, "PixelEncoding")
        self.stride = self.getProperty("AOIStride", "int")
        frame_bytes = self.getProperty("ImageSizeBytes", "int")

        print "framex", self.frame_x
        print "framey", self.frame_y
        print "stride", self.stride
        print "frame bytes", frame_bytes
        print "pixel encoding", self.pixel_encoding

        #
        # Create new buffers if the image size has changed. Allocate ~1GB
        # of memory for this purpose.
        #
        if (frame_bytes != self.frame_bytes):
            #n_buffers = int((1.0 * 1024 * 1024 * 1024)/frame_bytes)
            n_buffers = 4
            self.raw_data = []
            self.frame_data = []
            for i in range(n_buffers):
                a_buffer = AndorRawData(frame_bytes)
                sdk3.AT_QueueBuffer(self.camera_handle, a_buffer.getDataPtr(), a_buffer.size)
                self.raw_data.append(a_buffer)

                self.frame_data.append(AndorFrameData(self.frame_x * self.frame_y))

        self.frame_data_cur = 0
        self.frame_bytes = frame_bytes

    def getFrames(self):
        frames = []
        current_buffer = ctypes.POINTER(ctypes.c_char)()
        buffer_size = ctypes.c_longlong()
        while(self.waitBuffer(current_buffer, buffer_size)):

            # Convert the buffer to an image.
            check(sdk3_utility.AT_ConvertBuffer(current_buffer,
                                                self.frame_data[self.frame_data_cur].getDataPtr(),
                                                self.frame_x,
                                                self.frame_y,
                                                self.stride,
                                                ctypes.c_wchar_p(self.pixel_encoding),
                                                ctypes.c_wchar_p("Mono16")),
                  "AT_ConvertBuffer")

            frames.append(self.frame_data[self.frame_data_cur])

            # Update current frame.
            self.frame_data_cur += 1
            if (self.frame_data_cur == len(self.frame_data)):
                self.frame_data_cur = 0

            # Re-queue the buffers.
            check(sdk3.AT_QueueBuffer(self.camera_handle, current_buffer, buffer_size))

        return frames

    def getProperty(self, pname, ptype):
        if (ptype == "boolean"):
            return getBoolean(self.camera_handle, pname)
        elif (ptype == "float"):
            return getFloat(self.camera_handle, pname)
        elif (ptype == "int"):
            return getInteger(self.camera_handle, pname)
        elif (ptype == "str"):
            return getString(self.camera_handle, pname)
        else:
            print "Unknown type", ptype, "for", pname

    def setProperty(self, pname, ptype, pvalue):
        if (ptype == "boolean"):
            setBoolean(self.camera_handle, pname, pvalue)
        elif (ptype == "float"):
            setFloat(self.camera_handle, pname, pvalue)
        elif (ptype == "int"):
            setInteger(self.camera_handle, pname, pvalue)
        elif (ptype == "str"):
            setString(self.camera_handle, pname, pvalue)
        else:
            print "Unknown type", ptype, "for", pname

    def shutdown(self):
	check(sdk3.AT_Close(self.camera_handle), "AT_Close")
        check(sdk3.AT_FinaliseLibrary(), "AT_FinalizeLibrary")
	check(sdk3_utility.AT_FinaliseUtilityLibrary(), "AT_FinalizeUtilityLibrary")

    def startAcquisition(self):
        self.captureSetup()
        setEnumeratedString(self.camera_handle, "CycleMode", "Continuous")
        sendCommand(self.camera_handle, "AcquisitionStart")

    def stopAcquisition(self):
	sendCommand(self.camera_handle, "AcquisitionStop")
	check(sdk3.AT_Flush(self.camera_handle), "AT_Flush")

    def waitBuffer(self, current_buffer, buffer_size):
        resp = sdk3.AT_WaitBuffer(self.camera_handle, ctypes.byref(current_buffer), ctypes.byref(buffer_size), 50)
        assert (resp != 100), "Andor thinks there will be a buffer overflow, sigh.."
        if (resp == 0):
            return True
        elif (resp == 13):
            return False
        else:
            assert False, "Unexpected response " + str(resp)


if (__name__ == "__main__"):
    loadSDK3DLL("C:/Program Files/Andor SOLIS/")

    cam = SDK3Camera()
    if 0:
        print "model", cam.getProperty("CameraModel", "str")
        print "name", cam.getProperty("CameraName", "str")
        print "xsize", cam.getProperty("SensorWidth", "int")
        print "ysize", cam.getProperty("SensorHeight", "int")

    if 1:
        cam.setProperty("AOIWidth", "int", 1024)
        cam.setProperty("AOIHeight", "int", 1024)
        cam.setProperty("ExposureTime", "float", 0.1)
        cam.startAcquisition()
        for i in range(20):
            frames = cam.getFrames()
            if (len(frames) > 0):
                print frames[0].np_array
        cam.stopAcquisition()

    print "shutdown"
    cam.shutdown()
    print "done"

#    print "close"
#    closeSDK3DLL()


