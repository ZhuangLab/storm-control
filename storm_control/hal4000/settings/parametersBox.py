#!/usr/bin/env python
"""
Listview containing a variable number of elements representing 
all of the currently available parameters files.

Hazen 04/17
"""

import os

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.settings.parametersEditorDialog as parametersEditorDialog

import storm_control.hal4000.qtdesigner.settings_ui as settingsUi


class ParametersBox(QtWidgets.QGroupBox):
    """
    The group box that contains the parameters ListView.
    """
    editParameters = QtCore.pyqtSignal()
    newParameters = QtCore.pyqtSignal(object, bool)

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.default_parameters = None
        self.editor_dialog = None
        self.editor_window_title = module_params.get("setup_name") + " parameters editor"
        self.enabled = True
        self.qt_settings = qt_settings

        self.ui = settingsUi.Ui_GroupBox()
        self.ui.setupUi(self)

        self.ui.settingsListView.setStyleSheet("QListView { background-color: transparent;}")

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
        # If value was explicitly set to 'None' return the current parameters.
        if value is None:
            return self.getCurrentParameters().copy()

        # Otherwise return the requested parameters.
        else:
            q_item = self.ui.settingsListView.getQItemByValue(value)
            if q_item is not None:
                return self.ui.settingsListView.getItemParameters(q_item).copy()

    def handleEditorClosed(self):
        self.editor_dialog.closed.disconnect()
        self.editor_dialog.update.disconnect()
        self.editor_dialog = None

        # Reenable the ListView when we are done editing the parameters.
        self.enableUI(True)

    def handleEditorUpdate(self, parameters):
        self.newParameters.emit(parameters, True)

        # FIXME: Probably only want to do this if the change was successful.
        self.ui.settingsListView.setRCParametersStale(True)

    def handleEditParameters(self):

        # Disable the ListView while we are editing the parameters.
        self.enableUI(False)

        # Emit editParameters signal. This will cause settings.settings to emit
        # the "current parameters". Other modules will respond with their current
        # parameters we'll start the editor. We take this approach because the
        # version of the parameters that the list view are likely stale.
        self.editParameters.emit()

    def handleNewParameters(self, parameters):
        self.newParameters.emit(parameters, False)

    def handleSaveParameters(self, parameters):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                         "Choose File", 
                                                         os.path.dirname(str(parameters.get("parameters_file"))),
                                                         "*.xml")[0]
        if filename:
            if not filename.endswith(".xml"):
                filename += ".xml"
            parameters.set("parameters_file", filename)
            parameters.saveToFile(filename)
            setting_name = os.path.splitext(os.path.basename(filename))[0]
            self.ui.settingsListView.setRCParametersName(setting_name)
            self.ui.settingsListView.setRCParametersStale(False)
            self.ui.settingsListView.updateRCToolTip()

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

        Returns [found - True/False, current - True/False]
        """
        q_item = self.ui.settingsListView.getQItemByValue(value)
        if q_item is None:
            return [False, False]
        else:
            if (q_item == self.ui.settingsListView.getCurrentItem()):
                return [True, True]
            else:
                self.ui.settingsListView.setCurrentItem(q_item)
                return [True, False]

    def startParameterEditor(self):
        self.editor_dialog = parametersEditorDialog.ParametersEditorDialog(window_title = self.editor_window_title,
                                                                           qt_settings = self.qt_settings,
                                                                           parameters = self.ui.settingsListView.getCurrentParameters(),
                                                                           parent = halDialog.HalDialog.qt_parent)
        self.editor_dialog.closed.connect(self.handleEditorClosed)
        self.editor_dialog.update.connect(self.handleEditorUpdate)
        self.editor_dialog.show()

    def updateCurrentParameters(self, section, parameters):
        """
        This updates the currently selected parameters with values
        received either in the 'initial parameters' message, or as
        a response to the 'new parameters' message.
        """
        curp = self.ui.settingsListView.getCurrentParameters()
        curp.addSubSection(section,
                           svalue = parameters,
                           overwrite = True)

    def updateEditor(self):
        # We should not end up here if there is no editor dialog.
        assert (self.editor_dialog is not None)
        self.editor_dialog.updateParameters(self.getCurrentParameters())
        
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

