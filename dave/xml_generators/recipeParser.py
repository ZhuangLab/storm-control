#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# An xml parser class that takes a sequence recipe xml file and converts it to
# a flat sequence file that can be read by Dave
# ----------------------------------------------------------------------------------------
# Jeffrey Moffitt
# 1/5/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import os, sys
from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui
import xml_generator
import traceback

# ----------------------------------------------------------------------------------------
# XML Recipe Parser Class
# ----------------------------------------------------------------------------------------
class XMLRecipeParser(QtGui.QWidget):
    def __init__(self,
                 xml_filename = "",
                 output_filename = "",
                 verbose = True,
                 parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        # Initialize local attributes
        self.xml_filename = xml_filename
        self.verbose = verbose
        self.directory = ""
        
        self.main_element = []
        self.sequence_xml = []

        self.command_sequences = []

        self.items = []
        self.item_names = []
       
        self.loop_variables = []
        self.loop_variable_names = []
        self.loop_iterator = []

        self.flat_sequence = []
        self.flat_sequence_xml = []
        self.flat_sequence_file_path = output_filename

    # ------------------------------------------------------------------------------------
    # Make a copy of an etree 
    # ------------------------------------------------------------------------------------        
    def copyElementWithLoop(self, parent, new_parent):
        for child in parent:
            if child.tag == "loop":
                self.handleLoop(child, new_parent)
            elif child.tag == "variable_entry":
                self.handleVariableEntry(child, new_parent)
            elif child.attrib.get("increment") == "Yes":
                new_child = ElementTree.SubElement(new_parent, child.tag, child.attrib)
                if child.text == None: new_child.text = ""
                else:
                    new_child.text = str(child.text)
                    for [loop_ID, loop_iterator] in enumerate(self.loop_iterator):
                        pad_length = len(str(len(self.loop_variables[loop_ID])))
                        if loop_iterator >= 0:
                            new_child.text += "_" + str(loop_iterator).zfill(pad_length)
                
                if child.tail == None: new_child.tail = ""
                else: new_child.tail = str(child.tail)
                del new_child.attrib["increment"]
                self.copyElementWithLoop(child, new_child)
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

        # Add a tail to the last child for a pretty final xml file
        last_child = variable_entry[-1]
        last_child.tail = "\n"
        
        self.copyElementWithLoop(variable_entry, new_parent)
        
    # ------------------------------------------------------------------------------------
    # Create XML dialog for loading xml file and return parsed xml
    # ------------------------------------------------------------------------------------        
    def loadXML(self, xml_file_path, header = "Open XML File", file_types = "XML (*.xml)"):
        if xml_file_path == "":
            temp_file_path = str(QtGui.QFileDialog.getOpenFileName(self, header, self.directory, file_types))
            if os.path.isfile(temp_file_path):
                xml_file_path = temp_file_path
        try:
            # Parse xml
            xml = ElementTree.parse(xml_file_path)
            if self.verbose: print "Parsing: " + xml_file_path
            return (xml, xml_file_path)
        except:
            print "Invalid xml file: " + xml_file_path
            return (None, xml_file_path)

    # ------------------------------------------------------------------------------------
    # Parse loop variables and extract from file as needed
    # ------------------------------------------------------------------------------------        
    def parseLoopVariables(self):
        # Reset loop variables
        for i in range(len(self.loop_variable_names)):
            self.loop_iterator.append(-1) 
        
        # Expand out loop variables
        for loop in self.loop_variables:
            path_to_xml = ""
            file_path_elements = loop.findall("file_path")
            for file_path_element in file_path_elements:
                path_to_xml = file_path_element.text
                if path_to_xml == None: path_to_xml = ""

                # Remove file path element from loop element
                loop.remove(file_path_element)
                window_header = "Open Variable for " + loop.attrib["name"]

                local_directory = os.path.dirname(path_to_xml)
                if local_directory == "" and not path_to_xml == "":
                    path_to_xml = os.path.join(self.directory, path_to_xml)
                    path_to_xml = os.path.normpath(path_to_xml)

                loop_variable_xml, path_to_loop_variable_xml = self.loadXML(path_to_xml,
                                                                            header = window_header,
                                                                            file_types = "Position Files (*.xml *.txt)")

                # Check if the file contains flat position data
                if loop_variable_xml == None and os.path.isfile(path_to_loop_variable_xml):
                    new_loop_variable = ElementTree.Element("variable_entry")
                    loop_variable_xml = ElementTree.ElementTree(new_loop_variable)
                    pos_fp = open(path_to_loop_variable_xml, "r")
                    # Convert position data to elements
                    while True:
                        line = pos_fp.readline()
                        if not line: break
                        [x, y] = line.split(",")
                        new_value = ElementTree.SubElement(new_loop_variable, "value")
                        new_value.text = "\n"

                        x_child = ElementTree.SubElement(new_value, "stage_x")
                        x_child.text = x

                        y_child = ElementTree.SubElement(new_value, "stage_y")
                        y_child.text = y

                loop_variables = loop_variable_xml.getroot()

                for loop_variable in loop_variables:
                    loop.append(loop_variable)
                if self.verbose:
                    print "Extracted loop variables from " + path_to_loop_variable_xml

    # ------------------------------------------------------------------------------------
    # Load and parse a XML file with defined sequence recipe
    # ------------------------------------------------------------------------------------
    def parseXML(self, xml_file_path = ""):
        # Handle passed file name
        if not xml_file_path == "":
            self.xml_filename = xml_file_path

        # Open a file dialog if no path is provided
        xml, self.xml_filename = self.loadXML(self.xml_filename, header = "Open Sequence Recipe File")

        if xml == None:
            return None

        self.directory = os.path.dirname(os.path.abspath(self.xml_filename))

        # Extract main element
        self.main_element = xml.getroot()

        # Handle different xml formats
        if self.main_element.tag == "recipe":
            self.parseXMLRecipe()
        elif self.main_element.tag == "experiment": # old version
            self.parseXMLExperiment()
        else:
            print "Unexpected contents: " + self.xml_filename
            return ""

        return self.flat_sequence_file_path


    # ------------------------------------------------------------------------------------
    # Parse the recipe format
    # ------------------------------------------------------------------------------------
    def parseXMLRecipe(self):
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
        
        # Expand loop variables and parse from file if needed
        self.parseLoopVariables()

        # Find and replace items in command_sequence
        for command_sequence in self.command_sequences:
            command_sequence = self.replaceItems(command_sequence)

        # Create flat command sequence and convert to new xml element tree
        self.flat_sequence = ElementTree.Element("sequence")
        self.flat_sequence.text = "\n" # Clean up display

        # Fill sequence from command sequence elements
        for command_sequence in self.command_sequences:
            self.copyElementWithLoop(command_sequence, self.flat_sequence)

        # Create element tree and insert sequence
        self.flat_sequence_xml = ElementTree.ElementTree(self.flat_sequence)

        # Save flat sequence
        self.saveFlatSequence()

    # ------------------------------------------------------------------------------------
    # Parse the experiment format
    # ------------------------------------------------------------------------------------
    def parseXMLExperiment(self):
        # Get additional file paths
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self, "Positions File", self.directory, "*.txt"))
        self.directory = os.path.dirname(positions_filename)
        output_filename = str(QtGui.QFileDialog.getSaveFileName(self, "Generated File", self.directory, "*.xml"))
        try:
            xml_generator.generateXML(self.xml_filename, positions_filename, output_filename, self.directory, self)
            self.flat_sequence_file_path = output_filename
        except:
            QtGui.QMessageBox.information(self,
                                          "XML Generation Error",
                                          traceback.format_exc())
            self.flat_sequence_file_path = ""
    
    # ------------------------------------------------------------------------------------
    # Find and replace items in command sequence
    # ------------------------------------------------------------------------------------        
    def replaceItems(self, element):
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
                    item_child = self.replaceItems(item_child) # See if there are nest items
                    element.insert(child_count, item_child) # Add parsed item
                    child_count += 1
            else: # See if the nodes children have an item
                element.remove(child)
                element.insert(child_count, self.replaceItems(child))
                child_count += 1
        return element

    # ------------------------------------------------------------------------------------
    # Save flat sequence
    # ------------------------------------------------------------------------------------
    def saveFlatSequence(self):
        if self.flat_sequence_file_path == "":
            self.flat_sequence_file_path = str(QtGui.QFileDialog.getSaveFileName(self,
                                                                                 "Save XML Sequence",
                                                                                 self.directory,
                                                                                 "*.xml"))
            
        try:
            self.flat_sequence_xml.write(self.flat_sequence_file_path,
                                         encoding = 'ISO-8859-1',
                                         xml_declaration = True)
        except:
            QtGui.QMessageBox.information(self,"Error",
                                          "Error saving xml file")
            self.flat_sequence_file_path = ""

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        self.sequence_parser = XMLRecipeParser(xml_filename = "",
                                               verbose = True)
        self.sequence_parser.parseXML()

# ----------------------------------------------------------------------------------------
# Test Code
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    app.exec_()  
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
