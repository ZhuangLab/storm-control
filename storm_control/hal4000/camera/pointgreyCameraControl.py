#!/usr/bin/env python
"""
Camera control specialized for a Point Grey (Spinnaker) camera.

Tested on :
   GS3-U3-51S5M
   GS3-U3-41C6NIR

Hazen 01/19
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
        self.is_master = is_master
        
        # The camera functionality.
        self.camera_functionality = cameraFunctionality.CameraFunctionality(camera_name = self.camera_name,
                                                                            is_master = self.is_master,
                                                                            parameters = self.parameters)

        # Initialize library.
        spinnaker.pySpinInitialize(verbose = False)

        # Get the camera & set some defaults.
        self.camera = spinnaker.getCamera(config.get("camera_id"))
          
        # Set FLIR-specific camera properties to control relationship between
        # exposure time and frame rate: This dictionary will allow extension in the future if needed
        self.exposure_control = {"CameraControlExposure": True}
          
        # Extract preset values if provided
        if config.has("presets"):
            # Extract preset values
            presets = config.get("presets")
            
            print("Configuring preset values of spinnaker camera: " + str(config.get("camera_id")))
            
            # Loop over values and set them
            for p_name in presets.getAttrs():
                if self.camera.hasProperty(p_name): # Confirm the camera has the property and warn if not
                    p_value = presets.get(p_name)
                    self.camera.setProperty(p_name, p_value) # Set value
                    set_value = self.camera.getProperty(p_name).getValue() # Check set
                    print("   " + str(p_name) + ": " + str(p_value) + " (" + str(set_value) + ")")
                else:
                    if p_name not in self.exposure_control.keys():
                        print("!!!! preset " + str(p_name) + " is not a valid parameter for this camera")
            
            # Set the exposure-frame-rate-control parameters
            self.exposure_control["CameraControlExposure"] = presets.get("CameraControlExposure", True)
            print("Set exposure control properties:")
            for key in self.exposure_control.keys():
                print("   " + str(key) + ": " + str(self.exposure_control[key]))
                
        else:
            print("No presets provided for spinnaker camera: " + str(config.get("camera_id")))
        
        # Verify that we have turned off some of these 'features'.
        ## REMOVED THIS BLOCK AS IT IS CAMERA SPECIFIC
        #for feature in ["pgrDefectPixelCorrectionEnable",
        #                "BlackLevelClampingEnable",
        #                "SharpnessEnabled",
        #                "GammaEnabled"]:
        #    if self.camera.hasProperty(feature):
        #        assert not self.camera.getProperty(feature).getValue()

        # Configure 'master' cameras to not use triggering.
        #
        self.camera.getProperty("TriggerMode")
        if self.is_master:
            self.camera.setProperty("TriggerMode", "Off")

            # This line is connected to the DAQ.
            self.camera.setProperty("LineSelector", "Line1")
            self.camera.setProperty("LineSource", "ExposureActive")

            # This line is connected to the other cameras.
            self.camera.setProperty("LineSelector", "Line2")
            self.camera.setProperty("LineMode", "Output")
            self.camera.setProperty("LineSource", "ExposureActive")

        # Configure 'slave' cameras to use triggering.
        # We are following: http://www.ptgrey.com/KB/11052
        #
        # "Configuring Synchronized Capture with Multiple Cameras"
        #
        # Also, we connected the master camera to the DAQ card
        # using it's OPTO-OUT connection.
        #
        else:
            self.camera.setProperty("TriggerMode", "On")
            self.camera.setProperty("TriggerSource", "Line3")
            self.camera.setProperty("TriggerOverlap", "ReadOut")
            self.camera.setProperty("TriggerActivation", config.get("trigger_activation", "FallingEdge"))

        #
        # Dictionary of Point Grey specific camera parameters.
        #

        # All cameras can set these.
        self.pgrey_props = {"BlackLevel" : True,
                            "Gain" : True,
                            "Height" : True,
                            "OffsetX" : True,
                            "OffsetY" : True,
                            "Width" : True}

        # Only master cameras can set "AcquisitionFrameRate".
        if self.is_master:
            self.pgrey_props["AcquisitionFrameRate"] = True

            #
            # FIXME: We're using a made up max_value for this parameter because it is
            #        the default parameter. If we use the real range then any
            #        parameters that are added later could have their frame rate
            #        changed in an unexpected way. Unfortunately this also means that
            #        if the user goes above the real maximum on this parameter then
            #        the software will crash.
            #
            self.parameters.add(params.ParameterRangeFloat(description = "Acquisition frame rate (FPS)",
                                                           name = "AcquisitionFrameRate",
                                                           value = 10.0,
                                                           max_value = 5000,
                                                           min_value = self.camera.getProperty("AcquisitionFrameRate").getMinimum()))
                                                           
            
        # Slave cameras can set "ExposureTime".
        #
        # FIXME? If this is too large then the slave will be taking images
        #        at a different rate than master. Maybe this should be
        #        limited? Automatically set based on "master" frame rate?
        #
        else:
            self.pgrey_props["ExposureTime"] = True
            self.parameters.add(params.ParameterRangeFloat(description = "Exposure time (us)",
                                                           name = "ExposureTime",
                                                           value = 99800.0,
                                                           max_value = self.camera.getProperty("ExposureTime").getMaximum(),
                                                           min_value = self.camera.getProperty("ExposureTime").getMinimum()))
            
        # Load properties as required by the spinnaker Python wrapper.
        for pname in self.pgrey_props:
            self.camera.getProperty(pname)

        max_intensity = 2**12
        self.parameters.setv("max_intensity", max_intensity)

        # Set chip size and HAL parameter ranges.
        x_chip = self.camera.getProperty("WidthMax").getValue()
        self.parameters.setv("x_chip", x_chip)
        for pname in ["x_end", "x_start"]:
            self.parameters.getp(pname).setMaximum(x_chip)

        y_chip = self.camera.getProperty("HeightMax").getValue()
        self.parameters.setv("y_chip", y_chip)
        for pname in ["y_end", "y_start"]:
            self.parameters.getp(pname).setMaximum(y_chip)        

        #
        # Reset X, Y offsets. We do this here because otherwise the
        # initial ranges of these parameters will be incorrect and the
        # only way to fix them is using the parameters editor.
        #
        self.camera.setProperty("OffsetX", 0)
        self.camera.setProperty("OffsetY", 0)

        self.parameters.add(params.ParameterRangeFloat(description = "Black level",
                                                       name = "BlackLevel",
                                                       value = 1.0,
                                                       max_value = self.camera.getProperty("BlackLevel").getMaximum(),
                                                       min_value = self.camera.getProperty("BlackLevel").getMinimum()))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Gain",
                                                       name = "Gain",
                                                       value = 10.0,
                                                       max_value = self.camera.getProperty("Gain").getMaximum(),
                                                       min_value = self.camera.getProperty("Gain").getMinimum()))

        self.parameters.add(params.ParameterRangeInt(description = "AOI height",
                                                     name = "Height",
                                                     value = y_chip,
                                                     max_value = y_chip,
                                                     min_value = 4))

        self.parameters.add(params.ParameterRangeInt(description = "AOI x offset",
                                                     name = "OffsetX",
                                                     value = 0,
                                                     max_value = x_chip - 4,
                                                     min_value = 0))

        self.parameters.add(params.ParameterRangeInt(description = "AOI y offset",
                                                     name = "OffsetY",
                                                     value = 0,
                                                     max_value = y_chip - 4,
                                                     min_value = 0))

        self.parameters.add(params.ParameterRangeInt(description = "AOI width",
                                                     name = "Width",
                                                     value = x_chip,
                                                     max_value = x_chip,
                                                     min_value = 4))

        # Disable editing of the HAL versions of these parameters.
        for param in ["exposure_time", "x_bin", "x_end", "x_start", "y_end", "y_start", "y_bin"]:
            self.parameters.getp(param).setMutable(False)

        self.newParameters(self.parameters, initialization = True)
                             
    def newParameters(self, parameters, initialization = False):
        
        # Translate AOI information to parameters used by HAL.
        parameters.setv("x_end", parameters.get("OffsetX") + parameters.get("Width") - 1)
        parameters.setv("x_pixels", parameters.get("Width"))
        parameters.setv("x_start", parameters.get("OffsetX") + 1)
        
        parameters.setv("y_end", parameters.get("OffsetY") + parameters.get("Height") - 1)
        parameters.setv("y_pixels", parameters.get("Height"))
        parameters.setv("y_start", parameters.get("OffsetY") + 1)

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

                # Some fiddly handling of changing the ROI size in a way
                # that does not clash with the property ranges.
                if (pname == "Height"):
                    if (parameters.get(pname) > self.parameters.get(pname)):
                        self.camera.setProperty("OffsetY", parameters.get("OffsetY"))
                        
                elif (pname == "OffsetX"):
                    if (parameters.get(pname) > self.parameters.get(pname)):
                        self.camera.setProperty("Width", parameters.get("Width"))
                        
                elif (pname == "OffsetY"):
                    if (parameters.get(pname) > self.parameters.get(pname)):
                        self.camera.setProperty("Height", parameters.get("Height"))

                elif (pname == "Width"):
                    if (parameters.get(pname) > self.parameters.get(pname)):
                        self.camera.setProperty("OffsetX", parameters.get("OffsetX"))

                if (pname == "AcquisitionFrameRate"): #Coerce frame rate to range
                    max_value = self.camera.getProperty(pname).getMaximum()
                    min_value = self.camera.getProperty(pname).getMinimum()
                    coerced_value = min(parameters.get(pname), max_value)
                    coerced_value = max(coerced_value, min_value)
                    self.camera.setProperty(pname, coerced_value)
                else:
                    self.camera.setProperty(pname, parameters.get(pname))

            #
            # Update properties, note that the allowed ranges of many
            # of the parameters will likely change.
            #
            for pname in self.pgrey_props:

                #
                # Ugh. We don't want to change the ranges of some of the initial
                # parameters because could mess up the properties of any settings
                # files that are later loaded into HAL.
                #
                if initialization:
                    if pname in ["AcquisitionFrameRate", "ExposureTime", "Height", "OffsetX", "OffsetY", "Width"]:
                        continue

                param = self.parameters.getp(pname)
                param.setMaximum(self.camera.getProperty(pname).getMaximum())
                param.setMinimum(self.camera.getProperty(pname).getMinimum())
                param.setv(parameters.get(pname))

            # For master cameras, set the exposure time to be the maximum given the current frame rate.
            if self.is_master:
                #self.camera.setProperty("ExposureTime", self.camera.getProperty("ExposureTime").getMaximum())
                #self.parameters.setv("exposure_time", 1.0e-6 * self.camera.getProperty("ExposureTime").getValue())
                                
                                
                # Update the frame rate
                fps = self.camera.getProperty("AcquisitionFrameRate").getValue()
                self.parameters.setv("fps", fps)
                
                # Set the exposure time
                if self.exposure_control["CameraControlExposure"]: # Camera determines maximum exposure time
                    max_exposure = self.camera.getProperty("ExposureTime").getMaximum()
                else: 
                    max_exposure = 1e6/fps # Calculate theoretical max in microseconds
                self.camera.setProperty("ExposureTime", max_exposure)

                # Update the parameters to reflect the real value
                self.parameters.setv("exposure_time", 1.0e-6 * self.camera.getProperty("ExposureTime").getValue())

            # For slave cameras, just copy 'ExposureTime' to 'exposure_time' for
            # the benefit of the camera parameters viewer.
            else:
                self.parameters.setv("exposure_time", 1.0e-6 * self.camera.getProperty("ExposureTime").getValue())

            # Update camera frame size.
            self.parameters.setv("bytes_per_frame",
                                 2 * self.parameters.get("Height") * self.parameters.get("Width"))

            if running:
                self.startCamera()
                
            self.camera_functionality.parametersChanged.emit()

    def startCamera(self):
        #
        # Start the camera, then change the source for the line. There
        # can be several blank frames before the shutters start, but I
        # think this is better than having the shutters start running
        # before the master camera is ready to record. The slave cameras
        # work fine either way, and they will almost always have a
        # single empty frame before the shutters start.
        #
        super().startCamera()
        
        #
        # It appears that the camera continues to put out pulses even
        # when it is (at least in theory) not actually running. This
        # messes up the DAQ timing. To try and solve this problem we
        # re-configure the output source to one that is constant
        # when the camera stops.
        #
        if self.is_master:
            self.camera.setProperty("LineSelector", "Line1")
            self.camera.setProperty("LineSource", "ExposureActive")

    def stopCamera(self):
        super().stopCamera()
        if self.is_master:
            self.camera.setProperty("LineSelector", "Line1")
            if self.camera.hasProperty("VideoMode"):
                self.camera.setProperty("LineSource", "ExternalTriggerActive")
            else:
                self.camera.setProperty("LineSource", "ExposureActive")

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

