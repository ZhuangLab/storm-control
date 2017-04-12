#!/usr/bin/env python
"""
Draw the parameter with the correct style.

Provide widgets for editing parameters.

Hazen 04/17
"""

import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params


def drawParameter(parameter, painter, a_rect, widget):
    """
    Draws parameter with the appropriate style.
    """
    # FIXME: Figuring out how to draw all the controls is real
    #        headache, so just display text for now.
    painter.setClipRect(a_rect)
    painter.drawText(a_rect,
                     QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                     parameter.toString())
    
#    if isinstance(parameter, params.ParameterFloat):
#        # FIXME: How to draw this to look like a QLineEdit?
#        painter.setClipRect(a_rect)
#        painter.drawText(a_rect,
#                         QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
#                         parameter.toString())
#        #opt = QtWidgets.QStyleOptionFrame()
#        #style = widget.style()
#        #style.drawPrimitive(QtWidgets.QStyle.PE_PanelLineEdit, opt, painter, widget)
#    elif isinstance(parameter, params.ParameterInt):
#        painter.setClipRect(a_rect)
#        painter.drawText(a_rect,
#                         QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
#                         parameter.toString())
#        #opt = QtWidgets.QStyleOptionFrame()
#        #style = widget.style()
#        #style.drawPrimitive(QtWidgets.QStyle.PE_PanelLineEdit, opt, painter, widget)        
#    elif isinstance(parameter, params.ParameterRangeInt):
#        opt = QtWidgets.QStyleOptionSpinBox()
#        opt.rect = a_rect
#        opt.text = parameter.toString()
#        style = widget.style()
#        style.drawComplexControl(QtWidgets.QStyle.CC_SpinBox, opt, painter, widget)
#        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter, widget)
#    elif isinstance(parameter, params.ParameterSet):
#        opt = QtWidgets.QStyleOptionComboBox()
#        opt.rect = a_rect
#        opt.currentText = parameter.toString()
#        style = widget.style()
#        style.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter, widget)
#        style.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt, painter, widget)

    
def getEditor(parameter = None, parent = None):
    """
    Return the appropriate editor for a particular parameter.
    """
    if isinstance(parameter, params.ParameterFloat):
        return EditorFloat(parent = parent)
    elif isinstance(parameter, params.ParameterInt):
        return EditorInt(parent = parent)
    elif isinstance(parameter, params.ParameterRangeInt):
        return EditorRangeInt(parent = parent)
    elif isinstance(parameter, params.ParameterSet):
        return EditorSet(parent = parent)


class EditorMixin(object):
    """
    Mixin to provide functionality needed by the editors.
    """
    finished = QtCore.pyqtSignal(object)
    updateParameter = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.parameter = None
    
    def getParameter(self):
        return self.parameter
    
    def setParameter(self, parameter):
        self.parameter = parameter.copy()
    

class EditorNumber(QtWidgets.QLineEdit, EditorMixin):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.textChanged.connect(self.handleTextChanged)

    def handleTextChanged(self, text):
        self.parameter.setv(text)
        self.updateParameter.emit(self)

    def setParameter(self, parameter):
        super().setParameter(parameter)
        self.textChanged.disconnect()
        self.setText(self.parameter.toString())
        self.textChanged.connect(self.handleTextChanged)
        

class EditorFloat(EditorNumber):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.setValidator(QtGui.QDoubleValidator(self))


class EditorInt(EditorNumber):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.setValidator(QtGui.QIntValidator(self))


class EditorRangeInt(QtWidgets.QSpinBox, EditorMixin):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.valueChanged.connect(self.handleValueChanged)

    def handleValueChanged(self, new_value):
        self.parameter.setv(new_value)
        self.updateParameter.emit(self)

    def setParameter(self, parameter):
        super().setParameter(parameter)
        self.valueChanged.disconnect()
        self.setMaximum(self.parameter.getMaximum())
        self.setMinimum(self.parameter.getMinimum())
        self.setValue(self.parameter.getv())
        self.valueChanged.connect(self.handleValueChanged)
        
        
class EditorSet(QtWidgets.QComboBox, EditorMixin):
    
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

