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
            q_item = QtGui.QStandardItem()
            q_item.setData(EditorItemData(parameter = param))
            if param.isMutable():
                q_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                model.appendRow(q_item)
            #else:
            #    q_item.setFlags(QtCore.Qt.NoItemFlags)


class EditorItemData(object):
    """
    QVariant storage for parameters.
    """
    def __init__(self, parameter = None, modified = False, **kwds):
        super().__init__(**kwds)
        self.modified = modified
        self.parameter = parameter

    
class EditorModel(QtGui.QStandardItemModel):
    pass


class EditorTreeViewDelegate(QtWidgets.QStyledItemDelegate):
    margin = 2
    name_width = 100
    widget_width = 200

    def createEditor(self, parent, option, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            editor = parametersDrawersEditors.getEditor(parameter = data.parameter,
                                                        parent = parent)
            if editor is not None:
                editor.finished.connect(self.handleFinished)
                editor.updateParameter.connect(self.handleUpdateParameter)
            return editor
        else:
            return super().createEditor(parent, option, index)

    def getData(self, index):
        return index.model().itemFromIndex(index).data(role = QtCore.Qt.UserRole+1)

    def getEditorRect(self, option):
        a_rect = QtCore.QRect(option.rect.topLeft(),
                              option.rect.bottomRight())
        a_rect.setLeft(option.rect.left() + option.rect.width() - self.widget_width - 2*self.margin)
        a_rect.setWidth(self.widget_width)        
        a_rect.setTop(option.rect.top() + self.margin)
        a_rect.setHeight(option.rect.height() - 2*self.margin)
        return a_rect

    def handleFinished(self, editor):
        self.closeEditor.emit(editor)

    def handleUpdateParameter(self, editor):
        self.commitData.emit(editor)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            pen = painter.pen()
            
            parameter = data.parameter

            # Draw the text gray if it not mutable.
            if not parameter.isMutable():
                painter.setPen(QtGui.QColor(128, 128, 128))

            overall_width = option.rect.width()

            # Render parameter name.
            a_rect = QtCore.QRect(option.rect.topLeft(),
                                  option.rect.bottomRight())
            a_rect.setWidth(self.name_width)

            # Draw the text red if it has been modified.
            if data.modified:
                painter.setPen(QtGui.QColor(255, 0, 0))

            painter.setClipping(True)
            painter.setClipRect(a_rect)
            painter.drawText(a_rect,
                             QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                             parameter.getName())
            if data.modified:
                painter.setPen(pen)

            # Render parameter description.
            if (overall_width > 400):
                a_rect = QtCore.QRect(option.rect.topLeft(),
                                      option.rect.bottomRight())
                a_rect.setLeft(option.rect.left() + self.name_width + self.margin)
                a_rect.setWidth(overall_width - (self.name_width + self.widget_width + 3*self.margin))

                painter.setClipRect(a_rect)
                painter.drawText(a_rect,
                                 QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                                 parameter.getDescription())

            # Render control for editing.
            painter.setClipping(False)
            a_rect = self.getEditorRect(option)

            if parameter.isMutable():
                parametersDrawersEditors.drawParameter(parameter, painter, a_rect, option.widget)
            else:
                painter.setClipRect(a_rect)
                painter.drawText(a_rect,
                                 QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                                 parameter.toString())

            painter.setPen(pen)
            
#        else:
#            super().paint(painter, option, index)

    def setEditorData(self, editor, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            editor.setParameter(data.parameter)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        data = self.getData(index)
        if isinstance(data, EditorItemData):
            
            # Get the item from the model.
            q_item = model.itemFromIndex(index)

            # Check if the editor changed anything.
            if (q_item.data().parameter.getv() != editor.getParameter().getv()):
                
                # Update the item based on the editor change.
                q_item.data().parameter.setv(editor.getParameter().getv())

                # Save the updated item back in the model. The editor works on
                # a copy, so if we save the copy then we'll lose the connection
                # to the original parameters.
                q_item.setData(EditorItemData(modified = True,
                                              parameter = q_item.data().parameter))
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

    # This is a class variable so that it persists between sessions. There
    # should only ever be a single instance open at any given time.
    expanded = []

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
        self.ui.editorTreeView.collapsed.connect(self.handleCollapsed)
        self.ui.editorTreeView.expanded.connect(self.handleExpanded)
        self.ui.okButton.clicked.connect(self.handleOk)
        self.ui.updateButton.clicked.connect(self.handleUpdate)

        # Restore previous tree state, if any.
        self.reExpand()
        
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

    def handleCollapsed(self, model_index):
        item_name = self.editor_model.itemFromIndex(model_index).text()
        self.expanded.remove(item_name)

    def handleExpanded(self, model_index):
        item_name = self.editor_model.itemFromIndex(model_index).text()
        self.expanded.append(item_name)

    def handleItemChanged(self, q_item):
        self.changed_items[id(q_item)] = q_item
        self.ui.okButton.setStyleSheet("QPushButton { color : red }")
        self.ui.updateButton.setEnabled(True)

    def handleOk(self, boolean):
        self.close()

    def handleUpdate(self):
        self.update.emit(self.parameters)
        
    def reExpand(self):
        """
        Expand items in the tree view that were previously open.
        """
        if (len(self.expanded) == 0):
            return
        
        #
        # Disconnect this signal so we don't get duplicates
        # when we do the expansion.
        #
        self.ui.editorTreeView.expanded.disconnect(self.handleExpanded)

        #
        # Expand relevant items in the tree view.
        #
        # Works recursively. We are assuming that the names of the
        # expandable items are unique.
        #
        def expand(parent = QtCore.QModelIndex()):
            for i in range(self.editor_model.rowCount()):
                model_index = self.editor_model.index(i, 0, parent)
                item = self.editor_model.itemFromIndex(model_index)
                
                if item is None:
                    continue
                
                if item.hasChildren():
                    if item.text() in self.expanded:
                        self.ui.editorTreeView.setExpanded(model_index, True)
                    expand(parent = model_index)

        expand()

        # Re-connect signal.
        self.ui.editorTreeView.expanded.connect(self.handleExpanded)                    

    def updateParameters(self, new_parameters):

        self.changed_items = {}
        self.ui.okButton.setStyleSheet("QPushButton { color : black }")
        self.ui.updateButton.setEnabled(False)

        # Re-create model.
        self.parameters = new_parameters
        new_model = EditorModel()
        populateModel(new_model, self.parameters)
        self.editor_model.itemChanged.disconnect()
        self.ui.editorTreeView.setModel(new_model)
        self.editor_model = new_model
        self.editor_model.itemChanged.connect(self.handleItemChanged)

        # Restore previous tree view state.        
        self.reExpand()

