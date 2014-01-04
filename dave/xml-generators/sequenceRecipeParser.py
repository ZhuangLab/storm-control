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
import os, sys
from xml.dom import minidom, Node
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
        self.command_sequence = []
        self.items = []
        self.loop_variables = []
        self.flat_sequence = []

        # Parse XML
        self.parseXML()

    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: print "Closing valve commands"

    # ------------------------------------------------------------------------------------
    # Load and parse a XML file with defined sequence recipe
    # ------------------------------------------------------------------------------------
    def parseXML(self, xml_file_path = ""):
        # Handle passed file name
        if not xml_file_path == "":
            self.xml_filename = xml_file_path

        # Open a file dialog if no path is provided
        if self.xml_filename == "":
            temp_file_path = QtGui.QFileDialog.getOpenFileName(self,
                                                               "Open XML Recipe",
                                                               "*.xml")
            if os.path.isfile(temp_file_path):
                self.xml_filename = temp_file_path
        
        try:
            xml = minidom.parse(self.xml_filename)
            print "Parsing: " + self.xml_filename
        except:
            print "Invalid file: " + self.xml_filename
            return None

        # Extract main element
        self.main_element = xml.documentElement

        # Parse major components of recipe file
        for child in self.main_element.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                if child.tagName == "command_sequence":
                    self.command_sequence.append(child)
                if child.tagName == "item":
                    self.items.append(child)
                if child.tagName == "loop_variable":
                    self.loop_variables.append(child)        

        # Expand Loop Variables from File
        self.extractLoopVariablesFromFile()

        # Display parsing results
        if self.verbose:
            print self.command_sequence
            self.printRecipeElements(self.command_sequence)
            print self.items
            self.printRecipeElements(self.items)
            print self.loop_variables
            self.printRecipeElements(self.loop_variables)

        return True

    # ------------------------------------------------------------------------------------
    # Parse loop variables and extract from file as needed
    # ------------------------------------------------------------------------------------        
    def extractLoopVariablesFromFile(self):     
        # Expand out loop variables
        for loop in self.loop_variables:
            path_to_xml = ""
            file_path_elements = loop.getElementsByTagName("file_path")
            print file_path_elements
            for file_path_element in file_path_elements:
                text_nodes = self.findNodesByNodeType(file_path_element.childNodes,
                                                         node_type = Node.TEXT_NODE)

                print text_nodes
                # There should only be one, but if there are more concatenate the results
                for text_node in text_nodes: 
                    path_to_xml += text_node.nodeValue
                if not path_to_xml == "":
                    loop_variable_contents_xml = minidom.parse(path_to_xml)
                    for element in loop_variable_contents_xml.getElementsByTagName("value"):
                        loop.appendChild(element)
                    if self.verbose:
                        print "Extracted loop variables from " + path_to_xml
                else:
                    if self.verbose:
                        print "Found empty <file_path> tag"

    # ------------------------------------------------------------------------------------
    # Parse nodes by type (default is element nodes) 
    # ------------------------------------------------------------------------------------        
    def findNodesByNodeType(self, children, node_type = Node.ELEMENT_NODE):
        found_children = []
        for child in children:
            if child.nodeType == node_type:
                found_children.append(child)

        return found_children

    # ------------------------------------------------------------------------------------
    # Print elements 
    # ------------------------------------------------------------------------------------        
    def printRecipeElements(self, elements):
        for element in elements:
            xml_text = element.toxml()
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
