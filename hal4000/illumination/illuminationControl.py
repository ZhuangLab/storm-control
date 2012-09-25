#!/usr/bin/python
#
# Illumination control master classes.
#
# Hazen 6/09
#

from PyQt4 import QtCore, QtGui
import sip
from xml.dom import minidom, Node

import illumination.channelWidgets as channelWidgets

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.illumination_v1 as illuminationUi

#
# Illumination power control.
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

    def allOff(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,0)

    def autoControl(self, channels):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.channels[i].fskOnOff(1)
                    self.channels[i].setFilmMode(1)

    def closeEvent(self, event):
        self.shutDown()

    def getNumberChannels(self):
        return self.number_channels

    def manualControl(self):
        for channel in self.channels:
            channel.fskOnOff(0)
            channel.setFilmMode(0)

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

    def onOff(self, index, on):
        self.channels[index].update(on)

    def powerToVoltage(self, channel, power):
        assert power >= 0.0, "power out of range: " + str(power) + " " + str(channel)
        assert power <= 1.0, "power out of range: " + str(power) + " " + str(channel)
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                return self.settings[i].range * power - self.settings[i].min_voltage
        print "unknown channel: " + str(channel)
        return 0.0

    def remoteIncPower(self, channel, power_inc):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].incDisplayedAmplitude(power_inc)

    def remoteSetPower(self, channel, power):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].setDisplayedAmplitude(power)

    def reset(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,1)

    def saveHeader(self, fp):
        str = "frame"
        for i in range(self.number_channels):
            str = str + " {0:d}".format(self.settings[i].channel)
        fp.write(str + "\n")

    def savePowers(self, fp, frame):
        str = "{0:d}".format(frame)
        for channel in self.channels:
            str = str + " {0:.4f}".format(channel.getDisplayedAmplitude())
        fp.write(str + "\n")

    def shutDown(self):
        self.allOff()

    def turnOnOff(self, channels, on):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.onOff(i, on)


#
# Illumination power control dialog box
#
class IlluminationControl(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.fp = 0
        self.frame = 1
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0
        self.tcp_control = tcp_control

        # UI setup
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Illumination Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            #self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleOk)
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            #self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleQuit)
            self.ui.okButton.clicked.connect(self.handleQuit)

        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("setPower(int, float)"), self.tcpHandleSetPower)
            self.connect(self.tcp_control, QtCore.SIGNAL("incPower(int, float)"), self.tcpHandleIncPower)

        # set modeless
        self.setModal(False)

    @hdebug.debug
    def autoControl(self, channels_used):
        self.power_control.autoControl(channels_used)

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def closeFile(self):
        if self.fp:
            self.fp.close()
            self.fp = 0

    @hdebug.debug
    def getNumberChannels(self):
        return self.power_control.getNumberChannels()

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    @hdebug.debug
    def manualControl(self):
        self.power_control.manualControl()

    def newFrame(self):
        if self.fp:
            self.power_control.savePowers(self.fp, self.frame)
            self.frame += 1

    @hdebug.debug
    def newParameters(self, parameters):
        self.debug = parameters.debug
        self.power_control.newParameters(parameters)
        self.updateSize()

    @hdebug.debug
    def openFile(self, name):
        self.fp = open(name + ".power", "w")
        self.power_control.saveHeader(self.fp)
        self.frame = 1

    @hdebug.debug
    def quit(self):
        self.power_control.shutDown()

    @hdebug.debug
    def remoteIncPower(self, channel, power_inc):
        self.power_control.remoteIncPower(channel, power_inc)

    @hdebug.debug
    def remoteSetPower(self, channel, power):
        self.power_control.remoteSetPower(channel, power)

    @hdebug.debug
    def reset(self):
        self.power_control.reset()

    @hdebug.debug
    def startFilm(self, channels_used):
        self.autoControl(channels_used)
        self.turnOnOff(channels_used, 1)

    @hdebug.debug
    def stopFilm(self, channels_used):
        self.turnOnOff(channels_used, 0)
        self.manualControl()
        self.reset()

    @hdebug.debug
    def tcpHandleIncPower(self, channel, power_inc):
        self.remoteIncPower(channel, power_inc)

    @hdebug.debug
    def tcpHandleSetPower(self, channel, power):
        self.remoteSetPower(channel, power)

    @hdebug.debug
    def turnOnOff(self, channels, on):
        if on:
            self.power_control.allOff()
        self.power_control.turnOnOff(channels, on)

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
