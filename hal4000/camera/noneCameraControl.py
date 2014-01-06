#!/usr/bin/python
#
## @file
#
# This class provides software emulation of a camera for testing purposes.
#
# Hazen 09/13
#

import ctypes
import numpy
from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

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
        self.sleep_time = 50
        self.initCamera()

    ## getAcquisitionTimings
    #
    # Returns how fast the camera is running.
    #
    # @return A Python array containing the time it takes to take a frame.
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        time = 0.001 * float(self.sleep_time)
        return [time, time, time]

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

    ## havePreamp
    #
    # @return True, the emulation camera has a pre-amplifier.
    #
    @hdebug.debug
    def havePreamp(self):
        return True

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
    # Update the camera based on a new set of parameters. This creates
    # a fake image that we recycle as the picture from the camera.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        #self.initCamera()
        if (parameters.exposure_time > 0.010):
            self.sleep_time = int(1000.0 * parameters.exposure_time)
        else:
            self.sleep_time = 10
        size_x = parameters.x_pixels
        size_y = parameters.y_pixels
        self.fake_frame_size = [size_x, size_y]
        fake_frame = ctypes.create_string_buffer(2 * size_x * size_y)
        for i in range(size_x):
            for j in range(size_y):
                fake_frame[i*2*size_y + j*2] = chr(i % 128 + j % 128)
        self.fake_frame = numpy.fromstring(fake_frame, dtype = numpy.uint16)
        self.newFilmSettings(parameters, None)
        self.parameters = parameters

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
                aframe = frame.Frame(self.fake_frame, 
                                     self.frame_number,
                                     self.fake_frame_size[0],
                                     self.fake_frame_size[1],
                                     "camera1", 
                                     True)
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
                        
                # Emit new data signal.
                self.newData.emit([aframe], self.key)

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

