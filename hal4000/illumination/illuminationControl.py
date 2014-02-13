#!/usr/bin/python
#
## @file
#
# Illumination control master classes.
#
# Hazen 02/14
#

from PyQt4 import QtCore, QtGui
import sip
from xml.dom import minidom, Node

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.halModule as halModule
import illumination.channelWidgets as channelWidgets
import illumination.shutterControl as shutterControl

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.illumination_ui as illuminationUi

## QIlluminationControlWidget
#
# Illumination power control. This handles the part of the power
# control UI where the channels, buttons and radio buttons are
# drawn.
#
# Since the channel number and the index, at least in theory,
# do not have to correspond the program checks the requested
# channel number against the channel number stored for a
# particular channel. Is this necessary? People should not
# be editing the xx_illumination_control_settings.xml file 
# anyway so one could probably count on it not being so 
# confusing...
#
class QIlluminationControlWidget(QtGui.QWidget):

    ## __init__
    #
    # @param settings_file_name The name of XML file that describes the illumination channels.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, settings_file_name, parameters, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.channel_names = []

        # parse the settings file
        xml = minidom.parse(settings_file_name)
        blocks = xml.getElementsByTagName("block")
        self.settings = []
        for i in range(blocks.length):
            setting = channelWidgets.XMLToChannelObject(blocks[i].childNodes)
            self.channel_names.append(setting.description)
            self.settings.append(setting)
        self.number_channels = blocks.length

        # layout the widget
        self.setWindowTitle("Laser Power Control")
        self.last_parameters = 0
        self.channels = []
        self.newParameters(parameters)

        # go to manual control
        #for channel in self.channels:
        #    channel.setFrequency()
        self.manualControl()

    ## allOff
    #
    # Turn off all of the channels. This method is generally replaced with
    # a setup specific version.
    #
    @hdebug.debug
    def allOff(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,0)

    ## autoControl
    #
    # Configure all of the channels for filming with a shutter sequence.
    #
    # @param channels A python array containing the indices of the active channels.
    #
    @hdebug.debug
    def autoControl(self, channels):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.channels[i].fskOnOff(1)
                    self.channels[i].setFilmMode(1)

    ## closeEvent
    #
    # FIXME: Is this ever called?
    #
    # @param event A PyQt event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        self.shutDown()

    ## getChannelNames
    #
    # @return The names of the channels as list.
    #
    @hdebug.debug
    def getChannelNames(self):
        return self.channel_names

    ## getNumberChannels
    #
    # @return The number of channels.
    #
    @hdebug.debug
    def getNumberChannels(self):
        return self.number_channels

    ## manualControl
    #
    # Configure all the channels for filming without a shutter sequence.
    # This method is generally replaced with a setup specific version.
    #
    @hdebug.debug
    def manualControl(self):
        for channel in self.channels:
            channel.fskOnOff(0)
            channel.setFilmMode(0)

    ## newParameters
    #
    # Update the UI based on a new set of parameters.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        # Record the current state of all the old channels.
        if len(self.channels) > 0:
            for i, channel in enumerate(self.channels):
                n = self.settings[i].channel
                self.last_parameters.on_off_state[n] = channel.amOn()
                self.last_parameters.default_power[n] = channel.getCurrentDefaultPower()
                sip.delete(channel)
                channel = None
        # Delete old channels, if they exist.
        self.channels = []

    ## onOff
    #
    # Turn a channel on or off.
    #
    # @param index The channel number.
    # @param on True/False.
    #
    @hdebug.debug
    def onOff(self, index, on):
        self.channels[index].update(on)

    ## powerToVoltage
    #
    # Convert a power value (0.0 - 1.0) to a properly scaled voltage.
    #
    # @param channel The channel index.
    # @param power The power value.
    #
    # @return The voltage value that corresponds to the power value.
    #
    def powerToVoltage(self, channel, power):
        assert power >= 0.0, "power out of range: " + str(power) + " " + str(channel)
        assert power <= 1.0, "power out of range: " + str(power) + " " + str(channel)
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                return self.settings[i].range * power - self.settings[i].min_voltage
        print "unknown channel: " + str(channel)
        return 0.0

    ## remoteIncPower
    #
    # Handles non-UI requests to set the power of a channel.
    #
    # @param channel The channel index.
    # @param power_inc The amount to increment the power by.
    #
    @hdebug.debug
    def remoteIncPower(self, channel, power_inc):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].incDisplayedAmplitude(power_inc)

    ## remoteSetPower
    #
    # Handles non-UI requests to set the power of a channel.
    #
    # @param channel The channel index.
    # @param power The power value (0.0 - 1.0).
    #
    @hdebug.debug
    def remoteSetPower(self, channel, power):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].setDisplayedAmplitude(power)

    ## reset
    #
    # FIXME: This appears to set all the channels that are already on to on..
    #
    @hdebug.debug
    def reset(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,1)

    ## saveHeader
    #
    # This adds the header line to the .power file that is recorded during filming.
    #
    # @param fp The .power file's file-pointer.
    #
    def saveHeader(self, fp):
        str = "frame"
        for i in range(self.number_channels):
            str = str + " {0:d}".format(self.settings[i].channel)
        fp.write(str + "\n")

    ## savePowers
    #
    # This saves the current power in the .power file when a new frame is received.
    #
    # @param fp The .power file's file-pointer.
    # @param frame A frame object.
    #
    def savePowers(self, fp, frame):
        str = "{0:d}".format(frame)
        for channel in self.channels:
            str = str + " {0:.4f}".format(channel.getDisplayedAmplitude())
        fp.write(str + "\n")

    ## shutDown
    #
    # Turn all the channels off. This method is usually replaced
    # with a setup specific version.
    #
    @hdebug.debug
    def shutDown(self):
        self.allOff()

    ## turnOnOff
    #
    # Turns on/off all requested channels.
    #
    # @param channels A python array of channel indices.
    # @param on True/False.
    #
    @hdebug.debug
    def turnOnOff(self, channels, on):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.onOff(i, on)


## IlluminationControl
#
# Illumination power control dialog box. This is handles the dialog
# box that contains the above illumination control widget as well
# as the shutter control.
#
class IlluminationControl(QtGui.QDialog, halModule.HalModule):
    channelNames = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this dialog box.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QDialog.__init__(self, parent)
        halModule.HalModule.__init__(self)

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        self.fp = False
        self.running_shutters = False

        # UI setup
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Illumination Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        # set modeless
        self.setModal(False)

    ## autoControl.
    #
    # Calls QIlluminationControl's autoControl method.
    #
    # @param channels_used A Python array of channel indices.
    #
    @hdebug.debug
    def autoControl(self, channels_used):
        self.power_control.autoControl(channels_used)

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        self.power_control.shutDown()
        self.shutter_control.cleanup()
        self.shutter_control.shutDown()

    ## closeEvent
    #
    # Close the dialog if it has no parent, otherwise just hide it.
    #
    # @param event A PyQt event.
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
            if (signal[1] == "setPower"):
                signal[2].connect(self.remoteSetPower)
            elif (signal[1] == "incPower"):
                signal[2].connect(self.remoteIncPower)

            elif (signal[1] == "commMessage"):
                signal[2].connect(self.handleCommMessage)

    ## getNumberChannels
    #
    # Calls QIlluminationControl's getNumberChannels method.
    #
    # @return The number of active channels.
    #
    @hdebug.debug
    def getNumberChannels(self):
        return self.power_control.getNumberChannels()

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "channelNames", self.channelNames],
                [self.hal_type, "newColors", self.shutter_control.newColors],
                [self.hal_type, "newCycleLength", self.shutter_control.newCycleLength]]

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

        if (m_type == "setPower"):
            self.remoteSetPower(m_data[0], m_data[1])
        elif (m_type == "incPower"):
            self.remoteIncPower(m_data[0], m_data[1])

    ## handleOk
    #
    # Hide the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleQuit
    #
    # Close the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## manualControl
    #
    # Calls QIlluminationControl's manualControl method.
    #
    @hdebug.debug
    def manualControl(self):
        self.power_control.manualControl()

    ## moduleInit
    #
    @hdebug.debug
    def moduleInit(self):
        self.channelNames.emit(self.power_control.getChannelNames())

    ## newFrame
    #
    # Handles new frames. If there is a open file and the frame
    # is a master frame then this calls QIlluminationControl's
    # savePowers method.
    #
    # @param frame A camera.Frame object
    # @param filming True/False if we are currently filming.
    #
    def newFrame(self, frame, filming):
        if self.fp and frame.master:
            self.power_control.savePowers(self.fp, frame.number)

    ## newParameters
    #
    # Calls QIlluminationControl's newParameters method, then updates
    # the size of the dialog as appropriate to fit all of the controls.
    #
    # Note that the camera updates the kinetic_
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.power_control.newParameters(parameters)
        self.shutter_control.newParameters(parameters)
        self.updateSize()

    ## newShutters
    #
    # @param shutters_filename The name of a shutters XML file.
    #
    @hdebug.debug
    def newShutters(self, shutters_filename):
        self.shutter_control.parseXML(shutters_filename)

    ## remoteIncPower
    #
    # Calls QIlluminationControl's remoteIncPower method.
    #
    # @param channel The channel index.
    # @param power_inc The amount increment the power by.
    #
    @hdebug.debug
    def remoteIncPower(self, channel, power_inc):
        self.power_control.remoteIncPower(channel, power_inc)

    ## remoteSetPower
    #
    # Calls QIlluminationControl's remoteSetPower method.
    #
    # @param channel The channel index.
    # @param power The desired power (0.0 - 1.0).
    #
    @hdebug.debug
    def remoteSetPower(self, channel, power):
        self.power_control.remoteSetPower(channel, power)

    ## reset
    #
    # Calls QIlluminationControl's reset method.
    #
    @hdebug.debug
    def reset(self):
        self.power_control.reset()

    ## startFilm
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):

        # Recording the power.
        if film_name:
            self.fp = open(film_name + ".power", "w")
            self.power_control.saveHeader(self.fp)

        # Running the shutters.
        if run_shutters:
            self.running_shutters = True
            channels_used = self.shutter_control.getChannelsUsed()
            self.shutter_control.prepare()
            self.autoControl(channels_used)
            self.turnOnOff(channels_used, 1)
            self.shutter_control.setup()
            self.shutter_control.startFilm()

    ## stopFilm
    #
    # Called at the end of filming.
    #
    # @param film_writer The film writer object.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        if self.fp:
            self.fp.close()
            self.fp = False

        if self.running_shutters:
            self.shutter_control.stopFilm()

            # aotf cleanup
            channels_used = self.shutter_control.getChannelsUsed()
            self.turnOnOff(channels_used, 0)
            self.manualControl()
            self.reset()

            self.running_shutters = False

    ## turnOnOff
    #
    # If on is true, turn off all the channels (at the start of filming).
    # If on is false, turn off only the channels  used (at the end of filming).
    # 
    # @param channels A python array of channel indices.
    # @param on True/False.
    #
    @hdebug.debug
    def turnOnOff(self, channels, on):
        if on:
            self.power_control.allOff()
        self.power_control.turnOnOff(channels, on)

    ## updateSize
    #
    # Resize the dialog based on the size of the power control section
    # (i.e. the sliders, buttons, etc.).
    #
    @hdebug.debug
    def updateSize(self):
        pc_width = self.power_control.width()
        pc_height = self.power_control.height()
        self.ui.laserBox.setGeometry(10, 0, pc_width + 9, pc_height + 19)
        self.power_control.setGeometry(4, 15, pc_width, pc_height)

        lb_width = self.ui.laserBox.width()
        lb_height = self.ui.laserBox.height()
        self.ui.okButton.setGeometry(lb_width - 65, lb_height + 4, 75, 24)
        self.setFixedSize(lb_width + 18, lb_height + 36)
        

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
