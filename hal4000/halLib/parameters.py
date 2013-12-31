#!/usr/bin/python
#
## @file
#
# Handles parsing settings xml files and getting/setting 
# the resulting settings. Primarily designed for use
# by the hal acquisition program.
#
# Hazen 12/12
#

import copy
import os
from xml.dom import minidom, Node

default_params = 0

## copyAttributes
#
# Copy the attributes from the original object to the duplicate
# object, but only if the duplicate object does not already have
# an attribute of the same name.
#
# @param original The original object.
# @param duplicate The duplicate object.
#
def copyAttributes(original, duplicate):
    for k, v in original.__dict__.iteritems():
        if not hasattr(duplicate, k):
            setattr(duplicate, k, copy.copy(v))

## Hardware
#
# Parses a hardware file to create a hardware object.
#
# @param hardware_file The name of the XML file containing the hardware definitions.
#
# @return A hardware object.
#
def Hardware(hardware_file):
    xml = minidom.parse(hardware_file)

    # Create the hardware object.
    xml_object = StormXMLObject([])

    hardware_types = ["camera",
                      "focuslock",
                      "illumination",
                      "joystick",
                      "misc_control",
                      "shutters",
                      "stage",
                      "temperature_logger"]
    for h_type in hardware_types:
        h_xml = xml.getElementsByTagName(h_type).item(0)
        if h_xml:
            h_object = StormXMLObject(h_xml.childNodes)
            h_params_xml = h_xml.getElementsByTagName("parameters").item(0)
            if h_params_xml:
                h_object.parameters = StormXMLObject(h_params_xml.childNodes)
            else:
                h_object.parameters = False
            setattr(xml_object, h_type, h_object)

    return xml_object

## Parameters
#
# Parses a parameters file to create a parameters object.
#
# @param parameters_file The name of the XML file containing the parameter definitions.
# @param is_HAL (Optional) True/False HAL specific processing needs to be done.
#
# @return A parameters object.
#
def Parameters(parameters_file, is_HAL = False):
    xml = minidom.parse(parameters_file)

    # Read general settings
    settings = xml.getElementsByTagName("settings").item(0)
    xml_object = StormXMLObject(settings.childNodes)

    # Read camera1/camera2 settings (only used with dual camera setups).
    camera1 = xml.getElementsByTagName("camera1").item(0)
    if camera1:
        xml_object.camera1 = StormXMLObject(camera1.childNodes)

    camera2 = xml.getElementsByTagName("camera2").item(0)
    if camera2:
        xml_object.camera2 = StormXMLObject(camera2.childNodes)

    xml_object.parameters_file = parameters_file

    if (is_HAL):
        #
        # Perform HAL acquisition program specific modifications
        #
        # Store as the default, if the default does not exist.
        # If the default does exist, then fill in all the
        # missing parameters with values from the default.
        # This way only the default starting file has to have all
        # the parameters.
        #
        use_as_default = 0
        if hasattr(xml_object, "use_as_default"):
            use_as_default = xml_object.use_as_default

        global default_params
        if default_params:
            copyAttributes(default_params, xml_object)
            if hasattr(xml_object, "camera1"):
                copyAttributes(default_params.camera1, xml_object.camera1)
                copyAttributes(default_params.camera2, xml_object.camera2)
        
        if use_as_default or (not default_params):
            default_params = copy.deepcopy(xml_object)

        # Define some camera specific derivative parameters
        if hasattr(xml_object, "camera1"):
            setCameraParameters(xml_object.camera1)
            setCameraParameters(xml_object.camera2)
            xml_object.exposure_value = 0
            xml_object.accumulate_value = 0
            xml_object.kinetic_value = 0
        else:
            setCameraParameters(xml_object)

        # And a few random other things
        xml_object.notes = ""
        if not hasattr(xml_object, "extension"):
            xml_object.extension = xml_object.extensions[0]

        if not os.path.exists(xml_object.shutters):
            xml_object.shutters = os.path.dirname(parameters_file) + "/" + xml_object.shutters

        xml_object.parameters_file = parameters_file

    return xml_object

## setCameraParameters
#
# This sets some derived properties as well as some default properties of
# the camera part of the parameters object.
#
# @param camera A camera XML object.
#
def setCameraParameters(camera):
    camera.x_pixels = camera.x_end - camera.x_start + 1
    camera.y_pixels = camera.y_end - camera.y_start + 1
    if((camera.x_pixels % 4) != 0):
        raise AssertionError, "The camera ROI must be a multiple of 4 in x!"

    camera.ROI = [camera.x_start, camera.x_end, camera.y_start, camera.y_end]
    camera.binning = [camera.x_bin, camera.y_bin]

    camera.exposure_value = 0
    camera.accumulate_value = 0
    camera.kinetic_value = 0
    camera.bytesPerFrame = 2 * camera.x_pixels * camera.y_pixels/(camera.x_bin * camera.y_bin)
    camera.actual_temperature = 0

## setDefaultShutters
#
# This sets the shutter name parameter of the default parameters object.
#
# @param shutters_filename The name of the shutter file to use as the default.
#
def setDefaultShutter(shutters_filename):
    global default_params
    if default_params:
        default_params.shutters = shutters_filename

## setSetupName
#
# This sets the setup name parameter of a parameters object and the default parameters object.
#
# @param parameters A parameters object.
# @param setup_name The name of the setup, e.g. "none", "prism2".
#
def setSetupName(parameters, setup_name):
    parameters.setup_name = setup_name
    global default_params
    if default_params:
        default_params.setup_name = setup_name

## StormXMLObject
#
# A parameters object whose attributes are created dynamically
# by parsing an XML file.
#
class StormXMLObject:

    ## __init__
    #
    # Dynamically create class based on xml data parsed with the minidom library.
    #
    # @param nodes A list of XML nodes.
    #
    def __init__(self, nodes):

        # FIXME: someday this is going to cause a problem..
        max_channels = 8

        for node in nodes:
            if (node.nodeType == Node.ELEMENT_NODE):
                slot = node.nodeName

                # single parameter setting
                if len(node.childNodes) == 1:
                    # default power settings
                    if slot == "default_power":
                        if not hasattr(self, "default_power"):
                            self.on_off_state = []
                            self.default_power = []
                            for i in range(max_channels):
                                self.default_power.append(1.0)
                                self.on_off_state.append(0)
                        power = float(node.firstChild.nodeValue)
                        channel = int(node.attributes.item(0).value)
                        self.default_power[channel] = power
                    # power buttons
                    elif slot == "button":
                        if not hasattr(self, "power_buttons"):
                            self.power_buttons = []
                            for i in range(max_channels):
                                self.power_buttons.append([])
                        name = node.firstChild.nodeValue
                        channel = int(node.attributes.item(1).value)
                        power = float(node.attributes.item(0).value)
                        self.power_buttons[channel].append([name, power])
                    # all the other settings
                    else:
                        value = node.firstChild.nodeValue
                        type = node.attributes.item(0).value
                        if type == "int":
                            setattr(self, slot, int(value))
                        elif type == "int-array":
                            text_array = value.split(",")
                            int_array = []
                            for elt in text_array:
                                int_array.append(int(elt))
                            setattr(self, slot, int_array)
                        elif type == "float":
                            setattr(self, slot, float(value))
                        elif type == "float-array":
                            text_array = value.split(",")
                            float_array = []
                            for elt in text_array:
                                float_array.append(float(elt))
                            setattr(self, slot, float_array)
                        elif type == "string-array":
                            setattr(self, slot, value.split(","))
                        else: # everything else is assumed to be a (non-unicode) string
                            setattr(self, slot, str(value))


#
# Testing
# 

if __name__ == "__main__":
    import sys

    if 1:
        test = Hardware(sys.argv[1])
        print dir(test)
        for k,v in test.__dict__.iteritems():
            print k

    if 0:
        test = Parameters(sys.argv[1], True)
        if hasattr(test, "x_start"):
            print test.x_start, test.x_end, test.x_pixels, test.frames
        else:
            print test.camera1.x_start, test.camera1.x_end
        print test.default_power, len(test.default_power)
        print test.power_buttons, len(test.power_buttons)


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
