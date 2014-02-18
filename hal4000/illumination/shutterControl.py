#!/usr/bin/python
#
## @file
#
# This file contains the base class for shutter control.
#
# Hazen 02/14
#

from PyQt4 import QtCore

#from xml.dom import minidom, Node
import xml.etree.ElementTree as ElementTree

import sc_library.hdebug as hdebug

## ShutterControl
#
# Base class for shutter control.
#
# This class handles parsing XML shutter files and turning
# them into Python arrays that specify the different
# shutter/AOTF sequences. It also handles the various get functions.
# The user should subclass this class and add specialized setup, startFilm,
# stopFilm and cleanup methods following eg. storm3ShutterControl.
#
class ShutterControl(QtCore.QObject):
    newColors = QtCore.pyqtSignal(object)
    newCycleLength = QtCore.pyqtSignal(int)

    ## __init__
    #
    # powerToVoltage is a function that takes two arguments, (1) the channel, (2) the power
    # and returns what voltage corresponds to this power.
    #
    # @param powerToVoltage The function to use to convert (abstract) power to (real) voltage.
    #
    @hdebug.debug
    def __init__(self, powerToVoltage, parent):
        QtCore.QObject.__init__(self, parent)
        self.powerToVoltage = powerToVoltage

        self.kinetic_value = 1.0
        self.oversampling_default = 1
        self.number_channels = 0

    ## cleanup
    #
    # Cleanup after filming.
    # This is usually replaced in a hardware specific sub-class.
    #
    def cleanup(self):
        pass

    ## getChannelsUsed
    #
    # Returns which channels are used in the current shutter sequence.
    #
    # @return A python array of channel indices.
    #
    @hdebug.debug
    def getChannelsUsed(self):
        return self.channels_used

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.kinetic_value = parameters.kinetic_value

    ## parseXML
    #
    # This parses a XML file that defines a shutter sequence.
    #
    # @param shutters_file The name of the shutter sequence xml file.
    #
    @hdebug.debug
    def parseXML(self, shutters_file):
        self.channels_used = []
        self.colors = []
        self.frames = 0
        self.waveforms = []
        self.waveform_len = 0

        # Load XML shutters file.
        xml = ElementTree.parse(shutters_file).getroot()
        assert xml.tag == "repeat", shutters_file + " is not a shutters file."

        # Use user-specified oversampling (if requested)
        self.oversampling = self.oversampling_default
        if xml.find("oversampling") is not None:
            self.oversampling = int(xml.find("oversampling").text)

        # The length of the sequence.
        self.frames = int(xml.find("frames").text)

        #
        # We store a color to associate with each frame. This can be accessed by
        # other modules (such as the spot counter) to associate a color with the
        # a particular frame when, for example, updating the STORM image.
        #
        for i in range(self.frames):
            self.colors.append(0)

        #
        # Create waveforms.
        #
        # Blank waveforms are created for all channels, even those that are not used.
        #
        for i in range(self.number_channels):
            for j in range(self.frames * self.oversampling):
                self.waveforms.append(self.powerToVoltage(i, 0.0))
        self.waveform_len = self.frames * self.oversampling

        # Add in the events.
        for event in xml.findall("event"):
            channel = -1
            power = 0
            on = 0
            off = 0
            color = 0
            for node in event:
                if (node.tag == "channel"):
                    channel = int(node.text)
                elif (node.tag == "power"):
                    power = float(node.text)
                elif (node.tag == "on"):
                    on = int(float(node.text) * float(self.oversampling))
                elif (node.tag == "off"):
                    off = int(float(node.text) * float(self.oversampling))
                elif (node.tag == "color"):
                    color = []
                    colors = node.text.split(",")
                    for c in colors:
                        x = int(c)
                        if x < 0:
                            x = 0
                        if x > 255:
                            x = 255
                        color.append(x)
            if (channel != -1) and (channel < self.number_channels):
                assert on >= 0, "on out of range: " + str(on) + " " + str(channel)
                assert on <= self.frames * self.oversampling, "on out of range: " + str(on) + " " + str(channel)
                assert off >= 0, "off out of range: " + str(on) + " " + str(channel)
                assert off <= self.frames * self.oversampling, "off out of range: " + str(on) + " " + str(channel)

                # Channel waveform setup.
                if channel not in self.channels_used:
                    self.channels_used.append(channel)
                i = on
                voltage = self.powerToVoltage(channel, power)
                while i < off:
                    self.waveforms[channel * self.frames * self.oversampling + i] = voltage
                    i += 1

                # Color information setup.
                if color:
                    color_start = int(round(float(on)/float(self.oversampling)))
                    color_end = int(round(float(off)/float(self.oversampling)))
                    i = color_start
                    while i < color_end:
                        self.colors[i] = color
                        i += 1

        self.newColors.emit(self.colors)
        self.newCycleLength.emit(self.frames)

    ## prepare
    #
    # Called before setup to properly set the state of the hardware.
    # Usually this means making sure that the DAQ output lines are
    # set to the right initial values.
    #
    # This is usually replaced in a hardware specific sub-class.
    #
    def prepare(self):
        pass

    ## setup
    #
    # Called next to setup the hardware for filming. Usually this
    # means loading the shutter waveforms into the DAQ card and
    # configuring the timers of the DAQ card.
    #
    # This is usually replaced in a hardware specific sub-class.
    #
    def setup(self):
        pass

    ## shutDown
    #
    # Called to shutdown the hardware prior to the program exitting.
    #
    # This is usually replaced in a hardware specific sub-class.
    #
    def shutDown(self):
        pass

    ## startFilm
    #
    # Called at the start of filming. Usually this starts the various
    # tasks on the DAQ card.
    #
    # This is usually replaced in a hardware specific sub-class.
    #
    def startFilm(self):
        pass

    ## stopFilm
    #
    # Called at the end of filming to reset the hardware. Usually
    # this means configuring the DAQ card for non-shutter operation.
    #
    # This is usually replaced in a hardware specific sub-class.
    #
    def stopFilm(self):
        pass

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

