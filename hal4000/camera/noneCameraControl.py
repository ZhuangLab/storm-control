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
        self.fake_frame = 0
        self.frames_to_take = 0
        self.sleep_time = 50

    @hdebug.debug
    def getAcquisitionTimings(self):
        time = 0.001 * float(self.sleep_time)
        return [time, time, time]

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
        if (parameters.exposure_time > 0.010):
            self.sleep_time = int(1000.0 * parameters.exposure_time)
        else:
            self.sleep_time = 10
        size_x = parameters.x_pixels
        size_y = parameters.y_pixels
        self.fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                self.fake_frame[i*2*size_y + j*2] = chr(i % 128 + j % 128)
        self.newFilmSettings(parameters)

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.should_acquire and self.got_camera:
                aframe = frame.Frame(self.fake_frame, self.frame_number, self.type)
                self.newData.emit([aframe], self.key)

                if self.filming:
                    self.daxfile.saveFrame(self.fake_frame)

                if self.acq_mode == "fixed_length":
                    if (self.frame_number == (self.frames_to_take-1)):
                        self.should_acquire = 0
                        self.idleCamera.emit()

                self.frame_number += 1
            self.mutex.unlock()
            self.msleep(self.sleep_time)

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

