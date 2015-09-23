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

import camera.cameraControl as cameraControl
import sc_hardware.andor.andorSDK3 as andor

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
    def __init__(self, hardware, parent = None):
        cameraControl.HWCameraControl.__init__(self, hardware, parent)

        andor.loadSDK3DLL("C:/Program Files/Andor SOLIS/")
        if hardware:
            self.camera = andor.SDK3Camera(hardware.get("camera_id", 0))
        else:
            self.camera = andor.SDK3Camera()
        self.camera.setProperty("CycleMode", "enum", "Continuous")

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
            for key, value in p.__dict__.iteritems():
                if self.camera.hasFeature(key):
                    value_type = str(type(value).__name__)
                    self.camera.setProperty(key, value_type, value)

            self.got_camera = True

        except andor.AndorException:
            hdebug.logText("QCameraThread: Bad camera settings")
            print traceback.format_exc()
            self.got_camera = False

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
        if (film_settings.acq_mode == "fixed_length"):
            self.camera.setProperty("CycleMode", "enum", "Fixed")
            self.camera.setProperty("FrameCount", "int", film_settings.frames_to_take)
        else:
            self.camera.setProperty("CycleMode", "enum", "Continuous")

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

