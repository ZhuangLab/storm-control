#!/usr/bin/python
#
# Storm2 shutter control.
#
# Hazen 05/11
#

import nationalInstruments.nicontrol as nicontrol

import illumination.shutterControl as shutterControl

class AShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage):
        self.board = "PCIe-6259"
        self.dig_wv_task = 0
        self.oversampling_default = 1
        self.number_channels = 7
        self.dig_shutter_channels = [0, 1, 2, 3, 8, 9, 10]
        shutterControl.ShutterControl.__init__(self, powerToVoltage)

    def cleanup(self):
        if self.dig_wv_task:
            self.dig_wv_task.clearTask()
            self.dig_wv_task = 0

    def setup(self, kinetic_cycle_time):
        frequency = 1.001/kinetic_cycle_time

        self.dig_wv_task = nicontrol.DigitalWaveformOutput(self.board,
                                                           self.dig_shutter_channels[0])
        for i in range(self.number_channels - 1):
            self.dig_wv_task.addChannel(self.board,
                                        self.dig_shutter_channels[i + 1])

        # set up the waveform
        self.dig_wv_task.setWaveform(self.waveforms, frequency, clock = "PFI5")

    def startFilm(self):
        if self.dig_wv_task:
            self.dig_wv_task.startTask()

    def stopFilm(self):
        if self.dig_wv_task:
            self.dig_wv_task.clearTask()
            self.dig_wv_task = 0
                    
#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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

