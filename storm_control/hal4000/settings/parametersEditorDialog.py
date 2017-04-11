#!/usr/bin/env python
"""
The parameters editor dialog box.

Hazen 4/17
"""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.qtdesigner.params_editor_ui as paramsEditorUi
import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon


def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]


def populateModel(model, parameters):
    """
    (Recursively) populate the model.
    """
    for attr in parameters.getSortedAttrs():
        param = parameters.getp(attr)

        # Create a branch for sub-sections.
        if isinstance(param, params.StormXMLObject):
            parent = QtGui.QStandardItem(attr)
            parent.setFlags(QtCore.Qt.ItemIsEnabled)
            model.appendRow(parent)
            populateModel(parent, param)
            
        # Create items for (mutable) parameters.
        else:
            if param.isMutable():
                q_item = QtGui.QStandardItem()
                q_item.setData(EditorItemData(parameter = param))
                q_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                model.appendRow(q_item)
        

class EditorItemData(object):
    
    def __init__(self, parameter = None, **kwds):
        super().__init__(**kwds)
        self.parameter = parameter

    
class EditorModel(QtGui.QStandardItemModel):
    pass


class EditorTreeViewDelegate(QtWidgets.QStyledItemDelegate):
    margin = 2
    name_width = 100
    widget_width = 100

    def createEditor(self, parent, option, index):
        if isinstance(index.data(role = QtCore.Qt.UserRole+1), EditorItemData):        
            parameter = index.data(role = QtCore.Qt.UserRole+1).parameter
            if isinstance(parameter, params.ParameterSet):
                editor = QtWidgets.QComboBox(parent)
                for elt in sorted(parameter.getAllowed()):
                    editor.addItem(str(elt))
                editor.setCurrentIndex(editor.findText(str(parameter.getv())))
                return editor
        else:
            return super().createEditor(parent, option, index)

    def getEditorRect(self, option):
        a_rect = QtCore.QRect(option.rect.topLeft(),
                              option.rect.bottomRight())
        a_rect.setLeft(option.rect.left() + option.rect.width() - self.widget_width - 2*self.margin)
        a_rect.setWidth(self.widget_width)        
        a_rect.setTop(option.rect.top() + self.margin)
        a_rect.setHeight(option.rect.height() - 2*self.margin)
        return a_rect
        
    def paint(self, painter, option, index):
        if isinstance(index.data(role = QtCore.Qt.UserRole+1), EditorItemData):
            parameter = index.data(role = QtCore.Qt.UserRole+1).parameter

            overall_width = option.rect.width()

            # Render parameter name.
            a_rect = QtCore.QRect(option.rect.topLeft(),
                                  option.rect.bottomRight())
            a_rect.setWidth(self.name_width)

            painter.setClipping(True)
            painter.setClipRect(a_rect)
            painter.drawText(a_rect,
                             QtCore.Qt.AlignLeft,
                             parameter.getName())

            # Render parameter description.
            if (overall_width > 400):
                a_rect = QtCore.QRect(option.rect.topLeft(),
                                      option.rect.bottomRight())
                a_rect.setLeft(option.rect.left() + self.name_width + self.margin)
                a_rect.setWidth(overall_width - (self.name_width + self.widget_width + 3*self.margin))

                painter.setClipRect(a_rect)
                painter.drawText(a_rect,
                                 QtCore.Qt.AlignLeft,
                                 parameter.getDescription())

            # Render control for editting.
            painter.setClipping(False)
            a_rect = self.getEditorRect(option)

            opt = QtWidgets.QStyleOptionComboBox()
            opt.rect = a_rect
            opt.currentText = parameter.toString()
            
            style = option.widget.style()
            style.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter, option.widget)
            style.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt, painter, option.widget)

        else:
            super().paint(painter, option, index)

            
    def sizeHint(self, option, index):
        """
        This provides a little more space between the items.
        """
        result = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
        result.setHeight(2.0 * result.height())
        return result

    def updateEditorGeometry(self, editor, option, index):
        overall_width = option.rect.width()
        a_rect = self.getEditorRect(option)
        editor.setGeometry(a_rect)

    
class ParametersEditorDialog(QtWidgets.QDialog):
    """
    The parameters editor dialog with a TreeView based editor.
    """
    closed = QtCore.pyqtSignal()
    
    def __init__(self, window_title = None, qt_settings = None, parameters = None, **kwds):
        """
        """
        super().__init__(**kwds)
        self.module_name = "parameters_editor"
        self.parameters = parameters
        self.qt_settings = qt_settings

        # Load Ui.
        self.ui = paramsEditorUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Create model & add to the tree view.
        self.editor_model = EditorModel()
        populateModel(self.editor_model, self.parameters)
        self.ui.editorTreeView.setModel(self.editor_model)
        self.ui.editorTreeView.setHeaderHidden(True)
        self.ui.editorTreeView.setItemDelegate(EditorTreeViewDelegate())
        
        # Configure Ui.
        self.setWindowIcon(qtAppIcon.QAppIcon())
        self.setWindowTitle(window_title)
        
        self.move(self.qt_settings.value(self.module_name + ".pos", self.pos()))
        self.resize(self.qt_settings.value(self.module_name + ".size", self.size()))

        self.ui.parametersNameLabel.setText(getFileName(parameters.get("parameters_file")))
                
        self.ui.okButton.clicked.connect(self.handleOk)
        
    def closeEvent(self, event):
        self.closed.emit()
        self.qt_settings.setValue(self.module_name + ".pos", self.pos())
        self.qt_settings.setValue(self.module_name + ".size", self.size())
        self.qt_settings.sync()

    def handleOk(self, boolean):
        self.close()
