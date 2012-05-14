#!/usr/bin/python
#
# Storm4 shutter control.
#
# Channel 0 : 750 laser, shutter only
# Channel 1-5 : AOTF control
# Channel 6: 405 laser, direct modulation.
#
# AO 0-6 and DI 0-6 are all used, but AO0 is not connected 
# (as we don't have analog modulation for the 750 laser) and 
# DI6 is not connected as it is not necessary for the Cube 405 
# laser.
#
# Hazen 3/12
#

import nationalInstruments.nicontrol as nicontrol

import illumination.shutterControl as shutterControl

class AShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage):
        shutterControl.ShutterControl.__init__(self, powerToVoltage)
        self.oversampling_default = 1
        self.number_channels = 7

        self.board = "PCI-6733"
        self.ct_task = False
        self.ao_task = False
        self.do_task = False

        self.defaultAOTFLines()

    def cleanup(self):
        if self.ct_task:
            #for task in [self.ct_task, self.ao_task, self.do_task]:
            for task in [self.ao_task, self.do_task]:
                task.stopTask()
                task.clearTask()
            self.ct_task = False

    def defaultAOTFLines(self):
        for i in range(1,6):
            # set analog lines to default (max).
            nicontrol.setAnalogLine(self.board, i, self.powerToVoltage(i, 1.0))

            # set digital lines to high.
            nicontrol.setDigitalLine(self.board, i, True)

    def prepare(self):
        # This sets things so we don't get a burst of light at the
        # begining with all the lasers coming on.
        for i in range(self.number_channels):
            nicontrol.setAnalogLine(self.board, i, 0.0)
            nicontrol.setDigitalLine(self.board, i, False)

    def setup(self, kinetic_cycle_time):
        #
        # the counter runs slightly faster than the camera so that it is ready
        # to catch the next camera "fire" immediately after the end of the cycle.
        #
        frequency = (1.001/kinetic_cycle_time) * float(self.oversampling)

        # set up the analog channels
        self.ao_task = nicontrol.WaveformOutput(self.board, 0)
        for i in range(self.number_channels - 1):
            self.ao_task.addChannel(i + 1)

        # set up the digital channels
        self.do_task = nicontrol.DigitalWaveformOutput(self.board, 0)
        for i in range(self.number_channels - 1):
            self.do_task.addChannel(self.board, i + 1)

        # set up the waveforms
        #self.ao_task.setWaveform(self.waveforms, frequency)
        #self.do_task.setWaveform(self.waveforms, frequency)
        self.ao_task.setWaveform(self.waveforms, frequency, clock = "pfi0")
        self.do_task.setWaveform(self.waveforms, frequency, clock = "pfi0")

        # set up the counter
        self.ct_task = True
        #self.ct_task = nicontrol.CounterOutput(self.board, 0, frequency, 0.5)
        #self.ct_task.setCounter(self.waveform_len)
        #self.ct_task.setTrigger(0)

    def shutDown(self):
        self.prepare()

    def startFilm(self):
        if self.ct_task:
            #for task in [self.ct_task, self.ao_task, self.do_task]:
            for task in [self.ao_task, self.do_task]:
                task.startTask()

    def stopFilm(self):
        # stop the tasks
        self.cleanup()

        # reset all the analog signals
        self.defaultAOTFLines()
        task = nicontrol.VoltageOutput(self.board, 6)
        task.outputVoltage(self.powerToVoltage(6, 0.0))
        task.startTask()
        task.stopTask()
        task.clearTask()

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

