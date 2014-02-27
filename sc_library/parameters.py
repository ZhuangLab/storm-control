#!/usr/bin/python
#
## @file
#
# Handles parsing settings xml files and getting/setting 
# the resulting settings. Primarily designed for use
# by the hal acquisition program.
#
# Hazen 02/14
#

import copy
import os
import traceback
import xml.etree.ElementTree as ElementTree

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

## fileType
#
# Based on the root tag, returns the XML file type.
#
# @param xml_file An XML file.
# 
# @returns An array containing "parameters", "shutters" or "unknown" as the first element and XML parsing errors (if any) as the second element.
#
def fileType(xml_file):
    try:
        xml = ElementTree.parse(xml_file).getroot()
        if (xml.tag == "settings"):
            return ["parameters", False]
        elif (xml.tag == "repeat"):
            return ["shutters", False]
        else:
            return ["unknown", False]
    except:
        return ["unknown", traceback.format_exc()]

## Hardware
#
# Parses a hardware file to create a hardware object.
#
# @param hardware_file The name of the XML file containing the hardware definitions.
#
# @return A hardware object.
#
def Hardware(hardware_file):
    xml = ElementTree.parse(hardware_file).getroot()
    assert xml.tag == "hardware", hardware_file + " is not a hardware file."

    # Create the hardware object.
    xml_object = StormXMLObject([])

    # Load camera information.
    camera_xml = xml.find("camera")
    xml_object.camera = StormXMLObject([])
    xml_object.camera.module = camera_xml.find("module").text
    xml_object.camera.parameters = StormXMLObject(camera_xml.find("parameters"))

    # Load modules.
    xml_object.modules = []
    for xml_module in xml.find("modules"):

        # Create module based on XML
        module = StormXMLObject(xml_module)
        xml_parameters = xml_module.find("parameters")
        if xml_parameters is not None:
            module.parameters = StormXMLObject(xml_parameters)
        else:
            module.parameters = None

        # Add addition properties
        module.hal_type = xml_module.tag
        if (hasattr(module, "menu_item")):
            module.hal_gui = True
        else:
            module.hal_gui = False

        xml_object.modules.append(module)

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
    xml = ElementTree.parse(parameters_file).getroot()
    assert xml.tag == "settings", parameters_file + " is not a setting file."

    # Read general settings
    xml_object = StormXMLObject(xml)

    # Read camera1/camera2 settings (only used with dual camera setups).
    camera1 = xml.find("camera1")
    if camera1:
        xml_object.camera1 = StormXMLObject(camera1)

    camera2 = xml.find("camera2")
    if camera2:
        xml_object.camera2 = StormXMLObject(camera2)

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
class StormXMLObject(object):

    ## __init__
    #
    # Dynamically create class based on xml data parsed with the minidom library.
    #
    # @param nodes A list of XML nodes.
    #
    def __init__(self, nodes):

#        self.attributes = {}
        self.warned = False

        # FIXME: someday this is going to cause a problem..
        max_channels = 8

        for node in nodes:
            #print node.tag, node.text
            slot = node.tag

            # Parse default power setting.
            if (slot == "default_power"):
                if not hasattr(self, "default_power"):
                    self.on_off_state = []
                    self.default_power = []
                    for i in range(max_channels):
                        self.default_power.append(1.0)
                        self.on_off_state.append(0)
                power = float(node.text)
                channel = int(node.attrib["channel"])
                self.default_power[channel] = power

            # power buttons
            elif (slot == "button"):
                if not hasattr(self, "power_buttons"):
                    self.power_buttons = []
                    for i in range(max_channels):
                        self.power_buttons.append([])
                channel = int(node.attrib["channel"])
                name = node.text
                power = float(node.attrib["power"])
                self.power_buttons[channel].append([name, power])

            # all the other settings
            elif node.attrib.get("type", 0):
                node_type = node.attrib["type"]
                node_value = node.text
                if (node_type == "int"):
                    setattr(self, slot, int(node_value))
                elif (node_type == "int-array"):
                    text_array = node_value.split(",")
                    int_array = []
                    for elt in text_array:
                        int_array.append(int(elt))
                    setattr(self, slot, int_array)
                elif (node_type == "float"):
                    setattr(self, slot, float(node_value))
                elif (node_type == "float-array"):
                    text_array = node_value.split(",")
                    float_array = []
                    for elt in text_array:
                        float_array.append(float(elt))
                    setattr(self, slot, float_array)
                elif (node_type == "string-array"):
                    setattr(self, slot, node_value.split(","))
                elif (node_type == "boolean"):
                    if node_value == "True":
                        setattr(self, slot, True)
                    else:
                        setattr(self, slot, False)
                # everything else is assumed to be a (non-unicode) string
                else: 
                    setattr(self, slot, str(node_value))

    ## __getattribute__
    #
    # This method is over-written for the purpose of logging which
    # attributes of an instance are actually used.
    #
    # @param name The name of the attribute to return the value of.
    #
    # @return The value of the requested attribute.
    #
#    def __getattribute__(self, name):
#        if hasattr(self, "attributes") and (name != "attributes"):
#            if (name in self.attributes):
#                self.attributes[name] += 1
#        return object.__getattribute__(self, name)

    ## __setattr__
    #
    # This method is over-written for the purpose of logging which
    # attributes were added to the class after instantiation.
    #
    # @param name The name of attribute to set the value of.
    # @param value The value to set the attribute to.
    #
#    def __setattr__(self, name, value):
#        object.__setattr__(self, name, value)
#        if (name != "attributes"):
#            self.attributes[name] = 0

    ## unused
    #
    # @return A list of the attributes in the instance that were never used.
    # 
#    def unused(self):
#        if not self.warned:
#            self.warned = True
#            not_used = []
#            for key, value in self.attributes.iteritems():
#                if (value == 0):
#                    not_used.append(key)
#            return not_used
#        else:
#            return []
    def unused(self):
        return []

#
# Testing
# 

if __name__ == "__main__":
    import sys

    if 0:
        test = Parameters(sys.argv[1])
        print test.setup_name
        print "1:", test.unused()
        print "2:", test.unused()

    if 0:
        test = Hardware(sys.argv[1])
        for k,v in test.__dict__.iteritems():
            print k

        for module in test.modules:
            for k,v in module.__dict__.iteritems():
                print k,v
            print ""

    if 1:
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
