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
        self.command_sequences = []
        self.items = []
        self.loop_names = []
        self.loop_variables = []
        self.loop_iterator = []
        self.num_loop_elements = []
        self.flat_sequence = []
        self.root_element = []
        self.item_names = []
        
        # Parse XML
        self.parseXML()

        # Create flat command sequence
        self.createFlatSequence()
        print "Flat Sequence:"
        xml_text = self.flat_sequence.toxml()
        print xml_text

    # ------------------------------------------------------------------------------------
    # Create the flat sequence 
    # ------------------------------------------------------------------------------------        
    def createFlatSequence(self):
        if self.verbose: print "Creating flat sequence"
        self.flat_sequence = minidom.Document()
        self.root_element = self.flat_sequence.createElement("sequence")

        for command_sequence in self.command_sequences:
            print command_sequence
            print command_sequence.toxml()
            print command_sequence.lastChild
            self.addToFlatSequence(command_sequence)

        self.flat_sequence.appendChild(self.root_element)

    def addToFlatSequence(self, commands_to_add):
        for child in commands_to_add.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                print "Element node: " + child.tagName
                if child.tagName == "loop":
                    self.processLoopElement(child)
                else:
                    self.root_element.appendChild(child)
            elif child.nodeType == Node.TEXT_NODE:
                self.root_element.appendChild(child)
                print "Text node"
    
    # ------------------------------------------------------------------------------------
    # Process a loop element in the command sequence 
    # ------------------------------------------------------------------------------------        
    def processLoopElement(self, loop):
        # Find loop_variable(s) with the same name
        loop_name = loop.getAttribute("name")
        local_loop_variables = self.getElementsByAttribute(self.loop_variables, "name", loop_name)

        # Find entries for the loop variable
        variable_entries = []
        for local_loop_variable in local_loop_variables:
            for child in self.findNodesByNodeType(local_loop_variable.childNodes,
                                                  node_type = Node.ELEMENT_NODE):
                if child.tagName == "value":
                    variable_entries.append(child)

        # Record loop parameters and properties
        num_loop_elements = len(variable_entries)
        local_loop_ID = len(self.num_loop_elements) - 1
        self.current_loop_iterator.append(0)
        
        # Parse and insert loop
        for local_loop_iterator in range(num_loop_elements):
            self.current_loop_iterator[local_loop_ID] = local_loop_iterator
            for child in loop.childNodes:
                if child.nodeType == Node.TEXT_NODE:
                    self.root_element.appendChild(child)
                    print "Text node"
                elif child.nodeType == Node.ELEMENT_NODE:
                    if child.tagName == "loop":
                        self.processLoopElement(child)
                    elif child.tagName == "item":
                        pass
                    elif child.tagName == "variable_entry":
                        self.root_element.appendChild(variable_entries[local_loop_iterator])
                        
    # ------------------------------------------------------------------------------------
    # Return elements by name 
    # ------------------------------------------------------------------------------------        
    def getElementsByAttribute(self, nodes, attribute_name, attribute_value):
        found_nodes = []
        for node in nodes:
            if node.hasAttribute(attribute_name):
                if node.getAttribute(attribute_name) == attribute_value:
                    found_nodes.append(node)

        return found_nodes

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
        xml, self.xml_filename = self.loadXML(self.xml_filename, header = "Open Sequence Recipe File")

        # Extract main element
        self.main_element = xml.documentElement

        # Parse major components of recipe file
        for child in self.main_element.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                if child.tagName == "command_sequence":
                    self.command_sequences.append(child)
                if child.tagName == "item":
                    self.items.append(child)
                    self.item_names.append(child.getAttribute("name"))
                if child.tagName == "loop_variable":
                    self.loop_variables.append(child)        

        # Expand Loop Variables from File
        self.extractLoopVariablesFromFile()

        # Replace items in command_sequence
        for i, command_sequence in enumerate(self.command_sequences):
            self.command_sequences[i] = self.findAndReplaceItemsInNode(self.command_sequences[i])

        # Display parsing results
        if self.verbose:
            print self.command_sequences
            self.printRecipeElements(self.command_sequences)
            print self.items
            self.printRecipeElements(self.items)
            print self.loop_variables
            self.printRecipeElements(self.loop_variables)

        return True

    # ------------------------------------------------------------------------------------
    # Find and replace items in command sequence
    # ------------------------------------------------------------------------------------        
    def findAndReplaceItemsInNode(self, node):
        print "Parsing: " + str(node)
        for child in node.childNodes:
            time.sleep(0.1)
            print "Child: " + str(child)
            if child.nodeType == Node.ELEMENT_NODE:
                if child.tagName == "item":
                    item_name = child.getAttribute("name")
                    print "Found item " + item_name
                    child_ID = self.item_names.index(item_name)
                    found_item = self.items[child_ID]
                    print found_item
                    # Parse item children for <item> elements and append to current node
                    for item_child in found_item.childNodes:
                        print "Item Item: " + str(item_child)
                        item_child = self.findAndReplaceItemsInNode(item_child) # See if there are nest items
                        node.insertBefore(item_child, child)
                    # Remove the item element
                    node.removeChild(child)
                else: # See if the nodes children have an item
                    node.replaceChild(self.findAndReplaceItemsInNode(child), child)
        print "Done parsing:" + str(node)
        return node

    # ------------------------------------------------------------------------------------
    # Create and XML dialog for loading xml file and return parsed xml
    # ------------------------------------------------------------------------------------        
    def loadXML(self, xml_file_path, header = "Open XML File"):
        if xml_file_path == "":
            temp_file_path = QtGui.QFileDialog.getOpenFileName(self, header, "*.xml")
            if os.path.isfile(temp_file_path):
                xml_file_path = temp_file_path
        try:
            xml = minidom.parse(xml_file_path)
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
            file_path_elements = loop.getElementsByTagName("file_path")
            for file_path_element in file_path_elements:
                # Remove file path element from loop element
                loop.removeChild(file_path_element)

                # Find text nodes within file_path element and load file
                text_nodes = self.findNodesByNodeType(file_path_element.childNodes,
                                                      node_type = Node.TEXT_NODE)
                # There should only be one, but if there are more concatenate the results
                for text_node in text_nodes: 
                    path_to_xml += text_node.nodeValue

                loop_variable_xml, path_to_loop_variable_xml = self.loadXML(path_to_xml,
                                                                            header = "Open Loop Variable XML")
                for child in loop_variable_xml.childNodes:
                    loop.appendChild(child)
                if self.verbose:
                    print "Extracted loop variables from " + path_to_loop_variable_xml
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
