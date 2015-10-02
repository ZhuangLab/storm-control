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

from PyQt4 import QtCore, QtGui

default_params = 0

## copyParameters
#
# Creates a new object which is a copy of the original with values
# that also exist in new_parameters replaced with the values from
# new_parameters. This is so that you don't have to specify all of
# the settings in new_parameters, just the ones that you want to
# update.
#
# This is complicated somewhat by the fact that the new_parameters
# object might be "old" style, i.e. flat, or new style, i.e. a tree.
#
# @param ori_parameters The original parameters.
# @param new_parameters The new parameters.
#
def copyParameters(ori_parameters, new_parameters):

    # Create.
    params = copy.deepcopy(ori_parameters)
    copyParametersReplace("", params, new_parameters)

    # Check and add any new parameters.
    unrecognized = copyParametersCheck(params, new_parameters, new_parameters._is_new_)
    if (len(unrecognized) > 0):
        QtGui.QMessageBox.information(None,
                                      "Bad Parameters?",
                                      "The following parameters were not in the default list: " + ", ".join(unrecognized))

    return params

## copyParametersCheck
#
# Copy parameters in new_parameters that did not exist in
# ori_parameters. If they don't already exist and are not
# flagged with _is_new_ then add them to the list of
# unrecognized parameters.
#
# Notes
#  1. This assumes both parameters are tree style.
#  2. Only sub-sections can be marked as _is_new_, not
#     individual parameters.
#
# @param ori_parameters The original parameters.
# @param new_parameters The new parameters.
# @param allow_new Don't add new parameters to the unrecognized list.
#
# @return A list of the unrecognized parameters.
#
def copyParametersCheck(ori_parameters, new_parameters, allow_new):

    unrecognized = []
    for attr in new_parameters.getAttrs():
            
        prop = new_parameters.get(attr, mark_used = False)
        if isinstance(prop, StormXMLObject):
            if not ori_parameters.has(attr):
                if prop._is_new_ or allow_new:
                    ori_parameters.set(attr, StormXMLObject([]))
                    temp = ori_parameters.get(attr)
                    temp._is_new_ = True
                else:
                    unrecognized.append(attr)
                    #raise ParametersException("Unrecognized new section " + attr)

            # Allow new parameters for all sub-objects.
            if allow_new:
                unrecognized.extend(copyParametersCheck(ori_parameters.get(attr), prop, True))
            else:
                unrecognized.extend(copyParametersCheck(ori_parameters.get(attr), prop, prop._is_new_))

        else:
            if not ori_parameters.has(attr):
                ori_parameters._create_(attr, prop)
                if not allow_new:
                    if attr in new_parameters.getUnused():
                        unrecognized.append(attr)
                        #raise ParametersException("Unrecognized new parameter " + attr)

    return unrecognized

## copyParametersReplace
#
# This replaces all the parameters in original with their values
# from new, if duplicate has a corresponding value.
#
# @param root The current root object, e.g, "" or "camera1", etc.
# @param original The original parameters object.
# @param new The new parameters object.
#
def copyParametersReplace(root, original, new):

    for attr in original.getAttrs():

        prop = original.get(attr)
        if isinstance(prop, StormXMLObject):
            if (len(root) > 0):
                copyParametersReplace(root + "." + attr, prop, new)
            else:
                copyParametersReplace(attr, prop, new)
                
        else:
            # New is also a tree.
            if (len(root) > 0) and new.has(root + "." + attr):
                    original.set(attr, new.get(root + "." + attr))

            # New is flat.
            elif new.has(attr):
                original.set(attr, new.get(attr))

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
    xml_object = parameters(parameters_file, True, True)

    #
    # In the process of creating the complete parameters object we can
    # overwrite the use_as_default value, so we save it and then
    # resort it.
    #
    use_as_default = xml_object.get("use_as_default", False)
    
    global default_params
    if default_params:
        xml_object = copyParameters(default_params, xml_object)

    # Define some camera specific derivative parameters.
    #
    # FIXME: We are assuming that there won't be more than 5 cameras..
    #
    for i in range(5):
        attr = "camera" + str(i+1)
        if xml_object.has(attr):
            setCameraParameters(xml_object.get(attr))

    # And a few random other things
    xml_object.set("seconds_per_frame", 0)
    xml_object.set("initialized", False)

    film_xml = xml_object.get("film")
    film_xml.set("notes", "")
    if not film_xml.has("extension"):
        film_xml.set("extension", film_xml.extensions[0])

    illumination_xml = xml_object.get("illumination", False)
    if illumination_xml:
        if not os.path.exists(illumination_xml.get("shutters")):
            illumination_xml.set("shutters", os.path.dirname(parameters_file) + "/" + illumination_xml.get("shutters"))

        illumination_xml.set("shutter_colors", [])
        illumination_xml.set("shutter_data", [])
        illumination_xml.set("shutter_frames", -1)
        illumination_xml.set("shutter_oversampling", 0)

    if use_as_default or (not default_params):
        default_params = copy.deepcopy(xml_object)
    else:
        xml_object.set("use_as_default", False)

    return xml_object

## hardware
#
# Parses a hardware file to create a hardware object.
#
# @param hardware_file The name of the XML file containing the hardware definitions.
#
# @return A hardware object.
#
def hardware(hardware_file):
    xml = ElementTree.parse(hardware_file).getroot()
    if (xml.tag != "hardware"):
        raise ParametersException(hardware_file + " is not a hardware file.")

    # Create the hardware object.
    hardware = StormXMLObject(xml, recurse = True)

    # Add some additional properties to the modules.
    modules = hardware.get("modules")
    for module_name in modules.getAttrs():
        module = modules.get(module_name)
        module.set("hal_type", module_name)
        if module.has("menu_item"):
            module.set("hal_gui", True)
        else:
            module.set("hal_gui", False)

    return hardware

## parameters
#
# Parses a parameters file to create a parameters object.
#
# @param parameters_file The name of the XML file containing the parameter definitions.
#
# @return A parameters object.
#
def parameters(parameters_file, recurse = False, skip_added = False):
    xml = ElementTree.parse(parameters_file).getroot()
    if (xml.tag != "settings"):
        raise ParameterException(parameters_file + " is not a setting file.")

    # Create XML object.
    xml_object = StormXMLObject(xml, recurse, skip_added)
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

    # This restriction is necessary because in order to display
    # pictures as QImages they need to 32 bit aligned.
    if((camera.get("x_pixels") % 4) != 0):
        raise ParametersException("The camera ROI must be a multiple of 4 in x!")

    camera.set("ROI", [camera.get("x_start"),
                       camera.get("x_end"),
                       camera.get("y_start"),
                       camera.get("y_end")])
    camera.set("binning", [camera.get("x_bin"),
                           camera.get("y_bin")])

    camera.set("actual_temperature", 0)
    camera.set("exposure_value", 0)      # This is the actual exposure time.
    camera.set("cycle_value", 0)         # This is the time between frames.

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
    def __init__(self, nodes, recurse = False, skip_added = False):

        if isinstance(nodes, ElementTree.Element):
            self._is_new_ = bool(nodes.attrib.get("is_new", False))
        else:
            self._is_new_ = False
        self._recursed_ = False
        self._unused_ = {}
        self._warned_ = False

        # FIXME: someday this is going to cause a problem..
        max_channels = 8

        for node in nodes:
            slot = node.tag

            #
            # If requested, skip added properties. These are typically
            # properties that were programmatically added to the object
            # later and are not an intrinsic part of a settings file.
            #
            if skip_added and node.attrib.get("added", False):
                continue
                
            # Parse default power setting.
            if (slot == "default_power"):
                if not hasattr(self, "default_power"):
                    self._create_("on_off_state", [])
                    self._create_("default_power", [])
                    for i in range(max_channels):
                        self.default_power.append(1.0)
                        self.on_off_state.append(0)
                power = float(node.text)
                channel = int(node.attrib["channel"])
                self.default_power[channel] = power

            # Power buttons.
            elif (slot == "button"):
                if not hasattr(self, "power_buttons"):
                    self._create_("power_buttons", [])
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
                if (node_type == "boolean") or (node_type == "bool"):
                    if node_value == "True":
                        self._create_(slot, True)
                    else:
                        self._create_(slot, False)
                        
                elif (node_type == "float") or (node_type == "float64"):
                    self._create_(slot, float(node_value))
                elif (node_type == "float-array"):
                    text_array = node_value.split(",")
                    float_array = []
                    for elt in text_array:
                        float_array.append(float(elt))
                    self._create_(slot, float_array)

                elif (node_type == "int"):
                    self._create_(slot, int(node_value))
                elif (node_type == "int-array"):
                    text_array = node_value.split(",")
                    int_array = []
                    for elt in text_array:
                        int_array.append(int(elt))
                    self._create_(slot, int_array)
                    
                elif (node_type == "string") or (node_type == "str"):
                    self._create_(slot, str(node_value))
                elif (node_type == "string-array"):
                    self._create_(slot, node_value.split(","))
                    
                elif (node_type == "unicode"):
                    self._create_(slot, str(node_value))
                else:
                    raise ParametersException("unrecognized type, " + node_type)

            # Sub-node.
            elif recurse and (len(node) > 0):
                setattr(self, node.tag, StormXMLObject(node, recurse, skip_added))
                self._recursed_ = True

    ## copy()
    #
    # @return A deep copy of this object.
    #
    def copy(self):
        return copy.deepcopy(self)

    ## _create_
    #
    # Create a property. This is basically the same as set, but it also
    # adds the property name to the dictionary of unused properties. The
    # dictionary of unused properties is also used to keep track of what
    # was part this object originally and what was added later. So the
    # value in the dictionary (True/False) specifies if the property was
    # used and the fact that it is in the dictionary at all means that
    # it was not added later using set.
    #
    # @param pname A string containing the property name.
    # @param value The value to set the property too.
    #
    def _create_(self, pname, value):
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
            try:
                xml_object = self.get(pnames[0])
            except ParametersException as e:
                if default is not None:
                    return default
                else:
                    raise e
            else:
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
            xml_object = self.get(pnames[0], False)
            if xml_object:
                return xml_object.has(".".join(pnames[1:]))
            else:
                return False

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
                temp = value.toXML(attr)
                temp.set("is_new", str(value._is_new_))
                xml.append(temp)
            else:

                # Don't save the following.
                if attr in ["shutter_colors", "shutter_data"]:
                    continue

                # Mark parameters that were added after XML object creation, as
                # we may want to handle these differently later. These are the
                # parameters that were created using "set" instead of "create".
                added = False
                if not attr in self._unused_:
                    added = True
                
                # Handle default power settings.
                if (attr == "default_power"):
                    for i, elt in enumerate(value):
                        field = ElementTree.SubElement(xml, attr)
                        field.set("channel", str(i))
                        field.text = str(elt)

                # Handle button on / off state.
                elif (attr == "on_off_state"):
                    field = ElementTree.SubElement(xml, attr)
                    field.set("type", "int-array")
                    field.text = ",".join(map(lambda(x): str(int(x)), value))
                    
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
                    if added:
                        field.set("added", str(True))
                    field.text = ",".join(map(str, value))
                        
                # Everything else:
                else:
                    field = ElementTree.SubElement(xml, attr)
                    field.set("type", str(type(value).__name__))
                    if added:
                        field.set("added", str(True))
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

if (__name__ == "__main__"):

    import sys

    from xml.dom import minidom

    p1 = halParameters(sys.argv[1])
    p2 = halParameters(sys.argv[2])

    string = ElementTree.tostring(p2.toXML(), 'utf-8')
    reparsed = minidom.parseString(string)
    print reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1")    

        
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
