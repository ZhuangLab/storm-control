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

        # Add Andor SDK3 specific parameters.
        #
        cam_params = parameters.get("camera1")

        max_intensity = 2**16
        cam_params.add("max_intensity", params.ParameterInt("",
                                                            "max_intensity",
                                                            max_intensity,
                                                            is_mutable = False,
                                                            is_saved = False))

        [x_size, y_size] = [2048, 2048]
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

        [x_max_bin, y_max_bin] = [4,4]
        cam_params.add("x_bin", params.ParameterRangeInt("Binning in X",
                                                         "x_bin",
                                                         1, 1, x_max_bin))
        cam_params.add("y_bin", params.ParameterRangeInt("Binning in Y",
                                                         "y_bin",
                                                         1, 1, y_max_bin))

        cam_params.add("FanSpeed", params.ParameterSetString("Fan Speed",
                                                              "FanSpeed",
                                                              "On",
                                                              ["On", "Off"]))

        cam_params.add("SensorCooling", params.ParameterSetBoolean("Sensor cooling",
                                                                   "SensorCooling",
                                                                   True))

        cam_params.add("SimplePreAmpGainControl", params.ParameterSetString("Pre-amp gain control",
                                                                             "SimplePreAmpGainControl",
                                                                             "16-bit (low noise &amp; high well capacity)",
                                                                             ["16-bit (low noise &amp; high well capacity)", 
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
        p = parameters.get("camera1")

        size_x = (p.get("x_end") - p.get("x_start") + 1)/p.get("x_bin")
        size_y = (p.get("y_end") - p.get("y_start") + 1)/p.get("y_bin")
        p.set("x_pixels", size_x)
        p.set("y_pixels", size_y)

        try:

            # Set binning. Some cameras might support x_bin != y_bin to
            # for now we are requiring these to be equal.
            x_bin = p.get("x_bin")
            if (x_bin != p.get("y_bin")):
                raise AssertionError("unequal binning is not supported.")
            if (x_bin == 1):
                self.camera.setProperty("AOIBinning", "enum", "1x1")
            elif (x_bin == 2):
                self.camera.setProperty("AOIBinning", "enum", "2x2")
            elif (x_bin == 3):
                self.camera.setProperty("AOIBinning", "enum", "3x3")
            elif (x_bin == 4):
                self.camera.setProperty("AOIBinning", "enum", "4x4")
            elif (x_bin == 8):
                self.camera.setProperty("AOIBinning", "enum", "8x8")
            else:
                raise andor.AndorException("unsupported bin size " + str(p.get("x_bin")))

            # Set ROI location and size.
            if ((p.get("x_pixels") % x_bin) != 0) or ((p.get("y_pixels") % x_bin) != 0):
                raise andor.AndorException("image size must be a multiple of the bin size.")

            self.camera.setProperty("AOIWidth", "int", p.get("x_pixels")/x_bin)
            self.camera.setProperty("AOIHeight", "int", p.get("y_pixels")/x_bin)
            self.camera.setProperty("AOILeft", "int", p.get("x_start"))
            self.camera.setProperty("AOITop", "int", p.get("y_start"))

            # Set the rest of the camera properties.
            #
            # Note: These could overwrite the above. For example, if you
            #   have both "x_start" and "AOILeft" in the parameters
            #   file then "AOILeft" will overwrite "x_start". Trouble
            #   may follow if they are not set to the same value.
            #
            #for key, value in p.__dict__.iteritems():
            for key, value_obj in p.parameters.iteritems():
                value = value_obj.getv()
                value_type = str(type(value).__name__)
                print key, value_obj, value_type, value

                if self.camera.hasFeature(key):
                    value_type = str(type(value).__name__)
                    self.camera.setProperty(key, value_type, value)

            self.got_camera = True

        except andor.AndorException as error:
##            hdebug.logText("QCameraThread: Bad camera settings")
##            print traceback.format_exc()
##            self.got_camera = False
            self.got_camera = False
            error_message = "startFilm error in AndorSDK3: \n" + str(error)
            hdebug.logText(error_message)
            raise halModule.NewParametersException(error_message)

        if not p.has("bytes_per_frame"):
            p.set("bytes_per_frame", 2 * p.get("x_pixels") * p.get("y_pixels"))

        # Get the target temperature for the camera. On some 
        # cameras this cannot be set.
        if not p.has("temperature"):
            p.set("temperature", self.camera.getProperty("TemperatureControl", "enum"))

        self.parameters = p

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

