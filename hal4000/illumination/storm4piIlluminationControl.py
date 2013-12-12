#!/usr/bin/python
#
## @file
#
# Illumination control specialized for STORM4.
#
# Hazen 5/12
#

from PyQt4 import QtCore

import coherent.cube405 as cube405
import thorlabs.FW102C as FW102C

import illumination.channelWidgets as channelWidgets
import illumination.commandQueues as commandQueues
import illumination.illuminationControl as illuminationControl

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
        self.cube_queue = commandQueues.QSerialLaserComm(cube405.Cube405("COM3"))
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
# Illumination power control dialog box specialized for STORM3.
#
class AIlluminationControl(illuminationControl.IlluminationControl):
    def __init__(self, parameters, tcp_control, parent = None):
        illuminationControl.IlluminationControl.__init__(self, parameters, tcp_control, parent)
        self.power_control = STORM4QIlluminationControlWidget("illumination/storm4_illumination_control_settings.xml",
                                                              parameters,
                                                              parent = self.ui.laserBox)
        self.updateSize()


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
