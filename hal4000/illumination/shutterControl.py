#!/usr/bin/python
#
# Master class for shutter control.
#
# This class handles parsing XML shutter files and turning
# them into Python arrays that specify the different
# shutter/AOTF sequences. It also handles the various get functions.
# The user should subclass this class and add specialized setup, startFilm,
# stopFilm and cleanup methods following eg. storm3ShutterControl.
#
# Hazen 3/12
#

from xml.dom import minidom, Node

class ShutterControl():
    def __init__(self, powerToVoltage):
        self.powerToVoltage = powerToVoltage
        self.oversampling_default = 1
        self.number_channels = 0

    def cleanup(self):
        pass

    def getChannelsUsed(self):
        return self.channels_used

    def getColors(self):
        return self.colors

    def getCycleLength(self):
        return self.frames

    def parseXML(self, illumination_file):
        self.channels_used = []
        self.colors = []
        self.frames = 0
        self.waveforms = []
        self.waveform_len = 0

        # Load XML shutters file.
        self.xml = minidom.parse(illumination_file)

        # Use user-specified oversampling (if requested)
        self.oversampling = self.oversampling_default
        if self.xml.getElementsByTagName("oversampling"):
            self.oversampling = int(self.xml.getElementsByTagName("oversampling").item(0).firstChild.nodeValue)

        #
        # For now we only look at the repeat block, leaving the
        # option of having some sort of initialization block.
        #
        xml_repeat = self.xml.getElementsByTagName("repeat").item(0)
        frames = int(xml_repeat.getElementsByTagName("frames").item(0).firstChild.nodeValue)
        self.frames = frames
        events = xml_repeat.getElementsByTagName("event")

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
            for j in range(frames * self.oversampling):
                self.waveforms.append(self.powerToVoltage(i, 0.0))
        self.waveform_len = frames * self.oversampling

        # Add in the events.
        for event in events:
            channel = -1
            power = 0
            on = 0
            off = 0
            color = 0
            for node in event.childNodes:
                if node.nodeType == Node.ELEMENT_NODE:
                    if node.nodeName == "channel":
                        channel = int(node.firstChild.nodeValue)
                    elif node.nodeName == "power":
                        power = float(node.firstChild.nodeValue)
                    elif node.nodeName == "on":
                        on = int(float(node.firstChild.nodeValue) * float(self.oversampling))
                    elif node.nodeName == "off":
                        off = int(float(node.firstChild.nodeValue) * float(self.oversampling))
                    elif node.nodeName == "color":
                        color = []
                        colors = node.firstChild.nodeValue.split(",")
                        for c in colors:
                            x = int(c)
                            if x < 0:
                                x = 0
                            if x > 255:
                                x = 255
                            color.append(x)
            if (channel != -1) and (channel < self.number_channels):
                assert on >= 0, "on out of range: " + str(on) + " " + str(channel)
                assert on <= frames * self.oversampling, "on out of range: " + str(on) + " " + str(channel)
                assert off >= 0, "off out of range: " + str(on) + " " + str(channel)
                assert off <= frames * self.oversampling, "off out of range: " + str(on) + " " + str(channel)

                # Channel waveform setup.
                if channel not in self.channels_used:
                    self.channels_used.append(channel)
                i = on
                voltage = self.powerToVoltage(channel, power)
                while i < off:
                    self.waveforms[channel * frames * self.oversampling + i] = voltage
                    i += 1

                # Color information setup.
                if color:
                    color_start = int(round(float(on)/float(self.oversampling)))
                    color_end = int(round(float(off)/float(self.oversampling)))
                    i = color_start
                    while i < color_end:
                        self.colors[i] = color
                        i += 1

    def prepare(self):
        pass

    def setup(self, kinetic_cycle_time):
        pass

    def shutDown(self):
        pass

    def startFilm(self):
        pass
    
    def stopFilm(self):
        pass

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

