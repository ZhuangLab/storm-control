#!/usr/bin/env python
"""
Camera control specialized for an Andor SDK3 camera. Presumably
these are always sCMOS cameras.

Hazen 9/15
"""
from PyQt5 import QtCore

import storm_control.sc_hardware.andor.andorSDK3 as andor
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality

#import storm_control.hal4000.camera.frame as frame


class AndorSDK3CameraControl(cameraControl.HWCameraControl):
    """
    This class is used to control an Andor (sCMOS) camera.
    """

    def __init__(self, config = None, is_master = False, **kwds):
        """
        Create an Andor camera control object and initialize
        the camera.
        """
        kwds["config"] = config
        super().__init__(**kwds)
        self.is_master = is_master
        
        # The camera functionality.
        self.camera_functionality = cameraFunctionality.CameraFunctionality(camera_name = self.camera_name,
                                                                            have_temperature = True,
                                                                            is_master = is_master,
                                                                            parameters = self.parameters)
        
        # Load the library and start the camera.
        andor.loadSDK3DLL(config.get("andor_sdk"))
        self.camera = andor.SDK3Camera(config.get("camera_id"))

        # Dictionary of the Andor settings we'll use and their types.
        #
        # FIXME: Maybe the AndorSDK3 module should know the types?
        #
        self.andor_props = {"AOIBinning" : "enum",
                            "AOIHeight" : "int",
                            "AOILeft" : "int",
                            "AOITop" : "int",
                            "AOIWidth" : "int",
                            "CycleMode" : "enum",
                            "ExposureTime" : "float",
                            "FrameCount" : "int",
                            "FrameRate" : "float",
                            "FanSpeed" : "enum",
                            "IOInvert" : "bool",
                            "IOSelector" : "enum",
                            "SensorCooling" : "bool",
                            "SensorHeight" : "int",
                            "SensorTemperature" : "float",
                            "SensorWidth" : "int",
                            "SimplePreAmpGainControl" : "enum",
                            "TemperatureControl" : "enum",
                            "TemperatureStatus" : "enum",
                            "TriggerMode" : "enum"}
        
        self.camera.setProperty("CycleMode", self.andor_props["CycleMode"], "Continuous")

        # Set trigger mode.
        print(">", self.camera_name, "trigger mode set to", config.get("trigger_mode"))
        self.camera.setProperty("TriggerMode", self.andor_props["TriggerMode"], config.get("trigger_mode"))

        # Add Andor SDK3 specific parameters.
        #
        # FIXME: These parameter have different names but the same meaning as the
        #        parameters HAL defines. How to reconcile? It seems best to use
        #        these names as their meaning will be clearly to user.
        #
        max_intensity = 2**16
        self.parameters.setv("max_intensity", max_intensity)

        x_chip = self.camera.getProperty("SensorWidth", self.andor_props["SensorWidth"])
        y_chip = self.camera.getProperty("SensorHeight", self.andor_props["SensorHeight"])
        self.parameters.setv("x_chip", x_chip)
        self.parameters.setv("y_chip", y_chip)

        self.parameters.add(params.ParameterSetString(description = "AOI Binning",
                                                      name = "AOIBinning",
                                                      value = "1x1",
                                                      allowed = ["1x1", "2x2", "3x3", "4x4", "8x8"]))
        
        self.parameters.add(params.ParameterRangeInt(description = "AOI Width",
                                                     name = "AOIWidth",
                                                     value = x_chip,
                                                     min_value = 128,
                                                     max_value = x_chip))
        
        self.parameters.add(params.ParameterRangeInt(description = "AOI Height",
                                                     name = "AOIHeight",
                                                     value = y_chip,
                                                     min_value = 128,
                                                     max_value = y_chip))

        self.parameters.add(params.ParameterRangeInt(description = "AOI Left",
                                                     name = "AOILeft",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = x_chip/2))

        self.parameters.add(params.ParameterRangeInt(description = "AOI Top",
                                                     name = "AOITop",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = y_chip/2))

        self.parameters.add(params.ParameterSetString(description = "Fan Speed",
                                                      name = "FanSpeed",
                                                      value = "On",
                                                      allowed = ["On", "Off"]))

        self.parameters.add(params.ParameterSetBoolean(description = "Sensor cooling",
                                                       name = "SensorCooling",
                                                       value = True))

        self.parameters.add(params.ParameterSetString(description = "Pre-amp gain control",
                                                      name = "SimplePreAmpGainControl",
                                                      value = "16-bit (low noise & high well capacity)",
                                                      allowed = ["16-bit (low noise & high well capacity)", 
                                                                  "Something else.."]))

        self.parameters.add(params.ParameterRangeFloat(description = "Exposure time (seconds)", 
                                                       name = "ExposureTime", 
                                                       value = 0.1,
                                                       min_value = 0.0,
                                                       max_value = 10.0))

        # FIXME: We never actually set this. Maybe we can't?
        self.parameters.add(params.ParameterRangeFloat(description = "Target temperature", 
                                                       name = "temperature", 
                                                       value = -20.0,
                                                       min_value = -50.0,
                                                       max_value = 25.0))

        # Disable editing of the HAL versions of these parameters.
        for param in ["exposure_time", "x_bin", "x_end", "x_start", "y_end", "y_start", "y_bin"]:
            self.parameters.getp(param).setMutable(False)

        self.newParameters(self.parameters, initialization = True)
        
    def getTemperature(self):
        if self.camera_working:
            temperature = self.camera.getProperty("SensorTemperature",
                                                  self.andor_props["SensorTemperature"])
            status = self.camera.getProperty("TemperatureStatus",
                                             self.andor_props["TemperatureStatus"])
            if (status == "Stabilised"):
                status = "stable"
            else:
                status = "unstable"
            self.camera_functionality.temperature.emit({"camera" : self.camera_name,
                                                        "temperature" : temperature,
                                                        "state" : status})

    def newParameters(self, parameters, initialization = False):
        
        # Translate AOI information to parameters used by HAL.
        parameters.set("x_bin", int(parameters.get("AOIBinning")[0]))
        parameters.set("x_end", parameters.get("AOILeft") + parameters.get("AOIWidth") - 1)
        parameters.set("x_pixels", parameters.get("AOIWidth"))
        parameters.set("x_start", parameters.get("AOILeft"))
        
        parameters.set("y_bin", int(parameters.get("AOIBinning")[0]))
        parameters.set("y_end", parameters.get("AOITop") + parameters.get("AOIHeight") - 1)
        parameters.set("y_pixels", parameters.get("AOIHeight"))
        parameters.set("y_start", parameters.get("AOITop"))

        # Super class performs some simple checks & update some things.
        super().newParameters(parameters)

        # FIXME: Set ranges of Andor parameters based on binning?
        
        self.camera_working = True

        # Update the parameter values, only the Andor specific ones and
        # only if they are different.
        to_change = []
        for pname in self.andor_props:
            if self.parameters.has(pname):
                if (self.parameters.get(pname) != parameters.get(pname)) or initialization:
                    to_change.append(pname)

        if (len(to_change)>0):
            running = self.running
            if running:
                self.stopCamera()

            for pname in to_change:
                self.camera.setProperty(pname, self.andor_props[pname], parameters.get(pname))
                self.parameters.setv(pname, parameters.get(pname))

            if running:
                self.startCamera()

            # Get the target temperature for the camera. On some 
            # cameras this cannot be set.
            #
            # FIXME: What is this? Also we are don't seem to be setting the temperature?
            #
            #p.set("temperature", self.camera.getProperty("TemperatureControl", "enum"))

            # Update frame size & timing information.
            self.parameters.setv("bytes_per_frame",
                                 2 * self.parameters.get("AOIHeight") * self.parameters.get("AOIWidth"))
        
            self.parameters.setv("exposure_time",
                                 self.camera.getProperty("ExposureTime", self.andor_props["ExposureTime"]))
        
            self.parameters.setv("fps",
                                 self.camera.getProperty("FrameRate", self.andor_props["FrameRate"]))

            self.camera_functionality.parametersChanged.emit()

    def startFilm(self, film_settings, is_time_base):
        super().startFilm(film_settings, is_time_base)
        if self.camera_working and self.film_length is not None:
            self.camera.setProperty("CycleMode", self.andor_props["CycleMode"], "Fixed")
            self.camera.setProperty("FrameCount", self.andor_props["FrameCount"], self.film_length)

    def stopFilm(self):
        super().stopFilm()
        if self.camera_working:
            self.camera.setProperty("CycleMode", self.andor_props["CycleMode"], "Continuous")

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

