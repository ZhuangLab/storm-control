#!/usr/bin/python
#
# Prism2 shutter control.
#
# Channels 0-3 are controlled by the AOTF.
# Channel 4 is a Coherent 405 diode laser which is
# modulated directly.
# Channel 5 is the white light shutter.
#
# These are driven by the analog out lines of a
# National Instruments PCI-6722 card.
#
# Hazen 04/12
#

import nationalInstruments.nicontrol as nicontrol

import illumination.shutterControl as shutterControl

class AShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage):
        shutterControl.ShutterControl.__init__(self, powerToVoltage)
        self.oversampling_default = 100
        self.number_channels = 8

        self.ct_task = 0
        self.wv_task = 0
        self.board = "PCI-6722"

        self.defaultAOTFLines()

    def cleanup(self):
        if self.ct_task:
            self.ct_task.clearTask()
            self.wv_task.clearTask()
            self.ct_task = 0
            self.wv_task = 0

    def defaultAOTFLines(self):
        for i in range(self.number_channels):
            # set analog lines to default (max).
            nicontrol.setAnalogLine(self.board, i, self.powerToVoltage(i, 1.0))

    def prepare(self):
        # This sets things so we don't get a burst of light at the
        # begining with all the lasers coming on.
        for i in range(self.number_channels):
            nicontrol.setAnalogLine(self.board, i, 0.0)

    def setup(self, kinetic_cycle_time):
        assert self.ct_task == 0, "Attempt to call setup without first calling cleanup."
        #
        # the counter runs slightly faster than the camera so that it is ready
        # to catch the next camera "fire" immediately after the end of the cycle.
        #
        frequency = (1.001/kinetic_cycle_time) * float(self.oversampling)

        # set up the analog channels
        self.wv_task = nicontrol.WaveformOutput(self.board, 0)
        for i in range(self.number_channels - 1):
            self.wv_task.addChannel(i + 1)

        # set up the waveform
        self.wv_task.setWaveform(self.waveforms, frequency)

        # set up the counter
        self.ct_task = nicontrol.CounterOutput(self.board, 0, frequency, 0.5)
        self.ct_task.setCounter(self.waveform_len)
        self.ct_task.setTrigger(0)

    def startFilm(self):
        self.wv_task.startTask()
        self.ct_task.startTask()

    def stopFilm(self):
        # stop the tasks
        if self.ct_task:
            self.ct_task.stopTask()
            self.wv_task.stopTask()
            self.ct_task.clearTask()
            self.wv_task.clearTask()
            self.ct_task = 0
            self.wv_task = 0

        # reset all the analog signals.
        self.defaultAOTFLines()
#        for i in range(self.number_channels):
#            ao_task = nicontrol.VoltageOutput(self.board, i)
#            ao_task.outputVoltage(self.powerToVoltage(i, 0.0))
#            ao_task.startTask()
#            ao_task.stopTask()
#            ao_task.clearTask()
            
        
#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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

