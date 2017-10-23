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
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality
import storm_control.hal4000.camera.frame as frame


class NoneCameraControl(cameraControl.CameraControl):

    def __init__(self, config = None, is_master = False, **kwds):
        kwds["config"] = config
        super().__init__(**kwds)
        
        self.fake_frame = 0
        self.fake_frame_size = [0,0]
        self.sleep_time = 0

        #
        # The camera functionality. Note the connection to self.parameters
        # which should not be changed to point to some other parameters
        # object when the parameters change. This is enforced by the
        # getCameraConfiguration() method.
        #
        self.camera_functionality = cameraFunctionality.CameraFunctionality(camera_name = self.camera_name,
                                                                            have_emccd = True,
                                                                            have_preamp = True,
                                                                            have_shutter = True,
                                                                            have_temperature = True,
                                                                            is_master = is_master,
                                                                            parameters = self.parameters)
        #
        # In general these should be handled by a thread as they may be slow.
        #
        self.camera_functionality.setEMCCDGain = self.setEMCCDGain
        self.camera_functionality.toggleShutter = self.toggleShutter
        
        #
        # Override defaults with camera specific values.
        #
        self.parameters.set("exposure_time", params.ParameterRangeFloat(description = "Exposure time (seconds)", 
                                                                        name = "exposure_time", 
                                                                        value = 0.02,
                                                                        min_value = 0.01,
                                                                        max_value = 10.0))
        self.parameters.setv("max_intensity", 512)
        
        chip_size = 512
        for pname in ["x_start", "x_end", "y_start", "y_end"]:
            self.parameters.getp(pname).setMaximum(chip_size)

        self.parameters.setv("x_end", chip_size)
        self.parameters.setv("y_end", chip_size)
        self.parameters.setv("x_chip", chip_size)
        self.parameters.setv("y_chip", chip_size)
        
        #
        # Emulation camera specific parameters.
        #
        self.parameters.add(params.ParameterRangeFloat(description = "Camera rolling constant", 
                                                       name = "roll", 
                                                       value = 0.1,
                                                       min_value = 0.0,
                                                       max_value = 1.0))
        self.parameters.setv("roll", config.get("roll"))

        self.parameters.add(params.ParameterRangeInt(description = "EMCCD gain",
                                                     name = "emccd_gain",
                                                     value = 10,
                                                     min_value = 2,
                                                     max_value = 50))
        
        self.parameters.add(params.ParameterSetFloat(description = "Pre-amp gain",
                                                     name = "preampgain",
                                                     value = 1.0,
                                                     allowed = [1.0, 2.0, 5.0]))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Target temperature", 
                                                       name = "temperature", 
                                                       value = -20.0,
                                                       min_value = -50.0,
                                                       max_value = 25.0))

        self.newParameters(self.parameters, initialization = True)

    def newParameters(self, parameters, initialization = False):
        size_x = parameters.get("x_end") - parameters.get("x_start") + 1
        size_y = parameters.get("y_end") - parameters.get("y_start") + 1
        parameters.setv("x_pixels", size_x)
        parameters.setv("y_pixels", size_y)
        parameters.setv("bytes_per_frame", 2 * size_x * size_y)

        super().newParameters(parameters)

        # Figure out which parameters have changed.
        if initialization:
            changed_p_names = parameters.getAttrs()
        else:
            changed_p_names = params.difference(parameters, self.parameters)

        # Check if we actually need to do anything.
        if (len(changed_p_names) > 0):
            running = self.running
            if running:
                self.stopCamera()
        
            p = self.parameters

            # Update parameters.
            for pname in changed_p_names:
                p.set(pname, parameters.get(pname))

            # Configure camera.
            p = self.parameters
            if (p.get("exposure_time") < 0.010):
                p.set("exposure_time", 0.010)

            p.set("fps", 1.0/p.get("exposure_time"))

            self.fake_frame_size = [size_x, size_y]
            self.fake_frame = numpy.zeros(size_x * size_y, dtype = numpy.uint16)
            for i in range(size_x):
                for j in range(size_y):
                    self.fake_frame[j*size_x+i] = i % 128 + j % 128

            if running:
                self.startCamera()

            self.camera_functionality.parametersChanged.emit()
        
    def run(self):
        self.running = True
        self.thread_started = True
        while(self.running):
            aframe = frame.Frame(numpy.roll(self.fake_frame,
                                            int(self.frame_number * self.parameters.get("roll"))),
                                 self.frame_number,
                                 self.fake_frame_size[0],
                                 self.fake_frame_size[1],
                                 self.camera_name)
            self.frame_number += 1

            if self.film_length is not None:
                if (self.frame_number == self.film_length):
                    self.running = False

            # Emit new data signal.
            self.newData.emit([aframe])
            self.msleep(int(1000.0 * self.parameters.get("exposure_time")))


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

