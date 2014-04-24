#!/usr/bin/python
#
## @file
#
# This file contains hardware classes that interface with lasers.
#
# Hazen 04/14
#

from PyQt4 import QtCore

import illumination.hardwareModule as hardwareModule


## CoherentCube
#
# Laser class the interfaces with a Coherent Cube laser.
#
class CoherentCube(hardwareModule.BufferedAmplitudeModulation):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        hardwareModule.BufferedAmplitudeModulation.__init__(self, parameters, parent)

        self.amplitude_on = False

        import coherent.cube as cube
        self.cube_laser = cube.Cube(parameters.port)
        if not (self.cube_laser.getStatus()):
            self.working = False

    ## amplitudeOff
    #
    # Called when the module should turn off a channel.
    #
    # @param channel_id The channel id.
    #
    def amplitudeOff(self, channel_id):
        self.amplitude_on = False
        self.device_mutex.lock()
        self.cube_laser.setPower(0.0)
        self.device_mutex.unlock()

    ## amplitudeOn
    #
    # Called when the module should turn on a channel.
    #
    # @param channel_id The channel id.
    # @param amplitude The channel amplitude.
    #
    def amplitudeOn(self, channel_id, amplitude):
        self.amplitude_on = True
        self.setAmplitude(channel_id, amplitude)

    ## cleanup
    #
    # Called when the program closes to clean up.
    #
    def cleanup(self):
        hardwareModule.BufferedAmplitudeModulation.cleanup(self)
        self.cube_laser.shutDown()

    ## deviceSetAmplitude
    #
    # @param channel The channel.
    # @param amplitude The channel amplitude.
    #
    def deviceSetAmplitude(self, channel, amplitude):
        if self.amplitude_on:
            self.device_mutex.lock()
            self.cube_laser.setPower(0.01 * amplitude)
            self.device_mutex.unlock()
        
    ## startFilm
    #
    # Called at the start of filming (when shutters are active).
    #
    # @param seconds_per_frame How many seconds it takes to acquire each frame.
    # @param oversampling The number of values in the shutter waveform per frame.
    #
    def startFilm(self, seconds_per_frame, oversampling):
        hardwareModule.BufferedAmplitudeModulation.startFilm(self, seconds_per_frame, oversampling)
        self.device_mutex.lock()
        self.cube_laser.setExtControl(True)
        self.device_mutex.unlock()

    ## stopFilm
    #
    # Called at the end of filming (when shutters are active).
    #
    def stopFilm(self):
        hardwareModule.BufferedAmplitudeModulation.stopFilm(self)
        self.device_mutex.lock()
        self.cube_laser.setExtControl(False)
        self.device_mutex.unlock()


## NoneLaser
#
# Laser emulator.
#
class NoneLaser(hardwareModule.AmplitudeModulation):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        hardwareModule.AmplitudeModulation.__init__(self, parameters, parent)


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
