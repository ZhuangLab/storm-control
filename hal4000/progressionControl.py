#!/usr/bin/python
#
## @file
#
# The progression control dialog box.
#
# This dialog allows the user to configure an automatic
# starting power and power increment to use while taking
# STORM movies. This increases productivity & overall
# quality of life as the user can focus on surfing
# the internet while acquiring STORM movies without 
# getting distracted by constantly having to adjust 
# the laser powers.
#
# Hazen 02/14
#

import os
import sys
from PyQt4 import QtCore, QtGui

import halLib.halModule as halModule
import qtWidgets.qtAppIcon as qtAppIcon

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.progression_ui as progressionUi

## Channels
#
# Channels class which is specialized for various
# types of channel power progressions.
#
class Channels():

    ## __init__
    #
    # Create a generic channel object.
    #
    # @param parent The parent of the channel.
    #
    # FIXME: What is the parent for? We don't seem to use it.
    #
    def __init__(self, parent):
        self.height = 40
        self.powers = []

    ## newFrame
    #
    # Called when we get a new frame from the camera.
    #
    # @param frame_number The frame number of the frame.
    #
    def newFrame(self, frame_number):
        pass

    ## startFilm
    #
    # Called at the start of a film.
    #
    def startFilm(self):
        pass

    ## stopFilm
    #
    # Called when the film is stopped.
    #
    def stopFilm(self):
        pass

## MathChannels
#
# Channels class for mathematical progressions (linear, exponential).
#
class MathChannels(Channels):

    ## __init__
    #
    # Called to layout the GUI for math channels. These channels match
    # the channels of the illumination.
    #
    # @param channels The names of the channels.
    # @param x_positions The x positions at which to draw the GUI elements.
    # @param parameters The initial values for the adjustable GUI elements.
    # @param parent Not used?
    #
    def __init__(self, channels, x_positions, parameters, parent):
        Channels.__init__(self, parent)
        y = 40
        dy = 26
        self.channels = []
        self.which_checked = []
        for channel in channels:
            self.powers.append(0.0)
            self.which_checked.append(False)
            channel_frame = QtGui.QFrame(parent)
            channel_frame.setGeometry(0, y, 340, 24)

            # channel number
            channel_text = QtGui.QLabel(channel_frame)
            channel_text.setGeometry(x_positions[0], 2, 25, 18)
            channel_text.setText(channel)

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

    ## remoteSetChannel
    #
    # This is called by an external program to specify the
    # settings for a particular channel.
    #
    # @param which_channel The channel to set.
    # @param initial The channels initial power value.
    # @param inc The channels increment amount.
    # @param time The number of frames between increments.
    #
    def remoteSetChannel(self, which_channel, initial, inc, time):
        channel = self.channels[which_channel]
        channel[0].setChecked(True)
        channel[1].setValue(initial)
        channel[2].setValue(inc)
        channel[3].setValue(time)

    ## startFilm
    #
    # This is called when the filming starts. It returns the
    # desired initial powers for the various channels.
    #
    # @return Returns an array of arrays containing the active channels and their initial powers.
    #
    def startFilm(self):
        for i, channel in enumerate(self.channels):
            self.which_checked[i] = False
            self.powers[i] = (float(channel[1].value()))
            if channel[0].isChecked():
                self.which_checked[i] = True
        return [self.which_checked, self.powers]

    ## stopFilm
    #
    # This is called when the film stops. It resets the powers
    # to their initial values.
    #
    def stopFilm(self):
        for i, channel in enumerate(self.channels):
            self.powers[i] = (float(channel[1].value()))
        return [self.which_checked, self.powers]

## LinearChannels
#
# Channels class for linear progression.
#
class LinearChannels(MathChannels):

    ## __init__
    #
    # This is basically the same as for MathChannels. It also specifies
    # a maximum value for the increment spin box.
    #
    # @param channels The names of the channels.
    # @param x_positions The x positions at which to draw the GUI elements.
    # @param parameters The initial values for the adjustable GUI elements.
    # @param parent Not used?
    #
    def __init__(self, channels, x_positions, parameters, parent):
        MathChannels.__init__(self, channels, x_positions, parameters, parent)
        for channel in self.channels:
            channel[2].setMaximum(1.0)

    ## newFrame
    #
    # Called when we get a new frame from the camera. Returns the which
    # channels (if any) need to have their power adjusted.
    #
    # @param frame_number The frame number of the current frame.
    #
    # @return Returns an array of arrays containing the active channels and how much to increment their power by.
    #
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

## ExponentialChannels
#
# Channels class for exponential progression.
#
class ExponentialChannels(MathChannels):

    ## __init__
    #
    # This is basically the same as for MathChannels. It also specifies
    # the current and maximum value of the increment spin box.
    #
    # @param channels The names of the channels.
    # @param x_positions The x positions at which to draw the GUI elements.
    # @param parameters The initial values for the adjustable GUI elements.
    # @param parent Not used?
    #
    def __init__(self, channels, x_positions, parameters, parent):
        MathChannels.__init__(self, channels, x_positions, parameters, parent)
        for channel in self.channels:
            channel[2].setValue(1.05)
            channel[2].setMaximum(9.9)

    ## newFrame
    #
    # Called when we get a new frame from the camera. Returns the which
    # channels (if any) need to have their power adjusted.
    #
    # @param frame_number The frame number of the current frame.
    #
    # @return Returns an array of arrays containing the active channels and how much to increment their power by.
    #
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

## FileChannels
#
# Channels class for power file bases progression. This lets you
# replay the power settings that you used in previous films.
#
class FileChannels(Channels):

    ## __init__
    #
    # Initialize some file channel related variables.
    #
    def __init__(self, parent):
        Channels.__init__(self, parent)
        self.active = []
        self.start_powers = []
        self.file_ptr = False

    ## getNextPowers
    #
    # Read and parse the next line of the powers file, or False 
    # if we have reached the end of the file.
    #
    # @return Return an array containing the powers, or False.
    #
    def getNextPowers(self):
        line = self.file_ptr.readline()
        powers = False
        if line:
            powers = []
            powers_text = line.split(" ")[1:]
            for i in range(len(powers_text)):
                powers.append(float(powers_text[i]))
        return powers

    ## newFile
    #
    # Open a powers file & read the first line to get the initial
    # power values.
    #
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

    ## newFrame
    #
    # Called when we get a new frame from the camera. Returns the which
    # channels (if any) need to have their power adjusted.
    #
    # @param frame_number The frame number of the current frame.
    #
    # @return Returns an array of arrays containing the active channels and how much to increment their power by.
    #
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
            return [active, increment]
        else:
            return [[], []]

    ## startFilm
    #
    # This is called when the filming starts. It returns the
    # desired initial powers for the various channels. It also
    # rewinds the file pointer to beginning of the powers file.
    #
    # @return Returns an array of arrays containing the active channels and their initial powers.
    #
    def startFilm(self):
        if self.file_ptr:
            # reset file ptr
            self.file_ptr.seek(0)
            self.file_ptr.readline()
            # reset internal power record
            for i in range(len(self.start_powers)):
                self.powers[i] = self.start_powers[i]
            return [self.active, self.start_powers]
        else:
            return [[], []]

    ## stopFilm
    #
    # This is called when the film stops. It resets the powers
    # to their initial values.
    #
    def stopFilm(self):
        if self.file_ptr:
            return [self.active, self.start_powers]
        else:
            return [[], []]


## ProgressionControl
#
# Progression control dialog box
#
class ProgressionControl(QtGui.QDialog, halModule.HalModule):
    incPower = QtCore.pyqtSignal(int, float)
    setPower = QtCore.pyqtSignal(int, float)

    ## __init__
    #
    # This initializes things and sets up the UI of the power control
    # dialog box.
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent The (PyQt) parent of the dialog.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent):
        QtGui.QDialog.__init__(self, parent)
        halModule.HalModule.__init__(self)
        self.channels = False
        self.exp_channels = False
        self.linear_channels = False
        self.file_channels = False
        self.parameters = parameters
        self.use_was_checked = False
        self.which_checked = []

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = progressionUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Progression Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.progressionsCheckBox.stateChanged.connect(self.handleProgCheck)
        self.ui.loadFileButton.clicked.connect(self.newPowerFile)

        # set modeless
        self.setModal(False)

    ## addChannels
    #
    # Called to add the controls for the channels. The channel
    # information comes from the illuminationControl module.
    # This is called once after initialization and before the
    # dialog is displayed.
    #
    # @param channels A list containing the names of the channels.
    #
    def addChannels(self, channels):

        self.which_checked = []
        for i in range(len(channels)):
            self.which_checked.append(False)

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

    ## closeEvent
    #
    # This is called when the dialog is closed. If the dialog
    # has a parent then it ignores these events and hides itself instead.
    #
    # @param event A QEvent.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "commMessage"):
                signal[2].connect(self.handleCommMessage)
            elif (signal[1] == "channelNames"):
                signal[2].connect(self.addChannels)

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "incPower", self.incPower],
                [self.hal_type, "setPower", self.setPower]]

    ## handleCommMessage
    #
    # Handles all the message from tcpControl.
    #
    # @param message A tcpControl.TCPMessage object.
    #
    @hdebug.debug
    def handleCommMessage(self, message):

        m_type = message.getType()
        m_data = message.getData()

        if (m_type == "progressionLockout"):
            self.tcpHandleProgressionLockout()
        elif (m_type == "progressionFile"):
            self.tcpHandleProgressionFile(m_data[0])
        elif (m_type == "progressionSet"):
            self.tcpHandleProgressionSet(m_data[0], m_data[1], m_data[2], m_data[3])
        elif (m_type == "progressionType"):
            self.tcpHandleProgressionType(m_data[0])

    ## handleOk
    #
    # This is called when the user presses the close button. It hides
    # the dialog.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleProgCheck
    #
    # This is called when the user clicks the progression check box.
    #
    # @param state The state of the progession check box.
    #
    @hdebug.debug
    def handleProgCheck(self, state):
        if state:
            self.parameters.use_progressions = True
        else:
            self.parameters.use_progressions = False

    ## handleQuit
    #
    # This is called when the user clicks the quit button.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## newFrame
    #
    # This is called when we get new frames from the camera. It
    # calls the newFrame method of the active channels object.
    # If this returns that power updates are necessary then it
    # emits the appropriate progIncPower signals.
    #
    # @param frame The current frame object.
    # @param filming True/False if we are currently filming.
    #
    def newFrame(self, frame, filming):
        if filming and self.channels and frame.master:
            [active, increment] = self.channels.newFrame(frame.number)
            for i in range(len(active)):
                if active[i]:
                    self.incPower.emit(int(i), increment[i])

    ## newParameters
    #
    # This is called when there are new parameters. Note that there are
    # no parameter specific settings for all the GUI elements. This
    # just checks / unchecks the use progressions check box.
    #
    # @param parameters The new parameters.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        if parameters.use_progressions:
            self.ui.progressionsCheckBox.setChecked(True)
        else:
            self.ui.progressionsCheckBox.setChecked(False)

    ## newPowerFile
    #
    # Opens a file dialog where the user can specify a new power file.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def newPowerFile(self, bool):
        power_filename = QtGui.QFileDialog.getOpenFileName(self,
                                                           "New Power File",
                                                           str(self.parameters.directory),
                                                           "*.power")
        if power_filename:
            self.ui.filenameLabel.setText(power_filename[-40:])
            self.file_channels.newFile(power_filename)

    ## setInitialPower
    #
    # This emits progSetPower signals to set the power. This is called
    # at the start & end of filming.
    #
    # @param active Boolean array specifying whether or not a channel is active.
    # @param power The power to set the channel too.
    #
    def setInitialPower(self, active, power):
        for i in range(len(active)):
            if active[i]:
                self.setPower.emit(int(i), power[i])

    ## startFilm
    #
    # Called at the start of filming. If the progression dialog is
    # open and the use progressions check box is checked it figures 
    # out which tab is visible to determine which is the active channel
    # object. Then it sets the intial powers as specified by the
    # active channel.
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    def startFilm(self, film_name, run_shutters):
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
            self.setInitialPower(active, power)

    ## stopFilm
    #
    # Called when the film stops. This resets the powers to their
    # initial values.
    #
    # @param film_writer The film writer object.
    #
    def stopFilm(self, film_writer):
        if self.channels:
            [active, power] = self.channels.stopFilm()
            self.setInitialPower(active, power)
        if self.use_was_checked:
            self.use_was_checked = False
            self.ui.progressionsCheckBox.setChecked(True)

    ## tcpHandleProgressionFile
    #
    # Handles TCP/IP signal to set the power
    # file for file based power progressions.
    #
    # @param filename The filename of the power file.
    #
    @hdebug.debug
    def tcpHandleProgressionFile(self, filename):
        if os.path.exists(filename):
            self.ui.filenameLabel.setText(filename[-40:])
            self.file_channels.newFile(filename)

    ## tcpHandleProgressionSet
    #
    # Handles TCP/IP signal to set the values of a math channel.
    #
    # @param channel The channel number.
    # @param start_power The starting power.
    # @param frames The number of frames between increments.
    # @param increment The amount to increments.
    #
    @hdebug.debug
    def tcpHandleProgressionSet(self, channel, start_power, frames, increment):
        if self.ui.linearTab.isVisible():
            self.linear_channels.remoteSetChannel(channel, start_power, increment, frames)
        elif self.ui.expTab.isVisible():
            self.exp_channels.remoteSetChannel(channel, start_power, increment, frames)

    ## tcpHandleProgressionLockout
    #
    # Handles TCP/IP signal to lockout progressions.
    #
    def tcpHandleProgressionLockout(self):
        self.use_was_checked = self.ui.progressionsCheckBox.isChecked()
        self.ui.progressionsCheckBox.setChecked(False)

    ## tcpHandleProgressionType
    #
    # Handles TCP/IP signal to set the progression type.
    #
    # @param type This is one of "linear", "exponential" or "file"
    #
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
