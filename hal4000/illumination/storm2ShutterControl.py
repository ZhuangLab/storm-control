#!/usr/bin/python
#
# Storm2 shutter control.
#
# 405 - (Mod) Analog 0
# 488 - (Mod) Analog 1 - (FSK) Digital 10
# 560 - (Mod) Analog 2 - (FSK) Digital 11
# 642 - (Mod) Analog 3 - (FSK) Digital 12
# 750 - (Shutter) Digital 4
#
# Hazen 11/12
#

import nationalInstruments.nicontrol as nicontrol

import illumination.shutterControl as shutterControl

class AShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage):
        shutterControl.ShutterControl.__init__(self, powerToVoltage)
        self.oversampling_default = 100
        self.number_channels = 5
        
        self.dig_shutter_channels = [4,10,11,12]

        self.board = "PCIe-6259"
        self.ct_task = False
        self.ao_task = False
        self.do_task = False

        self.defaultAOTFLines()

    def cleanup(self):
        if self.ct_task:
            for task in [self.ct_task, self.ao_task, self.do_task]:
                task.stopTask()
                task.clearTask()
            self.ct_task = False

    def defaultAOTFLines(self):
        # set AOTF analog lines to default (max).
        for i in range(1,4):
            nicontrol.setAnalogLine(self.board, i, self.powerToVoltage(i, 1.0))

        for i in range(10,13):
            # set AOTF digital (FSK) lines to high.
            nicontrol.setDigitalLine(self.board, i, True)

    def prepare(self):
        # This sets things so we don't get a burst of light at the
        # begining with all the lasers coming on.

        # Set all analog channels to zero.
        for i in range(4):
            nicontrol.setAnalogLine(self.board, i, 0.0)

        # Close 752 shutter & set FSK lines on the AOTF.
        for channel in self.dig_shutter_channels:
            nicontrol.setDigitalLine(self.board, channel, False)

    def setup(self, kinetic_cycle_time):
        #
        # the counter runs slightly faster than the camera so that it is ready
        # to catch the next camera "fire" immediately after the end of the cycle.
        #
        frequency = (1.001/kinetic_cycle_time) * float(self.oversampling)

        # set up the analog channels
        self.ao_task = nicontrol.WaveformOutput(self.board, 0)
        for i in range(3):
            self.ao_task.addChannel(i + 1)

        # set up the digital channels
        self.do_task = nicontrol.DigitalWaveformOutput(self.board, self.dig_shutter_channels[0])
        for i in range(len(self.dig_shutter_channels) - 1):
            self.do_task.addChannel(self.board, self.dig_shutter_channels[i + 1])

        # create analog and digital waveforms from "master" waveforms
        analog_waveforms = []
        for i in range(4):
            analog_waveforms.extend(self.waveforms[((4-i)*self.waveform_len):((5-i)*self.waveform_len)])
        digital_waveforms = []

        # add 750 first
        digital_waveforms.extend(self.waveforms[0:self.waveform_len])
        
        # then 488, 560, 642
        for i in range(3):
            digital_waveforms.extend(self.waveforms[((3-i)*self.waveform_len):((4-i)*self.waveform_len)])

        # set up the waveforms
        self.ao_task.setWaveform(analog_waveforms, frequency, clock = "PFI12")
        self.do_task.setWaveform(digital_waveforms, frequency, clock = "PFI12")

        # set up the counter
        self.ct_task = True
        self.ct_task = nicontrol.CounterOutput(self.board, 0, frequency, 0.5)
        self.ct_task.setCounter(self.waveform_len)
        self.ct_task.setTrigger(0)

    def shutDown(self):
        self.prepare()

    def startFilm(self):
        if self.ct_task:
            for task in [self.ct_task, self.ao_task, self.do_task]:
                task.startTask()

    def stopFilm(self):
        # stop the tasks
        self.cleanup()

        # reset all the AOTF signals.
        self.defaultAOTFLines()

        # set Cube analog modulation line to 0.
        nicontrol.setAnalogLine(self.board, 0, self.powerToVoltage(3, 0.0))

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

