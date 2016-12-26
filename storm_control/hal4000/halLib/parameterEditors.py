#!/usr/bin/python
#
## @file
#
# Base class and widgets for editting parameters.
#
# Hazen 05/16
#

import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params


## ParametersTableWidget
#
# A base class for parameter editing widgets.
#
class ParametersTableWidget(object):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal):
        self.am_changed = False
        self.changed_signal = changed_signal
        self.desc_label = None
        self.name_label = None
        self.p_name = root_name + "." + parameter.getName()

    def resetChanged(self):
        self.am_changed = False
        self.name_label.setStyleSheet("QLabel { color: black }")
        
    def setChanged(self, changed):
        if (changed != self.am_changed):
            self.am_changed = changed
            if changed:
                self.name_label.setStyleSheet("QLabel { color: red }")
                return "modified"
            else:
                self.name_label.setStyleSheet("QLabel { color: black }")
                return "reverted"
        return "nochange"
    
    # These are the other UI elements that we might want to
    # modify that are associated with this parameter.
    def setLabels(self, name_label, desc_label):
        self.name_label = name_label
        self.desc_label = desc_label

    def updateParameter(self, new_parameter):
        pass


## ParametersTableWidgetDirectory.
#
# A widget for choosing directories.
#
class ParametersTableWidgetDirectory(QtWidgets.QPushButton, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QPushButton.__init__(self, str(parameter.getv()), parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.setFlat(True)

        self.clicked.connect(self.handleClick)

    @hdebug.debug        
    def handleClick(self,dummy):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                               "Choose Directory", 
                                                               self.text(),
                                                               QtWidgets.QFileDialog.ShowDirsOnly)[0]
        if directory:
            self.setText(directory)
            self.changed_signal.emit(self.p_name, directory)

    def updateParameter(self, new_parameter):
        self.setText(str(new_parameter.getv()))


## ParametersTableWidgetFilename.
#
# A widget for choosing filenames.
#
class ParametersTableWidgetFilename(QtWidgets.QPushButton, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QPushButton.__init__(self, str(parameter.getv()), parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        if parameter.use_save_dialog:
            self.fdialog = QtWidgets.QFileDialog.getSaveFileName
        else:
            self.fdialog = QtWidgets.QFileDialog.getOpenFileName

        self.setFlat(True)

        self.clicked.connect(self.handleClick)

    @hdebug.debug        
    def handleClick(self,dummy):
        
        filename = self.fdialog(self, "Choose File", os.path.dirname(str(self.text())), "*.*")[0]
        if filename:
            self.setText(filename)
            self.changed_signal.emit(self.p_name, filename)

    def updateParameter(self, new_parameter):
        self.setText(str(new_parameter.getv()))

                
## ParametersTableWidgetFloat
#
# A widget for floats without any range.
#
class ParametersTableWidgetFloat(QtWidgets.QLineEdit, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QLineEdit.__init__(self, str(parameter.getv()), parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.setValidator(QtGui.QDoubleValidator(self))
        self.textChanged.connect(self.handleTextChanged)

    @hdebug.debug        
    def handleTextChanged(self, new_text):
        self.changed_signal.emit(self.p_name, float(new_text))

    def updateParameter(self, new_parameter):
        self.setText(str(new_parameter.getv()))

            
## ParametersTableWidgetInt
#
# A widget for integers without any range.
#
class ParametersTableWidgetInt(QtWidgets.QLineEdit, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QLineEdit.__init__(self, str(parameter.getv()), parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.setValidator(QtGui.QIntValidator(self))
        self.textChanged.connect(self.handleTextChanged)

    @hdebug.debug        
    def handleTextChanged(self, new_text):
        self.changed_signal.emit(self.p_name, int(new_text))

    def updateParameter(self, new_parameter):
        self.setText(str(new_parameter.getv()))
        
        
## ParametersTableWidgetRangeFloat
#
# A widget for floats with a range.
#
class ParametersTableWidgetRangeFloat(QtWidgets.QDoubleSpinBox, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QDoubleSpinBox.__init__(self, parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.setMaximum(parameter.getMaximum())
        self.setMinimum(parameter.getMinimum())
        self.setDecimals(3)
        self.setValue(parameter.getv())
        
        self.valueChanged.connect(self.handleValueChanged)

    @hdebug.debug
    def handleValueChanged(self, new_value):
        self.changed_signal.emit(self.p_name, new_value)

    def updateParameter(self, new_parameter):
        self.valueChanged.disconnect()
        self.setMaximum(new_parameter.getMaximum())
        self.setMinimum(new_parameter.getMinimum())
        self.setValue(new_parameter.getv())
        self.valueChanged.connect(self.handleValueChanged)

            
## ParametersTableWidgetRangeInt
#
# A widget for integers with a range.
#
class ParametersTableWidgetRangeInt(QtWidgets.QSpinBox, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QSpinBox.__init__(self, parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        self.setMaximum(parameter.getMaximum())
        self.setMinimum(parameter.getMinimum())
        self.setValue(parameter.getv())
        
        self.valueChanged.connect(self.handleValueChanged)

    @hdebug.debug
    def handleValueChanged(self, new_value):
        self.changed_signal.emit(self.p_name, new_value)

    def updateParameter(self, new_parameter):
        self.valueChanged.disconnect()
        self.setMaximum(new_parameter.getMaximum())
        self.setMinimum(new_parameter.getMinimum())
        self.setValue(new_parameter.getv())
        self.valueChanged.connect(self.handleValueChanged)        

    
## ParametersTableWidgetSet
#
# Base class for parameters with a set of allowed values.
#
class ParametersTableWidgetSet(QtWidgets.QComboBox, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)

        for allowed in parameter.getAllowed():
            self.addItem(str(allowed))
            
        self.setCurrentIndex(self.findText(str(parameter.getv())))

        self.currentIndexChanged[str].connect(self.handleCurrentIndexChanged)

    def updateParameter(self, new_parameter):        
        self.currentIndexChanged[str].disconnect()
        self.clear()
        for allowed in new_parameter.getAllowed():
            self.addItem(str(allowed))
        self.setCurrentIndex(self.findText(str(new_parameter.getv())))
        self.currentIndexChanged[str].connect(self.handleCurrentIndexChanged)

        
## ParametersTableWidgetSetBoolean
#
# Boolean set.
#
class ParametersTableWidgetSetBoolean(ParametersTableWidgetSet):
        
    @hdebug.debug
    def handleCurrentIndexChanged(self, new_text):
        new_value = False
        if (str(new_text) == "True"):
            new_value = True
        self.changed_signal.emit(self.p_name, new_value)


## ParametersTableWidgetSetFloat
#
# Float set.
#
class ParametersTableWidgetSetFloat(ParametersTableWidgetSet):
        
    @hdebug.debug
    def handleCurrentIndexChanged(self, new_text):
        self.changed_signal.emit(self.p_name, float(new_text))
            
            
## ParametersTableWidgetSetInt
#
# Integer set.
#
class ParametersTableWidgetSetInt(ParametersTableWidgetSet):
        
    @hdebug.debug
    def handleCurrentIndexChanged(self, new_text):
        self.changed_signal.emit(self.p_name, int(new_text))

            
## ParametersTableWidgetSetString
#
# String set.
#
class ParametersTableWidgetSetString(ParametersTableWidgetSet):
        
    @hdebug.debug
    def handleCurrentIndexChanged(self, new_text):
        self.changed_signal.emit(self.p_name, str(new_text))

            
## ParametersTableWidgetString
#
# A widget for strings.
#
class ParametersTableWidgetString(QtWidgets.QLineEdit, ParametersTableWidget):

    @hdebug.debug
    def __init__(self, root_name, parameter, changed_signal, parent):
        QtWidgets.QLineEdit.__init__(self, str(parameter.getv()), parent)
        ParametersTableWidget.__init__(self, root_name, parameter, changed_signal)
        
        self.metrics = QtGui.QFontMetrics(QtGui.QApplication.font())

        self.textChanged.connect(self.handleTextChanged)

    @hdebug.debug
    def handleTextChanged(self, new_text):
        self.changed_signal.emit(self.p_name, str(new_text))

    def sizeHint(self):
        text = self.text() + "----"
        return self.metrics.size(QtCore.Qt.TextSingleLine, text)

    def updateParameter(self, new_parameter):        
        self.textChanged.disconnect()
        self.setText(str(new_parameter.getv()))
        self.textChanged.connect(self.handleTextChanged)
        
    
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

