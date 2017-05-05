#!/usr/bin/env python
"""
This file contains the various XML parsing functions.

Hazen 04/17
"""

import numpy

import xml.etree.ElementTree as ElementTree

import storm_control.sc_library.halExceptions as halExceptions


class ShutterXMLException(halExceptions.HalException):
    pass


class ShuttersInfo(object):
    """
    Stores the shutters information that will get sent to other modules.
    """
    def __init__(self,color_data = None, frames = None, **kwds):
        super().__init__(**kwds)
        self.color_data = color_data
        self.frames = frames

    def getColorData(self):
        return self.color_data

    def getFrames(self):
        return self.frames
        
        
def parseShuttersXML(number_channels, shutters_file, oversampling = 100):
    """
    This parses a XML file that defines a shutter sequence.

    FIXME: Not all setup support oversampling, this should complain if
           the setup does not support oversampling.
    """

    # Load XML shutters file.
    xml = ElementTree.parse(shutters_file).getroot()
    if (xml.tag != "repeat"):
        raise ShutterXMLException(shutters_file + " is not a shutters file.")

    # Use user-specified oversampling (if requested), otherwise use 100.
    oversampling = 100
    if xml.find("oversampling") is not None:
        oversampling = int(xml.find("oversampling").text)

    # The length of the sequence.
    frames = int(xml.find("frames").text)

    #
    # We store a color to associate with each frame. This can be accessed by
    # other modules (such as the spot counter) to associate a color with the
    # a particular frame when, for example, updating the STORM image.
    #
    color_data = []
    for i in range(frames):
        color_data.append(0)

    #
    # Create waveforms.
    #
    # Blank waveforms are created for all channels, even those that are not used.
    #
    waveforms = []
    for i in range(number_channels):
        waveforms.append(numpy.zeros(frames * oversampling))

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
                on = int(float(node.text) * float(oversampling))
            elif (node.tag == "off"):
                off = int(float(node.text) * float(oversampling))
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
        if (channel != -1) and (channel < number_channels):
            assert on >= 0, "on out of range: " + str(on) + " " + str(channel)
            assert on <= frames * oversampling, "on out of range: " + str(on) + " " + str(channel)
            assert off >= 0, "off out of range: " + str(on) + " " + str(channel)
            assert off <= frames * oversampling, "off out of range: " + str(on) + " " + str(channel)

            # Channel waveform setup.
            i = on
            waveform = waveforms[channel]
            while i < off:
                waveform[i] = power
                i += 1

            # Color information setup.
            if color:
                color_start = int(round(float(on)/float(oversampling)))
                color_end = int(round(float(off)/float(oversampling)))
                i = color_start
                while i < color_end:
                    color_data[i] = color
                    i += 1

    return [ShuttersInfo(color_data = color_data, frames = frames),
            waveforms,
            oversampling]


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

