#!/usr/bin/python
#
## @file
#
# Handles parsing settings xml files and getting/setting 
# the resulting settings. Primarily designed for use
# by the hal acquisition program.
#
# Hazen 06/15
#

import copy
import os
import traceback

from xml.dom import minidom
from xml.etree import ElementTree

default_params = 0

## copySettings
#
# Creates a new object which is a copy of the original with values
# that also exist in duplicate replaced with the values from
# duplicate.
#
# This is complicated somewhat by the fact that the duplicate
# settings might be "old" style, i.e. flat, or new style (which
# is only 1 level deep).
#
# @param original The original settings.
# @param duplicate The duplicate settings.
#
def copySettings(original, duplicate):
    settings = copy.deepcopy(original)

    for attr in settings.getAttrs():

        # Sub block parameter.
        if isinstance(settings.get(attr), StormXMLObject):
            sub_settings = settings.get(attr)

            # Duplicate also has sub blocks, only look in the same sub block.
            sub_duplicate = False
            if duplicate.get("_recursed_"):
                if duplicate.has(attr):
                    sub_duplicate = duplicate.get(attr)
            else:
                sub_duplicate = duplicate

            if sub_duplicate:
                for sub_attr in sub_settings.getAttrs():
                    if sub_duplicate.has(sub_attr):
                        sub_settings.set(sub_attr, sub_duplicate.get(sub_attr))

        # Main block parameter.
        else:
            if duplicate.has(attr):
                settings.set(attr, duplicate.get(attr))
    
    if duplicate.hasUnused():
        raise ParametersException("Unrecognized settings " + ",".join(map(lambda(x): "'" + str(x) + "'", duplicate.getUnused())))
                        
    return settings

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

## halParameters
#
# Parses a parameters file to create a parameters object specifically for HAL.
#
# @param parameters_file The name of the XML file containing the parameter definitions.
#
# @return A parameters object.
#
def halParameters(parameters_file):

    # Read general settings
    xml_object = Parameters(parameters_file)

    #
    # In the process of creating the complete parameters object we can
    # overwrite the use_as_default value, so we save it and then
    # resort it.
    #
    use_as_default = xml_object.get("use_as_default", False)
    
    global default_params
    if default_params:
        xml_object = copySettings(default_params, xml_object)

    if use_as_default or (not default_params):
        default_params = copy.deepcopy(xml_object)
    else:
        xml_object.set("use_as_default", False)
    
    # Define some camera specific derivative parameters
    for attr in ["camera", "camera1", "camera2"]:
        if xml_object.has(attr):
            setCameraParameters(xml_object.get(attr))

    # And a few random other things
    xml_object.set("seconds_per_frame", 0)
    xml_object.set("initialized", False)

    film_xml = xml_object.get("film")
    film_xml.set("notes", "")
    if not film_xml.has("extension"):
        film_xml.set("extension", film_xml.extensions[0])

    illumination_xml = xml_object.get("illumination")
    if not os.path.exists(illumination_xml.get("shutters")):
        illumination_xml.set("shutters", os.path.dirname(parameters_file) + "/" + illumination_xml.get("shutters"))

    illumination_xml.set("shutter_colors", [])
    illumination_xml.set("shutter_data", [])
    illumination_xml.set("shutter_frames", -1)
    illumination_xml.set("shutter_oversampling", 0)

    return xml_object

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
    if (xml.tag != "hardware"):
        raise ParametersException(hardware_file + " is not a hardware file.")

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
#
# @return A parameters object.
#
def Parameters(parameters_file):
    xml = ElementTree.parse(parameters_file).getroot()
    if (xml.tag != "settings"):
        raise ParameterException(parameters_file + " is not a setting file.")

    # Create XML object.
    xml_object = StormXMLObject(xml, True)
    xml_object.set("parameters_file", parameters_file)
    
    return xml_object

## setCameraParameters
#
# This sets some derived properties as well as some default properties of
# the camera part of the parameters object.
#
# @param camera A camera XML object.
#
def setCameraParameters(camera):
    
    camera.set("x_pixels", camera.get("x_end") - camera.get("x_start") + 1)
    camera.set("y_pixels", camera.get("y_end") - camera.get("y_start") + 1)
    if((camera.get("x_pixels") % 4) != 0):
        raise ParameterException("The camera ROI must be a multiple of 4 in x!")

    camera.set("ROI", [camera.get("x_start"),
                       camera.get("x_end"),
                       camera.get("y_start"),
                       camera.get("y_end")])
    camera.set("binning", [camera.get("x_bin"),
                           camera.get("y_bin")])

    camera.set("actual_temperature", 0)
    camera.set("exposure_time", 0)      # This is the actual exposure time.
    camera.set("cycle_time", 0)         # This is the time between frames.

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
    parameters.set("setup_name", setup_name)
    global default_params
    if default_params:
        default_params.set("setup_name", setup_name)


## ParametersException
#
# This is thrown when there is a problem with the parameters.
#
class ParametersException(Exception):

    ## __init__
    #
    # @param message The exception message.
    #
    def __init__(self, message):
        Exception.__init__(self, message)

        
## StormXMLObject
#
# A parameters object whose attributes are created dynamically
# by parsing an XML file. The use of the get() and set() methods
# is encouraged instead of direct property access via the dot.
#
class StormXMLObject(object):

    ## __init__
    #
    # Dynamically create class based on xml data.
    #
    # @param nodes A list of XML nodes.
    #
    def __init__(self, nodes, recurse = False):

        self._recursed_ = False
        self._unused_ = {}
        self._warned_ = False

        # FIXME: someday this is going to cause a problem..
        max_channels = 8

        for node in nodes:
            slot = node.tag

            # Parse default power setting.
            if (slot == "default_power"):
                if not hasattr(self, "default_power"):
                    self.create("on_off_state", [])
                    self.create("default_power", [])
                    for i in range(max_channels):
                        self.default_power.append(1.0)
                        self.on_off_state.append(0)
                power = float(node.text)
                channel = int(node.attrib["channel"])
                self.default_power[channel] = power

            # Power buttons.
            elif (slot == "button"):
                if not hasattr(self, "power_buttons"):
                    self.create("power_buttons", [])
                    for i in range(max_channels):
                        self.power_buttons.append([])
                channel = int(node.attrib["channel"])
                name = node.text
                power = float(node.attrib["power"])
                self.power_buttons[channel].append([name, power])

            # All the other settings.
            elif node.attrib.get("type", False):
                node_type = node.attrib["type"]
                node_value = node.text
                if (node_type == "int"):
                    self.create(slot, int(node_value))
                elif (node_type == "int-array"):
                    text_array = node_value.split(",")
                    int_array = []
                    for elt in text_array:
                        int_array.append(int(elt))
                    self.create(slot, int_array)
                elif (node_type == "float"):
                    self.create(slot, float(node_value))
                elif (node_type == "float-array"):
                    text_array = node_value.split(",")
                    float_array = []
                    for elt in text_array:
                        float_array.append(float(elt))
                    self.create(slot, float_array)
                elif (node_type == "string-array"):
                    self.create(slot, node_value.split(","))
                elif (node_type == "boolean"):
                    if node_value == "True":
                        self.create(slot, True)
                    else:
                        self.create(slot, False)
                # everything else is assumed to be a (non-unicode) string
                else: 
                    self.create(slot, str(node_value))

            # Sub-node.
            elif recurse and (len(node) > 0):
                setattr(self, node.tag, StormXMLObject(node, True))
                self._recursed_ = True

    ## copy()
    #
    # @return A deep copy of this object.
    #
    def copy(self):
        return copy.deepcopy(self)

    ## create
    #
    # Create a property. This is basically the same as set, but it also
    # adds the property name to the list of unused properties.
    #
    # @param pname A string containing the property name.
    # @param value The value to set the property too.
    #
    def create(self, pname, value):
        self._unused_[pname] = True
        self.set(pname, value)

    ## diff
    #
    # Return the parameters that are different in another StormXMLObject from
    # those in the current object. This does not check recursively.
    #
    # @param other The other StormXMLObject.
    #
    # @return The names of the properties that are different.
    #
    def diff(self, other):
        diffs = []
        for pname in filter(lambda(x): not isinstance(self.get(x, mark_used = False), StormXMLObject), self.getAttrs()):
            if (self.get(pname) != other.get(pname)):
                diffs.append(pname)
        return diffs
                        
    ## get
    #
    # Get a property of this object.
    #
    # @param pname A string containing the property name.
    # @param default (Optional) The value to use if the property is not found.
    #
    # @return The propery if found, otherwise default.
    #
    def get(self, pname, default = None, mark_used = True):

        # Check for sub-property.
        pnames = pname.split(".")
        if (len(pnames) > 1):
            xml_object = self.get(pnames[0])
            return xml_object.get(".".join(pnames[1:]), default, mark_used)

        if hasattr(self, pname):
            if mark_used:
                self.isUsed(pname)
            return getattr(self, pname)
        else:
            if default is not None:
                return default
            else:
                raise ParametersException("Requested property " + pname + " not found and no default was specified.")

    ## getAttrs
    #
    # Return the "relevant" attributes of the object, i.e. the ones that
    # are not internal or callable.
    #
    # @return A list of attributes.
    #
    def getAttrs(self):
        attrs = filter(lambda(x): x[0] != "_", sorted(dir(self)))
        return filter(lambda(x): not callable(self.get(x, mark_used = False)), attrs)

    ## getSubXMLObjects
    #
    # Return a list of the sub StormXMLObjects of the current object.
    #
    # @return A list of StormXMLObjects.
    #
    def getSubXMLObjects(self):
        return map(lambda(x): self.get(x), filter(lambda(y): isinstance(self.get(y, mark_used = False), StormXMLObject), self.getAttrs()))

    ## getUnused
    #
    # Returns a list of all unused parameters.
    #
    # @return The list of unused parameters.
    #
    def getUnused(self):
        unused = filter(lambda(x): self._unused_[x], self._unused_.keys())
        for elt in self.getSubXMLObjects():
            unused = unused + elt.getUnused()
        return unused
                
    ## has
    #
    # Return true if this object has a particular property.
    #
    # @param pname A string containing the property name.
    #
    # @return True if found, otherwise False.
    #
    def has(self, pname):

        # Check for sub-property.
        pnames = pname.split(".")
        if (len(pnames) > 1):
            xml_object = self.get(pnames[0])
            return xml_object.has(".".join(pnames[1:]))

        if hasattr(self, pname):
            self.isUsed(pname)
            return True
        else:
            return False

    ## hasUnused
    #
    # Returns True is there are unused parameters.
    #
    # @return True / False
    #
    def hasUnused(self):

        # Check current level.
        for key in self._unused_:
            if self._unused_[key]:
                return True

        # Check lower levels.
        for elt in self.getSubXMLObjects():
            if elt.hasUnused():
                return True
            
        return False
    
    ## isUsed
    #
    # Remove a property from the _unused_ list.
    #
    # @param pname The name of the property.
    #
    def isUsed(self, pname):
        if pname in self._unused_:
            self._unused_[pname] = False

    ## saveToFile
    #
    # Save the settings as XML in a file.
    #
    # @param filename The name of the file to save settings in.
    #
    def saveToFile(self, filename):
        rough_string = ElementTree.tostring(self.toXML())
        reparsed = minidom.parseString(rough_string)
        with open(filename, "w") as fp:
            fp.write(reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1"))
    
    ## set
    #
    # Set a property (or properties) of this object.
    #
    # @param pname A string containing the property name.
    # @param value The value to set the property too.
    #
    def set(self, pname, value):

        # Check for list of pnames and values.
        if isinstance(pname, list):
            if (len(pname) == len(value)):
                for i in range(len(pname)):
                    self.set(pname[i], value[i])
            else:
                raise ParameterException("Lengths do not match in parameters multi-set. " + str(len(pname)) + ", " + str(len(value)))
            return
        
        # Check for sub-property.
        pnames = pname.split(".")
        if (len(pnames) > 1):
            self.get(pnames[0]).set(".".join(pnames[1:]), value)
        else:
            setattr(self, pname, value)

    ## toXML
    #
    # Return an XML representation of this object.
    #
    # @param name (optional) The tag attribute to use for the current block of XML.
    #
    def toXML(self, name = "settings"):
        xml = ElementTree.Element(name)
        for attr in self.getAttrs():
            value = self.get(attr)
            if isinstance(value, StormXMLObject):
                xml.append(value.toXML(attr))
            else:

                # Don't save the following.
                if attr in ["shutter_colors", "shutter_data"]:
                    continue
                
                # Handle default power settings.
                if (attr == "default_power"):
                    for i, elt in enumerate(value):
                        field = ElementTree.SubElement(xml, attr)
                        field.set("channel", str(i))
                        field.text = str(elt)

                # Handle power buttons.
                elif (attr == "power_buttons"):
                    for i, elt in enumerate(value):
                        for sub_elt in elt:
                            field = ElementTree.SubElement(xml, "button")
                            field.set("channel", str(i))
                            field.set("power", str(sub_elt[1]))
                            field.text = sub_elt[0]

                # Lists.
                elif isinstance(value, list):
                    if (len(value) > 0) and isinstance(value[0], int):
                        list_type = "int-array"
                    elif (len(value) > 0) and isinstance(value[0], float):
                        list_type = "float-array"
                    else:
                        list_type = "string-array"

                    field = ElementTree.SubElement(xml, attr)
                    field.set("type", list_type)
                    field.text = ",".join(map(str, value))
                        
                # Everything else:
                else:
                    field = ElementTree.SubElement(xml, attr)
                    field.set("type", str(type(value).__name__))
                    field.text = str(value)

        return xml

    ## unused
    #
    # @return A list of the attributes in the instance that were never used.
    # 
    def unused(self):
        return []

#
# Testing
# 

if __name__ == "__main__":

    import sys

    from xml.dom import minidom
    
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
        p1 = halParameters(sys.argv[1]).get("camera1")
        p2 = halParameters(sys.argv[2]).get("camera1")
        for diff in p2.diff(p1):
            print diff, p1.get(diff), p2.get(diff)

#        string = ElementTree.tostring(p2.toXML(), 'utf-8')
#        reparsed = minidom.parseString(string)
#        print reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1")
        
#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
