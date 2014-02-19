#!/usr/bin/python
#
## @file
#
# This emulates two cameras at once.
#
# Hazen 01/14
#

import ctypes
import numpy
from PyQt4 import QtCore

# Debugging
import sc_library.hdebug as hdebug

import camera.cameraControl as cameraControl
import camera.frame as frame

## ACameraControl
#
# This emulates the control of two cameras at once.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create the dual camera emulation object.
    #
    # @param hardware A hardware object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parent = None):
        cameraControl.CameraControl.__init__(self, hardware, parent)
        self.camera1_fake_frame = 0
        self.camera1_frame_size = [0,0]
        self.camera2_fake_frame = 0
        self.camera2_frame_size = [0,0]
        self.frames_to_take = 0
        self.shutter1 = False
        self.shutter2 = False
        self.sleep_time = 50
        self.initCamera()

    ## getAcquisitionTimings
    #
    # Returns how long it takes to take a frame.
    #
    # @param which_camera Which camera to get the acquisition timings from.
    #
    # @return A python array containing the acquisition timings.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        time = 0.001 * float(self.sleep_time)
        return [time, time, time]
    
    ## getTemperature
    #
    # Returns a made up temperature from the indicated camera. Emulated cameras
    # run hot & are unstable..
    #
    # @param camera Which camera to get the temperature of.
    #
#    @hdebug.debug
#    def getTemperature(self, camera):
#        return [40, "unstable"]

    ## initCamera
    #
    # Initialize the camera.
    #
    def initCamera(self):
        if not self.camera:
            if hdebug.getDebug():
                print " Initializing None Camera Type"
            self.camera = 1
        self.got_camera = 1

    ## newFilmSettings
    #
    # Prepare the camera for the next acquisition.
    #
    # @param parameters A parameters object.
    # @param film_settings A film settings object or None.
    #
    @hdebug.debug
    def newFilmSettings(self, parameters, film_settings):
        self.stopCamera()
        self.mutex.lock()
        self.reached_max_frames = False
        if film_settings:
            self.filming = True
            self.acq_mode = film_settings.acq_mode
            self.frames_to_take = film_settings.frames_to_take
        else:
            self.filming = False
            self.acq_mode = "run_till_abort"
        self.mutex.unlock()

    ## newParameters
    #
    # Configure the camera based on the new parameters. This creates fake
    # data for each camera based on the parameters object. The data is
    # recycled by the control thread to make camera frames.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.initCamera()

        # Run at the speed determined by camera 1
        if (parameters.camera1.exposure_time > 0.010):
            self.sleep_time = int(1000.0 * parameters.camera1.exposure_time)
        else:
            self.sleep_time = 10

        # Set acquisition timing values for camera1 and camera2
        [parameters.camera1.exposure_value, parameters.camera1.accumulate_value, parameters.camera1.kinetic_value] = self.getAcquisitionTimings(0)
        [parameters.camera2.exposure_value, parameters.camera2.accumulate_value, parameters.camera2.kinetic_value] = self.getAcquisitionTimings(1)

        # Create fake image for camera 1
        size_x = parameters.camera1.x_pixels
        size_y = parameters.camera1.y_pixels
        self.camera1_frame_size = [size_x, size_y]
        camera1_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                camera1_fake_frame[i*2*size_y + j*2] = chr(i % 128 + j % 128)
        self.camera1_fake_frame = numpy.fromstring(camera1_fake_frame, dtype = numpy.uint16)

        # Create fake image for camera 2
        size_x = parameters.camera2.x_pixels
        size_y = parameters.camera2.y_pixels
        self.camera2_frame_size = [size_x, size_y]
        camera2_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                camera2_fake_frame[i*2*size_y + j*2] = chr(255 - (j % 128 + i % 128))
        self.camera2_fake_frame = numpy.fromstring(camera1_fake_frame, dtype = numpy.uint16)

        self.newFilmSettings(parameters, None)
        self.parameters = parameters

    ## run
    #
    # This thread generates fake data from each camera and broadcasts 
    # it using the newData signal. Saves the data if filming.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:

                # Fake data from camera1
                cam1_frame = frame.Frame(self.camera1_fake_frame, 
                                         self.frame_number,
                                         self.camera1_frame_size[0],
                                         self.camera1_frame_size[1],
                                         "camera1", 
                                         True)

                # Fake data from camera2
                cam2_frame = frame.Frame(self.camera2_fake_frame, 
                                         self.frame_number,         
                                         self.camera2_frame_size[0],
                                         self.camera2_frame_size[1],
                                         "camera2",
                                         False)

                self.frame_number += 1

                if self.filming:
                    if self.daxfile:
                        if (self.acq_mode == "fixed_length"):
                            if (self.frame_number <= self.frames_to_take):
                                self.daxfile.saveFrame(cam1_frame)
                                self.daxfile.saveFrame(cam2_frame)
                        else:
                            self.daxfile.saveFrame(cam1_frame)
                            self.daxfile.saveFrame(cam2_frame)

                    if (self.acq_mode == "fixed_length") and (self.frame_number == self.frames_to_take):
                        self.reached_max_frames = True
                        
                # Emit new data signal.
                self.newData.emit([cam1_frame, cam2_frame], self.key)

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
            self.msleep(self.sleep_time)

    ## toggleShutter
    #
    # Toggles the shutter of the indicated camera.
    #
    # @param camera Which camera to toggle the shutter of.
    #
    @hdebug.debug
    def toggleShutter(self, camera):
        if (camera == 1):
            self.shutter1 = not self.shutter1
            return self.shutter1
        else:
            self.shutter2 = not self.shutter2
            return self.shutter2

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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

