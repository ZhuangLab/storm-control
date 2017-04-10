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
                model.appendRow(q_item)
        

class EditorItemData(object):
    
    def __init__(self, parameter = None, **kwds):
        super().__init__(**kwds)
        self.parameter = parameter

    
class EditorModel(QtGui.QStandardItemModel):
    pass


class EditorTreeViewDelegate(QtWidgets.QStyledItemDelegate):
        
    def paint(self, painter, option, index):
        if isinstance(index.data(role = QtCore.Qt.UserRole+1), EditorItemData):
            parameter = index.data(role = QtCore.Qt.UserRole+1).parameter

            # Render parameter name.
            opt = QtWidgets.QStyleOptionButton()
            opt.rect = option.rect
            opt.text = "foo " + ",".join([parameter.getName(), parameter.getDescription()])
            opt.rect.setWidth(100)

            print(opt.rect)
            
            style = option.widget.style()
            style.drawItemText(painter,
                               opt.rect,
                               QtCore.Qt.AlignLeft,
                               option.palette,
                               (option.state == QtWidgets.QStyle.State_Enabled),
                               opt.text)

            # Render parameter description.

            # Render parameter editor.
            
                               
            #style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter, option.widget)
            #print(opt.text)
            #style.drawControl(QtWidgets.QStyle.CE_RadioButton, opt, painter, option.widget)

#            painter.drawText(option.rect,
#                             QtCore.Qt.AlignLeft,
#                             "bar")
                                     
            #opt = QtWidgets.QStyleOption()
            #opt.rect = option.rect
            #opt.text = "foo " + 

            #style = option.widget.style()
            #style.drawControl(QtWidgets.QStyle.CE_RadioButton, opt, painter, option.widget)
        else:
            super().paint(painter, option, index)

            
    def sizeHint(self, option, index):
        """
        This provides a little more space between the items.
        """
        result = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
        result.setHeight(1.1 * result.height())
        return result
    
    
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
        self.qt_settings.setValue(self.module_name + ".main", self.size())

    def handleOk(self, boolean):
        self.close()
