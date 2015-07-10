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
# Hazen 12/12
#

from ctypes import *
import time

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

## AndorCapabilities
#
# The Andor camera capabilities structure.
#
class AndorCapabilities(Structure):
    _fields_ = [("ulSize", c_ulong),
                ("ulAcqModes", c_ulong),
                ("ulReadModes", c_ulong),
                ("ulTriggerModes", c_ulong),
                ("ulCameraType", c_ulong),
                ("ulPixelMode", c_ulong),
                ("ulSetFunctions", c_ulong),
                ("ulGetFunctions", c_ulong),
                ("ulFeatures", c_ulong),
                ("ulPCICard", c_ulong),
                ("ulEMGainCapability", c_ulong),
                ("ulFTReadModes", c_ulong)]

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
        andor = oledll.LoadLibrary(andor_dll)

## andorCheck
#
# Checks the return value of andor function call. Throws an error if the function
# call was not successful.
#
# @param status The returned value of the function call.
# @param message A string message, usually this is the name of the function call.
#
def andorCheck(status, message):
    assert status == drv_success, message + " failed with status = " + str(status)

## getAvailableCameras
#
# Dealing with multiple cameras.
#
def getAvailableCameras():
    number_cameras = c_long()
    andorCheck(andor.GetAvailableCameras(byref(number_cameras)), "GetAvailableCameras")
    return number_cameras.value

## getCameraHandles
#
# Get handles for the cameras that are available.
#
def getCameraHandles():
    number_cameras = getAvailableCameras()
    assert number_cameras > 0, "No Andor cameras detected!!"
    handles = []
    temp = c_long()
    for i in range(getAvailableCameras()):
        andorCheck(andor.GetCameraHandle(i, byref(temp)), "GetCameraHandle")
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
        caps = AndorCapabilities(sizeof(c_ulong)*12,0,0,0,0,0,0,0,0,0,0,0)
        andorCheck(andor.GetCapabilities(byref(caps)), "GetCapabilities")
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

        # Determine camera pixel size.
        x_pixels = c_long()
        y_pixels = c_long()
        andorCheck(andor.GetDetector(byref(x_pixels), byref(y_pixels)), "GetDetector")
        self._props_['XPixels'] = x_pixels.value
        self._props_['YPixels'] = y_pixels.value

        # Determine camera head model.
        head_model = create_string_buffer(32)
        andorCheck(andor.GetHeadModel(head_model), "GetHeadModel")
        self._props_['HeadModel'] = head_model.value

        # Determine hardware version.
        plug_in_card_version = c_uint()
        flex_10k_file_version = c_uint()
        dummy1 = c_uint()
        dummy2 = c_uint()
        camera_firmware_version = c_uint()
        camera_firmware_build = c_uint()
        andorCheck(andor.GetHardwareVersion(byref(plug_in_card_version),
                                            byref(flex_10k_file_version),
                                            byref(dummy1),
                                            byref(dummy2),
                                            byref(camera_firmware_version),
                                            byref(camera_firmware_build)),
                   "GetHardwareVersion")
        self._props_["PlugInCardVersion"] = plug_in_card_version.value
        self._props_["Flex10kFileVersion"] = flex_10k_file_version.value
        self._props_["CameraFirmwareVersion"] = camera_firmware_version.value
        self._props_["CameraFirmwareBuild"] = camera_firmware_build.value

        # Determine vertical shift speeds.
        number = c_int()
        andorCheck(andor.GetNumberVSSpeeds(byref(number)), "GetNumberVSSpeeds")
        self._props_["VSSpeeds"] = range(number.value)
        for i in range(number.value):
            index = c_int(i)
            speed = c_float()
            andorCheck(andor.GetVSSpeed(index, byref(speed)), "GetVSSpeed")
            self._props_["VSSpeeds"][i] = speed.value

        # Determine horizontal shift speeds.
        andorCheck(andor.GetNumberADChannels(byref(number)), "GetNumberADChannels")
        self._props_["NumberADChannels"] = number.value
        self._props_["HSSpeeds"] = range(number.value)
        for i in range(number.value):
            channel = c_int(i)
            andorCheck(andor.GetNumberHSSpeeds(channel, 0, byref(number)), "GetNumberHSSpeeds")
            self._props_["HSSpeeds"][i] = range(number.value)
            for j in range(number.value):
                type = c_int(j)
                speed = c_float()
                andorCheck(andor.GetHSSpeed(channel, 0, type, byref(speed)), "GetHSSpeed")
                self._props_["HSSpeeds"][i][j] = speed.value
        
        # Determine temperature range.
        min_temp = c_int()
        max_temp = c_int()
        andorCheck(andor.GetTemperatureRange(byref(min_temp), byref(max_temp)), "GetTemperatureRange")
        self._props_["TemperatureRange"] = [min_temp.value, max_temp.value]

        # Determine preamp gains available.
        number = c_int()
        andorCheck(andor.GetNumberPreAmpGains(byref(number)), "GetNumberPreAmpGains")
        self._props_["PreAmpGains"] = range(number.value)
        for i in range(number.value):
            index = c_int(i)
            gain = c_float()
            andorCheck(andor.GetPreAmpGain(index, byref(gain)), "GetPreAmpGain")
            self._props_["PreAmpGains"][i] = gain.value

        # Determine EM gain range.
        low = c_int()
        high = c_int()
        andorCheck(andor.GetEMGainRange(byref(low), byref(high)), "GetEMGainRange")
        self._props_["EMGainRange"] = [low.value, high.value]

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
        i_state = c_int()
        andorCheck(andor.GetStatus(byref(i_state)), "GetStatus")
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
            raise AssertionError, "Driver is in a bad place?: " + str(state)

    #
    # Camera property queries
    #

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

    ## getProperties
    #
    # Return all the known camera properties
    #
    # @return Returns the camera properties.
    #
    def getProperties(self):
        return self._props_

    ## getVSSpeeds
    #
    # Return the camera vertical speeds
    #
    # @return Returns the camera vertical speeds.
    #
    def getVSSpeeds(self):
        return self._props_["VSSpeeds"]


    #
    # Temperature Control
    #

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

    ## getTemperature
    #
    # Return the current camera temperature.
    #
    # @return Return the camera temperature.
    #
    def getTemperature(self):
        setCurrentCamera(self.camera_handle)
        temperature = c_int()
        status = andor.GetTemperature(byref(temperature))
        if status == drv_temp_stabilized:
            return [temperature.value, "stable"]
        elif (status == drv_temp_off) or (status == drv_temp_not_stabilized) or (status == drv_temp_not_reached) or (status == drv_temp_drift):
            return [temperature.value, "unstable"]
        else:
            print "GetTemperature failed: ", status
            return [50, "unstable"]

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
        while status[1] == "unstable":
            time.sleep(5)
            status = camera.getTemperature()

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
        if temperature < t_min:
            print "setTemperature: Temperature is too low (" + str(temperature) + " < " + str(t_min)
            temperature = t_min
        if temperature > t_max:
            print "setTemperature: Temperature is too high (" + str(temperature) + " > " + str(t_max)
            temperature = t_max
        i_temp = c_int(temperature)
        andorCheck(andor.SetTemperature(i_temp), "SetTemperature")

    #
    # Shutter Control
    #
    # Calling either of these during acquisition will abort the acquisition
    #

    ## openShutter
    #
    # Open the camera shutter. This will abort the current acquisition.
    #
    def openShutter(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetShutter(0, 1, 0, 0)
        if status != drv_success:
            print "SetShutter (open) failed: ", status

    ## closeShutter
    #
    # Close the camera shutter. This will abort the current acquisition.
    def closeShutter(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetShutter(0, 2, 0, 0)
        if status != drv_success:
            print "SetShutter (closed) failed: ", status


    #
    # Acquisition Setup
    #
    # Calling any of these functions will abort the current acquisition
    #

    ## getAcquisitionTimings
    #
    # Get the acquisition timings. This will abort the current acquisition.
    #
    # @return Return the acquisition timings.
    #
    def getAcquisitionTimings(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        andorCheck(andor.GetAcquisitionTimings(byref(exposure), byref(accumulate), byref(kinetic)),
                   "GetAcqisitionTimings")
        return [exposure.value, accumulate.value, kinetic.value]

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
        except:
            print "getCurrentSetup: One or more parameters are not defined."

    ## getEMAdvanced
    #
    # Get the current advanced EM setting.
    #
    # @return Return the advanced EM setting (1 or 0).
    #
    def getEMAdvanced(self):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        state = c_int()
        andorCheck(andor.GetEMAdvanced(byref(state)), "GetEMAdvanced")
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
        low = c_int()
        high = c_int()
        andorCheck(andor.GetEMGainRange(byref(low), byref(high)), "GetEMGainRange")
        return [low.value, high.value]

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
        if mode == "single_frame":
            andorCheck(andor.SetAcquisitionMode(1), "SetAcquisitionMOde")
        elif mode == "fixed_length":
            andorCheck(andor.SetAcquisitionMode(3), "SetAcquisitionMode")
            andorCheck(andor.SetNumberAccumulations(1), "SetNumberAccumulations")
            andorCheck(andor.SetAccumulationCycleTime(0), "SetAccumulationCycleTime")
            andorCheck(andor.SetNumberKinetics(c_int(number_frames)), "SetNumberKinetics")
        elif mode == "run_till_abort":
            andorCheck(andor.SetAcquisitionMode(5), "SetAcquisitionMode")
        else:
            print "Unknown mode: " + mode
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
            andorCheck(andor.SetADChannel(c_int(channel)), "SetADChannel")
            andorCheck(andor.SetOutputAmplifier(c_int(channel)), "SetOutputAmplifier")
            self.adchannel = channel
        else:
            print "Invalid channel: ", channel

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
        andorCheck(andor.SetBaselineClamp(c_int(active)), "SetBaselineClamp")

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
        status = andor.SetEMAdvanced(c_int(enable))
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
        andorCheck(andor.SetEMCCDGain(c_int(gain)), "SetEMCCDGain")

    ## setEMGainMode
    #
    # Set the camera EM gain mode (i.e. linear, real, etc..)
    #
    # param mode The EM gain mode.
    #
    def setEMGainMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        status = andor.SetEMGainMode(c_int(mode))
        if (status == drv_not_supported):
            print "Warning: Setting EM Gain Mode is not supported by this camera."
        else:
            andorCheck(status, "SetEMGainMode")

    ## setExposureTime
    #
    # Set the exposure time.
    #
    # @param exposure_time The exposure time.
    #
    def setExposureTime(self, exposure_time):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetExposureTime(c_float(exposure_time)), "SetExposureTime")
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
        andorCheck(andor.SetFanMode(c_int(mode)), "SetFanMode")

    ## setFrameTransferMode
    #
    # Set frame transfer mode, 0 is off, 1 is on
    #
    # @param mode The frame transfer mode.
    #
    def setFrameTransferMode(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetFrameTransferMode(c_int(mode)), "SetFrameTransferMode")
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
        andorCheck(andor.SetHSSpeed(0, c_int(index)), "SetHSSpeed")
        self.hsspeed = speeds[index]

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
        status = andor.SetIsolatedCropMode(c_int(active),
                                           c_int(height),
                                           c_int(width),
                                           c_int(vbin),
                                           c_int(hbin))
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
        andorCheck(andor.SetKineticCycleTime(c_float(kinetic_time)), "SetKineticCycleTime")
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
        andorCheck(andor.SetPreAmpGain(c_int(index)), "SetPreAmpGain")

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
        andorCheck(andor.SetReadMode(c_int(mode)), "SetReadMode")

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
            raise AssertionError, "Invalid binning request: " + str(binning[0]) + "," + str(binning[1])
        if (ROI[0] > ROI[1]) or (ROI[0] >= x_pixels) or (ROI[1] > x_pixels):
            raise AssertionError, "Invalid x range: " + str(ROI[0]) + "," + str(ROI[1])
        if (ROI[2] > ROI[3]) or (ROI[2] >= y_pixels) or (ROI[3] > y_pixels):
            raise AssertionError, "Invalid y range: " + str(ROI[2]) + "," +str(ROI[3])
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetImage(c_int(binning[0]), c_int(binning[1]),
                                  c_int(ROI[0]), c_int(ROI[1]), c_int(ROI[2]), c_int(ROI[3])),
                   "SetImage")
        self.ROI = ROI
        self.binning = binning
        self.x_pixels = (self.ROI[1] - self.ROI[0] + 1)/self.binning[0]
        self.y_pixels = (self.ROI[3] - self.ROI[2] + 1)/self.binning[1]
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
        andorCheck(andor.SetTriggerMode(c_int(mode)), "SetTriggerMode")

    ## setFastExternalTrigger
    #
    # Set fast external trigger.
    #
    # @param mode The external trigger mode.
    def setFastExtTrigger(self, mode):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetFastExtTrigger(c_int(mode)), "SetFastTriggerMode")

    ## setVSAmplitude
    #
    # Vertical clock voltage.
    #
    # @param amplitude The vertical clock voltage.
    #
    def setVSAmplitude(self, amplitude):
        setCurrentCamera(self.camera_handle)
        self._abortIfAcquiring_()
        andorCheck(andor.SetVSAmplitude(c_int(amplitude)), "SetVSAmplitude")

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
        andorCheck(andor.SetVSSpeed(c_int(index)), "SetVSSpeed")
        self.vsspeed = speeds[index]

        
    #
    # Acquisition
    #

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

    ## getOldestImage16
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
            first = c_long(0)
            last = c_long(0)
            andor.GetNumberNewImages(byref(first), byref(last))
            diff = first.value - last.value
            if (diff > 1):
                print "  warning: acquisition is", diff, "frames behind..."
        buffer = create_string_buffer(2 * self.pixels)
        status = andor.GetOldestImage16(buffer, c_ulong(self.pixels))
        if status == drv_success:
            return [buffer, self.frame_size, "acquiring"]
        elif status == drv_no_new_data:
            state = _getStatus_()
            if state == drv_idle:
                return [0, self.frame_size, "idle"]
            else:
                return [0, self.frame_size, "acquiring"]
        else:
            raise AssertionError, "GetOldestImage16 failed: " + str(status)

    ## getImages16
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
        first = c_long(0)
        last = c_long(0)
        status = andor.GetNumberNewImages(byref(first), byref(last))

        # There is new data.
        if (status == drv_success):

            # Allocate space & get the data.
            diff = last.value - first.value + 1
            buffer_size = self.pixels * diff
            data_buffer = create_string_buffer(2 * buffer_size)
            valid_first = c_long(0)
            valid_last = c_long(0)
            status = andor.GetImages16(first, last, data_buffer, c_ulong(buffer_size), byref(valid_first), byref(valid_last))
            if (first.value != valid_first.value):
                print "getImages16 first value problem", first.value, valid_first.value
            if (last.value != valid_last.value):
                print "getImages16 last value problem", last.value, valid_last.value

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
                raise AssertionError, "GetImages16 failed: " + str(status)

        # There is no new data.
        elif (status == drv_no_new_data):
            if (state == drv_idle):
                return [frames, self.frame_size, "idle"]
            else:
                return [frames, self.frame_size, "acquiring"]

        # Something bad must have happened.
        else:
            raise AssertionError, "GetNumberNewImages failed: " + str(status)



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
        if 0:
            # I thought this might turn off the fan, which seems to run
            # pretty much all the time, but no luck there.
            print "Warming"
            current_temp = self.getTemperature()[0]
            while current_temp < 0:
                print "  Temperature:", current_temp
                time.sleep(5.0)
                current_temp = self.getTemperature()[0]
        andor.ShutDown()


#
# Testing section.
#

if __name__ == "__main__":

    def printDict(dictionary):
        keys = dictionary.keys()
        keys.sort()
        for key in keys:
            print key, '\t', dictionary[key]

    andor_path = "c:/Program Files/Andor SOLIS/Drivers/"
    loadAndorDLL(andor_path + "atmcd64d.dll")
    print getAvailableCameras(), "cameras connected"
    handles = getCameraHandles()
    print "camera handles: ", handles

    cameras = []
    for handle in handles:
        camera = AndorCamera(andor_path, handle)
        cameras.append(camera)
        print "Camera", handle, "Properties:"
        printDict(camera.getProperties())
        camera.setEMAdvanced(True)
        camera.setEMGainMode(2)
        print "Gain range:", camera.getEMGainRange()
        print "Advanced:", camera.getEMAdvanced()
        #camera.setEMCCDGain(250)
        print ""

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
# Copyright (c) 2012 Zhuang Lab, Harvard University
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

