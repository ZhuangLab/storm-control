#!/usr/bin/python
#
## @file
#
# Handles parsing sequence xml files and generating DaveActions.
#
# Hazen 05/14
#

from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

import daveActions


## DaveActionStandardItem
#
# A QStandardItem specialized to hold a DaveAction.
#
class DaveActionStandardItem(QtGui.QStandardItem):

    def __init__(self, node):
        dave_action_class = getattr(daveActions, node.tag)
        self.dave_action = dave_action_class()
        self.dave_action.setup(node)

        QtGui.QStandardItem.__init__(self, self.dave_action.getDescriptor())

## DaveStandardItemModel
#
# A QStandardItemModel specialized for Dave.
#
class DaveStandardItemModel(QtGui.QStandardItemModel):

    def __init__(self):
        QtGui.QStandardItemModel.__init__(self)



## parseSequenceFile
#
# @param xml_file The xml_file to parse to create the command sequence.
#
# @return A QStandardItemModel object for using in a QTreeView.
#
def parseSequenceFile(xml_file):
    model = QtGui.QStandardItemModel()
    xml = ElementTree.parse(xml_file).getroot()
    for outer_block_node in xml:
        outer_parent = QtGui.QStandardItem(outer_block_node.get("name", "NA"))
        for inner_block_node in outer_block_node:
            inner_parent = QtGui.QStandardItem(inner_block_node.get("name", "NA"))
            actions = []
            for action_node in inner_block_node:
                actions.append(DaveActionStandardItem(action_node))
            inner_parent.appendColumn(actions)
            outer_parent.appendRow(inner_parent)
        model.appendRow(outer_parent)

    return model

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
