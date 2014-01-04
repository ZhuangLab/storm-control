#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# An xml parser class that takes a sequence recipe xml file and converts it to
# a flat sequence file that can be read by Dave
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import os, sys, time
from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

# ----------------------------------------------------------------------------------------
# XML Recipe Parser Class
# ----------------------------------------------------------------------------------------
class XMLRecipeParser(QtGui.QWidget):
    def __init__(self, xml_filename = "", verbose = True, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        # Initialize local attributes
        self.xml_filename = xml_filename
        self.verbose = verbose
        self.main_element = []
        self.command_sequences = []
        self.items = []
        self.loop_names = []
        self.loop_variables = []
        self.loop_variable_names = []
        self.loop_iterator = []
        self.num_loop_elements = []
        self.flat_sequence = []
        self.item_names = []
        
        # Parse XML
        self.parseXML()

        # Create flat command sequence
        self.createFlatSequence()

    # ------------------------------------------------------------------------------------
    # Load and parse a XML file with defined sequence recipe
    # ------------------------------------------------------------------------------------
    def parseXML(self, xml_file_path = ""):
        # Handle passed file name
        if not xml_file_path == "":
            self.xml_filename = xml_file_path

        # Open a file dialog if no path is provided
        xml, self.xml_filename = self.loadXML(self.xml_filename, header = "Open Sequence Recipe File")

        # Extract main element
        self.main_element = xml.getroot()

        # Parse major components of recipe file
        for child in self.main_element:
            if child.tag == "command_sequence":
                self.command_sequences.append(child)
            if child.tag == "item":
                self.items.append(child)
                self.item_names.append(child.attrib["name"])
            if child.tag == "loop_variable":
                self.loop_variables.append(child)
                self.loop_variable_names.append(child.attrib["name"])

        # Reset loop variables
        for i in range(len(self.loop_variable_names)):
            self.loop_iterator.append(-1) 
        
        # Expand Loop Variables from File
        self.extractLoopVariablesFromFile()

        # Find and replace items in command_sequence
        for command_sequence in self.command_sequences:
            command_sequence = self.findAndReplaceItemsInElement(command_sequence)
        
        # Display parsing results
##        if self.verbose:
##            print self.command_sequences
##            self.printRecipeElements(self.command_sequences)
##            print self.items
##            self.printRecipeElements(self.items)
##            print self.loop_variables
##            self.printRecipeElements(self.loop_variables)

    # ------------------------------------------------------------------------------------
    # Find and replace items in command sequence
    # ------------------------------------------------------------------------------------        
    def createFlatSequence(self):
        self.flat_sequence = ElementTree.Element("sequence")
        self.flat_sequence_xml = ElementTree.ElementTree(element = self.flat_sequence)

        for command_sequence in self.command_sequences:
            for element in command_sequence:
                if element.tag == "loop":
                    self.appendElementsFromLoop(element)
                else:
                    print element
                    self.flat_sequence.append(element)

        print self.flat_sequence
        print ElementTree.tostring(self.flat_sequence)

    # ------------------------------------------------------------------------------------
    # Handle a loop
    # ------------------------------------------------------------------------------------        
    def appendElementsFromLoop(self, loop):
        # Initialize loop
        loop_name = loop.attrib["name"]
        print "starting: " + loop_name
        loop_ID = self.loop_variable_names.index(loop_name)
        variables = self.loop_variables[loop_ID]
                
        for local_iterator in range(len(variables)):
            self.loop_iterator[loop_ID] = local_iterator
            print self.loop_iterator
            for element in loop:
                if element.tag == "loop":
                    self.appendElementsFromLoop(element)
                elif element.tag == "variable_entry":
                    variable_name = element.attrib["name"]
                    variable_ID = self.loop_variable_names.index(variable_name)
                    loop_iterator = self.loop_iterator[variable_ID]
                    variable_entry = self.loop_variables[variable_ID][loop_iterator]
                    for entry in variable_entry:
                        self.flat_sequence.append(entry)
                
                else: # Check for internal variable_entry (slicing is crucial otherwise python replaces!)
                    self.flat_sequence.append(self.replaceInternalVariableEntries(element[:]))
        self.loop_iterator[loop_ID] = -1 # Reset not running flag
        
    # ------------------------------------------------------------------------------------
    # Handle a loop
    # ------------------------------------------------------------------------------------        
    def replaceInternalVariableEntries(self, elements):
        element_count = 0
        for [element_ID, element] in enumerate(elements):
            if element.tag == "variable_entry":
                variable_name = element.attrib["name"]
                loop_ID = self.loop_variable_names.index(variable_name)
                loop_iterator = self.loop_iterator[loop_ID]
                elements.remove(element)
                variable_entry = self.loop_variables[loop_ID][loop_iterator]
                print variable_entry
                for entry in variable_entry:
                    elements.insert(element_count, entry)
                    element_count += 1
            else:
                revised_element = self.replaceInternalVariableEntries(element)
                elements.remove(element)
                elements.insert(element_count, revised_element)
                element_count += 1
        return elements
    
    # ------------------------------------------------------------------------------------
    # Find and replace items in command sequence
    # ------------------------------------------------------------------------------------        
    def findAndReplaceItemsInElement(self, element):
        child_count = 0
        for [child_ID, child] in enumerate(element):
            if child.tag == "item":
                item_name = child.attrib["name"]
                item_ID = self.item_names.index(item_name)
                found_item = self.items[item_ID]
                # Remove current child
                element.remove(child)
                # Parse item children for <item> elements
                for [item_ID,item_child] in enumerate(found_item):
                    item_child = self.findAndReplaceItemsInElement(item_child) # See if there are nest items
                    element.insert(child_count, item_child) # Add parsed item
                    child_count += 1
            else: # See if the nodes children have an item
                element.remove(child)
                element.insert(child_count, self.findAndReplaceItemsInElement(child))
                child_count += 1
        return element

    # ------------------------------------------------------------------------------------
    # Create and XML dialog for loading xml file and return parsed xml
    # ------------------------------------------------------------------------------------        
    def loadXML(self, xml_file_path, header = "Open XML File"):
        if xml_file_path == "":
            temp_file_path = QtGui.QFileDialog.getOpenFileName(self, header, "*.xml")
            if os.path.isfile(temp_file_path):
                xml_file_path = temp_file_path
        try:
            xml = ElementTree.parse(xml_file_path)
            print xml
            if self.verbose: print "Parsing: " + xml_file_path
            return (xml, xml_file_path)
        except:
            print "Invalid file: " + xml_file_path
            return (None, "")

    # ------------------------------------------------------------------------------------
    # Parse loop variables and extract from file as needed
    # ------------------------------------------------------------------------------------        
    def extractLoopVariablesFromFile(self):     
        # Expand out loop variables
        for loop in self.loop_variables:
            path_to_xml = ""
            file_path_elements = loop.findall("file_path")
            for file_path_element in file_path_elements:
                path_to_xml = file_path_element.text
                if path_to_xml == None: path_to_xml = ""
                # Remove file path element from loop element
                loop.remove(file_path_element)
                
                loop_variable_xml, path_to_loop_variable_xml = self.loadXML(path_to_xml,
                                                                            header = "Open Loop Variable XML")
                loop_variables = loop_variable_xml.getroot()
                for loop_variable in loop_variables:
                    loop.append(loop_variable)
                if self.verbose:
                    print "Extracted loop variables from " + path_to_loop_variable_xml
                else:
                    if self.verbose:
                        print "Found empty <file_path> tag"

    # ------------------------------------------------------------------------------------
    # Print elements 
    # ------------------------------------------------------------------------------------        
    def printRecipeElements(self, elements):
        for element in elements:
            xml_text = ElementTree.tostring(element)
            print xml_text

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        self.sequence_parser = XMLRecipeParser(xml_filename = "sequence_recipe_example.xml",
                                               verbose = True)
    
##    # Parse loops
##    current_node = command_sequence
##    found_all_nodes = False
##    while not found_all_nodes:
##        for child in current_node.childNodes:
##            print child
##            if child.nodeType == Node.ELEMENT_NODE:
##                if len(child.getElementsByTagName("loop")) == 0:
##                    found_all_nodes = True
##                else:
##                    if child.tagName == "loop":
##                        loop_names.append(child.getAttribute("name"))
##                        value_number = getValueNumber(loop_names[-1], loop_variables)
##                        response_string = "Found Loop: " + loop_names[-1]
##                        response_string += " with " + str(value_number) + " elements"
##                        print response_string
##                        current_node = child

##    # Create new xml object
##    new_xml = minidom.Document()
##
##    # Create root element
##    root_element = new_xml.createElement("sequence")
##    
##    # Parse command_sequence    
##    loop_elements = command_sequence.getElementsByTagName("loop")
##    for loop_element in loop_elements:
##        for child in loop_element.childNodes:
##            if child.nodeType == Node.ELEMENT_NODE:
##                if child.tagName == "item":
##                    item_name = child.getAttribute("name")
##                    print "Found Item: " + item_name
##                    found_item = getChildByAttribute("name", item_name, items)
##                    if not found_item == None:
##                        for item_child in found_item.childNodes:
##                            if item_child.nodeType == Node.ELEMENT_NODE:
##                                root_element.appendChild(item_child)
##                                print "   " + item_child.tagName
##                    else:
##                        print "Item did not contain any children!"
##                else:
##                    root_element.appendChild(child)
##    print root_element.toxml()

##def getChildByAttribute(attr_name, attr_value, children):
##    for child in children:
##        if child.hasAttribute(attr_name):
##            if child.getAttribute(attr_name) == attr_value:
##                return child
##    return None
##
##def getValueNumber(loop_name, loop_variables):
##    for loop in loop_variables:
##        if loop.getAttribute("name") == loop_name:
##            return len(loop.getElementsByTagName("value"))
##
#### Recursive function to handle adding elements to new xml based on loop
##def parseLoop(loop, new_xml_sequence):
##    getChildBy
##    for child

#
# Testing
# 
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    app.exec_()  
#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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
