#!/usr/bin/python
#
## @file
#
# Widget containing variable number of radio buttons
# representing all the currently available parameters
# files.
#
# Hazen 02/16
#

import os

from PyQt4 import QtCore, QtGui

import qtdesigner.params_editor_ui as paramsEditorUi

import sc_library.hdebug as hdebug
import sc_library.parameters as params


def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]


## ParametersEditor
#
# This class handles the parameters editor dialog box.
#
class ParametersEditor(QtGui.QDialog):

    updateClicked = QtCore.pyqtSignal()
    
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.modified = False
        self.parameters = parameters

        self.ui = paramsEditorUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Parameter Editor")

        # Remove all tabs.
        for i in range(self.ui.editTabWidget.count()):
            self.ui.editTabWidget.removeTab(0)

        # Add tab for the parameters that are not in a sub-section.
        self.ui.editTabWidget.addTab(ParametersEditorTab(self.parameters, self), "Main")
        
        # Add tabs for each sub-section of the parameters.
        #
        # FIXME: skip feed parameters? Do they even work with the new style parameters?
        #
        attrs = self.parameters.getAttrs()
        for attr in attrs:
            prop = self.parameters.getp(attr)
            if isinstance(prop, params.StormXMLObject):
                self.ui.editTabWidget.addTab(ParametersEditorTab(prop, self),
                                             attr.capitalize())
    
        self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.updateButton.clicked.connect(self.handleUpdate)

    @hdebug.debug
    def closeEvent(self, event):
        if self.modified:
            reply = QtGui.QMessageBox.question(self,
                                               "Warning!",
                                               "Parameters have been changed, close anyway?",
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)
            if (reply == QtGui.QMessageBox.No):
                event.ignore()

    @hdebug.debug
    def handleQuit(self, boolean):
        self.close()

    @hdebug.debug
    def handleUpdate(self, boolean):
        self.updateClicked.emit()


## ParametersEditorTab
#
# This class handles a tab in the parameters editor dialog box.
#
class ParametersEditorTab(QtGui.QWidget):

    @hdebug.debug    
    def __init__(self, parameters, parent):
        QtGui.QWidget.__init__(self, parent)

        self.params_mvc = ParametersMVC(self)
        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.params_mvc)
        
        attrs = parameters.getAttrs()
        for attr in attrs:
            param = parameters.getp(attr)
            if not isinstance(param, params.StormXMLObject):
                self.params_mvc.addParameter(param)


## ParametersMVC
#
# Encapsulates a table view specialized for parameters and it's
# associated model. There will be one of these per tab.
#
class ParametersMVC(QtGui.QTableView):

    @hdebug.debug
    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)

        self.params_model = QtGui.QStandardItemModel(self)
        self.params_proxy_model = QtGui.QSortFilterProxyModel(self)
        self.params_proxy_model.setSourceModel(self.params_model)
        self.setModel(self.params_model)

    def addParameter(self, parameter):
        self.params_model.appendRow([QtGui.QStandardItem(parameter.name),
                                     QtGui.QStandardItem(str(parameter.value)),
                                     QtGui.QStandardItem(str(parameter.order))])


## ParametersRadioButton
#
# This class encapsulates a set of parameters and it's
# associated radio button.
#
class ParametersRadioButton(QtGui.QRadioButton):

    deleteSelected = QtCore.pyqtSignal()
    updateSelected = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parameters The parameters object to associate with this radio button.
    # @param parent (Optional) the PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QRadioButton.__init__(self, getFileName(parameters.get("parameters_file")), parent)
        self.changed = False
        self.delete_desired = False
        self.editor_dialog = None
        self.parameters = parameters

        self.delAct = QtGui.QAction(self.tr("Delete"), self)
        self.delAct.triggered.connect(self.handleDelete)

        self.editAct = QtGui.QAction(self.tr("Edit"), self)
        self.editAct.triggered.connect(self.handleEdit)

        self.saveAct = QtGui.QAction(self.tr("Save"), self)
        self.saveAct.triggered.connect(self.handleSave)


    ## contextMenuEvent
    #
    # This is called to create the popup menu when the use right click on the parameters box.
    #
    # @param event A PyQt event object.
    #
    @hdebug.debug
    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        if not self.isChecked():
            menu.addAction(self.delAct)
        menu.addAction(self.editAct)
        if self.changed:
            menu.addAction(self.saveAct)
        menu.exec_(event.globalPos())

    ## getParameters
    #
    # @return The parameters associated with this radio button.
    #
    @hdebug.debug
    def getParameters(self):
        return self.parameters

    ## handleDelete
    #
    # Handles the delete action.
    #
    @hdebug.debug
    def handleDelete(self):
        self.delete_desired = True
        self.deleteSelected.emit()

    ## handleEdit
    #
    # Handles the edit action.
    #
    @hdebug.debug
    def handleEdit(self, boolean):
        if self.editor_dialog is None:
            self.editor_dialog = ParametersEditor(self.parameters, self)
            self.editor_dialog.destroyed.connect(self.handleEditorDestroyed)
        self.editor_dialog.show()

    ## handleEditorDestroyed
    #
    @hdebug.debug
    def handleEditorDestroyed(self):
        print "destroyed"
        self.editor_dialog = None
        
    ## handleSave
    #
    # Handles the save action.
    #
    @hdebug.debug
    def handleSave(self):
        pass
        #self.saveSelected.emit()


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
    @hdebug.debug
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
    @hdebug.debug
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
    @hdebug.debug
    def getButtonNames(self):
        return map(lambda(x): x.text(), self.radio_buttons)

    ## getCurrentParameters
    #
    # @return The current parameters object.
    #
    @hdebug.debug
    def getCurrentParameters(self):
        return self.current_parameters

    ## getIndexOfParameters
    #
    # @param param_index An integer or a string specifying the identifier of the parameters.
    # 
    # @return The index of the requested parameters.
    #
    @hdebug.debug
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
    @hdebug.debug
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
    @hdebug.debug
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
    @hdebug.debug
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
    @hdebug.debug
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
    @hdebug.debug
    def startFilm(self):
        for button in self.radio_buttons:
            button.setEnabled(False)

    ## stopFilm
    #
    # Called at the end of filming to enable the radio buttons.
    #
    @hdebug.debug
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
    @hdebug.debug
    def toggleParameters(self, bool):
        for button in self.radio_buttons:
            if button.isChecked() and (button != self.current_button):
                self.current_button = button
                self.current_parameters = button.getParameters()
                self.settings_toggled.emit()


#
# The MIT License
#
# Copyright (c) 2016 Zhuang Lab, Harvard University
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

