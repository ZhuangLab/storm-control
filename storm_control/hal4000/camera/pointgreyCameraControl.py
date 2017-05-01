#!/usr/bin/env python
"""
Camera control specialized for a Point Grey (Spinnaker) camera.

Hazen 05/17
"""
import storm_control.sc_hardware.pointGrey.spinnaker as spinnaker
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality


class PointGreyCameraControl(cameraControl.HWCameraControl):
    """
    This class is used to control a Point Grey (Spinnaker) camera.
    """
    def __init__(self, config = None, is_master = False, **kwds):
        kwds["config"] = config
        super().__init__(**kwds)
        
        # The camera functionality.
        self.camera_functionality = cameraFunctionality.CameraFunctionality(camera_name = self.camera_name,
                                                                            is_master = is_master,
                                                                            parameters = self.parameters)

        # Initialize library.
        spinnaker.loadSpinnakerDLL(config.get("pgrey_dll"))
        spinnaker.spinSystemGetInstance()

        # Get the first camera & set some defaults.
        self.camera = spinnaker.spinGetCamera(config.get("camera_id"))

        # This is 12 bit mode.
        self.camera.getProperty("VideoMode")
        self.camera.setProperty("VideoMode", "Mode7")

        # We don't want any of these 'features'.
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

        # Dictionary of Point Grey specific camera parameters.
        #
        self.pgrey_props = {"AcquisitionFrameRate" : True,
                            "BlackLevel" : True,
                            "Gain" : True,
                            "Height" : True,
                            "OffsetX" : True,
                            "OffsetY" : True,
                            "Width" : True}

        max_intensity = 2**12
        self.parameters.setv("max_intensity", max_intensity)

        x_chip = self.camera.getProperty("WidthMax").spinNodeGetValue()
        y_chip = self.camera.getProperty("HeightMax").spinNodeGetValue()
        self.parameters.setv("x_chip", x_chip)
        self.parameters.setv("y_chip", y_chip)

        self.parameters.add(params.ParameterRangeFloat(description = "Acquisition frame rate (FPS)",
                                                       name = "AcquisitionFrameRate",
                                                       value = 10.0,
                                                       max_value = self.camera.getProperty("AcquisitionFrameRate").spinNodeGetMaximum(),
                                                       min_value = self.camera.getProperty("AcquisitionFrameRate").spinNodeGetMinimum()))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Black level",
                                                       name = "BlackLevel",
                                                       value = 1.0,
                                                       max_value = self.camera.getProperty("BlackLevel").spinNodeGetMaximum(),
                                                       min_value = self.camera.getProperty("BlackLevel").spinNodeGetMinimum()))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Gain",
                                                       name = "Gain",
                                                       value = 10.0,
                                                       max_value = self.camera.getProperty("Gain").spinNodeGetMaximum(),
                                                       min_value = self.camera.getProperty("Gain").spinNodeGetMinimum()))

        self.parameters.add(params.ParameterRangeInt(description = "AOI height",
                                                     name = "Height",
                                                     value = y_chip,
                                                     max_value = self.camera.getProperty("Height").spinNodeGetMaximum(),
                                                     min_value = self.camera.getProperty("Height").spinNodeGetMinimum()))

        self.parameters.add(params.ParameterRangeInt(description = "AOI x offset",
                                                     name = "OffsetX",
                                                     value = 0,
                                                     max_value = self.camera.getProperty("OffsetX").spinNodeGetMaximum(),
                                                     min_value = self.camera.getProperty("OffsetX").spinNodeGetMinimum()))

        self.parameters.add(params.ParameterRangeInt(description = "AOI y offset",
                                                     name = "OffsetY",
                                                     value = 0,
                                                     max_value = self.camera.getProperty("OffsetY").spinNodeGetMaximum(),
                                                     min_value = self.camera.getProperty("OffsetY").spinNodeGetMinimum()))

        self.parameters.add(params.ParameterRangeInt(description = "AOI width",
                                                     name = "Width",
                                                     value = x_chip,
                                                     max_value = self.camera.getProperty("Width").spinNodeGetMaximum(),
                                                     min_value = self.camera.getProperty("Width").spinNodeGetMinimum()))

        # Disable editing of the HAL versions of these parameters.
        for param in ["exposure_time", "x_bin", "x_end", "x_start", "y_end", "y_start", "y_bin"]:
            self.parameters.getp(param).setMutable(False)

        self.newParameters(self.parameters, initialization = True)
                             
    def newParameters(self, parameters, initialization = False):
        
        # Translate AOI information to parameters used by HAL.
        parameters.set("x_end", parameters.get("OffsetX") + parameters.get("Width") - 1)
        parameters.set("x_pixels", parameters.get("Width"))
        parameters.set("x_start", parameters.get("OffsetX") + 1)
        
        parameters.set("y_end", parameters.get("OffsetY") + parameters.get("Height") - 1)
        parameters.set("y_pixels", parameters.get("Height"))
        parameters.set("y_start", parameters.get("OffsetY") + 1)

        # Super class performs some simple checks & update some things.
        super().newParameters(parameters)

        self.camera_working = True

        # Update the parameter values, only the Point Grey specific 
        # ones and only if they are different.
        to_change = []
        for pname in self.pgrey_props:
            if (self.parameters.get(pname) != parameters.get(pname)) or initialization:
                to_change.append(pname)
        
        if (len(to_change)>0):
            running = self.running
            if running:
                self.stopCamera()

            # Change camera.
            for pname in to_change:
                self.camera.setProperty(pname, parameters.get(pname))

            # Update properties, note that the allowed ranges of many
            # of the parameters will likely change.
            for pname in self.pgrey_props:
                param = self.parameters.getp(pname)
                param.setMaximum(self.camera.getProperty(pname).spinNodeGetMaximum())
                param.setMinimum(self.camera.getProperty(pname).spinNodeGetMinimum())
                param.setv(parameters.get(pname))

            # Set the exposure time to be the maximum given the current frame rate.
            self.camera.setProperty("ExposureTime", self.camera.getProperty("ExposureTime").spinNodeGetMaximum())
            
            self.parameters.setv("exposure_time", 1.0e-6 * self.camera.getProperty("ExposureTime").spinNodeGetValue())
            self.parameters.setv("fps", self.camera.getProperty("AcquisitionFrameRate").spinNodeGetValue())

            if running:
                self.startCamera()
                
            self.camera_functionality.parametersChanged.emit()


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

