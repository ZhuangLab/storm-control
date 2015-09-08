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

import camera.frame as frame
import camera.cameraControl as cameraControl
import sc_hardware.andor.andorSDK3 as andor

## ACameraControl
#
# This class is used to control an Andor (sCMOS) camera.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create an Andor camera control object and initialize
    # the camera.
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        cameraControl.CameraControl.__init__(self, parameters, parent)

        self.stop_at_max = True
        
        andor.loadSDK3DLL("C:/Program Files/Andor SOLIS/")
        self.camera = andor.SDK3Camera(parameters.get("camera_id", 0))
        self.camera.setProperty("CycleMode", "enum", "Continuous")

    ## closeShutter
    #
    # Just stops the camera. The camera does not have a shutter.
    #
    @hdebug.debug
    def closeShutter(self):
        self.shutter = False
        self.stopCamera()

    ## getAcquisitionTimings
    #
    # Returns 1 over the frame rate of the camera.
    #
    # @return A python array containing the inverse of the internal frame rate.
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        exp_time = self.camera.getProperty("ExposureTime", "float")
        cycle_time = 1.0/self.camera.getProperty("FrameRate", "float")
        return [exp_time, cycle_time]

    ## getTemperature
    #
    # This camera does not have a temperature sensor so this returns
    # a meaningless value.
    #
    # @return The python array ["na", "stable"].
    #
    @hdebug.debug
    def getTemperature(self):
        temperature = self.camera.getProperty("SensorTemperature", "float")
        if (self.camera.getProperty("TemperatureStatus", "enum") == "Stabilised"):
            status = "stable"
        else:
            status = "unstable"
        return [temperature, status]

    ## haveTemperature
    #
    # Returns that this camera can measure its sensor temperature.
    #
    # @return True, this camera can measure its sensor temperature.
    #
    @hdebug.debug
    def haveTemperature(self):
        return True

    ## newFilmSettings
    #
    # Setup for new acquisition.
    #
    # @param parameters A parameters object.
    # @param film_settings A film settings object or None.
    #
    @hdebug.debug
    def newFilmSettings(self, parameters, film_settings):
        self.stopCamera()
        self.mutex.lock()
        p = parameters.get("camera1")
        self.reached_max_frames = False
        if film_settings:
            self.filming = True
            self.acq_mode = film_settings.acq_mode
            self.frames_to_take = film_settings.frames_to_take

            if (self.acq_mode == "fixed_length"):
                self.stop_at_max = True
            else:
                self.stop_at_max = False
        else:
            self.filming = False
            self.acq_mode = "run_till_abort"

        self.mutex.unlock()

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

        if not p.has("temperature"):
            p.set("temperature", self.camera.getProperty("TemperatureControl", "enum"))

        self.newFilmSettings(parameters, None)
        self.parameters = parameters


    ## openShutter
    #
    # Just stops the camera. The camera has no shutter.
    #
    @hdebug.debug
    def openShutter(self):
        self.shutter = True
        self.stopCamera()

    ## quit
    #
    # Stops the camera thread and shutsdown the camera.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        self.camera.shutdown()

    ## run
    #
    # The camera thread. This gets images from the camera, turns
    # them into frames and sends them out using the newData signal.
    # If the acquisition is being recorded it saves the frame
    # to disc. It also signals when max frames has been reached 
    # for a fixed length  acquisition.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:

                # Get data from camera and create frame objects.
                [frames, frame_size] = self.camera.getFrames()

                # Check if we got new frame data.
                if (len(frames) > 0):

                    # Create frame objects.
                    frame_data = []
                    for andor_frame in frames:
                        aframe = frame.Frame(andor_frame.getData(),
                                             self.frame_number,
                                             frame_size[0],
                                             frame_size[1],
                                             "camera1",
                                             True)
                        frame_data.append(aframe)
                        self.frame_number += 1

                        if self.filming:
                            if self.daxfile:
                                if (self.acq_mode == "fixed_length"):
                                    if (self.frame_number <= self.frames_to_take):
                                        self.daxfile.saveFrame(aframe)
                                else:
                                    self.daxfile.saveFrame(aframe)
            
                            if (self.acq_mode == "fixed_length") and (self.frame_number == self.frames_to_take):
                                self.reached_max_frames = True
                                break
                            
                    # Emit new data signal.
                    self.newData.emit(frame_data, self.key)

                    # Emit max frames signal.
                    #
                    # The signal is emitted here because if it is emitted before
                    # newData then you never see that last frame in the movie, which
                    # is particularly problematic for single frame movies.
                    #
                    if self.reached_max_frames:
                        self.max_frames_sig.emit()

            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(5)

    ## startCamera
    #
    # Start the camera. The key parameter is for synchronizing the main
    # process and the camera thread.
    #
    # @param key The ID value to use for frames from the current acquisition.
    #
    @hdebug.debug        
    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.key = key
        self.frame_number = 0
        self.max_frames_sig.reset()
        if self.got_camera:
            self.camera.startAcquisition()
        self.mutex.unlock()

    ## stopCamera
    #
    # Stops the camera
    #
    @hdebug.debug
    def stopCamera(self):
        if self.acquire.amActive():
            self.mutex.lock()
            if self.got_camera:
                self.camera.stopAcquisition()
            self.acquire.stop()
            self.mutex.unlock()
            while not self.acquire.amIdle():
                self.usleep(50)

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

