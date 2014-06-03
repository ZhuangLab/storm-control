#!/usr/bin/python
#
## @file
#
# Handles viewing (and parsing) sequence xml files and generating DaveActions.
#
# Hazen 06/14
#

from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

import daveActions


DaveActionType = QtGui.QStandardItem.UserType

## DaveActionStandardItem
#
# A QStandardItem specialized to hold a DaveAction.
#
class DaveActionStandardItem(QtGui.QStandardItem):

    ## __init__
    #
    # @param node A XML node describing the DaveAction.
    #
    def __init__(self, node):
        dave_action_class = getattr(daveActions, node.tag)
        self.dave_action = dave_action_class()
        self.dave_action.setup(node)

        QtGui.QStandardItem.__init__(self, self.dave_action.getDescriptor())

    ## getDaveAction
    #
    # @return The DaveAction associated with this item.
    #
    def getDaveAction(self):
        return self.dave_action

    ## type
    #
    # @return The type of the object (an int).
    #
    def type(self):
        return DaveActionType


## DaveCommandTreeViewer
#
# This class wraps the tree view and it's associated model.
#
class DaveCommandTreeViewer(QtGui.QTreeView):
    action_clicked = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parent (Optional) defaults to none.
    #
    def __init__(self, parent = None):
        QtGui.QTreeView.__init__(self, parent)

        #self.current_rect = None
        self.dv_model = None

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)

        self.clicked.connect(self.handleClick)

    ## getCurrentAction
    #
    # @return The current DaveAction or None if there are no actions.
    #
    def getCurrentAction(self):
        if self.dv_model:
            self.dv_model.getCurrentAction().getDaveAction()

    ## getNextAction
    #
    # @return The next DaveAction or None if there are no more actions.
    #
    def getNextAction(self):
        if self.dv_model:
            dave_action_si = self.dv_model.getNextAction()
            if dave_action_si is not None:
                self.update()
                return dave_action_si.getDaveAction()

    ## handleClick
    #
    # @param model_index The QModelIndex of the item that was clicked.
    #
    def handleClick(self, model_index):
        if self.dv_model is not None:
            qt_item = self.dv_model.itemFromIndex(model_index)
            if (qt_item.type() == DaveActionType):
                self.action_clicked.emit(qt_item)

    ## paintEvent
    #
    # Draw the tree with a rectangle around the current action.
    #
    # @param p_event A QPaintEvent object
    #
    def paintEvent(self, p_event):
        QtGui.QTreeView.paintEvent(self, p_event)

        if self.dv_model is not None:
            cur_item = self.dv_model.getCurrentAction()
            qt_model_index = self.dv_model.indexFromItem(cur_item)
            v_rect = self.visualRect(qt_model_index)
            while (v_rect.width() == 0) and (cur_item.parent() is not None):
                cur_item = cur_item.parent()
                qt_model_index = self.dv_model.indexFromItem(cur_item)
                v_rect = self.visualRect(qt_model_index)
            if (v_rect.width() != 0):
                select_rect = QtCore.QRect(0, 
                                           v_rect.top(),
                                           v_rect.right(),
                                           v_rect.height())
                painter = QtGui.QPainter(self.viewport())
                painter.setPen(QtGui.QColor(100,0,0))
                painter.drawRect(select_rect)

    ## reset
    #
    # Reset to the first DaveAction.
    #
    def reset(self):
        if self.dv_model is not None:
            self.dv_model.reset()
            self.update()

    ## setCurrentAction
    #
    # @param an_action The DaveAction to use as the current action.
    #
    def setCurrentAction(self, an_action):
        if self.dv_model is not None:
            self.dv_model.setCurrentAction(an_action)
            self.update()

    ## setModel
    #
    # @param qt_model The DaveStandardItemModel associated with the tree.
    #
    def setModel(self, dv_model):
        QtGui.QTreeView.setModel(self, dv_model)
        self.dv_model = dv_model
        self.reset()


## DaveStandardItemModel
#
# A QStandardItemModel specialized for Dave.
#
class DaveStandardItemModel(QtGui.QStandardItemModel):

    ## __init__
    #
    def __init__(self):
        QtGui.QStandardItemModel.__init__(self)

        self.dave_action_index = 0
        self.dave_action_si = []

    ## addActions
    #
    # @param dave_action_si An array of DaveActionStandardItems
    #
    def addActions(self, dave_action_si):
        self.dave_action_si.extend(dave_action_si)

    ## getCurrentAction
    #
    # @return The current DaveActionStandardItem.
    #
    def getCurrentAction(self):
        return self.dave_action_si[self.dave_action_index]

    ## getNextAction
    #
    # @return The next DaveActionStandardItem or none if there are no more items.
    #
    def getNextAction(self):
        self.dave_action_index += 1
        if (self.dave_action_index >= len(self.dave_action_si)):
            return None
        else:
            return self.dave_action_si[self.dave_action_index]

    ## reset
    #
    # Reset to the first DaveActionStandardItem.
    #
    def reset(self):
        self.dave_action_index = 0

    ## setCurrentAction
    #
    # @param an_action The DaveAction corresponding to the desired DaveActionStandardItem.
    #
    def setCurrentAction(self, an_action):
        self.dave_action_index = 0
        for i in range(len(self.dave_action_si)):
            if (self.dave_action_si[i].getDaveAction() == an_action):
                self.dave_action_index = i
                break
        else:
            print "Action not found."


## parseSequenceFile
#
# @param xml_file The xml_file to parse to create the command sequence.
#
# @return A QStandardItemModel object for using in a QTreeView.
#
def parseSequenceFile(xml_file):
    model = DaveStandardItemModel()
    xml = ElementTree.parse(xml_file).getroot()
    for outer_block_node in xml:
        outer_parent = QtGui.QStandardItem(outer_block_node.get("name", "NA"))
        outer_parent.setFlags(QtCore.Qt.ItemIsEnabled)
        for inner_block_node in outer_block_node:
            inner_parent = QtGui.QStandardItem(inner_block_node.get("name", "NA"))
            inner_parent.setFlags(QtCore.Qt.ItemIsEnabled)
            actions = []
            for action_node in inner_block_node:
                actions.append(DaveActionStandardItem(action_node))
            inner_parent.appendColumn(actions)
            model.addActions(actions)
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
