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
        """
        Return the length of the shutter sequence in frames.
        """
        return self.frames
        
        
def parseShuttersXML(channel_name_to_id, shutters_file, can_oversample = True):
    """
    This parses a XML file that defines a shutter sequence.

    FIXME: Not all setup support oversampling, but none of them currently set
           the can_oversample argument.
    """
    number_channels = len(channel_name_to_id)

    # Load XML shutters file.
    xml = ElementTree.parse(shutters_file).getroot()
    if (xml.tag != "repeat"):
        raise ShutterXMLException(shutters_file + " is not a shutters file.")

    # Use user-specified oversampling (if requested), otherwise use 100.
    if can_oversample:
        oversampling = 100
    else:
        oversampling = 1
        
    if xml.find("oversampling") is not None:
        oversampling = int(xml.find("oversampling").text)

    if ((not can_oversample) and (oversampling > 1)):
        raise ShutterXMLException("This setup does not support oversampling.")

    # The length of the sequence.
    frames = int(xml.find("frames").text)

    # The user is using the channel names rather than their ID's to specify
    # the different channels.
    by_name = False
    if xml.find("by_name") is not None:
        by_name = bool(int(xml.find("by_name").text))

    #
    # We store a color to associate with each frame. This can be accessed by
    # other modules (such as the spot counter) to associate a color with the
    # a particular frame when, for example, updating the STORM image.
    #
    color_data = []
    for i in range(frames):
        color_data.append(None)

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
        channel = None
        power = None
        on = None
        off = None
        color = False
        for node in event:
            if (node.tag == "channel"):

                # Channels by name.
                if by_name:
                    if (node.text in channel_name_to_id):
                        channel = channel_name_to_id[node.text]
                    else:
                        raise ShutterXMLException("Invalid channel descriptor " + str(node.text))
                    
                # Channels by ID.
                else:
                    try:
                        channel = int(node.text)
                    except ValueError:
                        raise ShutterXMLException("Invalid channel number " + str(node.text))
                    
            elif (node.tag == "power"):
                try:
                    power = float(node.text)
                except ValueError:
                    raise ShutterXMLException("Invalid channel power " + str(node.text))                    
            elif (node.tag == "on"):
                try:
                    on = int(float(node.text) * float(oversampling))
                except ValueError:
                    raise ShutterXMLException("Invalid on time " + str(node.text))
            elif (node.tag == "off"):
                try:
                    off = int(float(node.text) * float(oversampling))
                except ValueError:
                    raise ShutterXMLException("Invalid off time " + str(node.text))
            elif (node.tag == "color"):
                color = []
                colors = node.text.split(",")
                if (len(colors) != 3):
                    raise ShutterXMLException("'" + node.text + "' is not a valid color descriptor.")
                for c in colors:
                    x = int(c)
                    if x < 0:
                        x = 0
                    if x > 255:
                        x = 255
                    color.append(x)

        # Check values.
        if channel is None:
            raise ShutterXMLException("Event channel must be specified.")
        if power is None:
            raise ShutterXMLException("Event power must be specified.")
        if on is None:
            raise ShutterXMLException("Event on time must be specified.")
        if off is None:
            raise ShutterXMLException("Event off time must be specified.")

        # Check range.
        if (channel < 0):
            raise ShutterXMLException("Channel number is negative: " + str(channel) + ".")
        if (channel >= number_channels):
            raise ShutterXMLException("Channel number is too large: " + str(channel) + ".")        
        if (on < 0):
            raise ShutterXMLException("On time out of range: " + str(on) + " in channel " + str(channel) + ".")
        if (on > frames * oversampling):
            raise ShutterXMLException("On time out of range: " + str(on) + " in channel " + str(channel) + ".")
        if (off < 0):
            raise ShutterXMLException("Off time out of range: " + str(on) + " in channel " + str(channel) + ".")
        if (off > frames * oversampling):
            raise ShutterXMLException("Off time out of range: " + str(on) + " in channel " + str(channel) + ".")

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

