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
        new_command_sequence = ElementTree.Element("sequence")
        self.copyElementWithLoop(self.command_sequences[0],
                                 new_command_sequence)
        print ElementTree.tostring(new_command_sequence)
    
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

    # ------------------------------------------------------------------------------------
    # Make a copy of an etree 
    # ------------------------------------------------------------------------------------        
    def copyElementWithLoop(self, parent, new_parent):
        for child in parent:
            if child.tag == "loop":
                self.handleLoop(child, new_parent)
            elif child.tag == "variable_entry":
                self.handleVariableEntry(child, new_parent)
            elif child.attrib.get("increment_name") == "Yes":
                pass
            else:
                new_child = ElementTree.SubElement(new_parent, child.tag, child.attrib)
                if child.text == None: new_child.text = ""
                else: new_child.text = str(child.text)
                if child.tail == None: new_child.tail = ""
                else: new_child.tail = str(child.tail)
                self.copyElementWithLoop(child, new_child)

        return new_parent

    # ------------------------------------------------------------------------------------
    # Handle a loop element 
    # ------------------------------------------------------------------------------------        
    def handleLoop(self, loop, new_parent):
        loop_name = loop.attrib["name"]
        loop_ID = self.loop_variable_names.index(loop_name)

        for local_iterator in range(len(self.loop_variables[loop_ID])):
            self.loop_iterator[loop_ID] = local_iterator
            self.copyElementWithLoop(loop, new_parent)
        self.loop_iterator[loop_ID] = -1

    # ------------------------------------------------------------------------------------
    # Handle a variable entry element 
    # ------------------------------------------------------------------------------------        
    def handleVariableEntry(self,child, new_parent):
        variable_name = child.attrib["name"]
        loop_ID = self.loop_variable_names.index(variable_name)

        variable_entry = self.loop_variables[loop_ID][self.loop_iterator[loop_ID]]
        self.copyElementWithLoop(variable_entry, new_parent)

    # ------------------------------------------------------------------------------------
    # Make a replicate of an Element 
    # ------------------------------------------------------------------------------------        
    def replicateElement(parent, new_parent = None):
        if new_parent == None:
            new_parent = ElementTree.Element(parent.tag, parent.attrib)
            new_parent.text = str(parent.text)
            new_parent.tail = str(parent.tail)
            
        for child in parent:
            new_child = ElementTree.SubElement(new_parent, child.tag, child.attrib)
            new_child.text = str(child.text)
            new_child.tail = str(child.tail)
            replicateETree(child, new_child)

        return new_parent

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        self.sequence_parser = XMLRecipeParser(xml_filename = "sequence_recipe_example.xml",
                                               verbose = True)

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
