#!/usr/bin/python
#
## @file
#
# Handles viewing (and parsing) sequence xml files and generating DaveActions.
#
# Hazen 06/14
#

from xml.etree import ElementTree
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.dave.daveActions as daveActions


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
        self.valid = True

        QtGui.QStandardItem.__init__(self, self.dave_action.getDescriptor())
        self.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    ## getDaveAction
    #
    # @return The DaveAction associated with this item.
    #
    def getDaveAction(self):
        return self.dave_action

    ## getDaveActionID
    #
    # @return The id associated with the DaveAction associated with this item.
    #
    def getDaveActionID(self):
        return self.dave_action.getID()

    ## isValid
    #
    # @return True/False if the command is valid.
    #
    def isValid(self):
        return self.valid

    ## setUsageEstimates
    #
    # @param disk_usage The estimated disk_usage for the action
    # @param duration The estimated duration of the action
    #
    def setUsageEstimates(self, disk_usage, duration):
        self.dave_action.setDiskUsage(disk_usage)
        self.dave_action.setDuration(duration)

    ## setValid
    #
    # @param valid True/False if the DaveAction associated with this item is valid.
    #
    def setValid(self, valid):
        self.valid = valid
        if self.valid:
            self.setBackground(QtGui.QBrush(QtGui.QColor(255,255,255)))
        else:
            self.setBackground(QtGui.QBrush(QtGui.QColor(255,200,200)))

    ## type
    #
    # @return The type of the object (an int).
    #
    def type(self):
        return DaveActionType

    ## getParentName
    #
    # @return The display text of any associated parent
    #
    def getParentName(self):
        parent = self.parent()
        if parent == 0: # No parent
            return ""
        else:
            return str(parent.text())

## DaveCommandTreeViewer
#
# This class wraps the tree view and it's associated model.
#
class DaveCommandTreeViewer(QtWidgets.QTreeView):
    double_clicked = QtCore.pyqtSignal(object)
    update = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parent (Optional) defaults to none.
    #
    def __init__(self, parent = None):
        QtWidgets.QTreeView.__init__(self, parent)

        self.aborted = False
        self.dv_model = None

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)

        self.clicked.connect(self.handleClick)
        self.doubleClicked.connect(self.handleDoubleClick)
        
    ## abort
    #
    # Sets the abort flag to True & resets the model.
    #
    def abort(self):
        self.reset()
        self.aborted = True

    ## getActionTypes
    #
    # @return A list of DaveAction types (i.e. "hal" or "kilroy").
    #
    def getActionTypes(self):
        if self.dv_model is not None:
            return self.dv_model.getActionTypes()
        else:
            return []

    ## getCurrentIndex
    #
    # @return The current item index.
    #
    def getCurrentIndex(self):
        if self.dv_model is not None:
            return self.dv_model.getCurrentIndex()
        else:
            return 0

    ## getCurrentItem
    #
    # @return The current DaveActionStandardItem or None if there are no items.
    #
    def getCurrentItem(self):
        if self.dv_model is not None:
            return self.dv_model.getCurrentItem()

    ## getEstimates
    #
    # @return [time, space] estimates for the run.
    #
    def getEstimates(self):
        if self.dv_model is not None:
            return [self.dv_model.getRemainingTime(), self.dv_model.getRunSize()]
        else:
            return [0, 0]

    ## getNextItem
    #
    # @param (Optional) skip_invalid True/False to skip invalid commands. Defaults to True.
    #
    # @return The next DaveActionStandardItem or None if there are no more items.
    #
    def getNextItem(self, skip_invalid = True):
        if self.aborted:
            self.aborted = False
            return None

        if self.dv_model is not None:
            dave_action_si = self.dv_model.getNextItem(skip_invalid)
            if dave_action_si is not None:
                self.viewportUpdate()
                return dave_action_si

    ## getNumberItems
    #
    # @return Then number of items in the model.
    #
    def getNumberItems(self):
        if self.dv_model is not None:
            return self.dv_model.getNumberItems()
        else:
            return 1

    ## getRemainingTime
    #
    # @return The estimated time left in the experiment.
    #
    def getRemainingTime(self):
        if self.dv_model is not None:
            return self.dv_model.getRemainingTime(self.dv_model.getCurrentIndex())
        else:
            return 0

    ## handleClick
    #
    # @param model_index The QModelIndex of the item that was clicked.
    #
    def handleClick(self, model_index):
        if self.dv_model is not None:
            qt_item = self.dv_model.itemFromIndex(model_index)
            if (qt_item.type() == DaveActionType):
                self.update.emit(qt_item.getDaveAction().getLongDescriptor())

    ## handleDoubleClick
    #
    # @param model_index The QModelIndex of the time that was doubled clicked.
    #
    def handleDoubleClick(self, model_index):
        if self.dv_model is not None:
            qt_item = self.dv_model.itemFromIndex(model_index)
            if (qt_item.type() == DaveActionType):
                self.double_clicked.emit(qt_item)
    
    ## haveNextItem
    #
    # @return True/False if there is a next item available.
    #
    def haveNextItem(self):
        if self.dv_model is not None:
            return self.dv_model.haveNextItem()
        else:
            return False

    ## isAllValid
    #
    # @return True/False if all the items are valid.
    #
    def isAllValid(self):
        if self.dv_model is not None:
            return self.dv_model.isAllValid()
        else:
            return True

    ## paintEvent
    #
    # Draw the tree with a rectangle around the current action.
    #
    # @param p_event A QPaintEvent object
    #
    def paintEvent(self, p_event):
        QtWidgets.QTreeView.paintEvent(self, p_event)

        if self.dv_model is not None:
            cur_item = self.dv_model.getCurrentItem()
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

    ## resetItemIndex
    #
    # Reset to the first DaveAction.
    #
    def resetItemIndex(self):
        if self.dv_model is not None:
            self.dv_model.resetItemIndex()
            self.viewportUpdate()

    ## setAllValid
    #
    # @param valid True/False Sets the valid status of all the items.
    #
    def setAllValid(self, valid):
        if self.dv_model is not None:
            self.dv_model.setAllValid(valid)

    ## setCurrentAction
    #
    # @param an_action The DaveActionStandardItem to use as the current item.
    #
    def setCurrentAction(self, an_item):
        if self.dv_model is not None:
            self.dv_model.setCurrentAction(an_item)
            self.viewportUpdate()

    ## setCurrentItemValidity
    #
    # @param is_valid True/False determines the validity of the currentItem(s)
    #
    def setCurrentItemValid(self, is_valid):
        if self.dv_model is not None:
            self.dv_model.setCurrentItemValid(is_valid)

    ## setModel
    #
    # @param qt_model The DaveStandardItemModel associated with the tree.
    #
    def setModel(self, dv_model):
        self.dv_model = dv_model
        QtWidgets.QTreeView.setModel(self, self.dv_model)
        self.viewportUpdate()

    ## setTestMode
    #
    # @param test_mode True/False sets the test mode of the DaveStandardItemModel.
    #
    def setTestMode(self, test_mode):
        if self.dv_model is not None:
            self.dv_model.setTestMode(test_mode)

    ## updateEstimates
    #
    def updateEstimates(self):
        if self.dv_model is not None:
            self.dv_model.updateEstimates()
        
    ## viewportUpdate
    #
    # Update the viewport.
    #
    def viewportUpdate(self):
        item = self.dv_model.getCurrentItem()
        self.scrollTo(self.dv_model.indexFromItem(item))
        self.viewport().update()
        self.update.emit(item.getDaveAction().getLongDescriptor())


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
        self.dave_actions_cur = []   # The active list of DaveActionStandardItems
        self.dave_actions_all = []   # The full list of DaveActionStandardItems
        
        # Lists for fast validation.
        self.dave_actions_test = []  # A list of actions to validate
        self.dave_actions_test_dict = dict() # A dictionary of test ids and lists of actions that have these

        self.test_mode = False

    ## addItem
    #
    # @param dave_action_si A DaveActionStandardItem.
    #
    def addItem(self, dave_action_si):
        self.dave_actions_all.append(dave_action_si)
        self.dave_actions_cur.append(dave_action_si) # Build current actions simultaneously
        
        # Check if action requires validation
        action_id = dave_action_si.getDaveAction().getID()
        if action_id is not None:
            # Check for existing id
            is_present = False
            for id_value in self.dave_actions_test_dict.keys():
                if action_id == id_value:
                    is_present = True

            # Add to list if the id is not currently on the id list
            if not is_present:
                self.dave_actions_test.append(dave_action_si)
                self.dave_actions_test_dict[action_id] = [dave_action_si] # Start list
            else: # Add to current list of actions with the same id
                self.dave_actions_test_dict[action_id].append(dave_action_si)
        
    ## getActionTypes
    #
    # @return A list of DaveAction types (i.e. "hal" or "kilroy").
    #
    def getActionTypes(self):
        types = []
        for item in self.dave_actions_cur:
            type = item.getDaveAction().getActionType()
            if not type in types:
                types.append(type)
        return types

    ## getCurrentIndex
    #
    # @return The current item index.
    #
    def getCurrentIndex(self):
        return self.dave_action_index

    ## getCurrentItem
    #
    # @return The current DaveActionStandardItem.
    #
    def getCurrentItem(self):
        return self.dave_actions_cur[self.dave_action_index]

    ## getNextItem
    #
    # @param skip_invalid True/False to skip invalid commands.
    #
    # @return The next DaveActionStandardItem or none if there are no more items.
    #
    def getNextItem(self, skip_invalid):
        self.dave_action_index += 1

        # If requested, skip over invalid commands.
        if skip_invalid:
            while (self.dave_action_index < len(self.dave_actions_cur)) and (not self.dave_actions_cur[self.dave_action_index].isValid()):
                self.dave_action_index += 1

        if (self.dave_action_index >= len(self.dave_actions_cur)):
            return None
        else:
            return self.dave_actions_cur[self.dave_action_index]

    ## getNumberItems
    #
    # @return Then number of items in the model.
    #
    def getNumberItems(self):
        return len(self.dave_actions_cur)

    ## getRemainingTime
    #
    # @param start (Optional) The index of the command to start at, defaults to 0.
    #
    # @return An estimate of how much time is left in the run.
    #
    def getRemainingTime(self, start = 0):
        est_time = 0
        i = start
        while (i < len(self.dave_actions_cur)):
            item = self.dave_actions_cur[i]
            if item.isValid():
                est_time += item.getDaveAction().getDuration()
            i += 1
        return est_time

    ## getRunSize
    #
    # @return An estimate of the run size.
    #
    def getRunSize(self):
        est_space = 0
        for item in self.dave_actions_cur:
            if item.isValid():
                est_space += item.getDaveAction().getUsage()
        return est_space

    ## haveNextItem
    #
    # @return True/False if there is a next item available.
    #
    def haveNextItem(self):
        if ((self.dave_action_index + 1) >= len(self.dave_actions_cur)):
            return False
        else:
            return True

    ## isAllValid
    #
    # @return True/False if all the items are valid.
    #
    def isAllValid(self):
        all_valid = True
        for item in self.dave_actions_cur:
            if not item.isValid():
                all_valid = False
        return all_valid

    ## resetItemIndex
    #
    # Reset to the first DaveActionStandardItem.
    #
    def resetItemIndex(self):
        self.dave_action_index = 0

    ## setAllValid
    #
    # @param valid True/False Sets the valid status of all the items.
    #
    def setAllValid(self, valid):
        for item in self.dave_actions_all:
            item.setValid(valid)

    ## setCurrentItem
    #
    # @param an_item The desired DaveActionStandardItem.
    #
    def setCurrentAction(self, an_item):
        self.dave_action_index = 0
        for i in range(len(self.dave_actions_cur)):
            if (self.dave_actions_cur[i] == an_item):
                self.dave_action_index = i
                break
        else:
            print("item not found!")

    ## setCurrentItemValid
    #
    # @param is_Valid True/False determines the validity of the currentItem(s)
    #
    def setCurrentItemValid(self, is_valid):
        if self.test_mode:
            # Find current id
            current_item = self.dave_actions_cur[self.dave_action_index]
            current_action = current_item.getDaveAction()
            current_id = current_action.getID()

            print(current_id, is_valid)
            
            # Change validity of all actions that have this id
            for item in self.dave_actions_test_dict[current_id]:
                item.setValid(is_valid)
                
        else: # Not used
            item = self.dave_actions_cur[self.dave_action_index]
            item.setValid(is_valid)
                    
    ## setTestMode
    #
    # @param test_mode True/False sets the test mode.
    #
    def setTestMode(self, test_mode):
        if self.test_mode:
            if not test_mode: # Toggle off test mode
                self.test_mode = False
                self.dave_actions_cur = self.dave_actions_all # Recover full list
                self.resetItemIndex()
        else:
            if test_mode:
                self.test_mode = True
                self.dave_actions_cur = self.dave_actions_test # Set to test list
                self.resetItemIndex()

    ## updateEstimates
    #
    def updateEstimates(self):
        if self.test_mode: # Only needed in test mode

            # Find current id and the current disk usage and duration.
            current_item = self.dave_actions_cur[self.dave_action_index]
            current_action = current_item.getDaveAction()
            current_id = current_action.getID()
            disk_usage = current_action.getUsage()
            duration = current_action.getDuration()
            
            # Update usage estimated for all actions that have this id.
            for item in self.dave_actions_test_dict[current_id]:
                item.setUsageEstimates(disk_usage, duration)

## parseSequenceFile
#
# @param xml_file The xml_file to parse to create the command sequence.
#
# @return A DaveStandardItemModel object for using in a DaveCommandTreeViewer.
#
def parseSequenceFile(xml_file):
    model = DaveStandardItemModel()
    xml = ElementTree.parse(xml_file).getroot()
    recursiveParse(model, model, xml)
    return model

## recursiveParse
#
# Recursively parse the XML tree.
#
# @param model The root DaveStandardItemModel.
# @param model_branch_model A branch of a DaveStandardItemModel.
# @param xml_branch The current xml branch
# 
def recursiveParse(model, model_branch, xml_branch):
    for node in xml_branch:

        # Everything is either a branch.
        if (node.tag == "branch"):
            parent = QtGui.QStandardItem(node.get("name", "NA"))
            parent.setFlags(QtCore.Qt.ItemIsEnabled)
            model_branch.appendRow(parent)
            recursiveParse(model, parent, node)

        # Or a leaf (DaveAction).
        else:
            action = DaveActionStandardItem(node)
            model.addItem(action)
            model_branch.appendRow(action)

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
