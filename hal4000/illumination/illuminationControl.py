#!/usr/bin/python
#
## @file
#
# Illumination control master classes.
#
#  Methods called by HAL:
#
#    closeFile()
#      Called after filming ends to close the power log file.
#
#    getNumberChannels()
#      Returns the number of channels that are controlled.
#
#    newFrame()
#      Called when a new frame of data is available. This
#      causes illuminationControl to write the current
#      power settings into the power log file.
#
#    newParameters(parameters)
#      Update sliders, buttons, etc. on the dialog box with
#      new settings.
#
#    openFile(filename)
#      Called before filming starts with the filename for
#      logging the power setting during filming. This function
#      appends ".power" to the filename & opens the file.
#
#    powerToVoltage(channel, power)
#      Returns what voltage corresponds to what power
#      (0.0 - 1.0).
#
#    quit()
#      Cleanup and shutdown prior to the program ending.
#
#    remoteIncPower(channel, power_inc)
#      Increment power of channel about amount power_inc
#
#    remoteSetPower(channel, power)
#      Set power of channel about to power
#
#    show()
#      Display the illumination control dialog box.
#
#    startFilm(channels_used)
#      Setup for filming. Prepare the specified channels
#      for automatic control via the shutterControl class.
#
#    stopFilm(channels_used)
#      Cleanup from filming. Close the power log file. Revert
#      the specified channels to manual control mode.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui
import sip
from xml.dom import minidom, Node

import qtWidgets.qtAppIcon as qtAppIcon
import illumination.channelWidgets as channelWidgets

# Debugging
import halLib.hdebug as hdebug

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
    def __init__(self, settings_file_name, parameters, parent = None):
        QtGui.QWidget.__init__(self, parent)

        # parse the settings file
        xml = minidom.parse(settings_file_name)
        blocks = xml.getElementsByTagName("block")
        self.settings = []
        for i in range(blocks.length):
            self.settings.append(channelWidgets.XMLToChannelObject(blocks[i].childNodes))
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
    def closeEvent(self, event):
        self.shutDown()

    ## getNumberChannels
    #
    # @return The number of channels.
    #
    def getNumberChannels(self):
        return self.number_channels

    ## manualControl
    #
    # Configure all the channels for filming without a shutter sequence.
    # This method is generally replaced with a setup specific version.
    #
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
    def remoteSetPower(self, channel, power):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].setDisplayedAmplitude(power)

    ## reset
    #
    # FIXME: This appears to set all the channels that are already on to on..
    #
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
    def shutDown(self):
        self.allOff()

    ## turnOnOff
    #
    # Turns on/off all requested channels.
    #
    # @param channels A python array of channel indices.
    # @param on True/False.
    #
    def turnOnOff(self, channels, on):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.onOff(i, on)


## IlluminationControl
#
# Illumination power control dialog box. This is handles the dialog
# box that contains the above illumination control widget.
#
class IlluminationControl(QtGui.QDialog):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param tcp_control A TCP/IP control object.
    # @param parent (Optional) The PyQt parent of this dialog box.
    #
    @hdebug.debug
    def __init__(self, parameters, tcp_control, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.fp = 0
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0
        self.tcp_control = tcp_control

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

        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("setPower(int, float)"), self.tcpHandleSetPower)
            self.connect(self.tcp_control, QtCore.SIGNAL("incPower(int, float)"), self.tcpHandleIncPower)

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
        else:
            self.quit()

    ## closeFile
    #
    # Close the .power file at the end of filming.
    #
    @hdebug.debug
    def closeFile(self):
        if self.fp:
            self.fp.close()
            self.fp = 0

    ## getNumberChannels
    #
    # Calls QIlluminationControl's getNumberChannels method.
    #
    # @return The number of active channels.
    #
    @hdebug.debug
    def getNumberChannels(self):
        return self.power_control.getNumberChannels()

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

    ## newFrame
    #
    # Handles new frames. If there is a open file and the frame
    # is a master frame then this calls QIlluminationControl's
    # savePowers method.
    #
    def newFrame(self, frame):
        if self.fp and frame.master:
            self.power_control.savePowers(self.fp, frame.number)

    ## newParameters
    #
    # Calls QIlluminationControl's newParameters method, then updates
    # the size of the dialog as appropriate to fit all of the controls.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.power_control.newParameters(parameters)
        self.updateSize()

    ## openFile
    #
    # Called at the start of filming to open a file to save the
    # channel power values in.
    #
    # @param name The name of the file to save powers in.
    #
    @hdebug.debug
    def openFile(self, name):
        self.fp = open(name + ".power", "w")
        self.power_control.saveHeader(self.fp)
        self.frame = 1

    ## quit
    #
    # Calls QIlluminationControl's shutDown method.
    #
    @hdebug.debug
    def quit(self):
        self.power_control.shutDown()

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
    # Called at the start of filming.
    #
    @hdebug.debug
    def startFilm(self, channels_used):
        self.autoControl(channels_used)
        self.turnOnOff(channels_used, 1)

    ## stopFilm
    #
    # Called at the end of filming.
    #
    @hdebug.debug
    def stopFilm(self, channels_used):
        self.turnOnOff(channels_used, 0)
        self.manualControl()
        self.reset()

    ## tcpHandleIncPower
    #
    # Handles TCP/IP increment power requests.
    #
    # @param channel The channel index.
    # @param power_inc The amount to increment the power by.
    #
    @hdebug.debug
    def tcpHandleIncPower(self, channel, power_inc):
        self.remoteIncPower(channel, power_inc)

    ## tcpHandleSetPower
    #
    # Handles TCP/IP set power requests.
    #
    # @param channel The channel index.
    # @param power The value to set the power to.
    #
    @hdebug.debug
    def tcpHandleSetPower(self, channel, power):
        self.remoteSetPower(channel, power)

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
