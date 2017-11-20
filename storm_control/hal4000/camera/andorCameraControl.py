#!/usr/bin/env python
"""
Camera control specialized for an Andor ECCMD camera.

Hazen 04/17
"""
import copy
import os
from PyQt5 import QtCore

import storm_control.sc_hardware.andor.andorcontroller as andor
import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality


class AndorCameraControlException(halExceptions.HardwareException):
    pass

class AndorCameraControl(cameraControl.HWCameraControl):
    """
    This class is used to control Andor EMCCD cameras.
    """
    def __init__(self, config = None, is_master = False, **kwds):
        kwds["config"] = config
        super().__init__(**kwds)
        self.reversed_shutter = config.get("reversed_shutter", False)

        # The camera configuration.
        self.camera_functionality = cameraFunctionality.CameraFunctionality(camera_name = self.camera_name,
                                                                            have_emccd = True,
                                                                            have_preamp = True,
                                                                            have_shutter = True,
                                                                            have_temperature = True,
                                                                            is_master = is_master,
                                                                            parameters = self.parameters)
        self.camera_functionality.setEMCCDGain = self.setEMCCDGain
        self.camera_functionality.toggleShutter = self.toggleShutter

        # Load Andor DLL & get the camera.
        andor.loadAndorDLL(os.path.join(config.get("andor_path"), config.get("andor_dll")))
        handle = andor.getCameraHandles()[config.get("camera_id")]
        self.camera = andor.AndorCamera(config.get("andor_path"), handle)

        # Dictionary of Andor camera properties we'll support.
        self.andor_props = {"adchannel" : True,
                            "baselineclamp" : True,
                            "emccd_advanced" : True,
                            "emccd_gain" : True,
                            "emgainmode" : True,
                            "exposure_time" : True,
                            "extension" : True,
                            "external_trigger" : True,
                            "frame_transfer_mode" : True,
                            "hsspeed" : True,
                            "isolated_cropmode" : True,
                            "kinetic_cycle_time" : True,
                            "low_during_filming" : True,
                            "off_during_filming" : True,
                            "preampgain" : True,
                            "saved" : True,
                            "temperature" : True,
                            "vsamplitude" : True,
                            "vsspeed" : True,
                            "x_bin" : True,
                            "x_end" : True,
                            "x_start" : True,
                            "y_bin" : True,
                            "y_end" : True,
                            "y_start" : True}
        
        # Add Andor EMCCD specific parameters.
        self.parameters.setv("max_intensity", self.camera.getMaxIntensity())

        [gain_low, gain_high] = self.camera.getEMGainRange()
        self.parameters.add("emccd_gain", params.ParameterRangeInt(description = "EMCCD Gain",
                                                                   name = "emccd_gain",
                                                                   value = gain_low, 
                                                                   min_value = gain_low, 
                                                                   max_value = gain_high,
                                                                   order = 2))

        # Adjust ranges of the size and binning parameters.
        [x_size, y_size] = self.camera.getCameraSize()
        self.parameters.getp("x_end").setMaximum(x_size)
        self.parameters.getp("x_start").setMaximum(x_size)
        self.parameters.getp("y_end").setMaximum(y_size)
        self.parameters.getp("y_start").setMaximum(y_size)

        self.parameters.setv("x_end", x_size)
        self.parameters.setv("y_end", y_size)
        self.parameters.setv("x_chip", x_size)
        self.parameters.setv("y_chip", y_size)

        [x_max_bin, y_max_bin] = self.camera.getMaxBinning()
        self.parameters.getp("x_bin").setMaximum(x_max_bin)
        self.parameters.getp("y_bin").setMaximum(y_max_bin)

        # FIXME: Need to check if camera supports frame transfer mode.
        self.parameters.add(params.ParameterSetInt(description = "Frame transfer mode (0 = off, 1 = on)",
                                                   name = "frame_transfer_mode",
                                                   value = 1, 
                                                   allowed = [0, 1]))

        [mint, maxt] = self.camera.getTemperatureRange()
        self.parameters.add(params.ParameterRangeInt(description = "Target temperature",
                                                     name = "temperature",
                                                     value = -70, 
                                                     min_value = mint, 
                                                     max_value = maxt))

        preamp_gains = self.camera.getPreampGains()
        self.parameters.add(params.ParameterSetFloat(description = "Pre-amplifier gain",
                                                     name = "preampgain",
                                                     value = preamp_gains[0], 
                                                     allowed = preamp_gains))

        hs_speeds = self.camera.getHSSpeeds()[0]
        self.parameters.add(params.ParameterSetFloat(description = "Horizontal shift speed",
                                                     name = "hsspeed",
                                                     value = hs_speeds[0], 
                                                     allowed = hs_speeds))

        vs_speeds = self.camera.getVSSpeeds()
        self.parameters.add(params.ParameterSetFloat(description = "Vertical shift speed",
                                                     name = "vsspeed",
                                                     value = vs_speeds[-1], 
                                                     allowed = vs_speeds))

#        self.parameters.getp("exposure_time").setMaximum(self.camera.getMaxExposure())

        self.parameters.getp("exposure_time").setOrder(2)
        self.parameters.setv("exposure_time", 0.0)

        self.parameters.add(params.ParameterRangeFloat(description = "Kinetic cycle time (seconds)",
                                                       name = "kinetic_cycle_time",
                                                       value = 0.0, 
                                                       min_value = 0.0, 
                                                       max_value = 100.0))

        ad_channels = list(range(self.camera.getNumberADChannels()))
        self.parameters.add(params.ParameterSetInt(description = "Analog to digital converter channel",
                                                   name = "adchannel",
                                                   value = 0, 
                                                   allowed = ad_channels))

        n_modes = list(range(self.camera.getNumberEMGainModes()))
        self.parameters.add(params.ParameterSetInt(description = "EMCCD gain mode",
                                                   name = "emgainmode",
                                                   value = 0, 
                                                   allowed = n_modes))

        self.parameters.add(params.ParameterSetBoolean(description = "Baseline clamp",
                                                       name = "baselineclamp",
                                                       value = True))

        # FIXME: Need to get amplitudes from the camera.
        self.parameters.add(params.ParameterSetInt(description = "Vertical shift amplitude",
                                                   name = "vsamplitude",
                                                   value = 0, 
                                                   allowed = [0, 1, 2]))

        self.parameters.add(params.ParameterSetBoolean(description = "Fan off during filming",
                                                       name = "off_during_filming",
                                                       value = False))

        self.parameters.add(params.ParameterSetBoolean(description = "Fan low during filming",
                                                       name = "low_during_filming",
                                                       value = False))

        self.parameters.add(params.ParameterSetBoolean(description = "Use an external camera trigger",
                                                       name = "external_trigger",
                                                       value = False))

        self.parameters.add(params.ParameterString(description = "Camera head model", 
                                                   name = "head_model", 
                                                   value = self.camera.getHeadModel(),
                                                   is_mutable = False))

        self.parameters.add(params.ParameterSetBoolean(description = "Isolated crop mode",
                                                       name = "isolated_cropmode",
                                                       value = False))

        self.parameters.add(params.ParameterSetBoolean(description = "Advanced EMCCD gain mode",
                                                       name = "emccd_advanced",
                                                       value = False))

        self.newParameters(self.parameters, initialization = True)

    def closeShutter(self):
        super().closeShutter()
        if self.camera_working:
            running = self.running
            if running:
                self.stopCamera()

            if self.reversed_shutter:
                self.camera.openShutter()
            else:
                self.camera.closeShutter()

            if running:
                self.startCamera()

    def getTemperature(self):
        if self.camera_working:
            temp = self.camera.getTemperature()
            self.camera_functionality.temperature.emit({"camera" : self.camera_name,
                                                        "temperature" : temp[0],
                                                        "state" : temp[1]})

    def newParameters(self, parameters, initialization = False):
        size_x = parameters.get("x_end") - parameters.get("x_start") + 1
        size_y = parameters.get("y_end") - parameters.get("y_start") + 1
        parameters.setv("x_pixels", size_x)
        parameters.setv("y_pixels", size_y)
        parameters.setv("bytes_per_frame", 2 * size_x * size_y)

        super().newParameters(parameters)

        self.camera_working = True

        # Update the parameter values, only the Andor specific ones
        # and only if they are different.
        to_change = []
        for pname in self.andor_props:
            if (self.parameters.get(pname) != parameters.get(pname)) or initialization:
                to_change.append(pname)

        if (len(to_change) > 0):
            running = self.running
            if running:
                self.stopCamera()

            self.camera.setACQMode("run_till_abort")
            self.camera.setReadMode(4)

            current_roi = [self.parameters.get("x_start"), 
                           self.parameters.get("x_end"), 
                           self.parameters.get("y_start"), 
                           self.parameters.get("y_end")]

            current_binning = [self.parameters.get("x_bin"), 
                               self.parameters.get("y_bin")]

            new_roi = copy.deepcopy(current_roi)
            new_binning = copy.deepcopy(current_binning)

            #
            # Go through to to_change in this somewhat convoluted fashion so
            # that parameters get set in the proper order.
            #
            for pname in self.parameters.getSortedAttrs():

                if not pname in to_change:
                    continue

                if (pname == "adchannel"):
                    self.camera.setADChannel(parameters.get("adchannel"))
                    hs_speeds = self.camera.getHSSpeeds()[parameters.get("adchannel")]
                    prop = self.parameters.getp("hsspeed")
                    prop.setAllowed(hs_speeds)

                elif (pname == "baselineclamp"):
                    self.camera.setBaselineClamp(parameters.get("baselineclamp"))

                elif (pname == "emccd_advanced"):
                    self.camera.setEMAdvanced(parameters.get("emccd_advanced"))

                elif (pname == "emccd_gain"):
                    self.camera.setEMCCDGain(parameters.get("emccd_gain"))

                elif (pname == "emgainmode"):
                    self.camera.setEMGainMode(parameters.get("emgainmode"))
                    [gain_low, gain_high] = self.camera.getEMGainRange()
                    prop = self.parameters.getp("emccd_gain")
                    prop.setMinimum(gain_low)
                    prop.setMaximum(gain_high)

                elif (pname == "exposure_time"):
                    self.camera.setExposureTime(parameters.get("exposure_time"))

                elif (pname == "external_trigger"):
                    if parameters.get("external_trigger"):
                        self.camera.setTriggerMode(1)
                    else:
                        self.camera.setTriggerMode(0)

                elif (pname == "frame_transfer_mode"):
                    self.camera.setFrameTransferMode(parameters.get("frame_transfer_mode"))

                elif (pname == "hsspeed"):
                    self.camera.setHSSpeed(parameters.get("hsspeed"))
                    
                elif (pname == "kinetic_cycle_time"):
                    self.camera.setKineticCycleTime(parameters.get("kinetic_cycle_time"))

                elif (pname == "preampgain"):
                    self.camera.setPreAmpGain(parameters.get("preampgain"))

                elif (pname == "temperature"):
                    self.camera.setTemperature(parameters.get("temperature"))

                elif (pname == "vsamplitude"):
                    self.camera.setVSAmplitude(parameters.get("vsamplitude"))

                elif (pname == "vsspeed"):
                    self.camera.setVSSpeed(parameters.get("vsspeed"))

                elif (pname == "x_bin"):
                    new_binning[0] = parameters.get("x_bin")

                elif (pname == "x_end"):
                    new_roi[1] = parameters.get("x_end")

                elif (pname == "x_start"):
                    new_roi[0] = parameters.get("x_start")

                elif (pname == "y_bin"):
                    new_binning[1] = parameters.get("y_bin")

                elif (pname == "y_end"):
                    new_roi[3] = parameters.get("y_end")

                elif (pname == "y_start"):
                    new_roi[2] = parameters.get("y_start")

                else:
                    if not pname in ["extension", 
                                     "isolated_cropmode",
                                     "low_during_filming",
                                     "off_during_filming",
                                     "saved"]:
                        print(">> Unknown parameter '" + pname + "'")
                        #raise AndorCameraControlException("Unknown parameter '" + pname + "'")

                self.parameters.setv(pname, parameters.get(pname))

            if (new_roi != current_roi) or (new_binning != current_binning) or initialization:
                if parameters.get("isolated_cropmode"):
                    self.camera.setIsolatedCropMode(True, 
                                                    new_roi[3] - new_roi[2],
                                                    new_roi[1] - new_roi[0],
                                                    new_binning[1],
                                                    new_binning[0])
                else:
                    self.camera.setIsolatedCropMode(False,
                                                    new_roi[3] - new_roi[2],
                                                    new_roi[1] - new_roi[0],
                                                    new_binning[1],
                                                    new_binning[0])
                    self.camera.setROIAndBinning(new_roi, new_binning)

            for pname in ["bytes_per_frame", "x_pixels", "y_pixels"]:
                self.parameters.setv(pname, parameters.get(pname))

            [exposure_time, cycle_time] = self.camera.getAcquisitionTimings()[:-1]
            self.parameters.setv("exposure_time", exposure_time)
            self.parameters.setv("fps", 1.0/cycle_time)

            if running:
                self.startCamera()

            self.camera_functionality.parametersChanged.emit()

    def openShutter(self):
        super().openShutter()
        if self.camera_working:
            running = self.running
            if running:
                self.stopCamera()

            if self.reversed_shutter:
                self.camera.closeShutter()
            else:
                self.camera.openShutter()

            if running:
                self.startCamera()

    def setEMCCDGain(self, gain):
        super().setEMCCDGain(gain)
        if self.camera_working:
            running = self.running
            if running:
                self.stopCamera()

            self.camera.setEMCCDGain(gain)

            if running:
                self.startCamera()

    def startFilm(self, film_settings, is_time_base):
        super().startFilm(film_settings, is_time_base)
        if self.camera_working:
            if self.film_length is not None:
                if (self.film_length > 1000):
                    self.camera.setACQMode("run_till_abort")
                else:
                    self.camera.setACQMode("fixed_length", number_frames = self.film_length)
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

    def stopFilm(self):
        super().stopFilm()
        if self.camera_working:
            self.camera.setACQMode("run_till_abort")
            self.camera.setFrameTransferMode(self.parameters.get("frame_transfer_mode"))
            self.camera.setFanMode(1)

        
#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

