#!/usr/bin/python
#
## @file
#
# This class provides software emulation of a camera for testing purposes.
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
# A class the emulates the behaviour of a camera in software.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create the camera control object.
    #
    # @param hardware A hardware object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parent = None):
        cameraControl.CameraControl.__init__(self, hardware, parent)
        self.fake_frame = 0
        self.fake_frame_size = [0,0]
        self.sleep_time = 100

        if hardware:
            self.roll = hardware.get("roll")
        else:
            self.roll = 0
            
        self.initCamera()

    ## getAcquisitionTimings
    #
    # Returns how fast the camera is running.
    #
    # @param which_camera The camera to get the timing information for.
    #
    # @return A Python array containing the time it takes to take a frame.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        time = 0.001 * float(self.sleep_time)
        return [time, time]

    ## getProperties
    #
    # @return The properties of the camera as a dict.
    #
    @hdebug.debug
    def getProperties(self):
        return {"camera1" : frozenset(['have_preamp'])}
    
    ## initCamera
    #
    # Initializes the camera.
    #
    @hdebug.debug
    def initCamera(self):
        if not self.camera:
            if hdebug.getDebug():
                print " Initializing None Camera Type"
            self.camera = True
        self.got_camera = True

    ## newParameters
    #
    # Update the camera based on a new set of parameters. This creates
    # a fake image that we recycle as the picture from the camera.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        p = parameters.get("camera1")
        if (p.get("exposure_time") > 0.010):
            self.sleep_time = int(1000.0 * p.get("exposure_time"))
        else:
            self.sleep_time = 10
            
        size_x = p.get("x_pixels")/p.get("x_bin")
        size_y = p.get("y_pixels")/p.get("y_bin")
        self.fake_frame_size = [size_x, size_y]
        fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                fake_frame[j*2*size_x + i*2] = chr(i % 128 + j % 128)
        self.fake_frame = numpy.fromstring(fake_frame, dtype = numpy.uint16)
        
        if not p.has("bytes_per_frame"):
            p.set("bytes_per_frame", 2 * size_x * size_y)

        self.parameters = p

    ## run
    #
    # This thread generates frame objects from the emulated image, saves
    # them if requested and broadcast them using the newData signal. It
    # also signals when the end of fixed length film has been reached.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:
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

