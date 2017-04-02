#!/usr/bin/env python
"""
Listview containing a variable number of elements representing 
all of the currently available parameters files.

This now contains the widgets for the parameters editor as well.

Hazen 01/17
"""

import copy
import operator
import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.parameterEditors as pEditors
import storm_control.hal4000.qtdesigner.params_editor_ui as paramsEditorUi
import storm_control.hal4000.qtdesigner.settings_ui as settingsUi


def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]


def handleCustomParameter(root_name, parameter, changed_signal, parent):
    """
    Returns the appropriate editor widget for a custom parameter.
    """
    if parameter.editor is not None:
        return parameter.editor(root_name, parameter, changed_signal, parent)
    else:
        return pEditors.ParametersTableWidgetString(root_name, parameter, changed_signal, parent)


#
# Parameter editor dialog section.
#
class ParametersEditor(QtWidgets.QDialog):
    """
    This class handles the parameters editor dialog box.
    """
    updateClicked = QtCore.pyqtSignal()
    
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)

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

    def closeEvent(self, event):
        if (self.n_changed != 0):
            reply = QtWidgets.QMessageBox.question(self,
                                                   "Warning!",
                                                   "Parameters have been changed, close anyway?",
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)
            if (reply == QtWidgets.QMessageBox.No):
                event.ignore()
                
        self.accept()

    def enableUpdateButton(self, state):
        if state:
            self.ui.updateButton.setEnabled(True)
        else:
            self.ui.updateButton.setEnabled(False)

    def getParameters(self):
        """
        Returns the original parameters. The original parameters are
        not changed unless the update button is pressed.
        """
        return self.original_parameters

    def handleParameterChanged(self, pname, pvalue):
        """
        Handles the parameterChanged signals from the various parameter
        editor widgets. Basically this just keeps track of how many
        parameters have been changed, if any and updates the enabled/disabled
        state of the update button.
        """
        pname = str(pname)
        self.parameters.setv(pname, pvalue)
        is_modified = self.editor_widgets[pname].setChanged(self.parameters.get(pname) != self.original_parameters.get(pname))
        if (is_modified == "modified"):
            self.n_changed += 1
        elif (is_modified == "reverted"):
            self.n_changed -= 1

        self.updateDisplay()

    def handleQuit(self, boolean):
        self.close()

    def handleUpdate(self, boolean):
        """
        Overwrites the original parameters with the modified
        parameters and sends the updateClicked signal.
        """
        for widget in self.editor_widgets:
            self.editor_widgets[widget].resetChanged()
            
        self.original_parameters = copy.deepcopy(self.parameters)
        self.n_changed = 0
        self.updateClicked.emit()

    def updateDisplay(self):
        """
        Changes the state of the editor display depending on
        whether or not there are changed parameters.
        """
        self.enableUpdateButton(self.n_changed != 0)

    def updateParameters(self):
        """
        FIXME: HAL should not work this way! Pass changes to
               the parameters back as messages!

        Once the update parameters has been pressed, HAL and the
        various modules may change some of the parameter values
        in their newParameters() methods. This function is used so
        that these changes are reflected in the individual editor
        widgets.
        
        Note that the self.original_parameters object is what
        was passed to HAL.
        """
        for widget_name in self.editor_widgets:
            prop = self.original_parameters.getp(widget_name)
            self.editor_widgets[widget_name].updateParameter(prop)

    def updateParametersNameLabel(self):
        self.ui.parametersNameLabel.setText(getFileName(self.original_parameters.get("parameters_file")))


class ParametersEditorTab(QtWidgets.QWidget):
    """
    This class handles a tab in the parameters editor dialog box.
    """

    # The signal for the change of the value of a parameter.
    parameterChanged = QtCore.pyqtSignal(str, object)
    
    def __init__(self, root_name = "", parameters = None, **kwds):
        super().__init__(**kwds)

        self.editor_widgets = {}

        # Create scroll area for displaying the parameters table.
        scroll_area = QtWidgets.QScrollArea(self)
        layout = QtWidgets.QGridLayout(self)
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
    

class ParametersTable(QtWidgets.QWidget):
    """
    The table where all the different parameters will get displayed.
    """
    def __init__(self, root_name = "", **kwds):
        super().__init__(**kwds)

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)

        self.setLayout(QtWidgets.QGridLayout(self))
        self.layout().setColumnStretch(1, 1)
        for i, name in enumerate(["Name", "Description", "Value", "Order"]):
            label = QtWidgets.QLabel(name)
            label.setStyleSheet("QLabel { font-weight: bold }")
            self.layout().addWidget(label, 0, i)

    def addParameter(self, root_name, parameter, changed_signal):
        row = self.layout().rowCount()

        #
        # In order to have everything line up nicely in a grid we need
        # separate widgets for each column. However all the widgets are
        # related to a single parameter, so we associate the widgets
        # together under the editor widget.
        #
        name_label = QtWidgets.QLabel(parameter.getName())
        self.layout().addWidget(name_label, row, 0)
        desc_label = QtWidgets.QLabel(parameter.getDescription())
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
            print("No widget found for", type(parameter))
            new_widget = QtWidgets.QLabel(str(parameter.getv()))
        new_widget.setLabels(name_label, desc_label)
        self.layout().addWidget(new_widget.getQtWidget(), row, 2)

        self.layout().addWidget(QtWidgets.QLabel(str(parameter.order)), row, 3)

        return new_widget
        

#
# Parameters display section.
#
class ParametersBox(QtWidgets.QGroupBox):
    """
    
    """
    newParameters = QtCore.pyqtSignal(object, bool)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.default_parameters = None
        self.enabled = True

        self.ui = settingsUi.Ui_GroupBox()
        self.ui.setupUi(self)

        self.ui.settingsListView.setStyleSheet("background-color: transparent;")

        self.ui.settingsListView.editParameters.connect(self.handleEditParameters)
        self.ui.settingsListView.newParameters.connect(self.handleNewParameters)
        self.ui.settingsListView.saveParameters.connect(self.handleSaveParameters)

    def addParameters(self, parameters, is_default = False):
        """
        Add new parameters to the ListView.
        """
        if is_default:
            self.default_parameters = parameters
        name = os.path.splitext(os.path.basename(parameters.get("parameters_file")))[0]
        self.ui.settingsListView.addParameters(name, parameters)

    def copyDefaultParameters(self):
        """
        Make a copy of the parameters that were used for the
        default settings. This breaks the link between them
        and what is shown in GUI so that if the user changes
        the GUI default paramters it does not effect the
        'true' default parameters.
        """
        self.default_parameters = self.default_parameters.copy()

    def enableUI(self, state):
        self.enabled = state
        self.ui.settingsListView.setEnabled(state)

    def getCurrentParameters(self):
        """
        Return the current parameters.
        """
        return self.ui.settingsListView.getCurrentParameters()
        
    def getEnabled(self):
        return self.enabled

    def getParameters(self, value):
        """
        Return a copy of parameters that correspond to name, which could 
        be an integer (the row number) or the parameters name.
        """
        q_item = self.ui.settingsListView.getQItemByValue(value)
        if q_item is not None:
            return self.ui.settingsListView.getItemParameters(q_item).copy()

    def handleEditParameters(self, parameters):

        # Disable the ListView while we are editting the parameters.
        self.enableUI(False)

        #.. edit something ..

        # Re-enable the ListView.
        self.enableUI(True)

    def handleNewParameters(self, parameters):
        self.newParameters.emit(parameters, False)

    def handleSaveParameters(self, parameters):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                         "Choose File", 
                                                         os.path.dirname(str(parameters.get("parameters_file"))),
                                                         "*.xml")[0]
        if filename:
            self.changed = False
            self.setText(getFileName(filename))
            self.parameters.set("parameters_file", filename)
            if self.editor_dialog is not None:
                self.editor_dialog.updateParametersNameLabel()
            self.parameters.saveToFile(filename)
            self.updateDisplay()

    def markCurrentAsInitialized(self):
        cur_p = self.getCurrentParameters()
        cur_p.set("initialized", True)
        
    def newParametersFile(self, filename, is_default):
        """
        Load new parameters from a file.
        """
        new_p = params.halParameters(filename)
        [p, unrecognized] = params.copyParameters(self.default_parameters, new_p)
        if (len(unrecognized) > 0):
            msg = "The following parameters were not recognized: "
            msg += ", ".join(unrecognized) + ". Perhaps they are not in the correct sub-section?"
            halMessageBox.halMessageBoxInfo(msg)

        # Mark as not having been used.
        p.set("initialized", False)

        # In the current state, this will only work if the 'default' parameters
        # are also the currently selected parameters. This should not be a problem
        # for now as is_default will only be True at startup.
        if is_default:
            
            # Get the parameters labeled 'default'. They should exist because
            # we only expect to have to handle this at initialization.
            q_item = self.ui.settingsListView.getQItemByValue("default")

            # Replace them with these parameters.
            self.ui.settingsListView.setItemParameters(q_item, p)

            # Also set there parameters as default.
            #
            # FIXME: We'll have issues if the new default parameters are
            # bad, as there is no pathway to reset the default parameters.
            #
            self.default_parameters = p.copy()

            # Emit a 'new parameters' message.
            self.newParameters.emit(p, True)
            
        # Otherwise, just add the parameters to the ListView.
        else:
            self.addParameters(p)

    def revertSelection(self):
        """
        The currently selected parameters are bad, go back to the previous ones.
        """
        self.ui.settingsListView.revertToPreviousItem()

    def setParameters(self, value):
        """
        Set the current parameters to be those that correspond to name, which 
        can be an integer (the row number), or a string (the name of the parameters).
        """
        q_item = self.ui.settingsListView.getParametersItem(value)
        self.ui.settingsListView.setCurrentItem(q_item)

    def updateCurrentParameters(self, section, parameters):
        """
        This updates the currently selected parameters with values
        received either in the 'initial parameters' message, or as
        a response to the 'new parameters' message.
        """
        curp = self.ui.settingsListView.getCurrentParameters()
        print(">ucp", section)
        curp.addSubSection(section,
                           svalue = parameters,
                           overwrite = True)

    def updatePreviousParameters(self, section, parameters):
        """
        The modules will response to 'new parameters' by adding their current
        parameters to the response. Exchange whatever we had for each
        module with its current parameters.
        """
        prevp = self.ui.settingsListView.getPreviousParameters()
        if prevp is not None:
            prevp.addSubSection(section,
                                svalue = parameters,
                                overwrite = True)


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

