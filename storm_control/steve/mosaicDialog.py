#!/usr/bin/python
#
## @file
#
# A dialog that enables the user to enter the mosaic settings
# when loading older movies without a corresponding .xml file
# off-line.
#
# Hazen 07/15
#

import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.qtdesigner.mosaic_dialog_ui as mosaic_dialog_ui

values = [0.16, False, False, False, "100x", 100.0, 0.0, 0.0]

def execMosaicDialog():
    global values
    mdialog = MosaicDialog(values)
    mdialog.exec_()
    values = mdialog.getMosaicSettings()
    return values

def getMosaicSettings():
    global values
    return values

## MosaicControl
#
# Misc Control Dialog Box
#
class MosaicDialog(QtWidgets.QDialog):

    ## __init__
    #
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, initial_values, parent = None):
        QtWidgets.QDialog.__init__(self, parent)

        self.ui = mosaic_dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.pixDoubleSpinBox.setValue(initial_values[0])
        self.ui.horizCheckBox.setChecked(initial_values[1])
        self.ui.vertCheckBox.setChecked(initial_values[2])
        self.ui.transCheckBox.setChecked(initial_values[3])
        self.ui.objectiveLineEdit.setText(initial_values[4])
        self.ui.magDoubleSpinBox.setValue(initial_values[5])
        self.ui.xoffDoubleSpinBox.setValue(initial_values[6])
        self.ui.yoffDoubleSpinBox.setValue(initial_values[7])
        
        self.ui.okButton.clicked.connect(self.handleOk)
        
    ## getMosaicSettings
    #
    # @return The mosaic settings and information for the current objective.
    #
    def getMosaicSettings(self):
        return [self.ui.pixDoubleSpinBox.value(),
                self.ui.horizCheckBox.isChecked(),
                self.ui.vertCheckBox.isChecked(),
                self.ui.transCheckBox.isChecked(),
                str(self.ui.objectiveLineEdit.text()),
                self.ui.magDoubleSpinBox.value(),
                self.ui.xoffDoubleSpinBox.value(),
                self.ui.yoffDoubleSpinBox.value()]
    
    ## handleOk
    #
    # Hide the window.
    #
    # @param boolean Dummy parameter.
    #
    def handleOk(self, boolean):
        self.close()


## Stand alone test
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    dialog = MosaicDialog(values)
    dialog.show()
    app.exec_()

#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
