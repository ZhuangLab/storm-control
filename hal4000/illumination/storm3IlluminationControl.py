#!/usr/bin/python
#
## @file
#
# Illumination control specialized for STORM3.
#
# Hazen 02/14
#

from PyQt4 import QtCore

import nationalInstruments.nicontrol as nicontrol

import illumination.channelWidgets as channelWidgets
import illumination.commandQueues as commandQueues
import illumination.illuminationControl as illuminationControl
import illumination.shutterControl as shutterControl

import coherent.cube405 as cube405

#
# Illumination power control specialized for STORM3.
#
class STORM3QIlluminationControlWidget(illuminationControl.QIlluminationControlWidget):
    def __init__(self, settings_file_name, parameters, parent = None):
        # setup the AOTF communication thread
        self.aotf_queue = commandQueues.QCTAOTFThread()
        self.aotf_queue.start(QtCore.QThread.NormalPriority)
        self.aotf_queue.analogModulationOn()

        # setup the Cube communication thread
        self.cube_queue = commandQueues.QSerialLaserComm(cube405.Cube405(port = "COM13"))
        self.cube_queue.start(QtCore.QThread.NormalPriority)

        illuminationControl.QIlluminationControlWidget.__init__(self, settings_file_name, parameters, parent)

    def autoControl(self, channels):
        self.cube_queue.analogModulationOn()
        for channel in self.channels:
            channel.setFilmMode(1)

    def manualControl(self):
        self.cube_queue.analogModulationOff()
        for channel in self.channels:
            channel.setFilmMode(0)

    def newParameters(self, parameters):
        illuminationControl.QIlluminationControlWidget.newParameters(self, parameters)

        # Layout the widget
        dx = 50
        width = self.number_channels * dx

        # The height is based on how many buttons there are per channel,
        # so first we figure out the number of buttons per channel.
        max_buttons = 0
        for i in range(self.number_channels):
            n_buttons = len(parameters.power_buttons[i])
            if n_buttons > max_buttons:
                max_buttons = n_buttons
        height = 204 + max_buttons * 22

        # Set the size based on the number of channels and buttons
        self.resize(width, height)
        self.setMinimumSize(QtCore.QSize(width, height))
        self.setMaximumSize(QtCore.QSize(width, height))

        # Create the individual channels
        x = 0
        for i in range(self.number_channels):
            n = self.settings[i].channel
            if hasattr(self.settings[i], 'use_aotf'):
                channel = channelWidgets.QAOTFChannel(self,
                                                      self.settings[i],
                                                      parameters.default_power[n],
                                                      parameters.on_off_state[n],
                                                      parameters.power_buttons[n],
                                                      x,
                                                      dx,
                                                      height)
                channel.setCmdQueue(self.aotf_queue)
                channel.fskOnOff(1)
                self.channels.append(channel)
            elif hasattr(self.settings[i], 'use_cube405'):
                channel = channelWidgets.QCubeChannel(self,
                                                      self.settings[i],
                                                      parameters.default_power[n],
                                                      parameters.on_off_state[n],
                                                      parameters.power_buttons[n],
                                                      x,
                                                      dx,
                                                      height)
                channel.setCmdQueue(self.cube_queue)
                self.channels.append(channel)
            x += dx

        # Update the channels to reflect there current ui settings.
        for channel in self.channels:
            channel.uiUpdate()
                            
        # Save access to the previous parameters file so that
        # we can save the settings when the parameters are changed.
        self.last_parameters = parameters

    def shutDown(self):
        illuminationControl.QIlluminationControlWidget.shutDown(self)
        self.aotf_queue.stopThread()
        self.aotf_queue.wait()
        self.cube_queue.stopThread()
        self.cube_queue.wait()


#
# Storm3 shutter control.
#
# Channels 0-5 are controlled by the AOTF.
# Channel 6 is a Coherent 405 diode laser.
#
# These are driven by the analog out lines of a
# National Instruments PCI-6722 card.
#
class STORM3ShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage, parent):
        shutterControl.ShutterControl.__init__(self, powerToVoltage, parent)
        self.oversampling_default = 100
        self.number_channels = 7

        self.board = "PCI-6722"
        self.ct_task = False
        self.wv_task = False

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

    def setup(self):
        assert self.ct_task == 0, "Attempt to call setup without first calling cleanup."
        #
        # the counter runs slightly faster than the camera so that it is ready
        # to catch the next camera "fire" immediately after the end of the cycle.
        #
        frequency = (1.001/self.kinetic_value) * float(self.oversampling)

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


#
# Illumination power control dialog box specialized for STORM3.
#
class AIlluminationControl(illuminationControl.IlluminationControl):
    def __init__(self, hardware, parameters, parent = None):
        illuminationControl.IlluminationControl.__init__(self, parameters, parent)
        self.power_control = STORM3QIlluminationControlWidget("illumination/" + hardware.settings_xml,
                                                              parameters,
                                                              parent = self.ui.laserBox)
        self.shutter_control = STORM3ShutterControl(self.power_control.powerToVoltage,
                                                    self.ui.laserBox)
        self.updateSize()

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
