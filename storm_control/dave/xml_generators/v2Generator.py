#!/usr/bin/python
#
## @file
#
# An xml parser class that takes a sequence recipe xml file and converts it to
# a flat sequence file that can be read by Dave
#
# Jeffrey Moffitt
# 1/5/14
# 9/4/14: Updated to Dave4 format
# jeffmoffitt@gmail.com
#

# 
# Import
# 
import os
import sys
import traceback
from xml.etree import ElementTree
from xml.dom import minidom

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.dave.xml_generators.nodeToDict as nodeToDict

import storm_control.dave.daveActions as daveActions

## XMLRecipeParser
# 
# A class for parsing the version 2 dave files and generating dave primitive sequences
#
class XMLRecipeParser(QtWidgets.QWidget):

    ## __init__
    #
    # Initialize the class
    # @param xml_filename Name of the xml file to parse
    # @param output_filename Name of the xml file to generate
    # @param verbose Controls progress reporting
    #
    def __init__(self,
                 xml_filename = "",
                 output_filename = "",
                 verbose = True,
                 parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        
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
        self.xml_sequence_file_path = output_filename
        
        self.da_primitives_xml = []

        # A convenient list of dave actions required for parsing a <movie> tag
        self.movie_da_actions = [daveActions.DAMoveStage(),
                                 daveActions.DASetFocusLockTarget(),
                                 daveActions.DAFindSum(),
                                 daveActions.DACheckFocus(),
                                 daveActions.DARecenterPiezo(),
                                 daveActions.DASetParameters(),
                                 daveActions.DASetProgression(),
                                 daveActions.DASetDirectory(),
                                 daveActions.DADelay(),
                                 daveActions.DAPause(),
                                 daveActions.DATakeMovie()]

    ## convertToDaveXMLPrimitives
    #
    # @param primitives_xml The element tree that will contain dave primitives
    # @param flat_sequence The element tree that contains a flat sequence of higher order commands, e.g. <movie>
    #
    def convertToDaveXMLPrimitives(self, primitives_xml, flat_sequence):
        if self.verbose:
            print("---------------------------------------------------------")
            print("Converting to Dave Primitives")
        
        # Loop over all children
        for child in flat_sequence:
            if child.tag == "branch": # Generate block and call recursively to handle elements in blocks
                branch = ElementTree.SubElement(primitives_xml, "branch")
                branch.attrib["name"] = child.attrib["name"]
                self.convertToDaveXMLPrimitives(branch, child)
            
            elif child.tag == "movie": # Handle <movie> tag
                movie_block = ElementTree.SubElement(primitives_xml, "branch")
                name = child.find("name")

                # Determine name.
                if name is not None:
                    movie_block.set("name", name.text)
                else:
                    movie_block.set("name", "No Name Provided")

                # Determine dictionary
                movie_dict = nodeToDict.movieNodeToDict(child)
                for action in self.movie_da_actions:
                    new_node = action.createETree(movie_dict)
                    if new_node is not None:
                        movie_block.append(new_node)
            
            elif child.tag == "valve_protocol": # Handle <valve_protocol> tag
                new_node = daveActions.DAValveProtocol().createETree({"name": child.text})
                if new_node is not None:
                    primitives_xml.append(new_node)

            elif child.tag == "change_directory": # Handle change_directory tag
                new_node = daveActions.DASetDirectory().createETree({"directory": child.text})
                if new_node is not None:
                    primitives_xml.append(new_node)

            elif child.tag == "clear_warnings": # Handle the clear_warnings tag
                new_node = daveActions.DAClearWarnings().createETree({})
                if new_node is not None:
                    primitives_xml.append(new_node)
            else:
                pass
                ## Eventually display an unknown tag error. For now ignore

    ## copyChildren
    #
    # Handles copying children of the specified parent to the new_parent specifically handling <loop> and <variable_entry> tags
    #
    # @param parent The element tree to be copied
    # @param new_parent The element tree that will contain the flat sequence
    #       
    def copyChildren(self, parent, new_parent):
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
                self.copyChildren(child, new_child)
            else:
                new_child = ElementTree.SubElement(new_parent, child.tag, child.attrib)
                if child.text == None: new_child.text = ""
                else: new_child.text = str(child.text)
                if child.tail == None: new_child.tail = ""
                else: new_child.tail = str(child.tail)
                self.copyChildren(child, new_child)

        return new_parent

    ## handleLoop
    #
    # Handles iteration of loop variables and naming of branches corresponding to loops
    #
    # @param loop The element whos children should be copied and replicated
    # @param new_parent The element tree that will contain the flat sequence
    #             
    def handleLoop(self, loop, new_parent):
        loop_name = loop.attrib["name"]
        loop_ID = self.loop_variable_names.index(loop_name)
        loop_block = ElementTree.Element("branch")
        loop_block.attrib["name"] = loop_name
        for local_iterator in range(len(self.loop_variables[loop_ID])):
            self.loop_iterator[loop_ID] = local_iterator # Store iterator for updating names
            self.copyChildren(loop, loop_block)
        new_parent.append(loop_block)
        self.loop_iterator[loop_ID] = -1

    ## handleVariableEntry
    #
    # Handles proper replacement of <variable_entry> tags in loops
    #
    # @param child The variable entry node
    # @param new_parent The element tree that will contain the flat sequence
    #
    def handleVariableEntry(self, child, new_parent):
        variable_name = child.attrib["name"]
        loop_ID = self.loop_variable_names.index(variable_name)

        variable_entry = self.loop_variables[loop_ID][self.loop_iterator[loop_ID]]

        # Add a tail to the last child for a pretty final xml file
        last_child = variable_entry[-1]
        last_child.tail = "\n"
        
        self.copyChildren(variable_entry, new_parent)
        
    ## loadXML
    #
    # Load generic XML files
    #
    # @param xml_file_path The xml file path
    # @param header The header to display
    # @param file_types The file types to display
    #        
    def loadXML(self, xml_file_path, header = "Open XML File", file_types = "XML (*.xml)"):
        if xml_file_path == "":
            temp_file_path = QtWidgets.QFileDialog.getOpenFileName(self, header, self.directory, file_types)[0]
            if (len(temp_file_path) > 0):
                if os.path.isfile(temp_file_path):
                    xml_file_path = temp_file_path
            else:
                return (None, xml_file_path)
        try:
            # Parse xml
            xml = ElementTree.parse(xml_file_path)
            if self.verbose:
                print("Parsing: " + xml_file_path)
            return (xml, xml_file_path)

        # FIXME: Make this more specific. The error might not only be a path problem.
        except:
            print("Invalid xml file: " + xml_file_path)
            return (None, xml_file_path)

    ## parseLoopVariables
    #
    # Parse the original loop variable entries
    #        
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
                    print("Extracted loop variables from " + path_to_loop_variable_xml)

    ## parseXML
    #
    # Load a xml recipe file.
    #
    # @param xml_file_path Path to the xml file.
    #  
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
            print("Unexpected contents: " + self.xml_filename)
            return ""

        return self.xml_sequence_file_path

    ## parseXMLRecipe
    #
    # Parse the XML recipe file.
    #
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
            self.copyChildren(command_sequence, self.flat_sequence)

        # Create Dave action primitives
        self.da_primitives_xml = ElementTree.Element("sequence")
        self.da_primitives_xml.text = "\n"
        self.convertToDaveXMLPrimitives(self.da_primitives_xml, self.flat_sequence)

        # Save dave primitives
        self.saveDavePrimitives()

    ## parseXMLExperiment
    #
    # Not necessary because Dave handles this.
    #
    def parseXMLExperiment(self):
        # Get additional file paths
        positions_filename = QtWidgets.QFileDialog.getOpenFileName(self, "Positions File", self.directory, "*.txt")[0]
        self.directory = os.path.dirname(positions_filename)
        output_filename = QtWidgets.QFileDialog.getSaveFileName(self, "Generated File", self.directory, "*.xml")[0]
        try:
            xml_generator.generateXML(self.xml_filename, positions_filename, output_filename, self.directory, self)
            self.xml_sequence_file_path = output_filename
        except:
            QtWidgets.QMessageBox.information(self,
                                              "XML Generation Error",
                                              traceback.format_exc())
            self.xml_sequence_file_path = ""
    
    ## replaceItems
    #
    # Replace <item> tags in the command sequence.
    #
    # @param element An element tree element.
    #
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

    ## saveDavePrimitives
    #
    # Save the final dave primitives sequence.
    #
    def saveDavePrimitives(self):
        if self.xml_sequence_file_path == "":
            self.xml_sequence_file_path = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                                "Save XML Sequence",
                                                                                self.directory,
                                                                                "*.xml")[0]
        try:
            out_fp = open(self.xml_sequence_file_path, "w")
            rough_string = ElementTree.tostring(self.da_primitives_xml, 'utf-8')        
            reparsed = minidom.parseString(rough_string)
            out_fp.write(reparsed.toprettyxml(indent="  ", encoding = "ISO-8859-1").decode())
            out_fp.close()
            self.wrote_XML = True
        except:
            QtWidgets.QMessageBox.information(self,
                                              "Error saving xml file",
                                              traceback.format_exc())
            self.xml_sequence_file_path = ""

    ## writtenXMLPath
    #
    # Determine if an XML file was written.
    #
    def writtenXMLPath(self):
        return self.xml_sequence_file_path


# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        self.sequence_parser = XMLRecipeParser(xml_filename = "",
                                               verbose = True)
        self.sequence_parser.parseXML()

# ----------------------------------------------------------------------------------------
# Test Code
# ----------------------------------------------------------------------------------------
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
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
