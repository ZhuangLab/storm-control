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

def check(value, fn_name = "??"):
    if (value != 0):
        print "Error", value, "when calling function", fn_name
        return False
    else:
        print fn_name
        return True


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
        self.cameraHandle = ctypes.c_long()
	check(sdk3.AT_Open(cameraID, ctypes.byref(self.cameraHandle)), "AT_Open")

	self._properties = {}

	#self._properties["Name"] = getString(self.cameraHandle,
        #			"CameraName")
	#self._properties["Model"] = getString(self.cameraHandle,
	#		"CameraModel")
	#self._properties["Model"] = getString(self.cameraHandle,
	#		"CameraModel")
	#self._properties["XPixels"] = getInteger(self.cameraHandle,
	#		"SensorWidth")
	#self._properties["YPixels"] = getInteger(self.cameraHandle,
        #			"SensorHeight")
        #
	#self.frame_size = [self._properties["XPixels"], 
        #self._properties["YPixels"]]
	#self.setExposureTime(0.1)
	#self.setCycleMode("Continuous")

        #self.frameBuffer = []
	#self.bufferCycleThread = 0;


    def getCameraModel(self):
	return self._properties["Model"]

    def getDimensions(self):
	return [self._properties["XPixels"], self._properties["YPixels"]]

    def coolerOff(self):
	setBoolean(self.cameraHandle, "SensorCooling", 0)
 
    def coolerOn(self):
	setBoolean(self.cameraHandle, "SensorCooling", 1)

    ## setFanSpeed
    #
    # Set the fan speed of the camera
    #
    # @param fanSpeed the fan speed either "Off" or "On". Zyla does not 
    # support "low"
    def setFanMode(self, fanSpeed):
	setEnumeratedString(self.cameraHandle, "FanSpeed", fanSpeed)

    ## setTriggerMode
    #
    # Set the trigger mode of the camera
    #
    # @param triggerMode the trigger mode, either "Internal", "Software",
    # "External", "External Start", or "External Exposure"
    #
    def setTriggerMode(self, triggerMode):
	setEnumeratedString(self.cameraHandle, "TriggerMode", triggerMode)

    def getTemperature(self):
	return getFloat(self.cameraHandle, "SensorTemperature")

    def getExposureTime(self):
	return getFloat(self.cameraHandle, "ExposureTime")

    def setExposureTime(self, exposureTime):
        setFloat(self.cameraHandle, "ExposureTime", exposureTime)

    def getFrameRate(self):
	return getFloat(self.cameraHandle, "FrameRate")

    def setFrameRate(self, frameRate):
	setFloat(self.cameraHandle, "FrameRate", frameRate)

    ##setROIAndBinning
    #
    # Set the ROI and binning
    #
    # @param region [x1, x2, y1, y2] with x1<x2<XPixels and y1<y2<YPixels
    # @param binning [bx, by] the number of pixels to bin in x and y
    def setROIAndBinning(self, region, binning):
	setInteger(self.cameraHandle, "AOIHBin", binning[0])
	setInteger(self.cameraHandle, "AOIVBin", binning[1])
        setEnumeratedString(self.cameraHandle, "AOIBinning", str(binning) +
			"x" + str(binning))
	setInteger(self.cameraHandle, "AOIHeight", region[3]-region[2])
	setInteger(self.cameraHandle, "AOIWidth", region[1]-region[0])
	setInteger(self.cameraHandle, "AOILeft", region[0])
	setInteger(self.cameraHandle, "AOITop", region[2])

	self.ROI = region
	self.binning = binning
	self.x_pixels = (self.ROI[1] - self.ROI[0] + 1)/self.binning[0]
	self.y_pixels = (self.ROI[3] - self.ROI[2] + 1)/self.binning[1]
	self.pixels = self.x_pixels * self.y_pixels
	self.stride = getInteger(self.cameraHandle, "AOIStride")
	self.frame_size = [self.x_pixels, self.y_pixels]

    ##setCycleMode
    #
    # Sets the cycle mode for the camera
    #
    # @param mode the cycle mode. Either "Fixed" or "Continuous"
    #
    def setCycleMode(self, mode):
	setEnumeratedString(self.cameraHandle, "CycleMode", mode)

    def getCycleMode(self):
	return getEnumeratedString(self.cameraHandle, "CycleMode")

    def setFrameCount(self, frameCount):
	setInteger(self.cameraHandle, "FrameCount", frameCount)

    ## getImages16
    # 
    # Returns all new images in the acquisition buffer and empties the buffer.
    #
    # @return a 3 element array. The first element is an array containing the
    # frames acquired (possibly empty). The second is the image size.
    # The third is the state of the camera.
    #
    def getImages16(self):

	newImages = self.frameBuffer

	#empty the buffer and remove our reference to that memory so
	#it can be garbage collected
	self.frameBuffer = []

	print newImages

	if (self.isAcquiring()):
            return [newImages, self.frame_size, "acquiring"]

        else:
            return [newImages, self.frame_size, "idle"]

    ## getOldestImage16
    #
    # Returns the newest image and doesn't remove it from the buffer
    #
    def getOldestImage16(self):
        return [self.newImages[-1], self.frame_size, self.isAcquiring()]

    def isAcquiring(self):
	return getBoolean(self.cameraHandle, "CameraAcquiring")

    ##startAcquisition
    #
    # Begins acquiring images from this camera. If the images are not being
    # recorded, a circular buffer is used. If the images are being recorded,
    # the necesary memory is allocated and then acqusition begins, filling
    # up this memory.
    #
    def startAcquisition(self):
	imageSize = ctpyes.c_longlong(getInteger(self.cameraHandle, "ImageSizeBytes"))

#        self.bufferCycleThread = thread.start_new_thread(self._acquireCycleBuffers, ())
	
    ## acquireCycleBuffers
    #
    # Begins acquisition, waits for buffers, 
    # and requeues them and converts the output to 16bit and adds it to 
    # our image buffer
    #
#    def _acquireCycleBuffers(self):
#	imageSize = c_longlong(getInteger(self.cameraHandle, "ImageSizeBytes"))
#
#	imageBuffers = [] 
#	for i in range(50):
#	    imageBuffers.append(create_string_buffer(imageSize.value))
#	    check(sdk3.AT_QueueBuffer(self.cameraHandle, imageBuffers[i], imageSize), "AT_QueueBuffer")
#	    
#        sendCommand(self.cameraHandle, "AcquisitionStart")
#	currentBuffer = POINTER(c_char)()
#	bufferSize = c_longlong()
#
#	noError = True
#	#this causes problems if acquisition was stopped while we
#	# were waiting for the next frame
#	while (zyla.AT_WaitBuffer(self.cameraHandle, byref(currentBuffer), 
#		    byref(bufferSize), 10000) is 0):
#            newImage = create_string_buffer(2*self.frame_size[0]*
#			    self.frame_size[1])
#            zylaUtility.AT_ConvertBuffer(currentBuffer, 
#			    newImage,
#			    self.frame_size[0], self.frame_size[1],
#			    self.stride, c_wchar_p("Mono16"),
#			    c_wchar_p("Mono16"))
#
#	    #atomic operation
#	    self.frameBuffer.append(newImage)
#
#	    error = zyla.AT_QueueBuffer(self.cameraHandle, 
#			    currentBuffer, 
#			    bufferSize)
   
    def _abortIfAcquiring(self):
        if (self.isAcquiring()):
            self.stopAcquisition()

    def stopAcquisition(self):
	sendCommand(self.cameraHandle, "AcquisitionStop")
	check(sdk3.AT_Flush(self.cameraHandle), "AT_Flush")

    def shutdown(self):
        self._abortIfAcquiring()
	time.sleep(0.5)
	check(sdk3.AT_Close(self.cameraHandle), "AT_Close")
	check(sdk3_utility.AT_FinaliseUtilityLibrary(), "AT_FinalizeUtilityLibrary")


if (__name__ == "__main__"):
    loadSDK3DLL("C:/Program Files/Andor SOLIS/")
    print getCameraCount()
    cam = SDK3Camera()
    cam.shutdown()
    closeSDK3DLL()


