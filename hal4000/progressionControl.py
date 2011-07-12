#!/usr/bin/python
#
# Progression control dialog box.
#
# Hazen 11/09
#

import os
import sys
from PyQt4 import QtCore, QtGui

import halLib.parameters as params

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.progressionui_v1 as progressionUi

#
# Progression control.
#
# This dialog allows the user to configure an automatic
# starting power and power increment to use while taking
# STORM movies. This increases productivity & overall
# quality of life as the user can focus on surfing
# the internet while acquiring STORM movies without 
# getting distracted by constantly having to adjust 
# the laser powers.
#

#
# Channels class which is specialized for various
# types of channel power progressions.
#
class Channels():
    def __init__(self, parent):
        self.height = 40
        self.powers = []

    def newFrame(self, frame_number):
        pass

    def startFilm(self):
        pass

    def stopFilm(self):
        pass

#
# Channels class for mathematical progressions (linear, exponential).
#
class MathChannels(Channels):
    def __init__(self, number_channels, x_positions, parameters, parent):
        Channels.__init__(self, parent)
        y = 40
        dy = 26
        self.channels = []
        self.which_checked = []
        for i in range(number_channels):
            self.powers.append(0.0)
            self.which_checked.append(False)
            channel_frame = QtGui.QFrame(parent)
            channel_frame.setGeometry(0, y, 340, 24)

            # channel number
            channel_text = QtGui.QLabel(channel_frame)
            channel_text.setGeometry(x_positions[0], 2, 20, 18)
            channel_text.setText(str(i))

            # check box
            channel_active_check_box = QtGui.QCheckBox(channel_frame)
            channel_active_check_box.setGeometry(x_positions[1], 2, 18, 18)

            # initial value
            channel_initial_spin_box = QtGui.QDoubleSpinBox(channel_frame)
            channel_initial_spin_box.setGeometry(x_positions[2], 2, 68, 18)
            channel_initial_spin_box.setDecimals(4)
            channel_initial_spin_box.setMaximum(1.0)
            channel_initial_spin_box.setValue(parameters.pstart_value)
            channel_initial_spin_box.setSingleStep(0.0001)

            # increment
            channel_inc_spin_box = QtGui.QDoubleSpinBox(channel_frame)
            channel_inc_spin_box.setGeometry(x_positions[3], 2, 68, 18)
            channel_inc_spin_box.setDecimals(4)
            channel_inc_spin_box.setValue(parameters.pinc_value)
            channel_inc_spin_box.setSingleStep(0.0001)

            # time to increment
            channel_time_spin_box = QtGui.QSpinBox(channel_frame)
            channel_time_spin_box.setGeometry(x_positions[4], 2, 68, 18)
            channel_time_spin_box.setMinimum(100)
            channel_time_spin_box.setMaximum(100000)
            channel_time_spin_box.setValue(parameters.pframe_value)
            channel_time_spin_box.setSingleStep(100)
            
            self.channels.append([channel_active_check_box,
                                  channel_initial_spin_box,
                                  channel_inc_spin_box,
                                  channel_time_spin_box])

            y += dy

        self.height = y

    def remoteSetChannel(self, which_channel, initial, inc, time):
        channel = self.channels[which_channel]
        channel[0].setChecked(True)
        channel[1].setValue(initial)
        channel[2].setValue(inc)
        channel[3].setValue(time)

    def startFilm(self):
        for i, channel in enumerate(self.channels):
            self.which_checked[i] = False
            self.powers[i] = (float(channel[1].value()))
            if channel[0].isChecked():
                self.which_checked[i] = True
        return [self.which_checked, self.powers]

    def stopFilm(self):
        for i, channel in enumerate(self.channels):
            self.powers[i] = (float(channel[1].value()))
        return [self.which_checked, self.powers]

#
# Channels class for linear progression.
#
class LinearChannels(MathChannels):
    def __init__(self, channels, x_positions, parameters, parent):
        MathChannels.__init__(self, channels, x_positions, parameters, parent)
        for channel in self.channels:
            channel[2].setMaximum(1.0)

    def newFrame(self, frame_number):
        active = []
        increment = []
        for i, channel in enumerate(self.channels):
            if self.which_checked[i] and ((frame_number % channel[3].value()) == 0):
                active.append(True)
                increment.append(float(channel[2].value()))
            else:
                active.append(False)
                increment.append(float(channel[2].value()))
        return [active, increment]

#
# Channels class for exponential progression.
#
class ExponentialChannels(MathChannels):
    def __init__(self, channels, x_positions, parameters, parent):
        MathChannels.__init__(self, channels, x_positions, parameters, parent)
        for channel in self.channels:
            channel[2].setValue(1.05)
            channel[2].setMaximum(9.9)

    def newFrame(self, frame_number):
        active = []
        increment = []
        for i, channel in enumerate(self.channels):
            if self.which_checked[i] and ((frame_number % channel[3].value()) == 0):
                active.append(True)
                new_power = float(channel[2].value()) * self.powers[i]
                inc = new_power - self.powers[i]
                increment.append(inc)
                self.powers[i] = new_power
            else:
                active.append(False)
                increment.append(float(channel[2].value()))
        return [active, increment]

#
# Channels class for power file bases progression
#
class FileChannels(Channels):
    def __init__(self, parent):
        Channels.__init__(self, parent)
        self.active = []
        self.start_powers = []
        self.file_ptr = False

    def getNextPowers(self):
        line = self.file_ptr.readline()
        powers = False
        if line:
            powers = []
            powers_text = line.split(" ")[1:]
            for i in range(len(powers_text)):
                powers.append(float(powers_text[i]))
        return powers

    def newFile(self, filename):
        if os.path.exists(filename):
            self.file_ptr = open(filename, "r")
            self.file_ptr.readline()
            self.active = []
            self.start_powers = []
            powers = self.getNextPowers()
            if powers:
                for power in powers:
                    self.active.append(True)
                    self.powers.append(power)
                    self.start_powers.append(power)
        else:
            self.file_ptr = False

    def newFrame(self, frame_number):
        if self.file_ptr:
            powers = self.getNextPowers()
            active = []
            increment = []
            if powers:
                for i in range(len(powers)):
                    if powers[i] != self.powers[i]:
                        active.append(True)
                        increment.append(powers[i] - self.powers[i])
                        self.powers[i] = powers[i]
                    else:
                        active.append(False)
                        increment.append(False)
#            print "newFrame:"
#            print active
#            print increment
#            print ""
            return [active, increment]
        else:
            return [[], []]

    def startFilm(self):
        if self.file_ptr:
            # reset file ptr
            self.file_ptr.seek(0)
            self.file_ptr.readline()
            # reset internal power record
            for i in range(len(self.start_powers)):
                self.powers[i] = self.start_powers[i]

#            print "startFilm:", self.start_powers
            return [self.active, self.start_powers]
        else:
            return [[], []]

    def stopFilm(self):
        if self.file_ptr:
#            print "stopFilm:", self.start_powers
            return [self.active, self.start_powers]
        else:
            return [[], []]


#
# Progression control dialog box
#
class ProgressionControl(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, channels = 3, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.channels = False
        self.parameters = parameters
        self.debug = parameters.debug
        self.tcp_control = tcp_control
        self.use_was_checked = False
        self.which_checked = []

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        for i in range(channels):
            self.which_checked.append(False)

        # UI setup
        self.ui = progressionUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Progression Control")

        # linear increasing power tab setup
        self.linear_channels = LinearChannels(channels,
                                              [self.ui.channelLabel.pos().x(),
                                               self.ui.activeLabel.pos().x(),
                                               self.ui.startLabel.pos().x(),
                                               self.ui.incrementLabel.pos().x(),
                                               self.ui.framesLabel.pos().x()],
                                              self.parameters,
                                              self.ui.linearTab)

        # exponential increasing power tab setup
        self.exp_channels = ExponentialChannels(channels,
                                                [self.ui.channelLabel_2.pos().x(),
                                                 self.ui.activeLabel_2.pos().x(),
                                                 self.ui.startLabel_2.pos().x(),
                                                 self.ui.incrementLabel_2.pos().x(),
                                                 self.ui.framesLabel_2.pos().x()],
                                                self.parameters,
                                                self.ui.expTab)

        # increment power as specified in a file
        self.file_channels = FileChannels(self.ui.fileTab)

        # adjust overall size to match number of channels
        y = self.linear_channels.height + 65
        old_width = self.ui.progressionsBox.width()
        self.ui.progressionsBox.setGeometry(10, 0, old_width, y + 2)

        self.ui.okButton.setGeometry(old_width - 65, y + 5, 75, 24)
        self.ui.progressionsCheckBox.setGeometry(2, y + 7, 151, 18)

        self.setFixedSize(self.width(), y + 36)

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleQuit)
        self.connect(self.ui.progressionsCheckBox, QtCore.SIGNAL("stateChanged(int)"), self.handleProgCheck)
        self.connect(self.ui.loadFileButton, QtCore.SIGNAL("clicked()"), self.newPowerFile)

        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("progressionLockout()"), self.tcpHandleProgressionLockout)
            self.connect(self.tcp_control, QtCore.SIGNAL("progressionFile(PyQt_PyObject)"), self.tcpHandleProgressionFile)
            self.connect(self.tcp_control, QtCore.SIGNAL("progressionSet(int, float, int, float)"), self.tcpHandleProgressionSet)
            self.connect(self.tcp_control, QtCore.SIGNAL("progressionType(PyQt_PyObject)"), self.tcpHandleProgressionType)

        # set modeless
        self.setModal(False)

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleProgCheck(self, state):
        if state:
            self.parameters.use_progressions = 1
        else:
            self.parameters.use_progressions = 0

    @hdebug.debug
    def handleQuit(self):
        self.close()

    def newFrame(self, frame_number):
        if self.channels:
            [active, increment] = self.channels.newFrame(frame_number)
            for i in range(len(active)):
                if active[i]:
                    self.emit(QtCore.SIGNAL("progIncPower(int, float)"), 
                              int(i),
                              increment[i])

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        if parameters.use_progressions:
            self.ui.progressionsCheckBox.setChecked(True)
        else:
            self.ui.progressionsCheckBox.setChecked(False)

    def newPowerFile(self):
        power_filename = QtGui.QFileDialog.getOpenFileName(self,
                                                           "New Power File",
                                                           str(self.parameters.directory),
                                                           "*.power")
        if power_filename:
            self.ui.filenameLabel.setText(power_filename[-40:])
            self.file_channels.newFile(power_filename)

    def setPower(self, active, power):
        for i in range(len(active)):
            if active[i]:
                self.emit(QtCore.SIGNAL("progSetPower(int, float)"), 
                          int(i),
                          power[i])

    def startFilm(self):
        self.channels = False
        if (self.isVisible() and self.parameters.use_progressions):
            # determine which tab is active.
            if self.ui.linearTab.isVisible():
                self.channels = self.linear_channels
            elif self.ui.expTab.isVisible():
                self.channels = self.exp_channels
            elif self.ui.fileTab.isVisible():
                self.channels = self.file_channels
            [active, power] = self.channels.startFilm()
            self.setPower(active, power)

    def stopFilm(self):
        if self.channels:
            [active, power] = self.channels.stopFilm()
            self.setPower(active, power)
        if self.use_was_checked:
            self.use_was_checked = False
            self.ui.progressionsCheckBox.setChecked(True)

    @hdebug.debug
    def tcpHandleProgressionFile(self, filename):
        if os.path.exists(filename):
            self.ui.filenameLabel.setText(filename[-40:])
            self.file_channels.newFile(filename)

    @hdebug.debug
    def tcpHandleProgressionSet(self, channel, start_power, frames, increment):
        if self.ui.linearTab.isVisible():
            self.linear_channels.remoteSetChannel(channel, start_power, increment, frames)
        elif self.ui.expTab.isVisible():
            self.exp_channels.remoteSetChannel(channel, start_power, increment, frames)

    def tcpHandleProgressionLockout(self):
        self.use_was_checked = self.ui.progressionsCheckBox.isChecked()
        self.ui.progressionsCheckBox.setChecked(False)

    @hdebug.debug
    def tcpHandleProgressionType(self, type):
        self.show()
        self.ui.progressionsCheckBox.setChecked(True)
        if (type == "linear"):
            self.ui.tabWidget.setCurrentWidget(self.ui.linearTab)
        elif (type == "exponential"):
            self.ui.tabWidget.setCurrentWidget(self.ui.expTab)
        elif (type == "file"):
            self.ui.tabWidget.setCurrentWidget(self.ui.fileTab)

    def updateSize(self):
        pc_width = self.power_control.width()
        pc_height = self.power_control.height()
        self.ui.laserBox.setGeometry(10, 0, pc_width + 9, pc_height + 19)
        self.power_control.setGeometry(4, 15, pc_width, pc_height)

        lb_width = self.ui.laserBox.width()
        lb_height = self.ui.laserBox.height()
        self.ui.okButton.setGeometry(lb_width - 65, lb_height + 4, 75, 24)
        self.setFixedSize(lb_width + 18, lb_height + 36)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    progression = ProgressionControl(parameters, None)
    progression.show()
    app.exec_()

#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
