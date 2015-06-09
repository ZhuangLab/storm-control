# George Emanuel
#
# Not optimized for readout speed. Poor memory management. New memory is 
# allocated for each frame. Buffering code should be moved into its own
# class and optimized.
#
# 2015

from ctypes import *
import time
import thread

zyla = 0
zylaUtility = 0
def loadZylaDLL(zyla_dll = "atcore.dll"):
    global zyla, zylaUtility
    if (zyla == 0):
	zyla = oledll.LoadLibrary(zyla_dll)
	zylaUtility = oledll.LoadLibrary("atutility.dll")
	zyla.AT_InitialiseLibrary()
	zylaUtility.AT_InitialiseUtilityLibrary()

def closeZylaDLL():
    if (zyla is not 0):
	zyla.AT_FinaliseLibrary()

# Wrapper functions for DLL

def getCameraCount():
    return getInteger(1, "Device Count")

def sendCommand(handle, command):
    return zyla.AT_Command(handle, c_wchar_p(command))

def getString(handle, command):
    maxLength = c_int()
    error = zyla.AT_GetStringMaxLength(
		    handle, c_wchar_p(command), byref(maxLength))
    if (error is not 0):
        return ''
    response = c_wchar_p(' '*maxLength.value)
    error = zyla.AT_GetString(handle, c_wchar_p(command), response, maxLength)
    if (error is not 0):
        return ''
    return response.value

def setString(handle, command, string):
    return zyla.AT_SetString(handle, c_wchar_p(command), c_wchar_p(string))

def setEnumeratedString(handle, command, string):
    return zyla.AT_SetEnumString(handle, c_wchar_p(command), c_wchar_p(string))

def setEnumeratedIndex(handle, command, index):
    return zyla.AT_SetEnumIndex(handle, c_wchar_p(command), c_longlong(index))

def getEnumeratedIndex(handle, command):
    readIndex = c_longlong()
    error = zyla.AT_GetEnumIndex(handle, c_wchar_p(command), byref(readIndex))
    if (error is not 0):
	return -1
    return readIndex.value

def getEnumeratedString(handle, command):
    response = c_wchar_p(' '*100)
    error = zyla.AT_GetEnumStringByIndex(handle, c_wchar_p(command), 
		    c_longlong(getEnumeratedIndex(handle, command)),
	            response, 100)
    if (error is not 0):
        return ''
    return response.value

def getInteger(handle, command):
    readInt = c_longlong()
    error = zyla.AT_GetInt(handle, c_wchar_p(command), byref(readInt))
    if (error is not 0): 
	return -1
    return readInt.value

def setInteger(handle, command, value):
    return zyla.AT_SetInt(handle, c_wchar_p(command), c_longlong(value))

def getBoolean(handle, command):
    readBool = c_bool()
    error = zyla.AT_GetBool(handle, command, byref(readBool))
    return readBool.value

def setBoolean(handle, command, boolValue):
    return zyla.AT_SetBool(handle, command, c_bool(boolValue))

def getFloat(handle, command):
    readFloat = c_double()
    error = zyla.AT_GetFloat(handle, c_wchar_p(command), byref(readFloat))
    if (error is not 0):
	return -1
    return readFloat.value

def setFloat(handle, command, floatValue):
    return zyla.AT_SetFloat(handle, c_wchar_p(command), c_double(floatValue))


class ZylaCamera:

    def __init__(self, cameraID = 0):
        self.cameraHandle = c_long()
	zyla.AT_Open(cameraID, byref(self.cameraHandle))

	self._properties = {}

	self._properties["Name"] = getString(self.cameraHandle,
			"CameraName")
	self._properties["Model"] = getString(self.cameraHandle,
			"CameraModel")
	self._properties["Model"] = getString(self.cameraHandle,
			"CameraModel")
	self._properties["XPixels"] = getInteger(self.cameraHandle,
			"SensorWidth")
	self._properties["YPixels"] = getInteger(self.cameraHandle,
			"SensorHeight")

	self.frame_size = [self._properties["XPixels"], 
			self._properties["YPixels"]]
	self.setExposureTime(0.1)
	self.setCycleMode("Continuous")

        self.frameBuffer = []
	self.bufferCycleThread = 0;


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
	imageSize = c_longlong(getInteger(self.cameraHandle, "ImageSizeBytes"))

        self.bufferCycleThread = thread.start_new_thread(
			self._acquireCycleBuffers, ())
	
    ## acquireCycleBuffers
    #
    # Begins acquisition, waits for buffers, 
    # and requeues them and converts the output to 16bit and adds it to 
    # our image buffer
    #
    def _acquireCycleBuffers(self):
	imageSize = c_longlong(getInteger(self.cameraHandle, "ImageSizeBytes"))

	imageBuffers = [] 
	for i in range(50):
	    imageBuffers.append(create_string_buffer(imageSize.value))
	    zyla.AT_QueueBuffer(self.cameraHandle, imageBuffers[i], imageSize)
	    
        sendCommand(self.cameraHandle, "AcquisitionStart")
	currentBuffer = POINTER(c_char)()
	bufferSize = c_longlong()

	noError = True
	#this causes problems if acquisition was stopped while we
	# were waiting for the next frame
	while (zyla.AT_WaitBuffer(self.cameraHandle, byref(currentBuffer), 
		    byref(bufferSize), 10000) is 0):
            newImage = create_string_buffer(2*self.frame_size[0]*
			    self.frame_size[1])
            zylaUtility.AT_ConvertBuffer(currentBuffer, 
			    newImage,
			    self.frame_size[0], self.frame_size[1],
			    self.stride, c_wchar_p("Mono16"),
			    c_wchar_p("Mono16"))

	    #atomic operation
	    self.frameBuffer.append(newImage)

	    error = zyla.AT_QueueBuffer(self.cameraHandle, 
			    currentBuffer, 
			    bufferSize)
   
    def _abortIfAcquiring(self):
        if (self.isAcquiring()):
            self.stopAcquisition()

    def stopAcquisition(self):
	sendCommand(self.cameraHandle, "AcquisitionStop")
	zyla.AT_Flush(self.cameraHandle)

    def shutdown(self):
        self._abortIfAcquiring()
	time.sleep(0.5)
	zyla.AT_Close(self.cameraHandle)
	zylaUtility.AT_FinaliseUtilityLibrary()



