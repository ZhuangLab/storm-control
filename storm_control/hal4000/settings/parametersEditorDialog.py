#!/usr/bin/env python
"""
The parameters editor dialog box.

Hazen 4/17
"""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.qtdesigner.params_editor_ui as paramsEditorUi
import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon
import storm_control.hal4000.settings.parametersDrawersEditors as parametersDrawersEditors


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
    """
    QVariant storage for parameters.
    """
    def __init__(self, parameter = None, changed = False, **kwds):
        super().__init__(**kwds)
        self.changed = changed
        self.parameter = parameter

    
class EditorModel(QtGui.QStandardItemModel):
    pass


class EditorTreeViewDelegate(QtWidgets.QStyledItemDelegate):
    margin = 2
    name_width = 100
    widget_width = 100
        
    def createEditor(self, parent, option, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            editor = parametersDrawersEditors.getEditor(parameter = data.parameter,
                                                        parent = parent)
            if editor is not None:
                editor.editingFinished.connect(self.handleEditingFinished)
                editor.updateParameter.connect(self.handleUpdateParameter)
            return editor
        else:
            return super().createEditor(parent, option, index)

    def getData(self, index):
        return index.data(role = QtCore.Qt.UserRole+1)
    
    def getEditorRect(self, option):
        a_rect = QtCore.QRect(option.rect.topLeft(),
                              option.rect.bottomRight())
        a_rect.setLeft(option.rect.left() + option.rect.width() - self.widget_width - 2*self.margin)
        a_rect.setWidth(self.widget_width)        
        a_rect.setTop(option.rect.top() + self.margin)
        a_rect.setHeight(option.rect.height() - 2*self.margin)
        return a_rect

    def handleEditingFinished(self, editor):
        self.closeEditor.emit(editor)

    def handleUpdateParameter(self, editor):
        self.commitData.emit(editor)

    def paint(self, painter, option, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            parameter = data.parameter

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

            # Render control for editing.
            painter.setClipping(False)
            a_rect = self.getEditorRect(option)

            opt = QtWidgets.QStyleOptionComboBox()
            opt.rect = a_rect
            
            style = option.widget.style()
            parametersDrawersEditors.drawParameter(parameter, style, opt, painter, option.widget)

        else:
            super().paint(painter, option, index)

    def setEditorData(self, editor, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            editor.setParameter(data.parameter)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            model.setData(index, EditorItemData(changed = True,
                                                parameter = editor.getParameter()))
        else:
            super().setModelData(editor, model, index)

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
    update = QtCore.pyqtSignal(object)
    
    def __init__(self, window_title = None, qt_settings = None, parameters = None, **kwds):
        """
        """
        super().__init__(**kwds)
        self.changed_items = {}
        self.module_name = "parameters_editor"
        self.parameters = parameters.copy()
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
        self.ui.updateButton.setEnabled(False)

        self.editor_model.itemChanged.connect(self.handleItemChanged)
        self.ui.okButton.clicked.connect(self.handleOk)
        self.ui.updateButton.clicked.connect(self.handleUpdate)
        
    def closeEvent(self, event):
        if (len(self.changed_items) > 0):
            reply = halMessageBox.halMessageBoxResponse(self,
                                                        "Warning!",
                                                        "Parameters have not been updated, close anyway?")
            if (reply == QtWidgets.QMessageBox.No):
                event.ignore()
                return

        self.closed.emit()
        self.qt_settings.setValue(self.module_name + ".pos", self.pos())
        self.qt_settings.setValue(self.module_name + ".size", self.size())
        self.qt_settings.sync()

    def handleItemChanged(self, q_item):
        self.changed_items[id(q_item)] = q_item
        self.ui.okButton.setStyleSheet("QPushButton { color : red }")
        self.ui.updateButton.setEnabled(True)

    def handleOk(self, boolean):
        self.close()

    def handleUpdate(self):
        self.update.emit(self.parameters)

    def updateParameters(self, new_parameters):
        #
        # FIXME: For now we are just replacing the current model with a new
        #        model. What we should do is update the data in the current
        #        model with new parameters. In order to do this though we
        #        need to maintain a connection between each parameter and
        #        it's location in the model.
        #
        self.changed_items = {}
        self.ui.okButton.setStyleSheet("QPushButton { color : black }")
        self.ui.updateButton.setEnabled(False)

        self.parameters = new_parameters
        new_model = EditorModel()
        populateModel(new_model, self.parameters)
        self.editor_model.itemChanged.disconnect()
        self.ui.editorTreeView.setModel(new_model)
        self.editor_model = new_model
        self.editor_model.itemChanged.connect(self.handleItemChanged)
