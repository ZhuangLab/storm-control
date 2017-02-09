#!/usr/bin/env python
"""
This class provides software emulation of a camera for testing purposes.

Hazen 02/17
"""

import ctypes
import numpy
from PyQt5 import QtCore

import storm_control.sc_library.parameters as params
import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.camera.frame as frame

class NoneCameraControl(cameraControl.CameraControl):

    def __init__(self, config = None, **kwds):
        super().__init__(**kwds)

        self.camera = True
        self.camera_working = True
        
        self.fake_frame = 0
        self.fake_frame_size = [0,0]
        self.roll = config.get("roll")
        self.sleep_time = 100

    def getAcquisitionTimings(self, which_camera):
        return 0.001 * float(self.sleep_time)

    def newParameters(self, parameters):
        p = parameters.get("camera1")
        if (p.get("exposure_time") > 0.010):
            self.sleep_time = int(1000.0 * p.get("exposure_time"))
        else:
            self.sleep_time = 10
            
        size_x = int((p.get("x_end") - p.get("x_start") + 1)/p.get("x_bin"))
        size_y = int((p.get("y_end") - p.get("y_start") + 1)/p.get("y_bin"))
        p.set("x_pixels", size_x)
        p.set("y_pixels", size_y)
        self.fake_frame_size = [size_x, size_y]
        self.fake_frame = numpy.zeros(size_x * size_y, dtype = numpy.uint16)
        for i in range(size_x):
            for j in range(size_y):
                self.fake_frame[j*size_x+i] = i % 128 + j % 128
        
        if not p.has("bytes_per_frame"):
            p.set("bytes_per_frame", 2 * size_x * size_y)

        self.parameters = p

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.camera_working:
                aframe = frame.Frame(numpy.roll(self.fake_frame, int(self.frame_number * self.roll)),
                                     self.frame_number,
                                     self.fake_frame_size[0],
                                     self.fake_frame_size[1],
                                     "camera1", 
                                     True)
                self.frame_number += 1

                # Emit new data signal.
                self.newData.emit([aframe], self.key)
            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(self.sleep_time)

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

