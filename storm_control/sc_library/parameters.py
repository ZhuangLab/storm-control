#!/usr/bin/env python
"""
Handles parsing settings xml files and getting/setting 
the resulting settings.

Hazen 06/15
"""

import copy
import os
import traceback
import xml

from xml.dom import minidom
from xml.etree import ElementTree


#
# Functions.
#
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


def copyParameters(original_parameters, new_parameters):
    """
    Creates a new object which is a copy of the original with values
    that also exist in new_parameters replaced with the values from
    new_parameters. This is so that you don't have to specify all of
    the settings in new_parameters, just the ones that you want to
    update.
    """

    # Create.
    params = original_parameters.copy()
    copyParametersReplace("", params, new_parameters)

    # Check and add any new parameters.
    unrecognized = copyParametersAddNew(params, new_parameters, not new_parameters._validate_)
            
    return [params, unrecognized]


def copyParametersAddNew(original_parameters, new_parameters, allow_new):
    """
    A helper function for copyParameters().

    Copy parameters in new_parameters that did not exist in original_parameters. 
    If they don't already exist and are flagged with validate then add them to 
    the list of unrecognized parameters so that the user will know when they 
    have accidentally created new parameters.

    Notes:
    1. This assumes both parameters are tree style.
    2. Only sub-sections can be marked as validate, not
       individual parameters.
    """
    unrecognized = []
    for attr in new_parameters.getAttrs():

        prop = new_parameters.getp(attr)
        if isinstance(prop, StormXMLObject):
            if not original_parameters.has(attr):
                if allow_new or not prop._validate_:
                    original_parameters.addSubSection(attr)._validate_ = False
                else:
                    unrecognized.append(attr)
                    continue

            # Allow new parameters for all sub-objects.
            if allow_new:
                unrecognized.extend(copyParametersAddNew(original_parameters.get(attr),
                                                         prop,
                                                         True))

            # Otherwise it depends on the current objects _validate_ attribute.
            else:
                unrecognized.extend(copyParametersAddNew(original_parameters.get(attr),
                                                         prop,
                                                         not prop._validate_))

        else:
            if not original_parameters.has(attr):
                if allow_new:
                    original_parameters.addParameter(attr, prop)
                else:
                    unrecognized.append(attr)

    return unrecognized


def copyParametersReplace(root, original, new):
    """
    A helper function for copyParameters().

    This replaces all the parameters in original with their values
    from new, if new has a corresponding value. The idea is that
    the new parameters only need to specify what is different.

    Note: This no longer supports flat parameter trees for new.
    """
    for attr in original.getAttrs():

        prop = original.get(attr)

        # Recurse if this a branch.
        if isinstance(prop, StormXMLObject):
            if (len(root) > 0):
                copyParametersReplace(root + "." + attr, prop, new)
            else:
                copyParametersReplace(attr, prop, new)

        # Otherwise check for the corresponding node in new.
        else:
            attr_fullname = attr
            if (len(root) > 0):
                attr_fullname = root + "." + attr
            if new.has(attr_fullname):
                original.set(attr, new.get(attr_fullname))


def difference(params1, params2):
    """
    Return which parameters in params1 are different / don't 
    exist in params2.
    """
    differences = []
    
    def diffRecurse(root, p1, p2):
        for attr in p1.getAttrs():
            prop = p1.get(attr)

            if isinstance(prop, StormXMLObject):
                if p2.has(attr):
                    diffRecurse(root + attr + ".", prop, p2.get(attr))
                else:
                    differences.append(root + attr)
            else:
                if not p2.has(attr):
                    differences.append(root + attr)
                elif (prop != p2.get(attr)):
                    differences.append(root + attr)

    diffRecurse("", params1, params2)
    return differences

    
def fileType(xml_file):
    """
    Based on the root tag, returns the XML file type.
    """
    try:
        xml = ElementTree.parse(xml_file).getroot()
        if (xml.tag == "settings"):
            return ["parameters", False]
        elif (xml.tag == "repeat"):
            return ["shutters", False]
        else:
            return ["unknown", False]

    # FIXME: Don't catch all exceptions!
    except:
        return ["unknown", traceback.format_exc()]

    
def halParameters(parameters_file):
    """
    Parses a parameters file to create a parameters object specifically for HAL.
    """

    # Load parameters.
    xml_object = parameters(parameters_file, recurse = True)
    
    # Sometimes the user might drag in a parameters file that was
    # saved when taking a movie. Since some of the values were
    # specific to that movie we delete them (they are all in the
    # 'acquisition' section.
    xml_object.delete("acquisition")

    return xml_object


def parameters(parameters_file, recurse = False, add_filename_param = True):
    """
    Parses a parameters file to create a parameters object.
    """
    xml = ElementTree.parse(parameters_file).getroot()
    if (xml.tag != "settings"):
        raise ParametersException(parameters_file + " is not a setting file.")

    # Create XML object.
    xml_object = StormXMLObject(xml, recurse)
    if add_filename_param:
        xml_object.set("parameters_file", parameters_file)
    
    return xml_object


#
# Classes.
# 
class ParametersException(Exception):
    """
    This is thrown when there is a problem with the parameters.
    """
    pass

class ParametersExceptionGet(ParametersException):
    pass


class Parameter(object):
    """
    Base Parameter object.
    """
    def __init__(self,
                 description = "",
                 name = "",
                 value = None,
                 order = 1,
                 is_mutable = True,
                 is_saved = True,
                 **kwds):
        super().__init__(**kwds)

        self.description = description
        self.editor = None
        self.is_saved = is_saved
        self.is_mutable = is_mutable
        self.name = name
        self.order = order
        self.ptype = "string"
        self.value = None
        
        self.setv(value)

    def copy(self):
        return copy.deepcopy(self)
    
    def getDescription(self):
        return self.description

    def getEditor(self):
        return self.editor
    
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

    def setMutable(self, value):
        self.is_mutable = bool(value)

    def setOrder(self, new_order):
        self.order = new_order
        
    def setv(self, new_value):
        self.value = self.toType(new_value)

    def toString(self):
        return str(self.value)
    
    def toType(self, value):
        return value
        
    def toXML(self, parent, override_is_saved = False):
        if self.is_saved or override_is_saved:
            field = ElementTree.SubElement(parent, self.name)
            field.set("type", self.ptype)
            field.text = self.toString()
            return field

        
class ParameterCustom(Parameter):
    """
    This is a custom parameter whose editor and drawer will need
    to be set by its sub-class.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ptype = "custom"

        
class ParameterFloat(Parameter):
    """
    Floating point parameter.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.ptype = "float"

    def toType(self, new_value):
        return float(new_value)

        
class ParameterInt(Parameter):
    """
    Integer parameter.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.ptype = "int"

    def toType(self, new_value):
        return int(new_value)

        
class ParameterRange(Parameter):
    """
    Range parameter base class.
    """
    def __init__(self, min_value = 0.0, max_value = 1.0, **kwds):
        self.setMaximum(max_value)
        self.setMinimum(min_value)
        super().__init__(**kwds)

    def getMaximum(self):
        return self.max_value
    
    def getMinimum(self):
        return self.min_value

    def isRange(self):
        return True

    def setMaximum(self, new_maximum):
        self.max_value = self.toType(new_maximum)

    def setMinimum(self, new_minimum):
        self.min_value = self.toType(new_minimum)

    def setv(self, new_value):
        new_value = self.toType(new_value)
        if (new_value < self.min_value):
            self.value = self.min_value
        elif (new_value > self.max_value):
            self.value = self.max_value
        else:
            self.value = new_value

            
class ParameterRangeFloat(ParameterRange):
    """
    Float range parameter.
    """
    def __init__(self, decimals = 2, **kwds):
        super().__init__(**kwds)
        self.decimals = decimals
        self.ptype = "float"

    def getDecimals(self):
        return self.decimals
    
    def toType(self, value):
        return float(value)

        
class ParameterRangeInt(ParameterRange):
    """
    Integer range parameter
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.ptype = "int"

    def toType(self, value):
        return int(value)
    

class ParameterSet(Parameter):
    """
    Base class for sets.

    Note: sub-classes need to create the 'allowed' attribute.
    """
    
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def getAllowed(self):
        return self.allowed
    
    def isSet(self):
        return True

    def setAllowed(self, allowed):
        self.allowed = allowed
        
    def setv(self, new_value):
        new_value = self.toType(new_value)
        if new_value in self.allowed:
            self.value = new_value
        else:
            msg = "'" + str(new_value) + "' is not in the list of allowed values for "
            msg += self.name + ", " + str(self.allowed)
            raise ParametersException(msg)

            
class ParameterSetBoolean(ParameterSet):
    """
    Boolean set.
    """
    def __init__(self, **kwds):
        self.allowed = [True, False]
        super().__init__(**kwds)
        self.ptype = "boolean"

    def toType(self, value):
        if isinstance(value, int):
            return bool(value)
        elif isinstance(value, bool):
            return value
        elif (value == "0") or (value.lower() == "false"):
            return False
        else:
            return True
        

class ParameterSetFloat(ParameterSet):
    """
    Floats set.
    """
    def __init__(self, allowed = [], **kwds):
        self.allowed = list(map(float, allowed))
        super().__init__(**kwds)
        self.ptype = "float"

    def toType(self, value):
        return float(value)
        
    
class ParameterSetInt(ParameterSet):
    """
    Integers set.
    """
    def __init__(self, allowed = [], **kwds):
        self.allowed = list(map(int, allowed))
        super().__init__(**kwds)
        self.ptype = "int"
        
    def toType(self, new_value):
        return int(new_value)


class ParameterSetString(ParameterSet):
    """
    Strings set.
    """
    def __init__(self, allowed = [], **kwds):
        self.allowed = list(map(str, allowed))
        super().__init__(**kwds)

    def toType(self, new_value):
        if new_value is None:
            return ''
        else:
            return str(new_value)


class ParameterSimple(Parameter):
    """
    A simple parameter constructor
    """
    def __init__(self, name, value):
        kwds = {"name" : name,
                "value" : value,
                "is_mutable" : False,
                "is_saved" : False}
        super().__init__(**kwds)

        
class ParameterString(Parameter):
    """
    String parameter.
    """
    def toType(self, new_value):
        if new_value is None:
            return ''
        else:
            return str(new_value)
        

class ParameterStringDirectory(ParameterString):
    """
    This is parameter whose contents are the name of a directory.
    """
    pass


class ParameterStringFilename(ParameterString):
    """
    This is parameter whose contents are the name of a file.
    """
    def __init__(self, use_save_dialog = True, **kwds):
        super().__init__(**kwds)

        # Whether we should use a file open or a file save dialog.
        self.use_save_dialog = use_save_dialog


class StormXMLObject(object):
    """
    A collection of Parameters objects that are (usually) created 
    dynamically by parsing an XML file. All parameter names must 
    be unique for each section.
    """
    def __init__(self, nodes = None, recurse = False, validate = True, **kwds):
        super().__init__(**kwds)

        self._validate_ = validate
        self.parameters = {}

        if nodes is None:
            return

        if isinstance(nodes, ElementTree.Element):
            #
            # Check for both 'is_new' and 'validate'. 'is_new' is what we used
            # to call the flag to run checks when loading new parameters file
            # in HAL before we decided that this was a bad / confusing name
            # and changed it to 'validate'.
            #
            self._validate_ = not bool(nodes.attrib.get("is_new", self._validate_))
            self._validate_ = bool(nodes.attrib.get("validate", self._validate_))
            

        for node in nodes:
            param = None
            
            #
            # These are settings as specified in the defaul xml file. This will
            # (hopefully) provide a complete specification for each Parameter.
            #
            if node.attrib.get("type", False):
                node_type = node.attrib.get("type")
                kwds = {"name" : node.tag,
                        "value" : node.text,
                        "description" : node.attrib.get("desc", "None"),
                        "is_mutable" : (node.attrib.get("mutable", "true").lower() == "true"),
                        "order" : int(node.attrib.get("order", 1))}

                # Boolean
                if (node_type == "boolean"):
                    param = ParameterSetBoolean(**kwds)

                # Ranges.
                elif node.attrib.get("min", False):
                    kwds["min_value"] = node.attrib.get("min")
                    kwds["max_value"] = node.attrib.get("max")
                    if (node_type == "float"):
                        param = ParameterRangeFloat(**kwds)
                    elif (node_type == "int"):
                        param = ParameterRangeInt(**kwds)
                    else:
                        raise ParametersException("unrecognized range type, " + node_type)

                # Sets.
                elif node.attrib.get("values", False):
                    kwds["allowed"] = node.attrib.get("values").split(",")
                    if (node_type == "float"):
                        param = ParameterSetFloat(**kwds)
                    elif (node_type == "int"):
                        param = ParameterSetInt(**kwds)
                    elif (node_type == "string"):
                        param = ParameterSetString(**kwds)
                    else:
                        raise ParametersException("unrecognized set type, " + node_type)

                # The fallback if the element is not a set or a range.
                elif (node_type == "float"):
                    param = ParameterFloat(**kwds)

                elif (node_type == "int"):
                    param = ParameterInt(**kwds)

                # Other types of elements.
                elif (node_type == "custom"):
                    param = ParameterCustom(**kwds)

                elif (node_type == "directory"):
                    param = ParameterStringDirectory(**kwds)
                    
                elif (node_type == "filename"):
                    kwds["use_save_dialog"] = (node.attrib.get("use_save_dialog", "false").lower() == "true")
                    param = ParameterStringFilename(**kwds)

                elif (node_type == "string"):
                    param = ParameterString(**kwds)

                # These are deprecated and may disappear. They only remain so
                # that current Steve can read older data.
                elif (node_type == "float-array"):
                    param = ParameterCustom(**kwds)
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
                param = Parameter(description = "non_default", name = node.tag, value = node.text)

            # This handles sub-nodes.
            elif recurse and (len(node) > 0):
                self.parameters[node.tag] = StormXMLObject(node, True)

            # If we were able to make a parameter object add it to the record.
            if param is not None:
                self.addParameter(node.tag, param)

    def add(self, pname, pvalue = None):
        """
        Add a new Parameter to the parameters.
        """
        #
        # This lets us create parameters without having to specify
        # the name twice, which was really annoying..
        #
        if pvalue is None:
            if isinstance(pname, Parameter):
                pvalue = pname
                pname = pvalue.getName()
            else:
                raise ParametersException("pvalue for " + pname + " must be specified.")

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

    def addParameter(self, pname, pvalue):
        """
        Handles adding Parameters.
        """
        if pname in self.parameters:
            raise ParametersException("Parameter " + pname + " already exists.")
        else:
            if isinstance(pvalue, Parameter):
                self.parameters[pname] = pvalue
            else:
                self.parameters[pname] = ParameterSimple(pname, pvalue)

    def addSubSection(self, sname, svalue = None, overwrite = False):
        """
        Add a sub-section if it doesn't already exist. 

        If the optional svalue is specified and it is a StormXMLObject 
        then it will be used to initialize the new sub section.

        If the section already exists and overwrite is False then you
        will get an exception.
        """
        snames = sname.split(".")
        if (len(snames) > 1):
            if not snames[0] in self.parameters:
                cur_section = self.parameters[snames[0]] = StormXMLObject()
            else:
                cur_section = self.parameters[snames[0]]
            return cur_section.addSubSection(".".join(snames[1:]),
                                             svalue = svalue,
                                             overwrite = overwrite)
        else:
            if not sname in self.parameters:
                if isinstance(svalue, StormXMLObject):
                    self.parameters[sname] = svalue
                else:
                    self.parameters[sname] = StormXMLObject()
            else:
                if not overwrite:
                    raise ParametersException("Section " + sname + " already exists")
                if isinstance(svalue, StormXMLObject):
                    self.parameters[sname] = svalue
                else:
                    raise ParametersException("Object is a " + type(svalue) + " not a StormXMLObject")

            return self.parameters[sname]

    def copy(self):
        return copy.deepcopy(self)

    def delete(self, name):
        """
        Remove a sub-section or parameter (if it exists).
        """
        if self.has(name):
            names = name.split(".")
            if (len(names) > 1):
                self.get(".".join(names[:-1])).delete(names[-1])
            else:
                del self.parameters[name]

    def get(self, pname, default = None):
        """
        Returns either the value of the Parameter object specified by pname or
        the corresponding StormXMLObject.
        """
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

    def getAttrs(self):
        """
        Return a list of the property names.
        """
        return self.parameters.keys()

    def getOrder(self):
        """
        A convience so that we can sort these along with Parameter objects.
        """
        return 0
        
    def getp(self, pname):
        """
        Return the property specified by pname.
        """
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

    def getProps(self):
        """
        Return all the properties.
        """
        return self.parameters.values()

    def getSortedAttrs(self):
        """
        Return attributes sorted by order, then by name.
        """
        attrs = self.parameters.keys()
        return sorted(attrs, key = lambda x: (self.parameters[x].getOrder(), x))

    def has(self, pname):
        """
        Return true if this object has a particular Parameter.
        """
        try:
            prop = self.getp(pname)
        except ParametersExceptionGet:
            return False
        return True

    def saveToFile(self, filename, all_params = False):
        """
        Save the Parameters as XML in a file.
        """
        with open(filename, "w") as fp:
            fp.write(self.toString(all_params = all_params))

    def set(self, pname, pvalue):
        """
        FIXME: This is probably bad name as it is also a Python intrinsic.
        """
        # Check for list of pnames and values.
        if isinstance(pname, list):
            if (len(pname) == len(pvalue)):
                for i in range(len(pname)):
                    self.set(pname[i], pvalue[i])
            else:
                msg = "Lengths do not match in parameters multi-set. "
                msg += str(len(pname)) + ", " + str(len(pvalue))
                raise ParametersException(msg)
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

    def setv(self, pname, value):
        """
        Set a Parameters (or Parameters). This is different from
        set() in that it will throw an error if the parameter
        does not already exist.
        """
        
        # Check for list of pnames and values.
        if isinstance(pname, list):
            if (len(pname) == len(value)):
                for i in range(len(pname)):
                    self.setv(pname[i], value[i])
            else:
                msg = "Lengths do not match in parameters multi-set. "
                msg += str(len(pname)) + ", " + str(len(value))
                raise ParametersException(msg)
            return

        self.getp(pname).setv(value)

    def toString(self, all_params = False):
        """
        Return an XML string representation of this object.
        """
        rough_string = ElementTree.tostring(self.toXML(override_is_saved = all_params))
        try:
            reparsed = minidom.parseString(rough_string)
        except xml.parsers.expat.ExpatError as exception:
            print(rough_string)
            raise exception
        return reparsed.toprettyxml(indent = "  ", encoding = "ISO-8859-1").decode()

    def toXML(self, xml = None, name = "settings", override_is_saved = False):
        """
        Return an XML representation of this object.

        Use override_is_saved = True to get all of the parameters.
        """
        if xml is None:
            xml = ElementTree.Element(name)
        for key in sorted(self.parameters):
            value = self.parameters[key]
            if isinstance(value, StormXMLObject):
                child = ElementTree.SubElement(xml, key)
                child.set("validate", str(value._validate_))
                value.toXML(child, key, override_is_saved = override_is_saved)
                if (len(child) == 0):
                    xml.remove(child)
            else:
                value.toXML(xml, override_is_saved = override_is_saved)
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
