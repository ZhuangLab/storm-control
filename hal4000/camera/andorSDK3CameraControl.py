#!/usr/bin/python
#
## @file
#
# Camera control specialized for an Andor SDK3 camera. Presumably
# these are always sCMOS cameras.
#
# Hazen 9/15
#

from PyQt4 import QtCore
import os
import platform
import traceback
import copy

# Debugging
import sc_library.hdebug as hdebug

import sc_library.parameters as params
import camera.cameraControl as cameraControl
import sc_hardware.andor.andorSDK3 as andor
import halLib.halModule as halModule

## ACameraControl
#
# This class is used to control an Andor (sCMOS) camera.
#
class ACameraControl(cameraControl.HWCameraControl):

    ## __init__
    #
    # Create an Andor camera control object and initialize
    # the camera.
    #
    # @param hardware Camera hardware settings.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        cameraControl.HWCameraControl.__init__(self, hardware, parameters, parent)

        andor.loadSDK3DLL("C:/Program Files/Andor SOLIS/")
        if hardware:
            self.camera = andor.SDK3Camera(hardware.get("camera_id", 0))
        else:
            self.camera = andor.SDK3Camera()
        self.camera.setProperty("CycleMode", "enum", "Continuous")

        self.parameters = params.StormXMLObject([]) # Create empty parameters object

        # Add Andor SDK3 specific parameters.
        #
        cam_params = parameters.get("camera1")

        max_intensity = 2**16
        cam_params.add("max_intensity", params.ParameterInt("",
                                                            "max_intensity",
                                                            max_intensity,
                                                            is_mutable = False,
                                                            is_saved = False))

##        [x_size, y_size] = [2048, 2048]
##        cam_params.add("x_start", params.ParameterRangeInt("AOI X start",
##                                                           "x_start",
##                                                           1, 1, x_size))
##        cam_params.add("x_end", params.ParameterRangeInt("AOI X end",
##                                                         "x_end",
##                                                         x_size, 1, x_size))
##        cam_params.add("y_start", params.ParameterRangeInt("AOI Y start",
##                                                           "y_start",
##                                                           1, 1, y_size))
##        cam_params.add("y_end", params.ParameterRangeInt("AOI Y end",
##                                                         "y_end",
##                                                         y_size, 1, y_size))
##
##        [x_max_bin, y_max_bin] = [4,4]
##        cam_params.add("x_bin", params.ParameterRangeInt("Binning in X",
##                                                         "x_bin",
##                                                         1, 1, x_max_bin))
##        cam_params.add("y_bin", params.ParameterRangeInt("Binning in Y",
##                                                         "y_bin",
##                                                         1, 1, y_max_bin))

        cam_params.add("AOIBinning", params.ParameterSetString("AOI Binning",
                                                               "AOIBinning",
                                                               "1x1",
                                                               ["1x1", "2x2", "3x3", "4x4", "8x8"]))
        cam_params.add("AOIWidth", params.ParameterRangeInt("AOI Width",
                                                            "AOIWidth",
                                                            2048,
                                                            128, 2048))
        cam_params.add("AOIHeight", params.ParameterRangeInt("AOI Height",
                                                             "AOIHeight",
                                                             2048,
                                                             128, 2048))

        cam_params.add("AOILeft", params.ParameterRangeInt("AOI Left",
                                                           "AOILeft",
                                                           1,
                                                           1, 1028))

        cam_params.add("AOITop", params.ParameterRangeInt("AOI Top",
                                                          "AOITop",
                                                          1,
                                                          1, 1028))

        cam_params.add("FanSpeed", params.ParameterSetString("Fan Speed",
                                                              "FanSpeed",
                                                              "On",
                                                              ["On", "Off"]))

        cam_params.add("SensorCooling", params.ParameterSetBoolean("Sensor cooling",
                                                                   "SensorCooling",
                                                                   True))

        cam_params.add("SimplePreAmpGainControl", params.ParameterSetString("Pre-amp gain control",
                                                                             "SimplePreAmpGainControl",
                                                                             "16-bit (low noise & high well capacity)",
                                                                             ["16-bit (low noise & high well capacity)", 
                                                                              "Something else.."]))

        cam_params.add("ExposureTime", params.ParameterRangeFloat("Exposure time (seconds)", 
                                                                  "ExposureTime", 
                                                                  0.1, 0.0, 10.0))

    ## getAcquisitionTimings
    #
    # Returns 1 over the frame rate of the camera.
    #
    # @return A python array containing the inverse of the internal frame rate.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        exp_time = self.camera.getProperty("ExposureTime", "float")
        cycle_time = 1.0/self.camera.getProperty("FrameRate", "float")
        return [exp_time, cycle_time]

    ## getProperties
    #
    # @return The properties of the camera as a dict.
    #
    @hdebug.debug
    def getProperties(self):
        return {"camera1" : frozenset(['have_temperature'])}

    ## getTemperature
    #
    # Get the current camera temperature.
    #
    # @param which_camera Which camera to get the temperature of.
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def getTemperature(self, which_camera, parameters):
        temperature = self.camera.getProperty("SensorTemperature", "float")
        if (self.camera.getProperty("TemperatureStatus", "enum") == "Stabilised"):
            status = "stable"
        else:
            status = "unstable"
        parameters.set("camera1.actual_temperature", temperature)
        parameters.set("camera1.temperature_control", status)

    ## newParameters
    #
    # Update the camera parameters based on a new parameters object.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        # Get the camera parameters
        p = parameters.get("camera1")

        # Try setting the parameters
        try:
            # Loop over parameters
            for key in p.getAttrs():
                # Check for a difference from the current configuration
                if not (key in self.parameters.getAttrs()) or not (self.parameters.get(key) == p.get(key)):
                    if self.camera.hasFeature(key):
                        value = p.get(key)
                        value_type = str(type(value).__name__)
                        self.camera.setProperty(key, value_type, value)
            
            self.got_camera = True

        except andor.AndorException as error:
            self.got_camera = False
            error_message = "newParameters error in AndorSDK3: \n" + str(error)
            hdebug.logText(error_message)
            raise halModule.NewParametersException(error_message)

        # Get the target temperature for the camera. On some 
        # cameras this cannot be set.
        p.set("temperature", self.camera.getProperty("TemperatureControl", "enum"))

        # Update frame size
        p.set("bytes_per_frame", 2 * p.get("AOIHeight") * p.get("AOIWidth"))

        # Translate AOI information to values used by other hal modules
        p.set("x_bin", int(p.get("AOIBinning")[0]))
        p.set("y_bin", int(p.get("AOIBinning")[0]))
        p.set("x_start", p.get("AOILeft"))
        p.set("y_start", p.get("AOITop"))
        p.set("x_end", p.get("AOILeft") + p.get("AOIWidth") - 1)
        p.set("y_end", p.get("AOITop") + p.get("AOIHeight") - 1)
        p.set("x_pixels", p.get("AOIWidth"))
        p.set("y_pixels", p.get("AOIHeight"))

        # Record the current camera configuration
        self.parameters = copy.deepcopy(p)

    ## startFilm
    #
    # Called before filming in case the camera needs to do any setup.
    #
    # @param film_settings A film settings object.
    #
    @hdebug.debug
    def startFilm(self, film_settings):
        try:
            if (film_settings.acq_mode == "fixed_length"):
                self.camera.setProperty("CycleMode", "enum", "Fixed")
                self.camera.setProperty("FrameCount", "int", film_settings.frames_to_take)
            else:
                self.camera.setProperty("CycleMode", "enum", "Continuous")
        except andor.AndorException as error:
            error_message = "startFilm error in AndorSDK3: \n" + str(error)
            hdebug.logText(error_message)
            raise halModule.StartFilmException(error_message)

    ## stopFilm
    #
    # Called after filming in case the camera needs to do any teardown.
    #
    @hdebug.debug
    def stopFilm(self):
        self.camera.setProperty("CycleMode", "enum", "Continuous")


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

