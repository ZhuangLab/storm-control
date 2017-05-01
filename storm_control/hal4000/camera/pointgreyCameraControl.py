#!/usr/bin/python
#
## @file
#
# Camera control specialized for a Point Grey (Spinnaker) camera.
#
# Hazen 12/16
#

from PyQt4 import QtCore
import os
import platform
import traceback

# Debugging
import sc_library.hdebug as hdebug

import sc_library.parameters as params
import camera.frame as frame
import camera.cameraControl as cameraControl

import sc_hardware.pointGrey.spinnaker as spinnaker

## ACameraControl
#
# This class is used to control a Point Grey (Spinnaker) camera.
#
class ACameraControl(cameraControl.HWCameraControl):

    ## __init__
    #
    # Create a Spinnaker camera control object and initialize
    # the camera.
    #
    # @param hardware Camera hardware settings.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        cameraControl.HWCameraControl.__init__(self, hardware, parameters, parent)

        # Initialize library.
        spinnaker.loadSpinnakerDLL(r'C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2013\SpinnakerC_v120.dll')
        spinnaker.spinSystemGetInstance()

        # Get the first camera.
        self.camera = spinnaker.spinGetCamera(0)

        # Add Point Grey specific camera parameters.
        #
        # FIXME: These should all be obtained by querying the camera,
        #        and of course they should be adjustable.
        #
        
        cam_params = parameters.get("camera1")

        self.camera.getProperty("AcquisitionFrameRateAuto")
        self.camera.setProperty("AcquisitionFrameRateAuto", "Off")

        self.camera.getProperty("ExposureAuto")
        self.camera.setProperty("ExposureAuto", "Off")

        self.camera.getProperty("BlackLevelClampingEnable")
        self.camera.setProperty("BlackLevelClampingEnable", False)

        self.camera.getProperty("pgrDefectPixelCorrectionEnable")
        self.camera.setProperty("pgrDefectPixelCorrectionEnable", False)

        self.camera.getProperty("SharpnessEnabled")
        self.camera.setProperty("SharpnessEnabled", False)

        self.camera.getProperty("GammaEnabled")
        self.camera.setProperty("GammaEnabled", False)

        self.camera.getProperty("VideoMode")
        self.camera.setProperty("VideoMode", "Mode7")

        self.camera.getProperty("AcquisitionFrameRate")
        self.camera.setProperty("AcquisitionFrameRate", 100.0)

        self.camera.getProperty("ExposureTime")
        self.camera.setProperty("ExposureTime", 9910.0)

        self.camera.getProperty("BlackLevel")
        self.camera.setProperty("BlackLevel", 1.0)

        self.camera.getProperty("Gain")
        self.camera.setProperty("Gain", 10.0)

        x_start = self.camera.getProperty("OffsetX").spinNodeGetValue()
        x_end = x_start + self.camera.getProperty("Width").spinNodeGetValue() - 1
        y_start = self.camera.getProperty("OffsetY").spinNodeGetValue()
        y_end = y_start + self.camera.getProperty("Height").spinNodeGetValue() - 1

        cam_params.add("max_intensity", params.ParameterInt("",
                                                            "max_intensity",
                                                            4096,
                                                            is_mutable = False,
                                                            is_saved = False))

        cam_params.add("x_start", params.ParameterRangeInt("AOI X start",
                                                           "x_start",
                                                           x_start, 0, 2446))
        cam_params.add("x_end", params.ParameterRangeInt("AOI X end",
                                                         "x_end",
                                                         x_end, 1, 2447))
        cam_params.add("y_start", params.ParameterRangeInt("AOI Y start",
                                                           "y_start",
                                                           y_start, 0, 2046))
        cam_params.add("y_end", params.ParameterRangeInt("AOI Y end",
                                                         "y_end",
                                                         y_end, 1, 2047))

        cam_params.add("x_bin", params.ParameterRangeInt("Binning in X",
                                                         "x_bin",
                                                         1, 1, 4))
        cam_params.add("y_bin", params.ParameterRangeInt("Binning in Y",
                                                         "y_bin",
                                                         1, 1, 4))

        cam_params.add("exposure_time", params.ParameterRangeFloat("Exposure time (seconds)", 
                                                                   "exposure_time", 
                                                                   0.1, 0.0, 60.0))


    ## getAcquisitionTimings
    #
    # Returns the internal frame rate of the camera.
    #
    # @param which_camera The camera to get the timing information for.
    #
    # @return A python array containing the inverse of the internal frame rate.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        exposure_time = 1.0/self.camera.getProperty("AcquisitionFrameRate").spinNodeGetValue()
        return [exposure_time, exposure_time]

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
        
        p.set("bytes_per_frame", 2 * p.get("x_pixels") * p.get("y_pixels") / (p.get("x_bin") * p.get("y_bin")))
        
        self.parameters = p
        self.got_camera = True
        
    ## quit
    #
    # Stops the camera thread and shutsdown the camera.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        self.camera.release()
        spinnaker.spinSystemReleaseInstance()

#
# The MIT License
#
# Copyright (c) 2016 Zhuang Lab, Harvard University
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

