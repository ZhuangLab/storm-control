#!/usr/bin/python
#
## @file
#
# Widget containing variable number of radio buttons
# representing all the currently available parameters
# files.
#
# Hazen 01/14
#

import os

from PyQt4 import QtCore, QtGui

def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]


## Parameters
#
# This class encapsulates a set of parameters and their
# associated radio button.
#
class ParametersRadioButton(QtGui.QRadioButton):

    deleteSelected = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parameters The parameters object to associate with this radio button.
    # @param parent (Optional) the PyQt parent of this object.
    #
    def __init__(self, parameters, parent = None):
        QtGui.QRadioButton.__init__(self, getFileName(parameters.parameters_file), parent)
        self.delete_desired = False
        self.parameters = parameters

        self.delAct = QtGui.QAction(self.tr("Delete"), self)
        self.delAct.triggered.connect(self.handleDelete)

    ## contextMenuEvent
    #
    # This is called to create the popup menu when the use right click on the parameters box.
    #
    # @param event A PyQt event object.
    #
    def contextMenuEvent(self, event):
        if not self.isChecked():
            menu = QtGui.QMenu(self)
            menu.addAction(self.delAct)
            menu.exec_(event.globalPos())

    ## getParameters
    #
    # @return The parameters associated with this radio button.
    #
    def getParameters(self):
        return self.parameters

    ## handleDelete
    #
    # Handles the delete action.
    #
    def handleDelete(self):
        self.delete_desired = True
        self.deleteSelected.emit()


## QParametersBox
#
# This class handles displaying and interacting with
# the various parameter files that the user has loaded.
#
class QParametersBox(QtGui.QWidget):

    settings_toggled = QtCore.pyqtSignal(name = 'settingsToggled')

    ## __init__
    #
    # @param parent (Optional) the PyQt parent of this object.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.current_parameters = None
        self.current_button = False
        self.radio_buttons = []
        
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setMargin(4)
        self.layout.setSpacing(2)
        self.layout.addSpacerItem(QtGui.QSpacerItem(20, 
                                                    12,
                                                    QtGui.QSizePolicy.Minimum,
                                                    QtGui.QSizePolicy.Expanding))

    ## addParameters
    #
    # Add a set of parameters to the parameters box.
    #
    # @param parameters A parameters object.
    #
    def addParameters(self, parameters):
        self.current_parameters = parameters
        radio_button = ParametersRadioButton(parameters)
        self.radio_buttons.append(radio_button)
        self.layout.insertWidget(0, radio_button)
        radio_button.clicked.connect(self.toggleParameters)
        radio_button.deleteSelected.connect(self.handleDeleteSelected)
        if (len(self.radio_buttons) == 1):
            radio_button.click()

    ## getButtonNames
    #
    # @return A list containing the names of each of the buttons.
    #
    def getButtonNames(self):
        return map(lambda(x): x.text(), self.radio_buttons)

    ## getCurrentParameters
    #
    # @return The current parameters object.
    #
    def getCurrentParameters(self):
        return self.current_parameters

    ## getIndexOfParameters
    #
    # @param param_index An integer or a string specifying the identifier of the parameters.
    # 
    # @return The index of the requested parameters.
    #
    def getIndexOfParameters(self, param_index):
        button_names = self.getButtonNames()
        if param_index in button_names:
            return button_names.index(param_index)
        elif param_index in range(len(button_names)):
            return param_index
        else:
            return -1

    ## getParameters
    #
    # Returns the requested parameters if the request is valid.
    #
    # @param param_index An integer or a string specifying the identify of the parameters
    #
    def getParameters(self, param_index):
        index = self.getIndexOfParameters(param_index)
        if (index != -1):
            return self.radio_buttons[index].getParameters()
        else:
            return None

    ## handleDeleteSelected
    #
    # Handles the deleteSelected action from a parameters radio button.
    #
    def handleDeleteSelected(self):
        for [button_ID, button] in enumerate(self.radio_buttons):
            if button.delete_desired:
                self.layout.removeWidget(button)
                self.radio_buttons.remove(button)
                button.close()

    ## isValidParameters
    #
    # Returns true if the requested parameters exist.
    #
    # @param param_index An integer or a string specifying the identify of the parameters
    #
    def isValidParameters(self, param_index):
        # Warn if there are multiple parameters with the same name?
        if (self.getIndexOfParameters(param_index) != -1):
            return True
        else:
            return False
        
    ## setCurrentParameters
    #
    # Select one of the parameter choices in the parameters box.
    #
    # @param param_index The name or index of the requested parameters
    #
    # @return True/False is the selected parameters are the current parameters.
    #
    def setCurrentParameters(self, param_index):
        index = self.getIndexOfParameters(param_index)
        if (index != -1):
            if (self.radio_buttons[index] == self.current_button):
                return True
            else:
                self.radio_buttons[index].click()
                return False
        else:
            print "Requested parameter index not available", param_index
            return True

    ## startFilm
    #
    # Called at the start of filming to disable the radio buttons.
    #
    def startFilm(self):
        for button in self.radio_buttons:
            button.setEnabled(False)

    ## stopFilm
    #
    # Called at the end of filming to enable the radio buttons.
    #
    def stopFilm(self):
        for button in self.radio_buttons:
            button.setEnabled(True)
            
    ## toggleParameters
    #
    # This is called when one of the radio buttons is clicked to figure out
    # which parameters were selected. It emits a settings_toggled signal to
    # indicate that the settings have been changed.
    #
    # @param bool Dummy parameter.
    #
    def toggleParameters(self, bool):
        for button in self.radio_buttons:
            if button.isChecked() and (button != self.current_button):
                self.current_button = button
                self.current_parameters = button.getParameters()
                self.settings_toggled.emit()


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

