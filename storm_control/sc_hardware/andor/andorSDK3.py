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
import storm_control.sc_library.halExceptions as halExceptions

sdk3 = None
sdk3_utility = None

# Loading the DLL

def loadSDK3DLL(path):
    global sdk3, sdk3_utility
    if sdk3 is None:
        sdk3 = ctypes.oledll.LoadLibrary(path + "atcore.dll")
        sdk3_utility = ctypes.oledll.LoadLibrary(path + "atutility.dll")

# Wrapper functions for the DLL

def check(value, fn_name = "??", command = "??"):
    if (value != 0):
        error_message = "Error", value, "when calling function", fn_name, "with command", command
        print(error_message)
        raise AndorException(error_message) # Raise a hardware error
        
        return False
    else:
        return True

def getBoolean(handle, command):
    read_bool = ctypes.c_bool(False)
    check(sdk3.AT_GetBool(handle,
                          ctypes.c_wchar_p(command), 
                          ctypes.byref(read_bool)),
          "AT_GetBool",
          command)
    return read_bool.value

def getCameraCount():
    return getInteger(1, "Device Count")

def getEnumeratedIndex(handle, command):
    read_index = ctypes.c_longlong()
    if check(sdk3.AT_GetEnumIndex(handle, 
                                  ctypes.c_wchar_p(command), 
                                  ctypes.byref(read_index)), 
             "AT_GetEnumIndex",
             command):
        return read_index.value
    else:
        return -1

def getEnumeratedString(handle, command):
    max_size = 100
    response = ctypes.c_wchar_p(' ' * max_size)
    if check(sdk3.AT_GetEnumStringByIndex(handle, 
                                          ctypes.c_wchar_p(command), 
                                          ctypes.c_longlong(getEnumeratedIndex(handle, command)), 
                                          response, 
                                          ctypes.c_int(max_size)), 
             "AT_GetEnumStringByIndex",
             command):
        return response.value
    else:
        return ''

def getFloat(handle, command):
    read_float = ctypes.c_double()
    if check(sdk3.AT_GetFloat(handle, 
                              ctypes.c_wchar_p(command), 
                              ctypes.byref(read_float)), 
             "AT_GetFloat",
             command):
        return read_float.value
    else:
        return -1

def getFloatRange(handle, command):
    float_max = ctypes.c_double()
    float_min = ctypes.c_double()
    success_max = check(sdk3.AT_GetFloatMax(handle, 
                    ctypes.c_wchar_p(command), 
                    ctypes.byref(float_max)), 
                    "AT_GetIntMax", 
                    command)
    success_min = check(sdk3.AT_GetFloatMin(handle, 
                    ctypes.c_wchar_p(command), 
                    ctypes.byref(float_min)), 
                    "AT_GetIntMin", 
                    command)

    return [success_min and success_max, float_min.value, float_max.value]

def getInteger(handle, command):
    read_int = ctypes.c_longlong()
    if check(sdk3.AT_GetInt(handle, 
                            ctypes.c_wchar_p(command), 
                            ctypes.byref(read_int)), 
             "AT_GetInt", 
             command):
        return read_int.value
    else:
        return -1

def getIntegerRange(handle, command):
    int_max = ctypes.c_longlong()
    int_min = ctypes.c_longlong()
    success_max = check(sdk3.AT_GetIntMax(handle, 
                    ctypes.c_wchar_p(command), 
                    ctypes.byref(int_max)), 
                    "AT_GetIntMax", 
                    command)
    success_min = check(sdk3.AT_GetIntMin(handle, 
                    ctypes.c_wchar_p(command), 
                    ctypes.byref(int_min)), 
                    "AT_GetIntMin", 
                    command)

    return [success_min and success_max, int_min.value, int_max.value]

def getString(handle, command):
    max_length = ctypes.c_int()
    if not check(sdk3.AT_GetStringMaxLength(handle, 
                                            ctypes.c_wchar_p(command), 
                                            ctypes.byref(max_length)),
                 "AT_GetStringMaxLength",
                 command):
        return ''

    response = ctypes.c_wchar_p(' ' * max_length.value)
    if check(sdk3.AT_GetString(handle, 
                               ctypes.c_wchar_p(command), 
                               response, 
                               max_length), 
             "AT_GetString",
             command):
        return response.value
    else:
        return ''

def sendCommand(handle, command):
    return check(sdk3.AT_Command(handle, 
                                 ctypes.c_wchar_p(command)), 
                 "AT_Command",
                 command)

def setBoolean(handle, command, bool_value):
    return check(sdk3.AT_SetBool(handle, 
                                 ctypes.c_wchar_p(command), 
                                 ctypes.c_bool(bool_value)), 
                 "AT_SetBool",
                 command)

def setEnumeratedString(handle, command, string):
    return check(sdk3.AT_SetEnumString(handle, 
                                       ctypes.c_wchar_p(command), 
                                       ctypes.c_wchar_p(string)), 
                 "AT_SetEnumString",
                 command)

def setEnumeratedIndex(handle, command, index):
    return check(sdk3.AT_SetEnumIndex(handle, 
                                      ctypes.c_wchar_p(command), 
                                      ctypes.c_longlong(index)), 
                 "AT_SetEnumIndex",
                 command)

def setFloat(handle, command, float_value):
    success, min_value, max_value = getFloatRange(handle, command)
    if float_value < min_value:
        float_value = min_value
    elif float_value > max_value:
        float_value = max_value

    return check(sdk3.AT_SetFloat(handle, 
                                  ctypes.c_wchar_p(command), 
                                  ctypes.c_double(float_value)), 
                 "AT_SetFloat",
                 command)

def setInteger(handle, command, value):
    success, min_value, max_value = getIntegerRange(handle, command)
    if value < min_value:
        value = min_value
        print("Coerced " + str(command) + " to " + str(value))
    elif value > max_value:
        value = max_value
        print("Coerced " + str(command) + " to " + str(value))
    
    return check(sdk3.AT_SetInt(handle, 
                                ctypes.c_wchar_p(command), 
                                ctypes.c_int64(value)), 
                 "AT_SetInt",
                 command)

def setString(handle, command, string):
    return check(sdk3.AT_SetString(handle, 
                                   ctypes.c_wchar_p(command), 
                                   ctypes.c_wchar_p(string)), 
                 "AT_SetString",
                 command)

## AndorException
#
# Camera exception.
#
class AndorException(halExceptions.HardwareException):
    pass


## AndorRawData
#
# This class stores the raw data from the Andor camera, the "buffer".
#
class AndorRawData(object):

    def __init__(self, size = None, **kwds):
        super().__init__(**kwds)
        #self.np_array = numpy.require(numpy.empty(size, dtype = numpy.uint8),
        #                              dtype = numpy.uint8,
        #                              requirements = ['C_CONTIGUOUS', 'ALIGNED'])
        self.np_array = numpy.ascontiguousarray(numpy.empty(size, dtype = numpy.uint8))
        self.size = size

    def getDataPtr(self):
        return self.np_array.ctypes.data


## AndorFrameData
#
# This class stores the converted data from the Andor camera.
#
class AndorFrameData(object):
    
    def __init__(self, size = None, **kwds):
        super().__init__(**kwds)
        
        self.np_array = numpy.ascontiguousarray(numpy.empty(size, dtype = numpy.uint16))
        self.size = size

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data


## SDK3Camera
#
# The interface to and Andor SDK3 controlled camera.
#
class SDK3Camera(object):

    def __init__(self, camera_id = 0, **kwds):
        super().__init__(**kwds)
        
        self.camera_handle = ctypes.c_void_p()
        self.enumerated = frozenset(["AOIBinning",
                                     "AOILayout",
                                     "AuxiliaryOutSource",
                                     "AuxOutSourceTwo",
                                     "BitDepth",
                                     "ColourFilter",
                                     "CycleMode",
                                     "ElectronicShutteringMode",
                                     "EventSelector",
                                     "FanSpeed",
                                     "InterfaceType",
                                     "IOControl",
                                     "IODirection",
                                     "IOSelector",
                                     "PixelCorrection",
                                     "PixelEncoding",
                                     "PixelReadoutRate",
                                     "PreAmpGain",
                                     "PreAmpGainChannel",
                                     "PreAmpGainControl",
                                     "PreAmpGainSelector",
                                     "SensorReadoutMode",
                                     "SensorType",
                                     "ShutterMode",
                                     "ShutterOutputMode",
                                     "SimplePreAmpGainControl",
                                     "TemperatureStatus",
                                     "TriggerMode"])
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
        check(sdk3.AT_Open(ctypes.c_int(camera_id), ctypes.byref(self.camera_handle)), "AT_Open")

    def captureSetup(self):

        # Get current capture size.
        frame_x = self.getProperty("AOIWidth", "int")
        frame_y = self.getProperty("AOIHeight", "int")
        self.pixel_encoding = self.getProperty("PixelEncoding", "enum")
        self.stride = self.getProperty("AOIStride", "int")
        frame_bytes = self.getProperty("ImageSizeBytes", "int")
        n_buffers = min(int((2.0 * 1024 * 1024 * 1024)/frame_bytes), 2000)

        # Create new buffers if the image size has changed. This will allocate
        # space for ~4GB of buffers (2GB for raw buffers and 2GB for the the
        # frames), or space for 4000 frames (2000 for raw buffers and 2000 for
        # the frames). In theory we will not be able to write over active
        # frames because they would also be active buffers..
        #
        if (frame_bytes != self.frame_bytes):
            self.raw_data = []
            for i in range(n_buffers):
                self.raw_data.append(AndorRawData(size = frame_bytes))
                
        # frame_bytes can be the same even when the frame size is different.
        #
        if ((frame_x * frame_y) != (self.frame_x * self.frame_y)):
            self.frame_data = []
            for i in range(n_buffers):
                self.frame_data.append(AndorFrameData(size = frame_x * frame_y))

        for a_buffer in self.raw_data:
            sdk3.AT_QueueBuffer(self.camera_handle, 
                                ctypes.c_void_p(a_buffer.getDataPtr()), 
                                ctypes.c_int(a_buffer.size))

        self.frame_data_cur = 0
        self.frame_x = frame_x
        self.frame_y = frame_y
        self.frame_bytes = frame_bytes

    def getFrames(self):
        frames = []
        #current_buffer = ctypes.POINTER(ctypes.c_char)()
        current_buffer = ctypes.c_void_p()
        buffer_size = ctypes.c_longlong()

        while(self.waitBuffer(current_buffer, buffer_size)):

            # Convert the buffer to an image.
            check(sdk3_utility.AT_ConvertBuffer(current_buffer,
                                                ctypes.c_void_p(self.frame_data[self.frame_data_cur].getDataPtr()),
                                                ctypes.c_long(self.frame_x),
                                                ctypes.c_long(self.frame_y),
                                                ctypes.c_long(self.stride),
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

        return [frames, [self.frame_x, self.frame_y]]

    def getProperty(self, pname, ptype):
        if self.isEnumerated(pname):
            ptype = "enum"

        if (ptype == "bool"):
            return getBoolean(self.camera_handle, pname)
        elif (ptype == "enum"):
            return getEnumeratedString(self.camera_handle, pname)
        elif (ptype == "float"):
            return getFloat(self.camera_handle, pname)
        elif (ptype == "int"):
            return getInteger(self.camera_handle, pname)
        elif (ptype == "str"):
            return getString(self.camera_handle, pname)
        else:
            print("Unknown type", ptype, "for", pname)

    def hasFeature(self, pname):
        implemented = ctypes.c_bool(False)
        if check(sdk3.AT_IsImplemented(self.camera_handle, ctypes.c_wchar_p(pname), ctypes.byref(implemented))):
            return implemented.value
        else:
            return False

    def isEnumerated(self, pname):
        if pname in self.enumerated:
            return True
        else:
            return False

    def setProperty(self, pname, ptype, pvalue):
        #print "Setting: " + str(pname) + " " + str(ptype) + ": " + str(pvalue)
        # Handle a few special cases:
        if pname is "ExposureTime":
            setFloat(self.camera_handle, pname, pvalue)

            #
            # Force frame rate to highest value possible
            #
            # This will fail for some trigger modes, so we catch the
            # exception and print a warning.
            # 
            try:
                setFloat(self.camera_handle, "FrameRate", 1/(pvalue + 0.025)) # 25 ms was an empirical determination of deadtime
            except AndorException as e:
                print("Ignoring", str(e))
                
        elif pname is "FrameRate":
            print("WARNING: Setting FrameRate is not supported")
            setFloat(self.camera_handle, pname, pvalue)
            setFloat(self.camera_handle, "ExposureTime", 0) # Force exposure time to lowest possible value
            raise AndorException("FrameRate is not supported") # Raise a hardware error

        else:
            if self.isEnumerated(pname):
                ptype = "enum"

            if (ptype == "bool"):
                setBoolean(self.camera_handle, pname, pvalue)
            elif (ptype == "enum"):
                setEnumeratedString(self.camera_handle, pname, pvalue)
            elif (ptype == "float"):
                setFloat(self.camera_handle, pname, pvalue)
            elif (ptype == "int"):
                setInteger(self.camera_handle, pname, pvalue)
            elif (ptype == "str"):
                setString(self.camera_handle, pname, pvalue)
            else:
                print("Unknown type", ptype, "for", pname)
        

    def shutdown(self):
        check(sdk3.AT_Close(self.camera_handle), "AT_Close")
        check(sdk3.AT_FinaliseLibrary(), "AT_FinalizeLibrary")
        check(sdk3_utility.AT_FinaliseUtilityLibrary(), "AT_FinalizeUtilityLibrary")

    def startAcquisition(self):
        self.captureSetup()
        #setEnumeratedString(self.camera_handle, "CycleMode", "Continuous")
        sendCommand(self.camera_handle, "AcquisitionStart")

    def stopAcquisition(self):
        sendCommand(self.camera_handle, "AcquisitionStop")
        check(sdk3.AT_Flush(self.camera_handle), "AT_Flush")

    def waitBuffer(self, current_buffer, buffer_size):
        resp = sdk3.AT_WaitBuffer(self.camera_handle, ctypes.byref(current_buffer), ctypes.byref(buffer_size), 0)
        if (resp == 100):
            raise AndorException("Andor thinks there will be a buffer overflow, sigh..")
        elif (resp == 0):
            return True
        elif (resp == 13):
            return False
        else:
            print(resp)
            raise AndorException("Unexpected response " + str(resp))


if (__name__ == "__main__"):
    loadSDK3DLL("C:/Program Files/Andor SOLIS/")

    if False:
        cam1 = SDK3Camera(camera_id = 0)
        cam2 = SDK3Camera(camera_id = 1)
        for cam in [cam1, cam2]:
            print("model", cam.getProperty("CameraModel", "str"))
            print("name", cam.getProperty("CameraName", "str"))
            print("xsize", cam.getProperty("SensorWidth", "int"))
            print("ysize", cam.getProperty("SensorHeight", "int"))
            print("target", cam.getProperty("TemperatureControl", "enum"))
            print("shutdown")
            cam.shutdown()
            print("done")

    if True:
        cam = SDK3Camera(camera_id = 0)
        cam.setProperty("AOIWidth", "int", 2048)
        cam.setProperty("AOIHeight", "int", 2048)
        cam.setProperty("ExposureTime", "float", 0.01)
        cam.setProperty("CycleMode", "enum", "Fixed")
        cam.setProperty("FrameCount", "int", 10)
        cam.startAcquisition()
        for i in range(20):
            frames = cam.getFrames()[0]
            for frame in frames:
                print(i, frame.getData()[0])
            time.sleep(0.1)
        cam.stopAcquisition()
        print("shutdown")
        cam.shutdown()
        print("done")


#    print "close"
#    closeSDK3DLL()


