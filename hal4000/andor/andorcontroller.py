#!/usr/bin/python
#
# A ctypes based interface to Andor cameras.
# (Andor Software Version 2.82).
#
# Cameras are 1 indexed?
#
# Hazen 2/09
#

from ctypes import *
import time

# Andor constants & structures

drv_acquiring = 20072
drv_idle = 20073
drv_no_new_data = 20024
drv_success = 20002
drv_tempcycle = 20074
drv_temp_not_stabilized = 20035
drv_temp_off = 20034
drv_temp_stabilized = 20036
drv_temp_not_reached = 20037
drv_temp_drift = 20040

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


# Handles loading the library (only once)

andor = 0
def loadAndorDLL(andor_dll):
    global andor
    if(andor == 0):
        andor = oledll.LoadLibrary(andor_dll)
#        andor = oledll.LoadLibrary(andor_path + "ATMCD32D")


# helper functions
def _getStatus_():
    i_state = c_int()
    status = andor.GetStatus(byref(i_state))
    assert status == drv_success, "GetStatus failed: " + str(status)
    return i_state.value

def _abortIfAcquiring_():
    state = _getStatus_()
    if state == drv_acquiring :
        status = andor.AbortAcquisition()
        assert status == drv_success, "AbortAcquisition failed: " + str(status)
    elif state != drv_idle and state != drv_tempcycle:
        raise AssertionError, "Driver is a bad place?: " + str(state)
    

#
# The camera control class.
#

instantiated = 0
class AndorCamera:

    # Class instance variables
    
    #
    # Initializes the object by initializing the camera
    # then querying it to determine its various properties.
    #

    def __init__(self, andor_dll):
        # check that this class has not already been instantiated
        global instantiated
        assert instantiated == 0, "Attempt to instantiate two camera controller instances."

        # general
        self.pixels = 0

        # camera properties storage
        self._props_ = {}

        # load the andor DLL library
        loadAndorDLL(andor_dll)

        # initialize the camera
        status = andor.Initialize(andor_dll + "Detector.ini")
        assert status == drv_success, "Initialization failed: " + str(status)

        # determine camera capabilities (useful??)
        caps = AndorCapabilities(sizeof(c_ulong)*12,0,0,0,0,0,0,0,0,0,0,0)
        status = andor.GetCapabilities(byref(caps))
        assert status == drv_success, "GetCapabilities failed: " + str(status)
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

        # determine camera pixel size
        x_pixels = c_long()
        y_pixels = c_long()
        status = andor.GetDetector(byref(x_pixels), byref(y_pixels))
        assert status == drv_success, "GetDetector failed: " + str(status)
        self._props_['XPixels'] = x_pixels.value
        self._props_['YPixels'] = y_pixels.value

        # determine camera head model
        head_model = create_string_buffer(32)
        status = andor.GetHeadModel(head_model)
        assert status == drv_success, "GetHeadModel failed: " + str(status)
        self._props_['HeadModel'] = head_model.value

        # determine hardware version
        plug_in_card_version = c_uint()
        flex_10k_file_version = c_uint()
        dummy1 = c_uint()
        dummy2 = c_uint()
        camera_firmware_version = c_uint()
        camera_firmware_build = c_uint()
        status = andor.GetHardwareVersion(byref(plug_in_card_version),
                                          byref(flex_10k_file_version),
                                          byref(dummy1),
                                          byref(dummy2),
                                          byref(camera_firmware_version),
                                          byref(camera_firmware_build))
        assert status == drv_success, "GetHardwareVersion failed: " + status
        self._props_["PlugInCardVersion"] = plug_in_card_version.value
        self._props_["Flex10kFileVersion"] = flex_10k_file_version.value
        self._props_["CameraFirmwareVersion"] = camera_firmware_version.value
        self._props_["CameraFirmwareBuild"] = camera_firmware_build.value

        # determine vertical shift speeds
        number = c_int()
        status = andor.GetNumberVSSpeeds(byref(number))
        assert status == drv_success, "GetNumberVSSpeeds failed: " + str(status)
        self._props_["VSSpeeds"] = range(number.value)
        for i in range(number.value):
            index = c_int(i)
            speed = c_float()
            status = andor.GetVSSpeed(index, byref(speed))
            assert status == drv_success, "GetVSSpeed failed: " + str(status)
            self._props_["VSSpeeds"][i] = speed.value

        # determine horizontal shift speeds
        status = andor.GetNumberADChannels(byref(number))
        assert status == drv_success, "GetNumberADChannels failed: " + str(status)
        self._props_["NumberADChannels"] = number.value
        self._props_["HSSpeeds"] = range(number.value)
        for i in range(number.value):
            channel = c_int(i)
            status = andor.GetNumberHSSpeeds(channel, 0, byref(number))
            assert status == drv_success, "GetNumberHSSpeeds failed: " + str(status)
            self._props_["HSSpeeds"][i] = range(number.value)
            for j in range(number.value):
                type = c_int(j)
                speed = c_float()
                status = andor.GetHSSpeed(channel, 0, type, byref(speed))
                assert status == drv_success, "GetHSSpeed failed: " + str(status)
                self._props_["HSSpeeds"][i][j] = speed.value
        
        # determine temperature range
        min_temp = c_int()
        max_temp = c_int()
        status = andor.GetTemperatureRange(byref(min_temp), byref(max_temp))
        assert status == drv_success, "GetTemperatureRange failed: " + str(status)
        self._props_["TemperatureRange"] = [min_temp.value, max_temp.value]

        # determine preamp gains available
        number = c_int()
        status = andor.GetNumberPreAmpGains(byref(number))
        assert status == drv_success, "GetNumberPreAmpGains failed: " + str(status)
        self._props_["PreAmpGains"] = range(number.value)
        for i in range(number.value):
            index = c_int(i)
            gain = c_float()
            status = andor.GetPreAmpGain(index, byref(gain))
            assert status == drv_success, "GetPreAmpGain failed: " + str(status)
            self._props_["PreAmpGains"][i] = gain.value

        # determine EM gain range
        low = c_int()
        high = c_int()
        status = andor.GetEMGainRange(byref(low), byref(high))
        assert status == drv_success, "GetEMGainRange failed: " + str(status)
        self._props_["EMGainRange"] = [low.value, high.value]

        instantiated = 1


    #
    # Camera property queries
    #

    # Return the camera dimensions
    def getDimensions(self):
        return [self._props_["XPixels"], self._props_["YPixels"]]

    # Return the camera head model
    def getHeadModel(self):
        return self._props_["HeadModel"]

    # Return the camera horizontal speeds
    def getHSSpeeds(self):
        return self._props_["HSSpeeds"]

    # Return all the known camera properties
    def getProperties(self):
        return self._props_

    # Return the camera vertical speeds
    def getVSSpeeds(self):
        return self._props_["VSSpeeds"]


    #
    # Temperature Control
    #

    # Cooler control
    def coolerOff(self):
        status = andor.CoolerOFF()
        assert status == drv_success, "CoolerOff failed: " + str(status)

    def coolerOn(self):
        status = andor.CoolerON()
        assert status == drv_success, "CoolerOn failed: " + str(status)

    # Return the current camera temperature
    def getTemperature(self):
        temperature = c_int()
        status = andor.GetTemperature(byref(temperature))
        if status == drv_temp_stabilized:
            return [temperature.value, "stable"]
        elif (status == drv_temp_off) or (status == drv_temp_not_stabilized) or (status == drv_temp_not_reached) or (status == drv_temp_drift):
            return [temperature.value, "unstable"]
        else:
            print "GetTemperature failed: ", status
            return [50, "unstable"]

    # Loops until the camera stabilizes at the desired temperature
    def goToTemperature(self, temperature):
        self.setTemperature(temperature)
        status = self.getTemperature()
        while status[1] == "unstable":
            time.sleep(5)
            status = camera.getTemperature()

    # Set the camera temperature
    def setTemperature(self, temperature):
        self.coolerOn()
        [t_min, t_max] = self._props_["TemperatureRange"]
        if temperature < t_min:
            print "setTemperature: Temperature is too low (" + str(temperature) + " < " + str(t_min)
            temperature = t_min
        if temperature > t_max:
            print "setTemperature: Temperature is too high (" + str(temperature) + " > " + str(t_max)
            temperature = t_max
        i_temp = c_int(temperature)
        status = andor.SetTemperature(i_temp)
        assert status == drv_success, "SetTemperature failed: " + status
            

    #
    # Shutter Control
    #
    # Calling either of these during acquisition will abort the acquisition
    #

    def openShutter(self):
        _abortIfAcquiring_()
        status = andor.SetShutter(0, 1, 0, 0)
        if status != drv_success:
            print "SetShutter (open) failed: ", status

    def closeShutter(self):
        _abortIfAcquiring_()
        status = andor.SetShutter(0, 2, 0, 0)
        if status != drv_success:
            print "SetShutter (closed) failed: ", status


    #
    # Acquisition Setup
    #
    # Calling any of these functions will abort the current acquisition
    #

    # Get the acquisition timings.
    def getAcquisitionTimings(self):
        _abortIfAcquiring_()
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        status = andor.GetAcquisitionTimings(byref(exposure), byref(accumulate), byref(kinetic))
        assert status == drv_success, "getAquisitionTimings failed: " + str(status)
        return [exposure.value, accumulate.value, kinetic.value]

    # Get the current camera setup.
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

    # Sets up the camera in the appropriate acquisition mode &
    # returns the acquisition timing.
    # mode is one of "single_frame", "multiple_frame" or "free_running"    
    def setACQMode(self, mode, number_frames = "undef"):
        _abortIfAcquiring_()
        if mode == "single_frame":
            status = andor.SetAcquisitionMode(1)
            assert status == drv_success, "SetAcquisitionMode failed: " + str(status)
        elif mode == "fixed_length":
            status = andor.SetAcquisitionMode(3)
            assert status == drv_success, "SetAcquisitionMode failed: " + str(status)
            status = andor.SetNumberAccumulations(1)
            assert status == drv_success, "SetNumberAccumulations failed: " + str(status)
            status = andor.SetAccumulationCycleTime(0)
            assert status == drv_success, "SetAccumulationCycleTime failed: " + str(status)
        elif mode == "run_till_abort":
            status = andor.SetAcquisitionMode(5)
            assert status == drv_success, "SetAcquisitionMode failed: " + str(status)
        else:
            print "Unknown mode: " + mode
            return
        if mode == "fixed_length":
            status = andor.SetNumberKinetics(c_int(number_frames))
            assert status == drv_success, "SetNumberKinetics failed: " + str(status)
        self.acqmode = mode

    # ADChannel.
    def setADChannel(self, channel):
        if (channel >= 0) and (channel < self._props_["NumberADChannels"]):
            _abortIfAcquiring_()
            status = andor.SetADChannel(c_int(channel))
            assert status == drv_success, "SetADChannel failed: " + str(status)
            status = andor.SetOutputAmplifier(c_int(channel))
            assert status == drv_success, "SetOutputAmplifier failed: " + str(status)
            self.adchannel = channel
        else:
            print "Invalid channel: ", channel

    # Baseline clamp.
    def setBaselineClamp(self, active):
        if active:
            active = 1
        else:
            active = 0
        status = andor.SetBaselineClamp(c_int(active))
        assert status == drv_success, "SetBaselineClamp failed: " + str(status)

    # EM gain.
    def setEMCCDGain(self, gain):
        _abortIfAcquiring_()
        status = andor.SetEMCCDGain(gain)
        assert status == drv_success, "SetEMCCDGain failed: " + str(status)

    # EM gain mode.
    def setEMGainMode(self, mode):
        _abortIfAcquiring_()
        status = andor.SetEMGainMode(c_int(mode))
        assert status == drv_success, "SetEMGainMode failed: " + str(status)

    # Exposure time.
    def setExposureTime(self, exposure_time):
        _abortIfAcquiring_()
        status = andor.SetExposureTime(c_float(exposure_time))
        assert status == drv_success, "SetExposureTime failed: " + str(status)
        self.exposure_time = exposure_time

    # Set the fan mode
    # 0 = full, 1 = low, 2 = off
    def setFanMode(self, mode):
        _abortIfAcquiring_()
        status = andor.SetFanMode(c_int(mode))
        assert status == drv_success, "SetFanMode failed: " + str(status)

    # Set frame transfer mode
    # 0 is off, 1 is on
    def setFrameTransferMode(self, mode):
        _abortIfAcquiring_()
        status = andor.SetFrameTransferMode(c_int(mode))
        assert status == drv_success, "SetFrameTransferMode failed: " + str(status)
        self.frame_transfer_mode = mode

    # Horizontal shift speed.
    # This will choose the nearest HSSpeed to the requested hsspeed.
    def setHSSpeed(self, hsspeed):
        _abortIfAcquiring_()
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
#        print "HS", speeds, index
        status = andor.SetHSSpeed(0, c_int(index))
        assert status == drv_success, "SetHHSpeed failed: " + str(status)
        self.hsspeed = speeds[index]

    # Set the kinetic cycle time.
    # This is the time between frames.
    def setKineticCycleTime(self, kinetic_time):
        _abortIfAcquiring_()
        status = andor.SetKineticCycleTime(c_float(kinetic_time))
        assert status == drv_success, "SetKineticCyleTime failed: " + str(status)
        self.kinetic_cycle_time = kinetic_time

    # Set the preamp gain.
    # This will choose the nearest available gain to the requested gain.
    def setPreAmpGain(self, gain):
        _abortIfAcquiring_()
        gains = self._props_["PreAmpGains"]
        index = 0
        best = abs(gain - gains[index])
        for i in range(len(gains)):
            cur = abs(gain - gains[i])
            if cur < best:
                best = cur
                index = i
#        print "sPAG", index
        status = andor.SetPreAmpGain(c_int(index))
        assert status == drv_success, "SetPreAmpGain failed: " + str(status)
        
    # Set the read mode.
    # mode is a integer 0-4, with meaning as specfied in the andor documentation
    def setReadMode(self, mode):
        _abortIfAcquiring_()
        status = andor.SetReadMode(c_int(mode))
        assert status == drv_success, "SetReadMode failed: " + str(status)

    # ROI and Binning.
    # binning is [bx, by] where bx > 0, by > 0
    # ROI is [x1, x2, y1, y2] where x1 < x2 <= XPixels, y1 < y2 <= YPixels
    def setROIAndBinning(self, ROI, binning):
        x_pixels = self._props_["XPixels"]
        y_pixels = self._props_["YPixels"]
        if (binning[0] <= 0) or (binning[1] <= 0):
            raise AssertionError, "Invalid binning request: " + str(binning[0]) + "," + str(binning[1])
        if (ROI[0] > ROI[1]) or (ROI[0] >= x_pixels) or (ROI[1] > x_pixels):
            raise AssertionError, "Invalid x range: " + str(ROI[0]) + "," + str(ROI[1])
        if (ROI[2] > ROI[3]) or (ROI[2] >= y_pixels) or (ROI[3] > y_pixels):
            raise AssertionError, "Invalid y range: " + str(ROI[2]) + "," +str(ROI[3])
        _abortIfAcquiring_()
        status = andor.SetImage(c_int(binning[0]), c_int(binning[1]),
                                c_int(ROI[0]), c_int(ROI[1]), c_int(ROI[2]), c_int(ROI[3]))
        assert status == drv_success, "SetImage failed: " + str(status)
        self.ROI = ROI
        self.binning = binning
        self.pixels = (self.ROI[1] - self.ROI[0] + 1) * (self.ROI[3] - self.ROI[2] + 1) / (self.binning[0] * self.binning[1])

    # Set the trigger mode.
    def setTriggerMode(self, mode):
        _abortIfAcquiring_()
        status = andor.SetTriggerMode(c_int(mode))
        assert status == drv_success, "SetTriggerMode failed: " + str(status)

    # Vertical clock voltage.
    def setVSAmplitude(self, amplitude):
        _abortIfAcquiring_()
        status = andor.SetVSAmplitude(c_int(amplitude))
        assert status == drv_success, "SetVSAmplitude failed: " + str(status)

    # Vertical shift speed.
    # This will choose the nearest VSSpeed to the requested vsspeed.
    def setVSSpeed(self, vsspeed):
        _abortIfAcquiring_()
        speeds = self._props_["VSSpeeds"]
        index = 0
        best = abs(vsspeed - speeds[index])
        for i in range(len(speeds)):
            cur = abs(vsspeed - speeds[i])
#            print best, cur, i
            if cur < best:
                best = cur
                index = i
        status = andor.SetVSSpeed(c_int(index))
#        print "VS", speeds, index
        assert status == drv_success, "SetVSSpeed failed: " + str(status)
        self.vsspeed = speeds[index]

        
    #
    # Acquisition
    #
        
    # Start the acquisition.
    def startAcquisition(self):
        status = andor.StartAcquisition()
        assert status == drv_success, "StartAcquisition failed: " + str(status)

    # Stop the acquisition.
    def stopAcquisition(self):
        _abortIfAcquiring_()

    # Returns the oldest image in the acquisition buffer. 
    # Call until there is no new data.
    #
    # Returns the a 2 element array. The first element
    # is the frame data, or 0 if there are no new frames.
    # The second element is the state of the camera, i.e.
    # is it acquiring data? Or is it idle?
    #
    # Use this function with 16 bit cameras.
    def getOldestImage16(self):
        if 1:
            first = c_long(0)
            last = c_long(0)
            status = andor.GetNumberNewImages(byref(first), byref(last))
            diff = first.value - last.value
            if (diff > 1):
                print "  warning: acquisition is", diff, "frames behind..."
        buffer = create_string_buffer(2 * self.pixels)
        status = andor.GetOldestImage16(buffer, c_ulong(self.pixels))
        if status == drv_success:
            return [buffer, "acquiring"]
        elif status == drv_no_new_data:
            state = _getStatus_()
            if state == drv_idle:
                return [0, "idle"]
            else:
                return [0, "acquiring"]
        else:
            raise AssertionError, "GetOldestImage16 failed: " + str(status)

    # Returns all the new images in the acquisition buffer.
    #
    # Returns a 2 element array. The first element is an array
    # containing the frames acquired (possibly an empty array). The 
    # second is the current state of the camera.
    def getImages16(self):
        frames = []
        
        # Check to see if there is any new data, and if so, how much.
        first = c_long(0)
        last = c_long(0)
        status = andor.GetNumberNewImages(byref(first), byref(last))

        # There is new data.
        if status == drv_success:

            # Allocate space & get the data.
            diff = last.value - first.value + 1
            buffer_size = self.pixels * diff
            buffer = create_string_buffer(2 * buffer_size)
            valid_first = c_long(0)
            valid_last = c_long(0)
            status = andor.GetImages16(first, last, buffer, c_ulong(buffer_size), byref(valid_first), byref(valid_last))
            if first.value != valid_first.value:
                print "getImages16 first value problem", first.value, valid_first.value
            if last.value != valid_last.value:
                print "getImages16 last value problem", last.value, valid_last.value

            # Got the data. Split the data buffer up into frames.
            if status == drv_success:
                for i in range(diff):
                    frames.append(buffer[2*i*self.pixels:2*(i+1)*self.pixels])
                return [frames, "acquiring"]

            # Not sure if we can actually end up here, but just in case.
            elif status == drv_no_new_data:
                state = _getStatus_()
                if state == drv_idle:
                    return [frames, "idle"]
                else:
                    return [frames, "acquiring"]

            # Something bad happened.
            else:
                raise AssertionError, "GetImages16 failed: " + str(status)

        # There is no new data. Check if the camera is idle or acquiring.
        elif status == drv_no_new_data:
            state = _getStatus_()
            if state == drv_idle:
                return [frames, "idle"]
            else:
                return [frames, "acquiring"]

        # Something bad must have happened.
        else:
            raise AssertionError, "GetNumberNewImages failed: " + str(status)


    #
    # Shutdown
    #

    def shutdown(self):
        _abortIfAcquiring_()
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
        global instantiated
        instantiated = 0

#
# Testing section.
#

if __name__ == "__main__":

    def printDict(dictionary):
        keys = dictionary.keys()
        keys.sort()
        for key in keys:
            print key, '\t', dictionary[key]

    print "Initializing Camera"
#    camera = AndorCamera("c:/Program Files/Andor SOLIS/Drivers/")
    camera = AndorCamera("c:/Program Files (x86)/Andor SOLIS/Drivers/atmcd64d.dll")

    if 1:
        print "Camera Properties:"
        printDict(camera.getProperties())
        print ""

    number_frames = 10
    print "Setting up the camera:"
    camera.setReadMode(4)
    camera.setTemperature(0)
    camera.setTriggerMode(0)
    camera.setADChannel(0)
#    camera.setROIAndBinning([1,512,1,512],[1,1])
#    camera.setROIAndBinning([129,384,129,384],[1,1])
#    camera.setROIAndBinning([129,384,129,384],[1,1])
    camera.setROIAndBinning([1, 128, 1, 128], [1, 1])
    camera.setHSSpeed(11.1)
    camera.setVSAmplitude(0)
    camera.setVSSpeed(1.0)
    camera.setEMGainMode(0)
    camera.setEMCCDGain(0)
    camera.setBaselineClamp(1)
    camera.setPreAmpGain(2.4)
    camera.setACQMode("run_till_abort")
    camera.setFrameTransferMode(1)
    camera.setExposureTime(0.0)
    camera.setKineticCycleTime(0.0)
#    camera.setKineticCycleTime(0.0)

#    print "sleeping"
#    time.sleep(1)

    camera.setACQMode("run_till_abort")
    camera.setFrameTransferMode(1)

##    camera.setACQMode("fixed_length", number_frames)


    print ""
    print "Timings"
    print camera.getAcquisitionTimings()

    print ""
    print "Temperature"
    temp = camera.getTemperature()[0]
#    while temp < 5:
    if 0:
        for i in range(100):
            print i, temp
            time.sleep(0.5)
            temp = camera.getTemperature()[0]
        print camera.getTemperature()

    if 0:
        print ""
        print "Cooling"
        camera.setTemperature(-70)
        time.sleep(40)

    if 0:
        print camera.getTemperature()
        camera.setFanMode(2)
        print ""
        print "Acquiring"
        for i in range(1):
            print "Cycle", i
            acquired = 0
            print camera.getTemperature()
            camera.startAcquisition()
            while(acquired < number_frames):
                [frames, state] = camera.getImages16()
                time.sleep(0.5)
                if state == "acquiring":
                    acquired += len(frames)
                else:
                    acquired += 100
            camera.stopAcquisition()
        print "Timings"
        print camera.getAcquisitionTimings()
        camera.setFanMode(0)

    if 1:
        print ""
        print "Acquiring"
        camera.startAcquisition()
        acquired = 0
        while(acquired < (number_frames + 50)):
            print "Checking Camera"
            [frames, state] = camera.getImages16()
            time.sleep(0.5)
            if state == "acquiring":
                print " Acquired", len(frames)
                for frame in frames:
                    acquired += 1
                    print "  Frame", acquired, "[0,0]=", ord(frame[0]) +  256*ord(frame[1])
            else:
                print " Idle Camera"
                acquired += 100

        camera.stopAcquisition()


    print "shutdown"
    camera.shutdown()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

