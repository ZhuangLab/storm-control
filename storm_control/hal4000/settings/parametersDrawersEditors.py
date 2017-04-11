#!/usr/bin/env python
"""
Draw the parameter with the correct style.

Provide widgets for editing parameters.

Hazen 04/17
"""

import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params


def drawParameter(parameter, style, opt, painter, widget):
    """
    Draws parameter with the appropriate style.
    """
    if hasattr(parameter, "drawParameter"):
        parameter.drawParameter(style, opt, painter, widget)
    elif isinstance(parameter, params.ParameterSet):
        opt.currentText = parameter.toString()
        style.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter, widget)
        style.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt, painter, widget)

    
def getEditor(parameter = None, parent = None):
    """
    Return the appropriate editor for a particular parameter.
    """
    if parameter.getEditor() is not None:
        return parameter.getEditor()
    elif isinstance(parameter, params.ParameterSet):
        return ParameterEditorSet(parent = parent)


class ParameterEditorMixin(object):
    """
    Mixin to provide functionality needed by the editors.
    """
    editingFinished = QtCore.pyqtSignal(object)
    updateParameter = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.parameter = None
    
    def getParameter(self):
        return self.parameter
    
    def setParameter(self, parameter):
        self.parameter = parameter
    

class ParameterEditorSet(QtWidgets.QComboBox, ParameterEditorMixin):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.currentIndexChanged.connect(self.handleIndexChanged)

    def handleIndexChanged(self, new_index):
        self.parameter.setv(self.currentData())
        self.updateParameter.emit(self)

    def setParameter(self, parameter):
        super().setParameter(parameter)
        self.currentIndexChanged.disconnect()
        self.clear()
        for elt in sorted(self.parameter.getAllowed()):
            self.addItem(str(elt), elt)
        self.setCurrentIndex(self.findText(str(self.parameter.getv())))
        self.currentIndexChanged.connect(self.handleIndexChanged)

    
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

