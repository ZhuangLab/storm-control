#!/usr/bin/env python
"""
Handles parsing settings xml files and getting/setting 
the resulting settings.

Hazen 06/15
"""

import copy
import os
import traceback

from xml.dom import minidom
from xml.etree import ElementTree

from PyQt5 import QtCore, QtGui

default_params = 0


def config(config_file):
    """
    Parse a configuration file for a setup.
    """
    xml = ElementTree.parse(config_file).getroot()
    if (xml.tag != "config"):
        raise ParametersException(config_file + " is not a configuration file.")

    # Create the configuration object.
    config = StormXMLObject(nodes = xml, recurse = True)

    return config


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
    unrecognized = copyParametersAddNew(params, new_parameters, new_parameters._is_new_)
    if (len(unrecognized) > 0):
        if True:
            QtGui.QMessageBox.information(None,
                                          "Bad Parameters?",
                                          "The following parameters were not recognized: " + ", ".join(unrecognized) + ". Perhaps they are not in the correct sub-section?")
            #raise ParametersException("Unrecognized parameters.")
        else:
            print("The following parameters were not recognized: " + ", ".join(unrecognized))
            
    return params

## copyParametersAddNew
#
# Copy parameters in new_parameters that did not exist in
# ori_parameters. If they don't already exist and are not
# flagged with _is_new_ then add them to the list of
# unrecognized parameters so that the user will know when
# they have accidentally created new parameters.
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
def copyParametersAddNew(ori_parameters, new_parameters, allow_new):

    unrecognized = []
    for attr in new_parameters.getAttrs():

        prop = new_parameters.get(attr)
        if isinstance(prop, StormXMLObject):
            if not ori_parameters.has(attr):
                if prop._is_new_ or allow_new:
                    ori_parameters.addSubSection(attr)._is_new_ = True
                else:
                    unrecognized.append(attr)
                    continue
                    #raise ParametersException("Unrecognized new section " + attr)

            # Allow new parameters for all sub-objects.
            if allow_new:
                unrecognized.extend(copyParametersAddNew(ori_parameters.get(attr), prop, True))
            else:
                unrecognized.extend(copyParametersAddNew(ori_parameters.get(attr), prop, prop._is_new_))

        else:
            if not ori_parameters.has(attr):
                if allow_new:
                    ori_parameters.set(attr, prop)
                else:
                    unrecognized.append(attr)

    return unrecognized

## copyParametersReplace
#
# This replaces all the parameters in original with their values
# from new, if new has a corresponding value. The idea is that
# the new parameters only need to specify what is different.
#
# @param root The current root object, e.g, "" or "camera1", etc.
# @param original The original parameters object.
# @param new The new parameters object.
#
# Notes
#  1. For now this will also handle "old" flat style parameter
#     lists, thought that may change in the future.
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
    xml_object = parameters(parameters_file, True)

    # Sometimes the user might drag in a parameters file that was
    # saved when taking a movie. Since some of the values were
    # specific to that movie we delete them.
    xml_object.delete("acquisition")

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

## parameters
#
# Parses a parameters file to create a parameters object.
#
# @param parameters_file The name of the XML file containing the parameter definitions.
#
# @return A parameters object.
#
def parameters(parameters_file, recurse = False):
    xml = ElementTree.parse(parameters_file).getroot()
    if (xml.tag != "settings"):
        raise ParameterException(parameters_file + " is not a setting file.")

    # Create XML object.
    xml_object = StormXMLObject(xml, recurse)
    xml_object.set("parameters_file", parameters_file)
    
    return xml_object

## setDefaultParameters
#
# Use a copy of the specified parameters as the default parameters.
#
def setDefaultParameters(parameters):
    global default_params
    default_params = copy.deepcopy(parameters)
    
## setDefaultShutters
#
# This sets the shutter name parameter of the default parameters object.
#
# @param shutters_filename The name of the shutter file to use as the default.
#
def setDefaultShutter(shutters_filename):
    global default_params
    if default_params:
        default_params.set("shutters", shutters_filename)


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

class ParametersExceptionGet(ParametersException):
    pass


## Parameter
#
# A single parameter.
#
class Parameter(object):

    def __init__(self, description, name, value, order, is_mutable, is_saved):
        self.description = description
        self.is_saved = is_saved
        self.is_mutable = is_mutable
        self.name = name
        self.order = order
        self.ptype = "string"
        self.value = value
    
    def getDescription(self):
        return self.description

    def getName(self):
        return self.name
    
    def getOrder(self):
        return self.order
        
    def getv(self):
        return self.value

    def isMutable(self):
        return self.is_mutable
    
    def isRange(self):
        return False
    
    def isSet(self):
        return False

    def setv(self, new_value):
        self.value = new_value

    def toXML(self, parent):
        if self.is_saved:
            field = ElementTree.SubElement(parent, self.name)
            field.set("type", self.ptype)
            field.text = str(self.value)
            return field

        
## ParameterCustom
#
# This is a custom parameter whose behavior (i.e. it's editor)
# will be set by whichever module creates/uses it.
#
class ParameterCustom(Parameter):

    def __init__(self, description, name, value, order, is_mutable = True, is_saved = True):
        Parameter.__init__(self, description, name, value, order, is_mutable, is_saved)
        self.ptype = "custom"
        self.editor = None

        
## ParameterFloat
#
class ParameterFloat(Parameter):

    def __init__(self, description, name, value, order = 1, is_mutable = True, is_saved = True):
        Parameter.__init__(self, description, name, float(value), order, is_mutable, is_saved)
        self.ptype = "float"

    def setv(self, new_value):
        self.value = float(new_value)

        
## ParameterInt
#
class ParameterInt(Parameter):

    def __init__(self, description, name, value, order = 1, is_mutable = True, is_saved = True):
        Parameter.__init__(self, description, name, int(value), order, is_mutable, is_saved)
        self.ptype = "int"

    def setv(self, new_value):
        self.value = int(new_value)


## ParameterRange
#
class ParameterRange(Parameter):

    def __init__(self, description, name, value, min_value, max_value, order, is_mutable, is_saved):
        Parameter.__init__(self, description, name, value, order, is_mutable, is_saved)
        self.min_value = min_value
        self.max_value = max_value

    def getMaximum(self):
        return self.max_value
    
    def getMinimum(self):
        return self.min_value

    def isRange(self):
        return True

    def setMaximum(self, new_maximum):
        self.max_value = new_maximum

    def setMinimum(self, new_minimum):
        self.min_value = new_minimum

    def setv(self, new_value):
        if (new_value < self.min_value):
            self.value = self.min_value
        elif (new_value > self.max_value):
            self.value = self.max_value
        else:
            self.value = new_value


## ParameterRangeFloat
#
class ParameterRangeFloat(ParameterRange):

    def __init__(self, description, name, value, min_value, max_value, order = 1, is_mutable = True, is_saved = True):
        ParameterRange.__init__(self,
                                description,
                                name,
                                float(value),
                                float(min_value),
                                float(max_value),
                                order,
                                is_mutable,
                                is_saved)
        self.ptype = "float"
        
    def setv(self, new_value):
        ParameterRange.setv(self, float(new_value))
        
        
## ParameterRangeInt
#
class ParameterRangeInt(ParameterRange):
    
    def __init__(self, description, name, value, min_value, max_value, order = 1, is_mutable = True, is_saved = True):
        ParameterRange.__init__(self,
                                description,
                                name,
                                int(value),
                                int(min_value),
                                int(max_value),
                                order,
                                is_mutable,
                                is_saved)
        self.ptype = "int"

    def setv(self, new_value):
        ParameterRange.setv(self, int(new_value))

    
## ParameterSet
#
class ParameterSet(Parameter):

    def __init__(self, description, name, value, allowed, order, is_mutable, is_saved):
        Parameter.__init__(self, description, name, value, order, is_mutable, is_saved)
        self.allowed = allowed

    def getAllowed(self):
        return self.allowed
    
    def isSet(self):
        return True

    def setAllowed(self, allowed):
        self.allowed = allowed
        
    def setv(self, new_value):
        if new_value in self.allowed:
            self.value = new_value
        else:
            #for x in self.allowed:
            #    print len(x), len(new_value)
            #print self.name, self.allowed, "-", new_value, "-"
            raise ParametersException(str(new_value) + " is not in the list of allowed values for " + self.name + ", " + str(self.allowed))

            
## ParameterSetBoolean
#
class ParameterSetBoolean(ParameterSet):

    def __init__(self, description, name, value, order = 1, is_mutable = True, is_saved = True):
        allowed = [True, False]
        ParameterSet.__init__(self, description, name, self.parse(value), allowed, order, is_mutable, is_saved)
        self.ptype = "boolean"

    def parse(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, bool):
            return value
        elif (value == "0") or (value.lower() == "false"):
            return False
        else:
            return True
            
    def setv(self, new_value):
        ParameterSet.setv(self, self.parse(new_value))

        
## ParameterSetFloat
#
class ParameterSetFloat(ParameterSet):

    def __init__(self, description, name, value, allowed, order = 1, is_mutable = True, is_saved = True):
        allowed = list(map(float, allowed))
        ParameterSet.__init__(self, description, name, float(value), allowed, order, is_mutable, is_saved)
        self.ptype = "float"

    def setv(self, new_value):
        ParameterSet.setv(self, float(new_value))
        
    
## ParameterSetInt
#
class ParameterSetInt(ParameterSet):

    def __init__(self, description, name, value, allowed, order = 1, is_mutable = True, is_saved = True):
        allowed = list(map(int, allowed))
        ParameterSet.__init__(self, description, name, int(value), allowed, order, is_mutable, is_saved)
        self.ptype = "int"
        
    def setv(self, new_value):
        ParameterSet.setv(self, int(new_value))


## ParameterSetString
#
class ParameterSetString(ParameterSet):

    def __init__(self, description, name, value, allowed, order = 1, is_mutable = True, is_saved = True):
        allowed = list(map(str, allowed))
        if value is None:
            value = ''
        ParameterSet.__init__(self, description, name, str(value), allowed, order, is_mutable, is_saved)

    def setv(self, new_value):
        if new_value is None:
            new_value = ''
        ParameterSet.setv(self, str(new_value))
        

## ParameterSimple
#
class ParameterSimple(Parameter):

    def __init__(self, name, value):
        Parameter.__init__(self, "", name, value, 1, False, False)

        
## ParameterString
#
class ParameterString(Parameter):

    def __init__(self, description, name, value, order = 1, is_mutable = True, is_saved = True):
        if value is None:
            value = ''
        Parameter.__init__(self, description, name, str(value), order, is_mutable, is_saved)

    def setv(self, new_value):
        if new_value is None:
            new_value = ''
        Parameter.setv(self, str(new_value))


## ParameterStringDirectory
#
# This is parameter whose contents are the name of a directory.
#
class ParameterStringDirectory(ParameterString):
    pass


## ParameterStringFilename
#
# This is parameter whose contents are the name of a file.
#
class ParameterStringFilename(ParameterString):

    def __init__(self, description, name, value, use_save_dialog, order = 1, is_mutable = True, is_saved = True):

        # Whether we should use a file open or a file save dialog.
        self.use_save_dialog = use_save_dialog
        ParameterString.__init__(self, description, name, value, order, is_mutable, is_saved)


## StormXMLObject
#
# A collection of Parameters objects that are created dynamically
# by parsing an XML file. All parameter names must be unique for
# each section.
#
class StormXMLObject(object):

    ## __init__
    #
    # Dynamically create class based on xml data.
    #
    # @param nodes A list of XML nodes.
    #
    def __init__(self, nodes = None, recurse = False):

        self.parameters = {}

        if nodes is None:
            return
        
        if isinstance(nodes, ElementTree.Element):
            self._is_new_ = bool(nodes.attrib.get("is_new", False))
        else:
            self._is_new_ = False

        for node in nodes:
            param = None
            
            #
            # These are settings as specified in the defaul xml file. This will
            # (hopefully) provide a complete specification for each Parameter.
            #
            if node.attrib.get("type", False):
                description = node.attrib.get("desc", "None")
                mutable = (node.attrib.get("mutable", "true").lower() == "true")
                node_type = node.attrib.get("type")
                order = int(node.attrib.get("order", 1))

                # Boolean
                if (node_type == "boolean"):
                    param = ParameterSetBoolean(description,
                                                node.tag,
                                                node.text,
                                                order,
                                                mutable)

                # Ranges.
                elif node.attrib.get("min", False):
                    min_value = node.attrib.get("min")
                    max_value = node.attrib.get("max")
                    if (node_type == "float"):
                        param = ParameterRangeFloat(description,
                                                    node.tag,
                                                    node.text,
                                                    min_value,
                                                    max_value,
                                                    order,
                                                    mutable)
                    elif (node_type == "int"):
                        param = ParameterRangeInt(description,
                                                  node.tag,
                                                  node.text,
                                                  min_value,
                                                  max_value,
                                                  order,
                                                  mutable)
                    else:
                        raise ParametersException("unrecognized range type, " + node_type)

                # Sets.
                elif node.attrib.get("values", False):
                    allowed = node.attrib.get("values").split(",")
                    if (node_type == "float"):
                        param = ParameterSetFloat(description,
                                                  node.tag,
                                                  node.text,
                                                  allowed,
                                                  order,
                                                  mutable)
                    elif (node_type == "int"):
                        param = ParameterSetInt(description,
                                                node.tag,
                                                node.text,
                                                allowed,
                                                order,
                                                mutable)
                    elif (node_type == "string"):
                        param = ParameterSetString(description,
                                                   node.tag,
                                                   node.text,
                                                   allowed,
                                                   order,
                                                   mutable)
                    else:
                        raise ParametersException("unrecognized set type, " + node_type)

                # The fallback if the element is not a set or a range.
                elif (node_type == "float"):
                    param = ParameterFloat(description, node.tag, node.text, order, mutable)

                elif (node_type == "int"):
                    param = ParameterInt(description, node.tag, node.text, order, mutable)

                # Other types of elements.
                elif (node_type == "custom"):
                    param = ParameterCustom(description, node.tag, node.text, order, mutable)

                elif (node_type == "directory"):
                    param = ParameterStringDirectory(description, node.tag, node.text, order, mutable)
                    
                elif (node_type == "filename"):
                    if (node.attrib.get("use_save_dialog", "false").lower() == "true"):
                        param = ParameterStringFilename(description, node.tag, node.text, True, order, mutable)
                    else:
                        param = ParameterStringFilename(description, node.tag, node.text, False, order, mutable)

                elif (node_type == "string"):
                    param = ParameterString(description, node.tag, node.text, order, mutable)

                # These are deprecated and may disappear. They only remain so
                # that current Steve can read older data.
                elif (node_type == "float-array"):
                    param = ParameterCustom(description, node.tag, node.text, order, mutable)
                    print("Found deprecated parameter type: ", node_type )

                elif (node_type in ["float64", "int-array", "str", "string-array", "unicode", "bool"]):
                    print("Found deprecated parameter type: ", node_type, " ignoring.")

                else:
                    raise ParametersException("unrecognized type, " + node_type)

            # 
            # Settings from an (older) saved movie XML file which might not have parameter
            # type specifications. These must match an existing setting to be handled properly.
            #
            elif (len(node) == 0):
                param = Parameter("non_default", node.tag, node.text, 1, True, True)

            # This handles sub-nodes.
            elif recurse and (len(node) > 0):
                self.parameters[node.tag] = StormXMLObject(node, True)

            # If we were able to make a parameter object add it to the record.
            if param is not None:
                self.addParameter(node.tag, param)

    ## add
    #
    # Add a new Parameter to the parameters.
    #
    def add(self, pname, pvalue):
        pnames = pname.split(".")
        if (len(pnames) > 1):
            try:
                prop = self.get(pnames[0])
            except ParametersExceptionGet:
                self.addSubSection(pnames[0])
            prop = self.get(pnames[0])
            prop.add(".".join(pnames[1:]), pvalue)
        else:
            self.addParameter(pname, pvalue)

    ## addParameter
    #
    # Handles adding Parameters.
    #
    def addParameter(self, pname, pvalue):
        if pname in self.parameters:
            raise ParametersException("Parameter " + pname + " already exists.")
        else:
            if isinstance(pvalue, Parameter):
                self.parameters[pname] = pvalue
            else:
                self.parameters[pname] = ParameterSimple(pname, pvalue)

    ## addSubSection
    #
    # Add a sub-section if it doesn't already exist.
    #
    def addSubSection(self, sname):
        snames = sname.split(".")
        if (len(snames) > 1):
            self.get(".".join(snames[:-1])).addSubSection(sname[-1])
        else:
            if not sname in self.parameters:
                self.parameters[sname] = StormXMLObject([])
        return self.parameters[sname]
            
    ## copy
    #
    # @return A deep copy of this object.
    #
    def copy(self):
        return copy.deepcopy(self)

    ## delete
    #
    # Remove a sub-section or parameter (if it exists).
    #
    def delete(self, name):
        if self.has(name):
            names = name.split(".")
            if (len(names) > 1):
                self.get(".".join(names[:-1])).delete(names[-1])
            else:
                del self.parameters[name]

    ## get
    #
    # Returns either the value of the Parameter object specified by pname or
    # the corresponding StormXMLObject.
    #
    # @param pname A string containing the property name.
    # @param default (Optional) The value to use if the Parameter is not found.
    #
    # @return The value if found, otherwise default.
    #
    def get(self, pname, default = None):
        try:
            prop = self.getp(pname)
        except ParametersException:
            if default is not None:
                return default
            else:
                raise ParametersExceptionGet("Requested property " + pname + " not found and no default was specified.")
        else:
            if isinstance(prop, StormXMLObject):
                return prop
            else:
                return prop.getv()

    ## getAttrs
    #
    # @return a list of the property names.
    #
    def getAttrs(self):
        return self.parameters.keys()
                
    ## getp
    #
    # @return the property specified by pname.
    #
    def getp(self, pname):
        
        # Check for sub-property.
        pnames = pname.split(".")
        if (len(pnames) > 1):
            xml_object = self.getp(pnames[0])
            #print pnames, type(xml_object)
            return xml_object.getp(".".join(pnames[1:]))

        if pname in self.parameters:
            return self.parameters[pname]
        else:
            raise ParametersExceptionGet("Requested property " + pname + " not found")

    ## getProps
    #
    # @return all the properties.
    #
    def getProps(self):
        return self.parameters.values()
    
    ## has
    #
    # Return true if this object has a particular Parameter.
    #
    # @param pname A string containing the property name.
    #
    # @return True if found, otherwise False.
    #
    def has(self, pname):
        try:
            prop = self.getp(pname)
        except ParametersExceptionGet:
            return False
        return True

    ## saveToFile
    #
    # Save the Parameters as XML in a file.
    #
    # @param filename The name of the file to save settings in.
    #
    def saveToFile(self, filename):
        rough_string = ElementTree.tostring(self.toXML())
        reparsed = minidom.parseString(rough_string)
        with open(filename, "w") as fp:
            fp.write(reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1").decode())

    ## set
    #
    def set(self, pname, pvalue):

        # Check for list of pnames and values.
        if isinstance(pname, list):
            if (len(pname) == len(pvalue)):
                for i in range(len(pname)):
                    self.set(pname[i], pvalue[i])
            else:
                raise ParameterException("Lengths do not match in parameters multi-set. " + str(len(pname)) + ", " + str(len(pvalue)))
            return

        # If the parameter does not already exist a ParameterSimple
        # is created to hold the value of the parameter.
        try:
            temp = self.getp(pname)
            if isinstance(pvalue, Parameter):
                temp.setv(pvalue.getv())
            else:
                temp.setv(pvalue)
        except ParametersExceptionGet:
            self.add(pname, pvalue)

    ## setv
    #
    # Set a Parameters (or Parameters). This is different from
    # set() in that it will throw an error if the parameter
    # does not already exist.
    #
    # @param pname A string containing the Parameter name(s).
    # @param value The value(s) to set the Parameter too.
    #
    def setv(self, pname, value):

        # Check for list of pnames and values.
        if isinstance(pname, list):
            if (len(pname) == len(value)):
                for i in range(len(pname)):
                    self.setv(pname[i], value[i])
            else:
                raise ParameterException("Lengths do not match in parameters multi-set. " + str(len(pname)) + ", " + str(len(value)))
            return

        self.getp(pname).setv(value)

    ## toXML
    #
    # Return an XML representation of this object.
    #
    # @param name (optional) The tag attribute to use for the current block of XML.
    #
    def toXML(self, xml = None, name = "settings"):
        if xml is None:
            xml = ElementTree.Element(name)
        for key in sorted(self.parameters):
            value = self.parameters[key]
            if isinstance(value, StormXMLObject):
                child = ElementTree.SubElement(xml, key)
                child.set("is_new", str(value._is_new_))
                value.toXML(child, key)
                if (len(child) == 0):
                    xml.remove(child)
            else:
                value.toXML(xml)
        return xml


#
# Testing
# 

if (__name__ == "__main__"):

    import sys

    from xml.dom import minidom

    if True:
        p1 = halParameters(sys.argv[1])
        p2 = halParameters(sys.argv[2])

        string = ElementTree.tostring(p2.toXML(), 'utf-8')
        reparsed = minidom.parseString(string)
        print(reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1"))

    if False:
        pm = parameters(sys.argv[1], True)
        print(pm.get("film"))
        print(pm.get("film.directory"))
        
#        string = ElementTree.tostring(pm.toXML(), 'utf-8')
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
