#!/usr/bin/python
#
## @file
#
# A ctypes based interface to Andor SDK3.
#
# George ?/15.
# Hazen 9/15.
#

import ctypes
import time

sdk3 = None
sdk3_utility = None


# Loading the DLL

def loadSDK3DLL(path):
    global sdk3, sdk3_utility
    if sdk3 is None:
	sdk3 = ctypes.oledll.LoadLibrary(path + "atcore.dll")
	sdk3_utility = ctypes.oledll.LoadLibrary(path + "atutility.dll")
	check(sdk3.AT_InitialiseLibrary(), "AT_InitializeLibrary")
	check(sdk3_utility.AT_InitialiseUtilityLibrary(), "AT_InitialiseUtilityLibrary")

def closeSDK3DLL():
    if sdk3 is not None:
	sdk3.AT_FinaliseLibrary()


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
    if check(sdk3.AT_GetEnumIndex(handle, ctypes.c_wchar_p(command), ctypes.byref(readIndex)), "AT_GetEnumIndex"):
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
    return check(sdk3.AT_SetEnumString(handle, c_wchar_p(command), c_wchar_p(string)), "AT_SetEnumString")

def setEnumeratedIndex(handle, command, index):
    return check(sdk3.AT_SetEnumIndex(handle, c_wchar_p(command), c_longlong(index)), "AT_SetEnumIndex")

def setFloat(handle, command, float_value):
    return check(sdk3.AT_SetFloat(handle, c_wchar_p(command), c_double(float_value)), "AT_SetFloat")

def setInteger(handle, command, value):
    return check(sdk3.AT_SetInt(handle, c_wchar_p(command), c_longlong(value)), "AT_SetInt")

def setString(handle, command, string):
    return check(sdk3.AT_SetString(handle, c_wchar_p(command), c_wchar_p(string)), "AT_SetString")


class SDK3Camera:

    def __init__(self, cameraID = 0):
        self.camera_handle = ctypes.c_long()
	check(sdk3.AT_Open(cameraID, ctypes.byref(self.camera_handle)), "AT_Open")

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
            print "Unknown type", ptype

    def shutdown(self):
	check(sdk3.AT_Close(self.camera_handle), "AT_Close")
	check(sdk3_utility.AT_FinaliseUtilityLibrary(), "AT_FinalizeUtilityLibrary")


if (__name__ == "__main__"):
    loadSDK3DLL("C:/Program Files/Andor SOLIS/")
    print getCameraCount()
    cam = SDK3Camera()
    print "model", cam.getProperty("CameraModel", "str")
    print "name", cam.getProperty("CameraName", "str")
    print "xsize", cam.getProperty("SensorWidth", "int")
    print "ysize", cam.getProperty("SensorHeight", "int")
    cam.shutdown()
    closeSDK3DLL()


