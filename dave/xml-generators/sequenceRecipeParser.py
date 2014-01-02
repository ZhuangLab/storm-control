#!/usr/bin/python
#
## @file
#
# Creates command sequence xml from recipe xml files.
#
# Jeff 1/14
#

from xml.dom import minidom, Node, getDomImplementation
import halLib.hdebug as hdebug

## parseMovieXml
#
# Parses the XML file that describes the movies.
#
# @param movie_xml_filename The name of the XML file.
#
def parseMovieXml(movie_xml_filename):
    xml = minidom.parse(movie_xml_filename)
    print xml
    # Parse main element
    main_element = xml.documentElement
    command_sequence = []
    items = []
    loop_variables = []
    
    for child in main_element.childNodes:
        if child.nodeType == Node.ELEMENT_NODE:
            if child.tagName == "command_sequence":
                command_sequence = child
            if child.tagName == "item":
                items.append(child)
            if child.tagName == "loop_variable":
                loop_variables.append(child)

    impl = getDomImplementation()
    new_xml = impl.createDocument(None, "sequence", None)
    top_element = new_xml.documentElement
    top_element.appendChild(stuff)
    print new_xml
    print command_sequence, items, loop_variables
#
# Testing
# 
if __name__ == "__main__":
    parsed_commands = parseMovieXml("sequence_recipe_example.xml")

    
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
