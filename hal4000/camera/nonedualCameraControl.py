#!/usr/bin/python
#
## @file
#
# This emulates two cameras at once.
#
# Hazen 09/15
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
        self.sleep_time = 50
        self.shutter1 = False
        
        if hardware:
            self.roll = hardware.get("roll")
        else:
            self.roll = 0

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
        return [time, time]

    ## getNumberOfCameras
    #
    # @return The number of cameras that this module controls.
    #
    @hdebug.debug
    def getNumberOfCameras(self):
        return 2
    
    ## getProperties
    #
    # @return The properties of the cameras as a dict.
    #
    @hdebug.debug
    def getProperties(self):
        return {"camera1" : frozenset(['have_emccd', 'have_shutter', 'have_preamp']),
                "camera2" : frozenset(['have_temperature'])}
    
    ## getTemperature
    #
    # Returns a made up temperature from the indicated camera. Emulated cameras
    # run hot & are unstable..
    #
    # @param which_camera Which camera to get the temperature of.
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def getTemperature(self, which_camera, parameters):
        if (which_camera == "camera2"):
            temp = [-50, "unstable"]
            parameters.set(which_camera + ".actual_temperature", temp[0])
            parameters.set(which_camera + ".temperature_control", temp[1])
        
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
        if (parameters.get("camera1").get("exposure_time") > 0.010):
            self.sleep_time = int(1000.0 * parameters.get("camera1").get("exposure_time"))
        else:
            self.sleep_time = 10

        # Create fake image for camera 1
        size_x = parameters.get("camera1").get("x_pixels") / parameters.get("camera1").get("x_bin")
        size_y = parameters.get("camera1").get("y_pixels") / parameters.get("camera1").get("y_bin")
        self.camera1_frame_size = [size_x, size_y]
        camera1_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                camera1_fake_frame[i*2*size_y + j*2] = chr(i % 128 + j % 128)
        self.camera1_fake_frame = numpy.fromstring(camera1_fake_frame, dtype = numpy.uint16)

        if not parameters.has("camera1.bytes_per_frame"):
            parameters.set("camera1.bytes_per_frame", 2 * size_x * size_y
        
        # Create fake image for camera 2
        size_x = parameters.get("camera2").get("x_pixels") / parameters.get("camera2").get("x_bin")
        size_y = parameters.get("camera2").get("y_pixels") / parameters.get("camera2").get("y_bin")
        self.camera2_frame_size = [size_x, size_y]
        camera2_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                camera2_fake_frame[i*2*size_y + j*2] = chr(255 - (j % 128 + i % 128))
        self.camera2_fake_frame = numpy.fromstring(camera1_fake_frame, dtype = numpy.uint16)

        if not parameters.has("camera2.bytes_per_frame"):
            parameters.set("camera2.bytes_per_frame", 2 * size_x * size_y)
            
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
                cam1_frame = frame.Frame(numpy.roll(self.camera1_fake_frame, int(self.frame_number * self.roll)),
                                         self.frame_number,
                                         self.camera1_frame_size[0],
                                         self.camera1_frame_size[1],
                                         "camera1", 
                                         True)

                # Fake data from camera2
                cam2_frame = frame.Frame(numpy.roll(self.camera2_fake_frame, int(-self.frame_number * self.roll)),
                                         self.frame_number,
                                         self.camera2_frame_size[0],
                                         self.camera2_frame_size[1],
                                         "camera2",
                                         False)

                self.frame_number += 1

                # Emit new data signal.
                self.newData.emit([cam1_frame, cam2_frame], self.key)
            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(self.sleep_time)

    ## toggleShutter
    #
    # Toggles the shutter of the indicated camera.
    #
    # @param which_camera Which camera to toggle the shutter of.
    #
    @hdebug.debug
    def toggleShutter(self, which_camera):
        if (which_camera == "camera1"):
            self.shutter1 = not self.shutter1
            return self.shutter1

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

