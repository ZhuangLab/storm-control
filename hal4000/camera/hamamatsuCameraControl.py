#!/usr/bin/python
#
## @file
#
# Camera control specialized for a Hamamatsu camera.
#
# Hazen 10/13
#

from PyQt4 import QtCore
import os
import platform
import traceback

# Debugging
import sc_library.hdebug as hdebug

import camera.frame as frame
import camera.cameraControl as cameraControl
import sc_hardware.hamamatsu.hamamatsu_camera as hcam

## ACameraControl
#
# This class is used to control a Hamamatsu (sCMOS) camera.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create a Hamamatsu camera control object and initialize
    # the camera.
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        cameraControl.CameraControl.__init__(self, parameters, parent)

        self.stop_at_max = True

        self.camera = hcam.HamamatsuCameraMR(parameters.get("camera_id", 0))

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
    # Returns the internal frame rate of the camera.
    #
    # @return A python array containing the inverse of the internal frame rate.
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        #frame_rate = self.camera.getPropertyValue("internal_frame_rate")[0]

        # The camera frame rate seems to be max(exposure time, readout time).
        # This number may not be good accurate enough for shutter synchronization?
        exposure_time = self.camera.getPropertyValue("exposure_time")[0]
        readout_time = self.camera.getPropertyValue("timing_readout_time")[0]
        if (exposure_time < readout_time):
            frame_rate = 1.0/readout_time

            # Print a warning since the user probably does not want this to be true.
            hdebug.logText("Camera exposure time (" + str(exposure_time) + ") is less than the readout time (" + str(readout_time), True)

        else:
            frame_rate = 1.0/exposure_time

        temp = 1.0/frame_rate
        return [temp, temp, temp]

    ## getTemperature
    #
    # This camera does not have a temperature sensor so this returns
    # a meaningless value.
    #
    # @return The python array ["na", "stable"].
    #
    @hdebug.debug
    def getTemperature(self):
        return ["na", "stable"]

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
        p = parameters
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
        p = parameters

        try:
            # Set ROI location and size.
            self.camera.setPropertyValue("subarray_hpos", p.get("x_start"))
            self.camera.setPropertyValue("subarray_hsize", p.get("x_pixels"))
            self.camera.setPropertyValue("subarray_vpos", p.get("y_start"))
            self.camera.setPropertyValue("subarray_vsize", p.get("y_pixels"))

            # Set binning.
            if (p.get("x_bin") != p.get("y_bin")):
                raise AssertionError("unequal binning is not supported.")
            if (p.get("x_bin") == 1):
                self.camera.setPropertyValue("binning", "1x1")
            elif (p.get("x_bin") == 2):
                self.camera.setPropertyValue("binning", "2x2")
            elif (p.get("x_bin") == 4):
                self.camera.setPropertyValue("binning", "4x4")
            else:
                raise AssertionError("unsupported bin size", p.get("x_bin"))

            # Set the rest of the hamamatsu properties.
            #
            # Note: These could overwrite the above. For example, if you
            #   have both "x_start" and "subarray_hpos" in the parameters
            #   file then "subarray_hpos" will overwrite "x_start". Trouble
            #   may follow if they are not set to the same value.
            #
            for key, value in p.__dict__.iteritems():
                if (key == "binning"): # sigh..
                    continue
                if self.camera.isCameraProperty(key):
                    self.camera.setPropertyValue(key, value)


            # Set camera sub-array mode so that it will return the correct frame rate.
            self.camera.setSubArrayMode()

            self.got_camera = True

        except hcam.DCAMException:
            hdebug.logText("QCameraThread: Bad camera settings")
            print traceback.format_exc()
            self.got_camera = False

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
                    for hc_data in frames:
                        aframe = frame.Frame(hc_data.getData(),
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
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

