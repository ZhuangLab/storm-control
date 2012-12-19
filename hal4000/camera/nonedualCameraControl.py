#!/usr/bin/python
#
# No camera.
#
# Hazen 11/09
#

import ctypes
from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

import camera.cameraControl as cameraControl
import camera.frame as frame

class ACameraControl(cameraControl.CameraControl):
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        cameraControl.CameraControl.__init__(self, parameters, parent)
        self.camera1_fake_frame = 0
        self.camera1_frame_size = [0,0]
        self.camera2_fake_frame = 0
        self.camera2_frame_size = [0,0]
        self.frames_to_take = 0
        self.shutter1 = False
        self.shutter2 = False
        self.sleep_time = 50

    @hdebug.debug
    def getAcquisitionTimings(self):
        time = 0.001 * float(self.sleep_time)
        return [time, time, time]

    @hdebug.debug
    def getTemperature(self, camera):
        return [40, "unstable"]

    def initCamera(self):
        if not self.camera:
            if hdebug.getDebug():
                print " Initializing None Camera Type"
            self.camera = 1
        self.got_camera = 1

    @hdebug.debug
    def newFilmSettings(self, parameters, filming = 0):
        self.stopCamera()
        self.mutex.lock()
        self.parameters = parameters
        p = parameters
        if filming:
            self.acq_mode = p.acq_mode
        else:
            self.acq_mode = "run_till_abort"
        self.frames = []
        self.acquired = 0
        self.filming = filming
        self.frames_to_take = p.frames
        self.mutex.unlock()

    @hdebug.debug
    def newParameters(self, parameters):
        self.initCamera()

        # Run at the speed determined by camera 1
        if (parameters.camera1.exposure_time > 0.010):
            self.sleep_time = int(1000.0 * parameters.camera1.exposure_time)
        else:
            self.sleep_time = 10

        # Set acquisition timing values for camera1 and camera2
        [parameters.camera1.exposure_value, parameters.camera1.accumulate_value, parameters.camera1.kinetic_value] = self.getAcquisitionTimings()
        [parameters.camera2.exposure_value, parameters.camera2.accumulate_value, parameters.camera2.kinetic_value] = self.getAcquisitionTimings()

        # Create fake image for camera 1
        size_x = parameters.camera1.x_pixels
        size_y = parameters.camera1.y_pixels
        self.camera1_frame_size = [size_x, size_y]
        self.camera1_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                self.camera1_fake_frame[i*2*size_y + j*2] = chr(i % 128 + j % 128)

        # Create fake image for camera 2
        size_x = parameters.camera2.x_pixels
        size_y = parameters.camera2.y_pixels
        self.camera2_frame_size = [size_x, size_y]
        self.camera2_fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                self.camera2_fake_frame[i*2*size_y + j*2] = chr(255 - (j % 128 + i % 128))

        self.newFilmSettings(parameters)

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.should_acquire and self.got_camera:

                # Fake data from camera1
                aframe = frame.Frame(self.camera1_fake_frame, 
                                     self.frame_number,
                                     self.camera1_frame_size[0],
                                     self.camera1_frame_size[1],
                                     "camera1", 
                                     True)
                self.newData.emit([aframe], self.key)

                if self.filming:
                    self.daxfile.saveFrame(aframe)

                # Fake data from camera2
                aframe = frame.Frame(self.camera2_fake_frame, 
                                     self.frame_number,         
                                     self.camera2_frame_size[0],
                                     self.camera2_frame_size[1],
                                     "camera2",
                                     False)
                self.newData.emit([aframe], self.key)

                if self.filming:
                    self.daxfile.saveFrame(aframe)


                if self.acq_mode == "fixed_length":
                    if (self.frame_number == (self.frames_to_take-1)):
                        self.should_acquire = 0
                        self.idleCamera.emit()

                self.frame_number += 1
            self.mutex.unlock()
            self.msleep(self.sleep_time)

    @hdebug.debug
    def setEMCCDGain(self, camera, gain):
        pass

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
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

