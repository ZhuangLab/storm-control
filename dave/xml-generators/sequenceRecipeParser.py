#!/usr/bin/python
#
## @file
#
# Creates command sequence xml from recipe xml files.
#
# Jeff 1/14
#

from xml.dom import minidom, Node
import halLib.hdebug as hdebug

class XMLRecipeParser():
    def __init__(self, xml_filename, verbose = True):

        self.xml_filename = xml_filename
        self.verbose = verbose
        
        self.main_element = []
        self.command_sequence = []
        self.items = []
        self.loop_variables = []

        self.parseXML()

    def parseXML(self):
        try:
            xml = minidom.parse(self.xml_filename)
            print "Parsing: " + self.xml_filename
        except:
            print "Invalid file: " + self.xml_filename

        # Extract main element
        self.main_element = xml.documentElement

        # Parse major components of recipe file
        for child in self.main_element.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                if child.tagName == "command_sequence":
                    self.command_sequence = child
                if child.tagName == "item":
                    self.items.append(child)
                if child.tagName == "loop_variable":
                    self.loop_variables.append(child)        

        # Expand Loop Variables from File
        self.extractLoopVariablesFromFile()
        
    def extractLoopVariablesFromFile(self):
                        
        # Expand out loop variables
        for loop in self.loop_variables:
            path_to_xml = None
            for child in loop.childNodes:
                if child.nodeType == Node.ELEMENT_NODE:
                    if child.tagName == "file_path":
                        for grand_child in child.childNodes:
                            if grand_child.nodeType == Node.TEXT_NODE:
                                path_to_xml = grand_child.nodeValue
                        if not path_to_xml == None:
                            loop_variable_contents_xml = minidom.parse(path_to_xml)
                            for element in loop_variable_contents_xml.getElementsByTagName("value"):
                                loop.appendChild(element)
                            if self.verbose:
                                print "Extracted loop variables from " + path_to_xml
                        else:
                            if self.verbose:
                                print "Found empty <file_path> tag"
            
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
    xml_recipe_parser = XMLRecipeParser("sequence_recipe_example.xml", verbose = True)
    #parsed_commands = parseXMLRecipe("stage_position_example.xml")

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
