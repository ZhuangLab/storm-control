#!/usr/bin/python
#
## @file
#
# A ctypes based interface to Andor cameras.
# (Andor Software Version 2.82).
#
# Cameras are 1 indexed?
#
# This can control more than one camera.
#
# Hazen 09/15
#

import ctypes
import numpy
import time

import storm_control.sc_library.halExceptions as halExceptions


# Andor constants & structures.

drv_acquiring = 20072
drv_idle = 20073
drv_no_new_data = 20024
drv_not_available = 20992
drv_not_supported = 20991
drv_success = 20002
drv_tempcycle = 20074
drv_temp_not_stabilized = 20035
drv_temp_off = 20034
drv_temp_stabilized = 20036
drv_temp_not_reached = 20037
drv_temp_drift = 20040
drv_p1invalid = 20066


## AndorCapabilities
#
# The Andor camera capabilities structure.
#
class AndorCapabilities(ctypes.Structure):
    _fields_ = [("ulSize", ctypes.c_ulong),
                ("ulAcqModes", ctypes.c_ulong),
                ("ulReadModes", ctypes.c_ulong),
                ("ulTriggerModes", ctypes.c_ulong),
                ("ulCameraType", ctypes.c_ulong),
                ("ulPixelMode", ctypes.c_ulong),
                ("ulSetFunctions", ctypes.c_ulong),
                ("ulGetFunctions", ctypes.c_ulong),
                ("ulFeatures", ctypes.c_ulong),
                ("ulPCICard", ctypes.c_ulong),
                ("ulEMGainCapability", ctypes.c_ulong),
                ("ulFTReadModes", ctypes.c_ulong)]

## loadAndorDLL
#
# Handles loading the library (only once).
#
# @param andor_dll The fullpath and filename of the Andor DLL
#
andor = 0
def loadAndorDLL(andor_dll):
    global andor
    if(andor == 0):
        andor = ctypes.oledll.LoadLibrary(andor_dll)

## andorCheck
#
# Checks the return value of andor function call. Throws an error if the function
# call was not successful.
#
# @param status The returned value of the function call.
# @param message A string message, usually this is the name of the function call.
#
def andorCheck(status, message):
    if (status != drv_success):
        raise AndorEMCCDException(message + " failed with status = " + str(status))

## getAvailableCameras
#
# Dealing with multiple cameras.
#
def getAvailableCameras():
    number_cameras = ctypes.c_long()
    andorCheck(andor.GetAvailableCameras(ctypes.byref(number_cameras)), "GetAvailableCameras")
    return number_cameras.value

## getCameraHandles
#
# Get handles for the cameras that are available.
#
def getCameraHandles():
    number_cameras = getAvailableCameras()
    assert number_cameras > 0, "No Andor cameras detected!!"
    handles = []
    temp = ctypes.c_long()
    for i in range(getAvailableCameras()):
        andorCheck(andor.GetCameraHandle(i, ctypes.byref(temp)), "GetCameraHandle")
        handles.append(temp.value)
    return handles

## setCurrentCamera
#
# This sets which camera to talk to. This is called before pretty much all the
# other calls to the Andor library to be sure of talking to the correct camera.
#
# @param camera_handle The handle of the camera to make active.
#
current_handle = -1
def setCurrentCamera(camera_handle):
    global current_handle
    if camera_handle:
        if (current_handle != camera_handle):
            current_handle = camera_handle
            andorCheck(andor.SetCurrentCamera(camera_handle), "SetCurrentCamera")


## AndorException
#
# Camera exception.
#
class AndorEMCCDException(halExceptions.HardwareException):
    pass


## AndorFrameData
#
# This class stores the data in a single frame from the Andor camera.
#
class AndorFrameData():
    
    def __init__(self, np_array):
        self.np_array = np_array

    def getData(self):
        return self.np_array


## AndorCamera
#
# The camera control class.
#
class AndorCamera:

    ## __init__
    #
    # Initializes the object by initializing the camera
    # then querying it to determine its various properties.
    #
    # @param andor_path The path to the Detector.ini file.
    # @param camera_handle The handle to use for in this camera object.
    #
    def __init__(self, andor_path, camera_handle):
        self.camera_handle = camera_handle

        # General
        self.pixels = 0

        # Camera properties storage.
        self._props_ = {}

        # Initialize the camera.
        setCurrentCamera(self.camera_handle)
        andorCheck(andor.Initialize(andor_path + "Detector.ini"), "Initialize")

        # Determine camera capabilities (useful??).
        caps = AndorCapabilities(ctypes.sizeof(ctypes.c_ulong)*12,0,0,0,0,0,0,0,0,0,0,0)
        andorCheck(andor.GetCapabilities(ctypes.byref(caps)), "GetCapabilities")
        self._props_['AcqModes'] = caps.ulAcqModes
        self._props_['ReadModes'] = caps.ulReadModes
        self._props_['TriggerModes'] = caps.ulTriggerModes
        self._props_['CameraType'] = caps.ulCameraType
        self._props_['PixelMode'] = caps.ulPixelMode
        self._props_['SetFunctions'] = caps.ulSetFunctions
        self._props_['GetFunctions'] = caps.ulGetFunctions
        self._props_['Features'] = caps.ulFeatures
        self._props_['PCICard'] = caps.ulPCICard
        self._props_['EMGainCapability'] = caps.ulEMGainCapability
        self._props_['FTReadModes'] = caps.ulFTReadModes

        # Determine camera bit depth.

        # FIXME: Use andor.GetBitDepth()
        for i in [[1, 2**8], [2, 2**14], [4, 2**16], [8, 2**32]]:
            if (i[0] & self._props_['PixelMode']):
                self._props_['MaxIntensity'] = i[1]

        # Determine camera pixel size.
        x_pixels = ctypes.c_long()
        y_pixels = ctypes.c_long()
        andorCheck(andor.GetDetector(ctypes.byref(x_pixels), ctypes.byref(y_pixels)), "GetDetector")
        self._props_['XPixels'] = x_pixels.value
        self._props_['YPixels'] = y_pixels.value

        # Determine camera head model.
        head_model = ctypes.create_string_buffer(32)
        andorCheck(andor.GetHeadModel(head_model), "GetHeadModel")
        self._props_['HeadModel'] = head_model.value.decode("utf-8")

        # Determine hardware version.
        plug_in_card_version = ctypes.c_uint()
        flex_10k_file_version = ctypes.c_uint()
        dummy1 = ctypes.c_uint()
        dummy2 = ctypes.c_uint()
        camera_firmware_version = ctypes.c_uint()
        camera_firmware_build = ctypes.c_uint()
        andorCheck(andor.GetHardwareVersion(ctypes.byref(plug_in_card_version),
                                            ctypes.byref(flex_10k_file_version),
                                            ctypes.byref(dummy1),
                                            ctypes.byref(dummy2),
                                            ctypes.byref(camera_firmware_version),
                                            ctypes.byref(camera_firmware_build)),
                   "GetHardwareVersion")
        self._props_["PlugInCardVersion"] = plug_in_card_version.value
        self._props_["Flex10kFileVersion"] = flex_10k_file_version.value
        self._props_["CameraFirmwareVersion"] = camera_firmware_version.value
        self._props_["CameraFirmwareBuild"] = camera_firmware_build.value

        # Determine vertical shift speeds.
        number = ctypes.c_int()
        andorCheck(andor.GetNumberVSSpeeds(ctypes.byref(number)), "GetNumberVSSpeeds")
        self._props_["VSSpeeds"] = list(range(number.value))
        for i in range(number.value):
            index = ctypes.c_int(i)
            speed = ctypes.c_float()
            andorCheck(andor.GetVSSpeed(index, ctypes.byref(speed)), "GetVSSpeed")
            self._props_["VSSpeeds"][i] = round(speed.value, 4)

        # Determine horizontal shift speeds.
        andorCheck(andor.GetNumberADChannels(ctypes.byref(number)), "GetNumberADChannels")
        self._props_["NumberADChannels"] = number.value
        self._props_["HSSpeeds"] = list(range(number.value))
        for i in range(number.value):
            channel = ctypes.c_int(i)
            andorCheck(andor.GetNumberHSSpeeds(channel, 0, ctypes.byref(number)), "GetNumberHSSpeeds")
            self._props_["HSSpeeds"][i] = list(range(number.value))
            for j in range(number.value):
                type = ctypes.c_int(j)
                speed = ctypes.c_float()
                andorCheck(andor.GetHSSpeed(channel, 0, type, ctypes.byref(speed)), "GetHSSpeed")
                self._props_["HSSpeeds"][i][j] = round(speed.value, 4)
        
        # Determine temperature range.
        min_temp = ctypes.c_int()
        max_temp = ctypes.c_int()
        andorCheck(andor.GetTemperatureRange(ctypes.byref(min_temp), ctypes.byref(max_temp)), "GetTemperatureRange")
        self._props_["TemperatureRange"] = [min_temp.value, max_temp.value]

        # Determine preamp gains available.
        number = ctypes.c_int()
        andorCheck(andor.GetNumberPreAmpGains(ctypes.byref(number)), "GetNumberPreAmpGains")
        self._props_["PreAmpGains"] = list(range(number.value))
        for i in range(number.value):
            index = ctypes.c_int(i)
            gain = ctypes.c_float()
            andorCheck(andor.GetPreAmpGain(index, ctypes.byref(gain)), "GetPreAmpGain")
            self._props_["PreAmpGains"][i] = round(gain.value, 2)

        # Determine EM gain range.
        low = ctypes.c_int()
        high = ctypes.c_int()
        andorCheck(andor.GetEMGainRange(ctypes.byref(low), ctypes.byref(high)), "GetEMGainRange")
        self._props_["EMGainRange"] = [low.value, high.value]

        # Determine number of EM gain modes.
        n_modes = 0
        while (self.setEMGainMode(n_modes)):
            n_modes += 1
        self._props_["NumberEMGainModes"] = n_modes - 1
        self.setEMGainMode(0)

        # Determine the maximum binning values.
        max_binning = ctypes.c_int()
        andorCheck(andor.GetMaximumBinning(4, 0, ctypes.byref(max_binning)), "GetMaximumBinning")
        self._props_["MaxBinning"] = [max_binning.value]
        andorCheck(andor.GetMaximumBinning(4, 1, ctypes.byref(max_binning)), "GetMaximumBinning")
        self._props_["MaxBinning"].append(max_binning.value)
        
        # Determine maximum exposure time.
        max_exp = ctypes.c_float()
        andorCheck(andor.GetMaximumExposure(ctypes.byref(max_exp)), "GetMaximumExposure")
        self._props_["MaxExposure"] = max_exp.value

    #
    # Helper functions.
    #

    ## _getStatus_
    #
    # Gets the camera status.
    #
    # @return Returns the camera status.
    #
    def _getStatus_(self):
        i_state = ctypes.c_int()
        andorCheck(andor.GetStatus(ctypes.byref(i_state)), "GetStatus")
        return i_state.value

    ## _abortIfAcquiring)
    #
    # Stops the camera if the camera is currently acquiring.
    #
    def _abortIfAcquiring_(self):
        state = self._getStatus_()
        if state == drv_acquiring :
            andorCheck(andor.AbortAcquisition(), "AbortAcquisition")
        elif state != drv_idle and state != drv_tempcycle:
            raise AndorEMCCDException("Driver is in a bad place?: " + str(state))

    ## closeShutter
    #
    # Close the camera shutter. This will abort the current acquisition.
    def closeShutter(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetShutter(0, 2, 0, 0)
        if (status != drv_success):
            print("SetShutter (closed) failed: ", status)

    ## coolerOff
    #
    # Turn the camera cooling off.
    #
    def coolerOff(self):
        setCurrentCamera(self.camera_handle)
        andorCheck(andor.CoolerOFF(), "CoolerOff")

    ## coolerOn
    #
    # Turn the camera cooling on.
    #
    def coolerOn(self):
        setCurrentCamera(self.camera_handle)
        andorCheck(andor.CoolerON(), "CoolerOn")

    ## getAcquisitionTimings
    #
    # Get the acquisition timings. This will abort the current acquisition.
    #
    # @return Return the acquisition timings.
    #
    def getAcquisitionTimings(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        exposure = ctypes.c_float()
        accumulate = ctypes.c_float()
        kinetic = ctypes.c_float()
        andorCheck(andor.GetAcquisitionTimings(ctypes.byref(exposure), ctypes.byref(accumulate), ctypes.byref(kinetic)),
                   "GetAcqisitionTimings")
        return [exposure.value, kinetic.value, accumulate.value]

    ## getCameraSize
    #
    # @return The size of camera in pixels
    #
    def getCameraSize(self):
        return [self._props_['XPixels'], self._props_['YPixels']]

    ## getCurrentSetup
    #
    # Get the current camera setup.
    #
    # @return Return the current camera setup.
    #
    def getCurrentSetup(self):
        try:
            return {'acqmode': self.acqmode,
                    'adchannel': self.adchannel,
                    'exposure_time': self.exposure_time,
                    'frame_transfer_mode': self.frame_transfer_mode,
                    'hsspeed': self.hsspeed,
                    'kinetic_cycle_time': self.kinetic_cycle_time,
                    'ROI': self.ROI,
                    'binning': self.binning,
                    'vsspeed': self.vsspeed}

        # FIXME: This should be more specific.
        except Exception as exception:
            print(str(exception))
            print("getCurrentSetup: One or more parameters are not defined.")

    ## getDimensions
    #
    # Return the camera dimensions
    #
    # @return Returns the camera dimensions in pixels.
    #
    def getDimensions(self):
        return [self._props_["XPixels"], self._props_["YPixels"]]

    ## getHeadModel
    #
    # Return the camera head model
    #
    # @return Returns the camera head model.
    #
    def getHeadModel(self):
        return self._props_["HeadModel"]

    ## getHSSpeeds
    #
    # Return the camera horizontal speeds
    #
    # @return Returns the camera horizontal speeds.
    #
    def getHSSpeeds(self):
        return self._props_["HSSpeeds"]

    ## getEMAdvanced
    #
    # Get the current advanced EM setting.
    #
    # @return Return the advanced EM setting (1 or 0).
    #
    def getEMAdvanced(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        state = ctypes.c_int()
        andorCheck(andor.GetEMAdvanced(ctypes.byref(state)), "GetEMAdvanced")
        return state.value

    ## getEMGainRange
    #
    # Get the EM gain range. This will abort the current acquisition.
    #
    # @return Return the EM gain range.
    #
    def getEMGainRange(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        low = ctypes.c_int()
        high = ctypes.c_int()
        andorCheck(andor.GetEMGainRange(ctypes.byref(low), ctypes.byref(high)), "GetEMGainRange")
        return [low.value, high.value]

    ## getFrames
    #
    # Gets all of the available frames.
    #
    # @return [frames, [frame x size, frame y size]]
    #
    def getFrames(self):
        setCurrentCamera(self.camera_handle)
        frames = []

        # Check whether camera is idle or acquiring first.
        state = self._getStatus_()

        # Check to see if there is any new data, and if so, how much.
        first = ctypes.c_long(0)
        last = ctypes.c_long(0)
        status = andor.GetNumberNewImages(ctypes.byref(first), ctypes.byref(last))

        # There is new data.
        if (status == drv_success):

            # Allocate space & get the data.
            diff = last.value - first.value + 1
            buffer_size = self.pixels * diff
            data_buffer = numpy.ascontiguousarray(numpy.empty(buffer_size, dtype = numpy.uint16))
            valid_first = ctypes.c_long(0)
            valid_last = ctypes.c_long(0)
            status = andor.GetImages16(first, 
                                       last, 
                                       data_buffer.ctypes.data, 
                                       ctypes.c_ulong(buffer_size), 
                                       ctypes.byref(valid_first), 
                                       ctypes.byref(valid_last))

            # FIXME: Should we raise an AndorException here? This almost always
            #        means something has gone wrong.
            if (first.value != valid_first.value):
                print("getImages16 first value problem", first.value, valid_first.value)
            if (last.value != valid_last.value):
                print("getImages16 last value problem", last.value, valid_last.value)

            # Got the data. Split the data buffer up into frames.
            if (status == drv_success):
                for i in range(diff):
                    frames.append(AndorFrameData(data_buffer[i*self.pixels:(i+1)*self.pixels]))
                return [frames, self.frame_size]
                    
            # Not sure if we can actually end up here, but just in case.
            elif (status == drv_no_new_data):
                return [frames, self.frame_size]

            # Something bad happened.
            else:
                raise AndorEMCCDException("andor.GetImages16 failed with error code: " + str(status))

        # There is no new data.
        elif (status == drv_no_new_data):
            return [frames, self.frame_size]

        # Something bad must have happened.
        else:
            raise AndorEMCCDException("andor.GetNumberNewImages failed with error code: " + str(status))

    ## getImages16
    #
    # This works, but it is deprecated, use getFrames().
    #
    # Returns all the new images in the acquisition buffer.
    #
    # Returns a 2 element array. The first element is an array
    # containing the frames acquired (possibly an empty array). The 
    # second is the current state of the camera.
    #
    # @return Returns the images as an array of ctypes string buffers each of which contains the frame data.
    #
    def getImages16(self):
        setCurrentCamera(self.camera_handle)
        frames = []

        # Check whether camera is idle or acquiring first.
        state = self._getStatus_()

        # Check to see if there is any new data, and if so, how much.
        first = ctypes.c_long(0)
        last = ctypes.c_long(0)
        status = andor.GetNumberNewImages(ctypes.byref(first), ctypes.byref(last))

        # There is new data.
        if (status == drv_success):

            # Allocate space & get the data.
            diff = last.value - first.value + 1
            buffer_size = self.pixels * diff
            data_buffer = ctypes.create_string_buffer(2 * buffer_size)
            valid_first = ctypes.c_long(0)
            valid_last = ctypes.c_long(0)
            status = andor.GetImages16(first, last, data_buffer, ctypes.c_ulong(buffer_size), ctypes.byref(valid_first), ctypes.byref(valid_last))
            if (first.value != valid_first.value):
                print("getImages16 first value problem", first.value, valid_first.value)
            if (last.value != valid_last.value):
                print("getImages16 last value problem", last.value, valid_last.value)

            # Got the data. Split the data buffer up into frames.
            if (status == drv_success):
                for i in range(diff):
                    frames.append(data_buffer[2*i*self.pixels:2*(i+1)*self.pixels])
                if (state == drv_idle):
                    return [frames, self.frame_size, "idle"]
                else:
                    return [frames, self.frame_size, "acquiring"]

            # Not sure if we can actually end up here, but just in case.
            elif (status == drv_no_new_data):
                if (state == drv_idle):
                    return [frames, self.frame_size, "idle"]
                else:
                    return [frames, self.frame_size, "acquiring"]

            # Something bad happened.
            else:
                raise AndorEMCCDException("GetImages16 failed: " + str(status))

        # There is no new data.
        elif (status == drv_no_new_data):
            if (state == drv_idle):
                return [frames, self.frame_size, "idle"]
            else:
                return [frames, self.frame_size, "acquiring"]

        # Something bad must have happened.
        else:
            raise AndorEMCCDException("GetNumberNewImages failed: " + str(status))

    ## getMaxBinning
    #
    # @return [max binning in x, max binning in y]
    #
    def getMaxBinning(self):
        return self._props_["MaxBinning"]

    ## getMaxExposure
    #
    # @return The maximum exposure time (in seconds)
    #
    def getMaxExposure(self):
        return self._props_["MaxExposure"]

    ## getMaxIntensity
    #
    # @return The maximum intensity the camera can record.
    def getMaxIntensity(self):
        return self._props_['MaxIntensity']

    ## getNumberADChannels
    #
    # @return The number of AD channels available
    #
    def getNumberADChannels(self):
        return self._props_["NumberADChannels"]

    ## getNumberEMGainModes
    #
    # @return How many EM gain modes the camera supports.
    #
    def getNumberEMGainModes(self):
        return self._props_["NumberEMGainModes"]

    ## getOldestImage16
    #
    # This works, but it is deprecated, use getFrames().
    #
    # Returns the oldest image in the acquisition buffer. 
    # Call until there is no new data.
    #
    # Returns the a 2 element array. The first element
    # is the frame data, or 0 if there are no new frames.
    # The second element is the state of the camera, i.e.
    # is it acquiring data? Or is it idle?
    #
    # Use this function with 16 bit cameras.
    #
    # @return Returns the oldest frame as a ctypes string buffer.
    #
    def getOldestImage16(self, check = True):
        setCurrentCamera(self.camera_handle)
        if check:
            first = ctypes.c_long(0)
            last = ctypes.c_long(0)
            andor.GetNumberNewImages(ctypes.byref(first), ctypes.byref(last))
            diff = first.value - last.value
            if (diff > 1):
                print("  warning: acquisition is", diff, "frames behind...")
        c_buffer = ctypes.create_string_buffer(2 * self.pixels)
        status = andor.GetOldestImage16(c_buffer, ctypes.c_ulong(self.pixels))
        if status == drv_success:
            return [c_buffer, self.frame_size, "acquiring"]
        elif status == drv_no_new_data:
            state = _getStatus_()
            if state == drv_idle:
                return [0, self.frame_size, "idle"]
            else:
                return [0, self.frame_size, "acquiring"]
        else:
            raise AndorEMCCDException("GetOldestImage16 failed: " + str(status))

    ## getPreampGains
    #
    # @return Return the available pre-amp gains.
    #
    def getPreampGains(self):
        return self._props_["PreAmpGains"]

    ## getProperties
    #
    # Return all the known camera properties
    #
    # @return Returns the camera properties.
    #
    def getProperties(self):
        return self._props_

    ## getTemperature
    #
    # Return the current camera temperature.
    #
    # @return Return the camera temperature.
    #
    def getTemperature(self):
        setCurrentCamera(self.camera_handle)
        temperature = ctypes.c_int()
        status = andor.GetTemperature(ctypes.byref(temperature))
        if status == drv_temp_stabilized:
            return [temperature.value, "stable"]
        elif (status == drv_temp_off) or (status == drv_temp_not_stabilized) or (status == drv_temp_not_reached) or (status == drv_temp_drift):
            return [temperature.value, "unstable"]
        else:
            print("GetTemperature failed: ", status)
            return [50, "unstable"]

    ## getTemperatureRange
    #
    # @return [min temperature, max_temperature]
    #
    def getTemperatureRange(self):
        return self._props_["TemperatureRange"]

    ## getVSSpeeds
    #
    # Return the camera vertical speeds
    #
    # @return Returns the camera vertical speeds.
    #
    def getVSSpeeds(self):
        return self._props_["VSSpeeds"]

    ## goToTemperature
    #
    # Loops until the camera stabilizes at the desired temperature.
    #
    # @param temperature The desired temperature.
    #
    def goToTemperature(self, temperature):
        setCurrentCamera(self.camera_handle)
        self.setTemperature(temperature)
        status = self.getTemperature()
        while (status[1] == "unstable"):
            time.sleep(5)
            status = camera.getTemperature()

    ## openShutter
    #
    # Open the camera shutter. This will abort the current acquisition.
    #
    def openShutter(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetShutter(0, 1, 0, 0)
        if (status != drv_success):
            print("SetShutter (open) failed: ", status)

    ## setACQMode
    #
    # Sets up the camera in the appropriate acquisition mode &
    # returns the acquisition timing. This will abort the current acquisition.
    #
    # @param mode Is one of "single_frame", "fixed_length" or "run_till_abort"
    # @param number_frames (Optional) The number of frames. This must be specified for the "fixed_length" mode.
    #
    def setACQMode(self, mode, number_frames = "undef"):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        if (mode == "single_frame"):
            andorCheck(andor.SetAcquisitionMode(1), "SetAcquisitionMOde")
        elif (mode == "fixed_length"):
            andorCheck(andor.SetAcquisitionMode(3), "SetAcquisitionMode")
            andorCheck(andor.SetNumberAccumulations(1), "SetNumberAccumulations")
            andorCheck(andor.SetAccumulationCycleTime(0), "SetAccumulationCycleTime")
            andorCheck(andor.SetNumberKinetics(ctypes.c_int(number_frames)), "SetNumberKinetics")
        elif (mode == "run_till_abort"):
            andorCheck(andor.SetAcquisitionMode(5), "SetAcquisitionMode")
        else:
            print("Unknown mode: " + mode)
            return
        self.acqmode = mode

    ## setADChannel
    #
    # Set which ADChannel the camera should use.
    #
    # @param channel The number of the channel to use.
    #
    def setADChannel(self, channel):
        setCurrentCamera(self.camera_handle)
        if (channel >= 0) and (channel < self._props_["NumberADChannels"]):
            self._abortIfAcquiring_()
            andorCheck(andor.SetADChannel(ctypes.c_int(channel)), "SetADChannel")
            andorCheck(andor.SetOutputAmplifier(ctypes.c_int(channel)), "SetOutputAmplifier")
            self.adchannel = channel
        else:
            print("Invalid channel: ", channel)

    ## setBaselineClamp
    #
    # Turn the baseline clamp on or off.
    #
    # @param active True/False baseline clamp on/off
    #
    def setBaselineClamp(self, active):
        setCurrentCamera(self.camera_handle)
        if active:
            active = 1
        else:
            active = 0
        andorCheck(andor.SetBaselineClamp(ctypes.c_int(active)), "SetBaselineClamp")

    ## setEMAdvanced
    #
    # Allow access to higher EM gain levels.
    #
    # @param enable True/False to enable access.
    #
    def setEMAdvanced(self, enable):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        if enable:
            enable = 1
        else:
            enable = 0
        status = andor.SetEMAdvanced(ctypes.c_int(enable))
        if (enable == 1):
            andorCheck(status, "SetEMAdvanced")
        else:
            if (status == drv_not_supported):
                return
            if (status == drv_not_available):
                return
            andorCheck(status, "SetEMAdvanced")

    ## setEMCCDGain
    #
    # Set the camera EM gain.
    #
    # @param gain The camera gain value.
    #
    def setEMCCDGain(self, gain):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetEMCCDGain(ctypes.c_int(gain)), "SetEMCCDGain")

    ## setEMGainMode
    #
    # Set the camera EM gain mode (i.e. linear, real, etc..)
    #
    # @param mode The EM gain mode.
    #
    # @returns Whether the mode could be set or not.
    #
    def setEMGainMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetEMGainMode(ctypes.c_int(mode))
        if (status == drv_not_supported):
            print("Warning: Setting EM Gain Mode is not supported by this camera.")
            return False
        elif (status == drv_p1invalid):
            return False
        else:
            andorCheck(status, "SetEMGainMode")
            return True

    ## setExposureTime
    #
    # Set the exposure time.
    #
    # @param exposure_time The exposure time.
    #
    def setExposureTime(self, exposure_time):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetExposureTime(ctypes.c_float(exposure_time)), "SetExposureTime")
        self.exposure_time = exposure_time

    ## setFanMode
    #
    # Set the fan mode, 0 = full, 1 = low, 2 = off
    #
    # @param mode The fan mode.
    #
    def setFanMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetFanMode(ctypes.c_int(mode)), "SetFanMode")

    ## setFastExternalTrigger
    #
    # Set fast external trigger.
    #
    # @param mode The external trigger mode.
    def setFastExtTrigger(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetFastExtTrigger(ctypes.c_int(mode)), "SetFastTriggerMode")

    ## setFrameTransferMode
    #
    # Set frame transfer mode, 0 is off, 1 is on
    #
    # @param mode The frame transfer mode.
    #
    def setFrameTransferMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetFrameTransferMode(ctypes.c_int(mode)), "SetFrameTransferMode")
        self.frame_transfer_mode = mode

    ## setHSSpeed
    #
    # Horizontal shift speed.
    # This will choose the nearest HSSpeed to the requested hsspeed.
    #
    # @param hsspeed The desired horizontal shift speed.
    #
    def setHSSpeed(self, hsspeed):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        if not hasattr(self, "adchannel"):
            self.adchannel = 0
        speeds = self._props_["HSSpeeds"][self.adchannel]
        index = 0
        best = abs(hsspeed - speeds[index])
        for i in range(len(speeds)):
            cur = abs(hsspeed - speeds[i])
            if cur < best:
                best = cur
                index = i
        andorCheck(andor.SetHSSpeed(0, ctypes.c_int(index)), "SetHSSpeed")
        self.hsspeed = speeds[index]
        return self.hsspeed

    ## setIsolatedCropMode
    #
    # Turn on/off isolated crop mode (if available).
    #
    def setIsolatedCropMode(self, active, height, width, vbin, hbin):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        if active:
            active = 1
        else:
            active = 0
        status = andor.SetIsolatedCropMode(ctypes.c_int(active),
                                           ctypes.c_int(height),
                                           ctypes.c_int(width),
                                           ctypes.c_int(vbin),
                                           ctypes.c_int(hbin))
        if (active == 1):
            andorCheck(status, "SetIsolatedCropMode")
        else:
            if (status != drv_not_supported):
                andorCheck(status, "SetIsolatedCropMode")

    ## setKineticCycleTime
    #
    # Set the kinetic cycle time.
    # This is the time between frames.
    #
    # @param kinetic_time The time between frames.
    def setKineticCycleTime(self, kinetic_time):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetKineticCycleTime(ctypes.c_float(kinetic_time)), "SetKineticCycleTime")
        self.kinetic_cycle_time = kinetic_time

    ## setPreAmpGain
    #
    # Set the preamp gain.
    # This will choose the nearest available gain to the requested gain.
    #
    # @param gain The desired preamp gain.
    #
    def setPreAmpGain(self, gain):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        gains = self._props_["PreAmpGains"]
        index = 0
        best = abs(gain - gains[index])
        for i in range(len(gains)):
            cur = abs(gain - gains[i])
            if cur < best:
                best = cur
                index = i
        andorCheck(andor.SetPreAmpGain(ctypes.c_int(index)), "SetPreAmpGain")
        return gains[index]

    ## setReadMode
    #
    # Set the read mode.
    # mode is a integer 0-4, with meaning as specfied in the andor documentation
    #
    # @param mode The read mode.
    #
    def setReadMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetReadMode(ctypes.c_int(mode)), "SetReadMode")

    ## setROIAndBinning
    #
    # Set the ROI and Binning.
    #
    # @param ROI [x1, x2, y1, y2] where x1 < x2 <= XPixels, y1 < y2 <= YPixels
    # @param binning [bx, by] where bx > 0, by > 0
    #
    def setROIAndBinning(self, ROI, binning):
        x_pixels = self._props_["XPixels"]
        y_pixels = self._props_["YPixels"]
        if (binning[0] <= 0) or (binning[1] <= 0):
            raise AndorEMCCDException("Invalid binning request: " + str(binning[0]) + "," + str(binning[1]))
        if (ROI[0] > ROI[1]) or (ROI[0] >= x_pixels) or (ROI[1] > x_pixels):
            raise AndorEMCCDException("Invalid x range: " + str(ROI[0]) + "," + str(ROI[1]))
        if (ROI[2] > ROI[3]) or (ROI[2] >= y_pixels) or (ROI[3] > y_pixels):
            raise AndorEMCCDException("Invalid y range: " + str(ROI[2]) + "," +str(ROI[3]))
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetImage(ctypes.c_int(binning[0]), ctypes.c_int(binning[1]),
                                  ctypes.c_int(ROI[0]), ctypes.c_int(ROI[1]), ctypes.c_int(ROI[2]), ctypes.c_int(ROI[3])),
                   "SetImage")
        self.ROI = ROI
        self.binning = binning
        self.x_pixels = int((self.ROI[1] - self.ROI[0] + 1)/self.binning[0])
        self.y_pixels = int((self.ROI[3] - self.ROI[2] + 1)/self.binning[1])
        self.pixels = self.x_pixels * self.y_pixels
        self.frame_size = [self.x_pixels, self.y_pixels]

    ## setTriggerMode
    #
    # Set the trigger mode.
    #
    # @param mode The trigger mode.
    #
    def setTriggerMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetTriggerMode(ctypes.c_int(mode)), "SetTriggerMode")

    ## setTemperature
    #
    # Set the camera temperature.
    #
    # @param temperature The desired temperature.
    #
    def setTemperature(self, temperature):
        setCurrentCamera(self.camera_handle)
        self.coolerOn()
        [t_min, t_max] = self._props_["TemperatureRange"]
        if (temperature < t_min):
            print("setTemperature: Temperature is too low (" + str(temperature) + " < " + str(t_min))
            temperature = t_min
        if (temperature > t_max):
            print("setTemperature: Temperature is too high (" + str(temperature) + " > " + str(t_max))
            temperature = t_max
        i_temp = ctypes.c_int(temperature)
        andorCheck(andor.SetTemperature(i_temp), "SetTemperature")

    ## setVSAmplitude
    #
    # Vertical clock voltage.
    #
    # @param amplitude The vertical clock voltage.
    #
    def setVSAmplitude(self, amplitude):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetVSAmplitude(ctypes.c_int(amplitude)), "SetVSAmplitude")

    ## setVSSpeed
    #
    # Vertical shift speed.
    # This will choose the nearest VSSpeed to the requested vsspeed.
    #
    # @param vsspeed The desired vertical shift speed.
    #
    def setVSSpeed(self, vsspeed):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        speeds = self._props_["VSSpeeds"]
        index = 0
        best = abs(vsspeed - speeds[index])
        for i in range(len(speeds)):
            cur = abs(vsspeed - speeds[i])
            if cur < best:
                best = cur
                index = i
        andorCheck(andor.SetVSSpeed(ctypes.c_int(index)), "SetVSSpeed")
        self.vsspeed = speeds[index]
        return self.vsspeed

    ## shutdown
    #
    # Abort the current acquisition (if acquiring), close the shutter and
    # turn the cooler off.
    #
    def shutdown(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        self.closeShutter()
        self.coolerOff()
        if False:
            # I thought this might turn off the fan, which seems to run
            # pretty much all the time, but no luck there.
            print("Warming")
            current_temp = self.getTemperature()[0]
            while(current_temp < 0):
                print("  Temperature:", current_temp)
                time.sleep(5.0)
                current_temp = self.getTemperature()[0]
        andor.ShutDown()

    ## startAcquisition
    #
    # Start the acquisition.
    #
    def startAcquisition(self):
        setCurrentCamera(self.camera_handle)
        andorCheck(andor.StartAcquisition(), "StartAcquisition")

    ## stopAcquisition
    #
    # Stop the acquisition.
    #
    def stopAcquisition(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()


#
# Testing section.
#

if __name__ == "__main__":

    def printDict(dictionary):
        for key in sorted(dictionary):
            print(key, '\t', dictionary[key])

    andor_path = "c:/Program Files/Andor SOLIS/Drivers/"
    loadAndorDLL(andor_path + "atmcd64d.dll")
    print(getAvailableCameras(), "cameras connected")
    handles = getCameraHandles()
    print("camera handles: ", handles)

    cameras = []
    for handle in handles:
        camera = AndorCamera(andor_path, handle)
        cameras.append(camera)
        print("Camera", handle, "Properties:")
        printDict(camera.getProperties())
        camera.setEMAdvanced(True)
        camera.setEMGainMode(2)
        print("Gain range:", camera.getEMGainRange())
        print("Advanced:", camera.getEMAdvanced())
        #camera.setEMCCDGain(250)
        print("")

#    camera = AndorCamera("c:/Program Files/Andor SOLIS/Drivers/")
#    camera = AndorCamera("c:/Program Files (x86)/Andor SOLIS/Drivers/atmcd64d.dll")

#    if 1:
#        print "Camera Properties:"
#        printDict(camera.getProperties())
#        print ""

    for camera in cameras:
        camera.shutdown()


#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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

