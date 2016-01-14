#!/usr/bin/python
#
## @file
#
# Camera control specialized for an Andor ECCMD camera.
#
# Hazen 09/15
#

from PyQt4 import QtCore
import numpy
import os
import platform
import traceback

# Debugging
import sc_library.hdebug as hdebug

import sc_library.parameters as params
import camera.frame as frame
import camera.cameraControl as cameraControl
import sc_hardware.andor.andorcontroller as andor

## ACameraControl
#
# The CameraControl class specialized to control a Andor camera.
#
class ACameraControl(cameraControl.HWCameraControl):

    ## __init__
    #
    # Create the CameraControl class.
    #
    # @param hardware Camera hardware settings.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        cameraControl.HWCameraControl.__init__(self, hardware, parameters, parent)

        if hardware and hardware.has("pci_card"):
            self.initCamera(hardware.get("pci_card"))
        else:
            self.initCamera()

        # Add Andor EMCCD specific parameters.
        #
        # FIXME: We should get at least some of the values by polling the camera.
        #
        cam_params = parameters.get("camera1")
        cam_params.add("max_intensity", params.ParameterInt("",
                                                            "max_intensity",
                                                            10000,
                                                            is_mutable = False,
                                                            is_saved = False))

        # FIXME: Need to update based on the current EM gain mode.
        [gain_low, gain_high] = self.camera.getEMGainRange()
        cam_params.add("emccd_gain", params.ParameterRangeInt("EMCCD Gain",
                                                              "emccd_gain",
                                                              gain_low, gain_low, gain_high))

        [x_size, y_size] = self.camera.getCameraSize()
        cam_params.add("x_start", params.ParameterRangeInt("AOI X start",
                                                           "x_start",
                                                           1, 1, x_size))
        cam_params.add("x_end", params.ParameterRangeInt("AOI X end",
                                                         "x_end",
                                                         x_size, 1, x_size))
        cam_params.add("y_start", params.ParameterRangeInt("AOI Y start",
                                                           "y_start",
                                                           1, 1, y_size))
        cam_params.add("y_end", params.ParameterRangeInt("AOI Y end",
                                                         "y_end",
                                                         y_size, 1, y_size))
        cam_params.add("x_bin", params.ParameterRangeInt("Binning in X",
                                                         "x_bin",
                                                         1, 1, 4))
        cam_params.add("y_bin", params.ParameterRangeInt("Binning in Y",
                                                         "y_bin",
                                                         1, 1, 4))
        cam_params.add("frame_transfer_mode", params.ParameterSetInt("Frame transfer mode (0 = off, 1 = on)",
                                                                     "frame_transfer_mode",
                                                                     1, [0, 1]))
        cam_params.add("temperature", params.ParameterRangeInt("Temperature",
                                                               "temperature",
                                                               -70, -70, 20))

        preamp_gains = self.camera.getPreampGains()
        print preamp_gains
        cam_params.add("preampgain", params.ParameterSetFloat("Pre-amplifier gain",
                                                              "preampgain",
                                                              preamp_gains[0], preamp_gains))

        # FIXME: Need to update based on the AD channel.
        hs_speeds = self.camera.getHSSpeeds()[0]
        print hs_speeds
        cam_params.add("hsspeed", params.ParameterSetFloat("Horizontal shift speed",
                                                           "hsspeed",
                                                           hs_speeds[0], hs_speeds))

        vs_speeds = self.camera.getVSSpeeds()
        print vs_speeds
        cam_params.add("vsspeed", params.ParameterSetFloat("Vertical shift speed",
                                                           "vsspeed",
                                                           vs_speeds[0], vs_speeds))

        cam_params.add("exposure_time", params.ParameterRangeFloat("Exposure time (seconds)", 
                                                                   "exposure_time", 
                                                                   0.0, 0.0, 100.0))
        cam_params.add("kinetic_cycle_time", params.ParameterRangeFloat("Kinetic cycle time (seconds)",
                                                                        "kinetic_cycle_time",
                                                                        0.0, 0.0, 100.0))
        cam_params.add("adchannel", params.ParameterSetInt("Analog to digital converter channel",
                                                           "adchannel",
                                                           0, [0, 1]))
        cam_params.add("emgainmode", params.ParameterSetInt("EMCCD gain mode",
                                                            "emgainmode",
                                                            0, [0, 1, 2]))
        cam_params.add("baselineclamp", params.ParameterSetBoolean("Baseline clamp",
                                                                   "baselineclamp",
                                                                   True))
        cam_params.add("vsamplitude", params.ParameterSetInt("Vertical shift amplitude",
                                                             "vsamplitude",
                                                             0, [0, 1, 2]))
        cam_params.add("off_during_filming", params.ParameterSetBoolean("Fan off during filming",
                                                                        "off_during_filming",
                                                                        False))
        cam_params.add("low_during_filming", params.ParameterSetBoolean("Fan low during filming",
                                                                        "low_during_filming",
                                                                        False))
        cam_params.add("external_trigger", params.ParameterSetBoolean("Use an external camera trigger",
                                                                      "external_trigger",
                                                                      False))
        cam_params.add("head_model", params.ParameterString("Camera head model", "head_model", "",
                                                            is_mutable = False))

    ## closeShutter
    #
    # Close the shutter.
    #
    @hdebug.debug
    def closeShutter(self):
        self.shutter = False
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.openShutter()
            else:
                self.camera.closeShutter()

    ## getAcquisitionTimings
    #
    # Returns how fast the camera is running.
    #
    # @param which_camera The camera to get the timing information for.
    #
    # @return A Python array containing the time it takes to take a frame.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        if self.got_camera:
            return self.camera.getAcquisitionTimings()[:-1]
        else:
            return [1.0, 1.0]

    ## getProperties
    #
    # @return The properties of the camera as a dict.
    #
    @hdebug.debug
    def getProperties(self):
        return {"camera1" : frozenset(['have_emccd', 'have_preamp', 'have_shutter', 'have_temperature'])}

    ## getTemperature
    #
    # Get the current camera temperature.
    #
    # @param which_camera Which camera to get the temperature of.
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def getTemperature(self, which_camera, parameters):
        temp = [50, "unstable"]
        if self.got_camera:
            temp = self.camera.getTemperature()
        parameters.set("camera1.actual_temperature", temp[0])
        parameters.set("camera1.temperature_control", temp[1])

    ## initCamera
    #
    # This tries to find the right driver file to operate the camera
    # based on the OS type (32 or 64bit) and a search of the common
    # Andor directory names.
    #
    # @param pci_card (Optional) The ID of the PC card to use.
    #
    @hdebug.debug
    def initCamera(self, pci_card = 0):
        if not self.camera:
            hdebug.logText("Initializing Andor Camera", False)

            if (platform.architecture()[0] == "32bit"):
                path = "c:/Program Files/Andor Solis/"
                driver = "atmcd32d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files/Andor iXon/Drivers/"
                driver = "atmcd32d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

            else:
                path = "c:/Program Files/Andor Solis/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files (x86)/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

            hdebug.logText("Can't find Andor Camera drivers")

    ## initCameraHelperFn
    #
    # Given the path, driver and pci_card ID this creates a Andor
    # camera controller class.
    #
    # @param path The path to the Andor camera DLL.
    # @param driver The name of the Andor camera DLL.
    # @param pci_card The ID of the PCI card.
    #
    @hdebug.debug
    def initCameraHelperFn(self, path, driver, pci_card):
        andor.loadAndorDLL(path + driver)
        handle = andor.getCameraHandles()[pci_card]
        self.camera = andor.AndorCamera(path, handle)

    ## newParameters
    #
    # Called when the user selects a new parameters file.
    #
    # @param parameters The new parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        p = parameters.get("camera1")

        size_x = (p.get("x_end") - p.get("x_start") + 1)/p.get("x_bin")
        size_y = (p.get("y_end") - p.get("y_start") + 1)/p.get("y_bin")
        p.set("x_pixels", size_x)
        p.set("y_pixels", size_y)

        self.reversed_shutter = p.get("reversed_shutter")
        try:
            self.camera.setACQMode("run_till_abort")

            hdebug.logText("Setting Read Mode", False)
            self.camera.setReadMode(4)

            hdebug.logText("Setting Temperature", False)
            self.camera.setTemperature(p.get("temperature"))

            hdebug.logText("Setting Trigger Mode", False)
            self.camera.setTriggerMode(0)

            hdebug.logText("Setting ROI and Binning", False)
            cam_roi = [p.get("x_start"), p.get("x_end"), p.get("y_start"), p.get("y_end")]
            cam_binning = [p.get("x_bin"), p.get("y_bin")]
            if p.get("isolated_cropmode", False):
                self.camera.setIsolatedCropMode(True, 
                                                cam_roi[3] - cam_roi[2],
                                                cam_roi[1] - cam_roi[0],
                                                cam_binning[1],
                                                cam_binning[0])
            else:
                self.camera.setIsolatedCropMode(False,
                                                cam_roi[3] - cam_roi[2],
                                                cam_roi[1] - cam_roi[0],
                                                cam_binning[1],
                                                cam_binning[0])
                self.camera.setROIAndBinning(cam_roi, cam_binning)

            hdebug.logText("Setting Horizontal Shift Speed", False)
            p.set("hsspeed", self.camera.setHSSpeed(p.get("hsspeed")))

            hdebug.logText("Setting Vertical Shift Amplitude", False)
            self.camera.setVSAmplitude(p.get("vsamplitude"))

            hdebug.logText("Setting Vertical Shift Speed", False)
            p.set("vsspeed", self.camera.setVSSpeed(p.get("vsspeed")))

            hdebug.logText("Setting EM Gain Mode", False)
            self.camera.setEMGainMode(p.get("emgainmode"))

            hdebug.logText("Setting Advanced EM Gain Control", False)
            self.camera.setEMAdvanced(p.get("emccd_advanced", False))

            hdebug.logText("Setting EM Gain", False)
            self.camera.setEMCCDGain(p.get("emccd_gain"))

            hdebug.logText("Setting Baseline Clamp", False)
            self.camera.setBaselineClamp(p.get("baselineclamp"))

            hdebug.logText("Setting Preamp Gain", False)
            p.set("preampgain", self.camera.setPreAmpGain(p.get("preampgain")))

            hdebug.logText("Setting Acquisition Mode", False)
            self.camera.setACQMode("run_till_abort")

            hdebug.logText("Setting Frame Transfer Mode", False)
            self.camera.setFrameTransferMode(p.get("frame_transfer_mode"))

            hdebug.logText("Setting Exposure Time", False)
            self.camera.setExposureTime(p.get("exposure_time"))

            hdebug.logText("Setting Kinetic Cycle Time", False)
            self.camera.setKineticCycleTime(p.get("kinetic_cycle_time"))

            hdebug.logText("Setting ADChannel", False)
            self.camera.setADChannel(p.get("adchannel"))

            p.set("head_model", self.camera.getHeadModel())
            p.set(["em_gain_low", "em_gain_high"], self.camera.getEMGainRange())

            hdebug.logText("Camera Initialized", False)
            self.got_camera = True
        except:
            hdebug.logText("andorCameraControl: Bad camera settings")
            print traceback.format_exc()
            self.got_camera = False

        if not p.has("bytes_per_frame"):
            p.set("bytes_per_frame", 2 * p.get("x_pixels") * p.get("y_pixels") / (p.get("x_bin") * p.get("y_bin")))

        self.parameters = p

    ## openShutter
    #
    # Open the camera shutter.
    #
    @hdebug.debug
    def openShutter(self):
        self.shutter = True
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.closeShutter()
            else:
                self.camera.openShutter()

    ## setEMCCDGain
    #
    # Set the EMCCD gain of the camera.
    #
    # @param which_camera The camera to set the gain of.
    # @param gain The desired EMCCD gain value.
    #
    @hdebug.debug
    def setEMCCDGain(self, which_camera, gain):
        if self.got_camera:
            self.camera.setEMCCDGain(gain)

    ## startFilm
    #
    # Called before filming in case the camera needs to do any setup.
    #
    # @param film_settings A film settings object.
    #
    @hdebug.debug
    def startFilm(self, film_settings):
        if (film_settings.acq_mode == "fixed_length"):
            if (film_settings.frames_to_take > 1000):
                self.camera.setACQMode("run_till_abort")
            else:
                self.camera.setACQMode("fixed_length", number_frames = film_settings.frames_to_take)

        else:
            self.camera.setACQMode("run_till_abort")

        # Due to what I can only assume is a bug in some of the
        # older Andor software you need to reset the frame
        # transfer mode after setting the aquisition mode.
        self.camera.setFrameTransferMode(self.parameters.get("frame_transfer_mode"))

        # Set camera fan to low. This is overriden by the off option
        if self.parameters.get("low_during_filming"):
            self.camera.setFanMode(1) # fan on low

        # This is for testing whether the camera fan is shaking the
        # the camera, adding noise to the images.
        if self.parameters.get("off_during_filming"):
            self.camera.setFanMode(2) # fan off

    ## stopFilm
    #
    # Called after filming in case the camera needs to do any teardown.
    #
    @hdebug.debug
    def stopFilm(self):
        self.camera.setACQMode("run_till_abort")
        self.camera.setFrameTransferMode(self.parameters.get("frame_transfer_mode"))
        self.camera.setFanMode(1)
        
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

