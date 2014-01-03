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

## parseMovieXml
#
# Parses the XML file that describes the movies.
#
# @param movie_xml_filename The name of the XML file.
#
def parseXMLRecipe(movie_xml_filename):
    xml = minidom.parse(movie_xml_filename)

    # Parse main element
    main_element = xml.documentElement
    command_sequence = []
    items = []
    loop_variables = []

    loop_numbers = []
    loop_number_names = []
    
    for child in main_element.childNodes:
        if child.nodeType == Node.ELEMENT_NODE:
            if child.tagName == "command_sequence":
                command_sequence = child
            if child.tagName == "item":
                items.append(child)
            if child.tagName == "loop_variable":
                loop_variables.append(child)

    # Create new xml object
    new_xml = minidom.Document()

    # Create root element
    root_element = new_xml.createElement("sequence")
    
    # Parse command_sequence    
    loop_elements = command_sequence.getElementsByTagName("loop")
    for loop_element in loop_elements:
        for child in loop_element.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                if child.tagName == "item":
                    item_name = child.getAttribute("name")
                    print "Found Item: " + item_name
                    found_item = getChildByAttribute("name", item_name, items)
                    if not found_item == None:
                        for item_child in found_item.childNodes:
                            if item_child.nodeType == Node.ELEMENT_NODE:
                                root_element.appendChild(item_child)
                                print "   " + item_child.tagName
                    else:
                        print "Item did not contain any children!"
                else:
                    root_element.appendChild(child)
    print root_element.toxml()

def getChildByAttribute(attr_name, attr_value, children):
    for child in children:
        if child.hasAttribute(attr_name):
            if child.getAttribute(attr_name) == attr_value:
                return child
    return None

#
# Testing
# 
if __name__ == "__main__":
    parsed_commands = parseXMLRecipe("sequence_recipe_example.xml")

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
