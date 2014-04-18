#!/usr/bin/python
#
## @file
#
# Illumination control specialized for STORM4.
#
# Hazen 02/14
#

from PyQt4 import QtCore

import coherent.cube405 as cube405
import nationalInstruments.nicontrol as nicontrol
import thorlabs.FW102C as FW102C

import illumination.channelWidgets as channelWidgets
import illumination.commandQueues as commandQueues
import illumination.illuminationControl as illuminationControl
import illumination.shutterControl as shutterControl

#
# Illumination power control specialized for STORM4.
#
class STORM4QIlluminationControlWidget(illuminationControl.QIlluminationControlWidget):
    def __init__(self, settings_file_name, parameters, parent = None):
        # setup the AOTF communication thread
        self.aotf_queue = commandQueues.QCT64BitAOTFThread()
        self.aotf_queue.start(QtCore.QThread.NormalPriority)
        self.aotf_queue.analogModulationOn()

        # setup the Cube communication thread
        self.cube_queue = commandQueues.QSerialLaserComm(cube405.Cube405("COM6"))
        self.cube_queue.start(QtCore.QThread.NormalPriority)

        # Setup the filter wheel communication thread.
        # There is only one filter wheel, which is in 750 laser path.
        self.fw_queue = commandQueues.QSerialFilterWheelComm(FW102C.FW102C("COM5"))
        self.fw_queue.start(QtCore.QThread.NormalPriority)

        # setup for NI communication with mechanical shutters (digital, unsynced)
        self.shutter_queue = commandQueues.QNiDigitalComm()

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
            elif hasattr(self.settings[i], 'use_filter_wheel'):
                channel = channelWidgets.QFilterWheelChannel(self,
                                                             self.settings[i],
                                                             parameters.default_power[n],
                                                             parameters.on_off_state[n],
                                                             parameters.power_buttons[n],
                                                             x,
                                                             dx,
                                                             height)
                channel.setCmdQueue(self.fw_queue)
                channel.setShutterQueue(self.shutter_queue)
                self.channels.append(channel)
            x += dx

        # Update the channels to reflect their current ui settings.
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
        self.fw_queue.stopThread()
        self.fw_queue.wait()

#
# Shutter control specialized for Storm4.
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
class STORM4ShutterControl(shutterControl.ShutterControl):
    def __init__(self, powerToVoltage, parent):
        shutterControl.ShutterControl.__init__(self, powerToVoltage, parent)
        self.oversampling_default = 100
        self.number_channels = 7

        self.board = "PCI-6733"
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

    def setup(self):
        #
        # the counter runs slightly faster than the camera so that it is ready
        # to catch the next camera "fire" immediately after the end of the cycle.
        #
        frequency = (1.001/self.kinetic_value) * float(self.oversampling)

        # set up the analog channels
        self.ao_task = nicontrol.WaveformOutput(self.board, 0)
        for i in range(self.number_channels - 1):
            self.ao_task.addChannel(i + 1)

        # set up the digital channels
        self.do_task = nicontrol.DigitalWaveformOutput(self.board, 0)
        for i in range(self.number_channels - 1):
            self.do_task.addChannel(self.board, i + 1)

        # set up the waveforms
        self.ao_task.setWaveform(self.waveforms, frequency)
        self.do_task.setWaveform(self.waveforms, frequency)

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

        # reset all the analog signals
        self.defaultAOTFLines()
        task = nicontrol.VoltageOutput(self.board, 6)
        task.outputVoltage(self.powerToVoltage(6, 0.0))
        task.startTask()
        task.stopTask()
        task.clearTask()


#
# Illumination power control dialog box specialized for STORM3.
#
class AIlluminationControl(illuminationControl.IlluminationControl):
    def __init__(self, hardware, parameters, parent = None):
        illuminationControl.IlluminationControl.__init__(self, parameters, parent)
        self.power_control = STORM4QIlluminationControlWidget("illumination/storm4_illumination_control_settings.xml",
                                                              parameters,
                                                              parent = self.ui.laserBox)
        self.shutter_control = STORM4ShutterControl(self.power_control.powerToVoltage,
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
