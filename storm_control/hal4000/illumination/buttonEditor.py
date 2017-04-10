#!/usr/bin/python
#
## @file
#
# Custom editor for illumination power buttons.
#
# Hazen 05/16
#

from operator import itemgetter
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug

import storm_control.hal4000.settings.parametersEditors as parametersEditors
import storm_control.hal4000.illumination.button_editor_ui as buttonEditorUi


## ButtonEditorRow
#
# A single row in the button editor table.
#
class ButtonEditorRow(QtWidgets.QWidget):

    delete = QtCore.pyqtSignal(object)

    def __init__(self, channel, name, power, channel_names, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(0,0,0,0)

        # Channel selector combo box.
        self.channel_cbox = QtWidgets.QComboBox(self)
        self.channel_cbox.addItems(channel_names)
        self.channel_cbox.setCurrentIndex(channel)
        self.channel_cbox.setMaximumWidth(100)
        self.channel_cbox.setMinimumWidth(100)
        self.layout().addWidget(self.channel_cbox)

        # Button name editor.
        self.name_editor = QtWidgets.QLineEdit(name, self)
        self.name_editor.setMaximumWidth(100)
        self.name_editor.setMinimumWidth(100)
        self.layout().addWidget(self.name_editor)
                
        # Button value spin box.
        self.power_sbox = QtWidgets.QDoubleSpinBox(self)
        self.power_sbox.setValue(power)
        self.power_sbox.setMinimum(0.0)
        self.power_sbox.setMaximum(1.0)
        self.power_sbox.setSingleStep(0.1)
        self.power_sbox.setMaximumWidth(100)
        self.power_sbox.setMinimumWidth(100)
        self.layout().addWidget(self.power_sbox)

        # Delete button
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.setMaximumWidth(100)
        self.delete_button.setMinimumWidth(100)
        self.delete_button.clicked.connect(self.handleDeleteAction)
        self.layout().addWidget(self.delete_button)
        
        self.layout().addStretch()

    def getValues(self):
        return [self.channel_cbox.currentIndex(),
                str(self.name_editor.text()),
                self.power_sbox.value()]

    def handleDeleteAction(self, boolean):
        self.delete.emit(self)

        
## ButtonEditorTable
#
# The table where all the different buttons will get displayed.
#
class ButtonEditorTable(QtWidgets.QWidget):

    def __init__(self, buttons, channel_names, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)

        self.channel_names = channel_names
        
        self.setLayout(QtWidgets.QVBoxLayout(self))

        # Add header row.
        widget = QtWidgets.QWidget(self)
        widget.setLayout(QtWidgets.QHBoxLayout(widget))
        for i, name in enumerate(["Channel", "Name", "Power"]):
            label = QtWidgets.QLabel(name, widget)
            label.setStyleSheet("QLabel { font-weight: bold }")
            label.setMaximumWidth(100)
            label.setMinimumWidth(100)
            widget.layout().addWidget(label)
        widget.layout().addStretch()
        self.layout().addWidget(widget)

        # Add a row for each button.
        n_rows = 1
        self.be_rows = []

        # The buttons array has one element for each channel.
        for i, channel_buttons in enumerate(buttons):

            # Each channel element has zero or more power buttons.
            for power_button in channel_buttons:
                be_row = ButtonEditorRow(i, power_button[0], power_button[1], channel_names, self)
                be_row.delete.connect(self.handleDeleteRow)
                self.layout().addWidget(be_row)
                self.be_rows.append(be_row)

        # The add element a row button.
        self.add_button = QtWidgets.QPushButton("Add Button")
        self.add_button.clicked.connect(self.handleAddRow)
        self.layout().addWidget(self.add_button)

    def getButtons(self):

        # Create a list of all the buttons sorted by power.
        buttons = []
        for be_row in self.be_rows:
            buttons.append(be_row.getValues())
        buttons = sorted(buttons, key=itemgetter(2), reverse = True)

        # Create button list of lists.
        button_list = []
        for i in range(len(self.channel_names)):
            button_list.append([])

        # Add buttons to the appropriate channel.
        for button in buttons:
            button_list[button[0]].append([button[1], button[2]])
        
        return button_list
        
    def handleAddRow(self):
        be_row = ButtonEditorRow(0, "None", 0.0, self.channel_names, self)
        be_row.delete.connect(self.handleDeleteRow)
        self.layout().insertWidget(self.layout().count()-1, be_row)
        self.be_rows.append(be_row)
        
    def handleDeleteRow(self, be_row):
        self.layout().removeWidget(be_row)
        self.be_rows.remove(be_row)
        
        
## ParametersTablePowerButtonEditor
#
# A widget for editting power buttons.
#
class ParametersTablePowerButtonEditor(parametersEditors.ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        parameterEditors.ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.qt_widget = QtWidgets.QPushButton.__init__(self, "Edit Buttons", parent)

        self.buttons = parameter.getv()
        self.channel_names = parameter.channel_names

        self.qt_widget.clicked.connect(self.handleClick)

    @hdebug.debug
    def handleClick(self, dummy):
        new_buttons = runButtonEditor(self.buttons, self.channel_names)
        if new_buttons is not None:
            self.changed_signal.emit(self.p_name, new_buttons)

    def updateParameter(self, new_parameter):
        self.buttons = new_parameter.getv()


## QButtonEditorDialog
#
# The button editor dialog box.
#
class QButtonEditorDialog(QtWidgets.QDialog):

    def __init__(self, buttons, channel_names):
        QtWidgets.QDialog.__init__(self)

        self.was_accepted = False

        self.ui = buttonEditorUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.be_table = ButtonEditorTable(buttons, channel_names, self)
        self.ui.scrollArea.setWidget(self.be_table)
        self.ui.scrollArea.setWidgetResizable(True)
        
        self.ui.buttonBox.accepted.connect(self.handleAccepted)
        self.ui.buttonBox.rejected.connect(self.handleRejected)

    def getButtons(self):
        if self.was_accepted:
            return self.be_table.getButtons()
        else:
            return None

    def handleAccepted(self):
        self.was_accepted = True
        self.close()

    def handleRejected(self):
        self.close()
        

## runButtonEditor
#
# Run the button editor dialog box.
#
def runButtonEditor(buttons, channel_names):
    bdialog = QButtonEditorDialog(buttons, channel_names)
    bdialog.exec_()
    return bdialog.getButtons()


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
