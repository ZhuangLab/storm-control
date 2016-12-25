#!/usr/bin/python
#
## @file
#
# A collection of classes to control the construction and display of Dave Warning
# objects with the goal of providing enhanced user control over when and how Dave
# pauses in response to issues encountered during a run. 
#
# Jeff 1/16 
#

## Imports.
from PyQt5 import QtCore, QtGui, QtWidgets
from datetime import datetime

## DaveWarning
#
# A QStandardItem specialized to hold information about a DaveWarning
#
class DaveWarning(QtGui.QStandardItem):

    ## __init__
    #
    # @param dave_action_si The daveActionStandardItem on which the error was generated
    # @param message_str A string describing the error (Typically provided by the message)
    #
    def __init__(self, dave_action_si,
                 message_str = "Unknown warning",
                 descriptor = "Unknown warning"):
        # Archive dave action corresponding to the warning
        self.dave_action_si = dave_action_si
        self.warning_str = message_str
        self.descriptor = descriptor
        self.creation_time = datetime.now()
        self.parent_name = dave_action_si.getParentName()

        # Initislize standard item and set display/selectability properties
        QtGui.QStandardItem.__init__(self, descriptor)
        self.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
    
    ## getDaveStandardItem
    #
    # @return The DaveActionStandardItem associated with this item.
    #
    def getDaveActionStandardItem(self):
        return self.dave_action_si

    ## getDescriptor
    #
    # @return The name of the warning.
    #
    def getDescriptor(self):
        return self.descriptor

    ## getWarningMessage
    #
    # @return The warning message associated with this item.
    #
    def getWarningMessage(self):
        return self.warning_str

    ## getParentName
    #
    # @return The name of the parent of the Dave Action that generated the warning.
    #
    def getParentName(self):
        return self.parent_name

    ## getFullInfo
    #
    # Create a formatted string describing the full information around the warning
    #
    # @return A string describing everything about the warning
    #
    def getFullInfo(self):
        warning_string = self.descriptor + ": \n"
        warning_string = warning_string + "Created: " + str(self.creation_time) + "\n"
        warning_string = warning_string + "Parent: " + self.parent_name + "\n"
        warning_string = warning_string + self.warning_str + "\n"
        return warning_string

## DaveWarningsModel
#
# A QStandardItemModel specialized for Dave Warnings.
#
class DaveWarningsModel(QtGui.QStandardItemModel):

    ## __init__
    #
    def __init__(self):
        QtGui.QStandardItemModel.__init__(self)
        self.dave_warning_sis = [] # List of all DaveWarningStandardItems

    ## addItem
    #
    # @param dave_warning_si A DaveWarningStandardItem.
    #
    def addItem(self, dave_warning_si):
        self.dave_warning_sis.append(dave_warning_si)
        self.appendRow(dave_warning_si)

    ## count
    #
    # @return Then number of items in the model.
    #
    def count(self):
        return len(self.dave_warning_sis)

    ## createSummaryMessage
    #
    # Create a summary message for all warnings
    #
    def createSummaryMessage(self):
        summary_message = "Exceeded the maximum number of warnings: \n"
        for dw_item in self.dave_warning_sis:
            summary_message = summary_message + "\n"
            summary_message = summary_message + dw_item.getFullInfo()
        return summary_message

## DaveWarningsViewer
#
# This class wraps the list view and it's associated model.
#
class DaveWarningsViewer(QtWidgets.QListView):
    double_clicked = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parent (Optional) defaults to none.
    #
    def __init__(self, parent = None):
        QtWidgets.QListView.__init__(self, parent)

        self.warnings_model = DaveWarningsModel() # Initialize the model
        QtWidgets.QListView.setModel(self, self.warnings_model)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.doubleClicked.connect(self.handleDoubleClick)

    ## addWarning
    #
    # @param dave_action_si A DaveWarningStandardItem associated with the warning
    # @param message_str The warning message
    # @param descriptor the displayed description
    #
    def addWarning(self, dave_action_si,
                 message_str = "Unknown warning",
                 descriptor = "Unknown warning"):

        dave_warning_si = DaveWarning(dave_action_si,
                                      message_str = message_str,
                                      descriptor = descriptor)

        # Add the item, and scroll to it
        self.warnings_model.addItem(dave_warning_si)
        self.scrollTo(self.warnings_model.indexFromItem(dave_warning_si))

        # Draw viewport
        self.viewport().update()

    ## clearWarnings
    #
    # Clear all warnings
    #
    def clearWarnings(self):
        # Simply create a new empty model
        self.warnings_model = DaveWarningsModel() # Initialize the model
        QtWidgets.QListView.setModel(self, self.warnings_model)

        # Draw viewport
        self.viewport().update()

    ## count
    #
    # @return Then number of items in the model.
    #
    def count(self):
        if self.warnings_model is not None:
            return self.warnings_model.count()
        else:
            return 0

    ## handleDoubleClick
    #
    # @param model_index The QModelIndex of the time that was doubled clicked.
    #
    def handleDoubleClick(self, model_index):
        if self.warnings_model is not None:
            qt_item = self.warnings_model.itemFromIndex(model_index)
            self.double_clicked.emit(qt_item)

    ## getSummaryMessage
    #
    # Return the summary message
    #
    def getSummaryMessage(self):
        return self.warnings_model.createSummaryMessage()

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
