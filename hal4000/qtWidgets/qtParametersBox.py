#!/usr/bin/python
#
## @file
#
# Widget containing variable number of radio buttons
# representing all the currently available parameters
# files.
#
# This now contains the widgets for the
# parameters editor as well.
#
# Hazen 02/16
#

import copy
import operator
import os

from PyQt4 import QtCore, QtGui

import qtdesigner.params_editor_ui as paramsEditorUi

import sc_library.hdebug as hdebug
import sc_library.parameters as params

import halLib.parameterEditors as pEditors

def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]


## handleCustomParameter
#
# Returns the appropriate editor widget for a custom parameter.

def handleCustomParameter(root_name, parameter, changed_signal, parent):
    if parameter.editor is not None:
        return parameter.editor(root_name, parameter, changed_signal, parent)
    else:
        return pEditors.ParametersTableWidgetString(root_name, parameter, changed_signal, parent)


## ParametersEditor
#
# This class handles the parameters editor dialog box.
#
class ParametersEditor(QtGui.QDialog):

    updateClicked = QtCore.pyqtSignal()
    
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.editor_widgets = {}  # This dictionary stores all the editor
                                  # widgets indexed by the parameter name.
        self.n_changed = 0
        self.original_parameters = parameters
        self.parameters = copy.deepcopy(parameters)

        self.ui = paramsEditorUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Parameter Editor")

        # Set parameters name.
        self.updateParametersNameLabel()
                                            
        # Remove all tabs.
        for i in range(self.ui.editTabWidget.count()):
            self.ui.editTabWidget.removeTab(0)

        # Add tab for the parameters that are not in a sub-section (i.e. "main").
        new_tab = ParametersEditorTab("", self.parameters, self)
        if (new_tab.getWidgetCount() > 0):
            new_tab.parameterChanged.connect(self.handleParameterChanged)
            self.ui.editTabWidget.addTab(new_tab, "Main")
            self.editor_widgets.update(new_tab.getWidgets())
        else:
            new_tab.close()
        
        # Add tabs for each sub-section of the parameters.
        attrs = sorted(self.parameters.getAttrs())
        for attr in attrs:
            prop = self.parameters.getp(attr)
            if isinstance(prop, params.StormXMLObject):
                new_tab = ParametersEditorTab(attr, prop, self)
                if (new_tab.getWidgetCount() > 0):
                    new_tab.parameterChanged.connect(self.handleParameterChanged)
                    self.ui.editTabWidget.addTab(new_tab, attr.capitalize())
                    self.editor_widgets.update(new_tab.getWidgets())
                else:
                    new_tab.close()

        self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.updateButton.clicked.connect(self.handleUpdate)

        self.updateDisplay()

    @hdebug.debug
    def closeEvent(self, event):
        if (self.n_changed != 0):
            reply = QtGui.QMessageBox.question(self,
                                               "Warning!",
                                               "Parameters have been changed, close anyway?",
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)
            if (reply == QtGui.QMessageBox.No):
                event.ignore()

    def enableUpdateButton(self, state):
        if state:
            self.ui.updateButton.setEnabled(True)
        else:
            self.ui.updateButton.setEnabled(False)

    ## getParameters
    #
    # Returns the original parameters. The original parameters are
    # not changed unless the update button is pressed.
    #
    def getParameters(self):
        return self.original_parameters

    ## handleParameterChanged
    #
    # Handles the parameterChanged signals from the various parameter
    # editor widgets. Basically this just keeps track of how many
    # parameters have been changed, if any and updates the enabled/disabled
    # state of the update button.
    #
    def handleParameterChanged(self, pname, pvalue):
        pname = str(pname)
        self.parameters.setv(pname, pvalue)
        is_modified = self.editor_widgets[pname].setChanged(self.parameters.get(pname) != self.original_parameters.get(pname))
        if (is_modified == "modified"):
            self.n_changed += 1
        elif (is_modified == "reverted"):
            self.n_changed -= 1

        self.updateDisplay()

    @hdebug.debug
    def handleQuit(self, boolean):
        self.close()

    ## handleUpdate
    #
    # Overwrites the original parameters with the modified
    # parameters and sends the updateClicked signal.
    #
    @hdebug.debug
    def handleUpdate(self, boolean):
        for widget in self.editor_widgets:
            self.editor_widgets[widget].resetChanged()
            
        self.original_parameters = copy.deepcopy(self.parameters)
        self.n_changed = 0
        self.updateClicked.emit()

    ## updateDisplay
    #
    # Changes the state of the editor display depending on
    # whether or not there are changed parameters.
    #
    def updateDisplay(self):
        self.enableUpdateButton(self.n_changed != 0)

    ## updateParameters
    #
    # Once the update parameters has been pressed, HAL and the
    # various modules may change some of the parameter values
    # in their newParameters() methods. This function is used so
    # that these changes are reflected in the individual editor
    # widgets.
    #
    # Note that the self.original_parameters object is what
    # was passed to HAL.
    #
    def updateParameters(self):
        for widget_name in self.editor_widgets:
            prop = self.original_parameters.getp(widget_name)
            self.editor_widgets[widget_name].updateParameter(prop)

    def updateParametersNameLabel(self):
        self.ui.parametersNameLabel.setText(getFileName(self.original_parameters.get("parameters_file")))


## ParametersEditorTab
#
# This class handles a tab in the parameters editor dialog box.
#
class ParametersEditorTab(QtGui.QWidget):

    # The signal for the change of the value of a parameter.
    parameterChanged = QtCore.pyqtSignal(str, object)
    
    @hdebug.debug    
    def __init__(self, root_name, parameters, parent):
        QtGui.QWidget.__init__(self, parent)
        self.editor_widgets = {}

        # Create scroll area for displaying the parameters table.
        scroll_area = QtGui.QScrollArea(self)
        layout = QtGui.QGridLayout(self)
        layout.addWidget(scroll_area)

        # Create the parameters table & add to the scroll area.
        self.params_table = ParametersTable(root_name, scroll_area)
        scroll_area.setWidget(self.params_table)
        scroll_area.setWidgetResizable(True)
        
        # Get the parameters.
        all_props = parameters.getProps()
        param_props = []
        for prop in all_props:
            if not isinstance(prop, params.StormXMLObject) and prop.isMutable():
                param_props.append(prop)

        # Sort and add to the table.
        #
        # The keys in the widget dictionary correspond to the full name of
        # the parameter, e.g. "camera1.exposure_time".
        #
        param_props = sorted(param_props, key = operator.attrgetter('order', 'name'))
        for prop in param_props:
            new_widget = self.params_table.addParameter(root_name,
                                                        prop,
                                                        self.parameterChanged)
            self.editor_widgets[new_widget.p_name] = new_widget
                                

    def getWidgetCount(self):
        return len(self.editor_widgets)

    def getWidgets(self):
        return self.editor_widgets
    

## ParametersTable
#
# The table where all the different parameters will get displayed.
#
class ParametersTable(QtGui.QWidget):

    @hdebug.debug
    def __init__(self, root_name, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)

        self.setLayout(QtGui.QGridLayout(self))
        self.layout().setColumnStretch(1, 1)
        for i, name in enumerate(["Name", "Description", "Value", "Order"]):
            label = QtGui.QLabel(name)
            label.setStyleSheet("QLabel { font-weight: bold }")
            self.layout().addWidget(label, 0, i)

    @hdebug.debug
    def addParameter(self, root_name, parameter, changed_signal):
        row = self.layout().rowCount()

        #
        # In order to have everything line up nicely in a grid we need
        # separate widgets for each column. However all the widgets are
        # related to a single parameter, so we associate the widgets
        # together under the editor widget.
        #
        name_label = QtGui.QLabel(parameter.getName())
        self.layout().addWidget(name_label, row, 0)
        desc_label = QtGui.QLabel(parameter.getDescription())
        self.layout().addWidget(desc_label, row, 1)

        # Find the matching editor widget based on the parameter type.
        types = [[params.ParameterCustom, handleCustomParameter],
                 [params.ParameterFloat, pEditors.ParametersTableWidgetFloat],
                 [params.ParameterInt, pEditors.ParametersTableWidgetInt],
                 [params.ParameterRangeFloat, pEditors.ParametersTableWidgetRangeFloat],                 
                 [params.ParameterRangeInt, pEditors.ParametersTableWidgetRangeInt],
                 [params.ParameterSetBoolean, pEditors.ParametersTableWidgetSetBoolean],
                 [params.ParameterSetFloat, pEditors.ParametersTableWidgetSetFloat],
                 [params.ParameterSetInt, pEditors.ParametersTableWidgetSetInt],
                 [params.ParameterSetString, pEditors.ParametersTableWidgetSetString],
                 [params.ParameterString, pEditors.ParametersTableWidgetString],
                 [params.ParameterStringDirectory, pEditors.ParametersTableWidgetDirectory],
                 [params.ParameterStringFilename, pEditors.ParametersTableWidgetFilename]]
        table_widget = next((a_type[1] for a_type in types if (type(parameter) is a_type[0])), None)
        if (table_widget is not None):
            new_widget = table_widget(root_name,
                                      parameter,
                                      changed_signal,
                                      self)
        else:
            print "No widget found for", type(parameter)
            new_widget = QtGui.QLabel(str(parameter.getv()))
        new_widget.setLabels(name_label, desc_label)
        self.layout().addWidget(new_widget, row, 2)
        
        self.layout().addWidget(QtGui.QLabel(str(parameter.order)), row, 3)

        return new_widget
        
    
## ParametersRadioButton
#
# This class encapsulates a set of parameters and it's
# associated radio button.
#
class ParametersRadioButton(QtGui.QRadioButton):

    deleteSelected = QtCore.pyqtSignal(object)
    duplicateSelected = QtCore.pyqtSignal(object)
    updateClicked = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters The parameters object to associate with this radio button.
    # @param parent (Optional) the PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QRadioButton.__init__(self, getFileName(parameters.get("parameters_file")), parent)
        self.changed = False
        self.editor_dialog = None
        self.parameters = parameters

        self.delAct = QtGui.QAction(self.tr("Delete"), self)
        self.delAct.triggered.connect(self.handleDelete)

        self.duplicateAct = QtGui.QAction(self.tr("Duplicate"), self)
        self.duplicateAct.triggered.connect(self.handleDuplicate)

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

        # If it is not the current button it can be deleted.
        if not self.isChecked():
            menu.addAction(self.delAct)
            menu.addAction(self.duplicateAct)
        
        # If it is the current button it's parameters can be edited.
        else:
            menu.addAction(self.editAct)
            menu.addAction(self.duplicateAct)

        # If it has been changed then it can be saved.
        if self.changed:
            menu.addAction(self.saveAct)
            
        menu.exec_(event.globalPos())

    ## enableEditor
    #
    def enableEditor(self):
        if self.editor_dialog is not None:
            self.editor_dialog.enableUpdateButton(self.isChecked())
        
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
    def handleDelete(self, boolean):
        self.deleteSelected.emit(self)

    ## handleDuplicate
    #
    # Handles the duplicate action.
    #
    @hdebug.debug
    def handleDuplicate(self, boolean):
        self.duplicateSelected.emit(self)
    
    ## handleEdit
    #
    # Handles the edit action.
    #
    @hdebug.debug
    def handleEdit(self, boolean):
        if self.editor_dialog is None:
            self.editor_dialog = ParametersEditor(self.parameters, self)
            self.editor_dialog.destroyed.connect(self.handleEditorDestroyed)
            self.editor_dialog.updateClicked.connect(self.handleUpdate)
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
    def handleSave(self, boolean):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                         "Choose File", 
                                                         os.path.dirname(str(self.parameters.get("parameters_file"))),
                                                         "*.xml"))
        if filename:
            self.changed = False
            self.setText(getFileName(filename))
            self.parameters.set("parameters_file", filename)
            self.editor_dialog.updateParametersNameLabel()
            self.parameters.saveToFile(filename)
            self.updateDisplay()

    ## handleUpdate
    #
    # Handles when the update button is clicked in the parameters editor.
    #
    def handleUpdate(self):
        self.changed = True
        self.parameters = self.editor_dialog.getParameters()
        self.updateClicked.emit(self)
        self.updateDisplay()

    ## updateDisplay
    #
    def updateDisplay(self):
        if self.changed:
            #
            # FIXME: I really wanted to change the text color but for reasons that
            #        are completely opaque to me this appears to be impossible short
            #        of creating a custom radio button widget.
            #
            self.setStyleSheet("QRadioButton { background-color: rgb(255,200,200); }")
        else:
            self.setStyleSheet("")
        self.update()

    ## updateParameters
    #
    def updateParameters(self):
        if self.editor_dialog is not None:
            self.editor_dialog.updateParameters()

        
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

        self.button_group = QtGui.QButtonGroup(self)
        
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
        
        self.button_group.addButton(radio_button)
        self.layout.insertWidget(0, radio_button)
        self.radio_buttons.append(radio_button)

        radio_button.clicked.connect(self.toggleParameters)
        radio_button.deleteSelected.connect(self.handleDelete)
        radio_button.duplicateSelected.connect(self.handleDuplicate)
        radio_button.updateClicked.connect(self.handleUpdate)
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

    ## handleDelete
    #
    # Handles the deleteSelected signal from a parameters radio button.
    #
    @hdebug.debug
    def handleDelete(self, button):
        self.button_group.removeButton(button)
        self.layout.removeWidget(button)
        self.radio_buttons.remove(button)
        button.close()

    ## handleDuplicate
    #
    # Handles the duplicateSelected signal from a parameters radio button.
    #
    @hdebug.debug
    def handleDuplicate(self, button):
        parameters = button.getParameters()
        self.addParameters(copy.deepcopy(parameters))

    ## handleUpdate
    #
    # Handles the updateClicked signal from a parameters radio button.
    #
    @hdebug.debug
    def handleUpdate(self, button):
        self.current_parameters = button.getParameters()
        self.settings_toggled.emit()
        
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
            button.enableEditor()
            if button.isChecked() and (button != self.current_button):
                self.current_button = button
                self.current_parameters = button.getParameters()
                self.settings_toggled.emit()

    ## updateParameters
    #
    # This is called by HAL after calling newParameters so that any changes
    # to the parameters can flow back to the parameter editor (if it exists).
    #
    def updateParameters(self):
        for button in self.radio_buttons:
            if button.isChecked():
                button.updateParameters()

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

