#!/usr/bin/python
#
## @file
#
# Handles parsing sequence xml files and generating DaveActions.
#
# Hazen 05/14
#

from xml.etree import ElementTree

import daveActions


## createAction
#
# Creates a DaveAction from the node of an ElementTree.
#
# @param node The node of an ElementTree.
#
# @return The DaveAction.
#
def createAction(node):
    d_class = getattr(daveActions, node.tag)
    d_instance = d_class()
    d_instance.setup(node)
    return d_instance

## parseSequenceFile
#
# @param xml_file The xml_file to parse to create the command sequence.
#
# @return A list of DaveActions.
#
def parseSequenceFile(xml_file):
    actions = []
    xml = ElementTree.parse(xml_file).getroot()
    for block_node in xml:
        for action_node in block_node:
            actions.append(createAction(action_node))
    return actions

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
