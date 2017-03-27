#!/usr/bin/env python
"""
This is the customized Listview, model, etc.

Hazen 03/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions


def getItemData(q_std_item):
    return q_std_item.data()


class ParametersItemData(object):
    """
    WTF? Apparently Qt clones items when dragging and dropping
    making it very difficult use customized QStandardItems in
    a re-orderable list. So instead we store the data in an object
    and store the object in a QStandardItem. Hackish..
    """
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.checked = False
        self.parameters = parameters
        self.stale = False  # Edited but not saved.

    
class ParametersListViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    This lets us draw items that look like radio buttons.
    """
    def __init__(self, model = None, **kwds):
        super().__init__(**kwds)
        self.model = model

    def paint(self, painter, option, index):
        note = self.model.itemFromIndex(index)

        opt = QtWidgets.QStyleOptionButton()
        if getItemData(note).checked:
            opt.state = QtWidgets.QStyle.State_On
        opt.rect = option.rect
        opt.text = note.text()
        
        style = option.widget.style()
        style.drawControl(QtWidgets.QStyle.CE_RadioButton, opt, painter, option.widget)
        
    def sizeHint(self, option, index):
        """
        This provides a little more space between the items.
        """
        result = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
        result.setHeight(1.2 * result.height())
        return result

    
class ParametersMVC(QtWidgets.QListView):
    editParameters = QtCore.pyqtSignal(object)
    newParameters = QtCore.pyqtSignal(object)
    saveParameters = QtCore.pyqtSignal(object)

    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.current_item = None
        self.model = ParametersStandardItemModel(self)
        self.previous_item = None
        self.rc_item = None
        self.setModel(self.model)

        # This enables the user to re-order the items by dragging them.
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        # Custom drawing of the items.
        self.setItemDelegate(ParametersListViewDelegate(model = self.model))

        self.selectionModel().selectionChanged.connect(self.handleSelectionChange)

        # Actions for the pop-up menu.
        self.deleteAction = QtWidgets.QAction(self.tr("Delete"), self)
        self.duplicateAction = QtWidgets.QAction("Duplicate", self)
        self.editAction = QtWidgets.QAction(self.tr("Edit"), self)
        self.saveAction = QtWidgets.QAction(self.tr("Save"), self)

        self.deleteAction.triggered.connect(self.handleDelete)
        self.duplicateAction.triggered.connect(self.handleDuplicate)
        self.editAction.triggered.connect(self.handleEdit)
        self.saveAction.triggered.connect(self.handleSave)

        # Testing.
        if False:
            for name in ["setting 1", "setting 2", "setting 3"]:
                self.addParameters(name, "foo")

    def addParameters(self, name, parameters):
        qitem = QtGui.QStandardItem(name)
        qitem.setData(ParametersItemData(parameters = parameters))
        self.model.insertRow(0, qitem)

        # The first parameter in is the default current parameters.
        if (self.model.rowCount() == 1):
            self.current_item = qitem
            getItemData(qitem).checked = True

    def getCurrentParameters(self):
        return getItemData(self.current_item).parameters
    
    def getParametersItem(self, value):
        """
        This returns a QStandardItem including it's data from the model.

        value can a string or an integer.
        """
        if isinstance(value, str):
            items = self.model.findItems(value)

            #
            # FIXME: Not sure we actually want to throw an error here, maybe we
            #        should just return a list of matching parameters?
            #
            if (len(items) > 1):
                raise halExceptions.HalException("Found", len(items), "parameter files with the requested name")
            elif (len(items) == 1):
                return items[0]
        else:
            return self.model.item(value)

    def getPreviousParameters(self):
        if self.previous_item is not None:
            return getItemData(self.previous_item).parameters    

    def getSelectedItem(self, selection):
        return self.model.itemFromIndex(selection.indexes()[0])

    def handleDelete(self, boolean):
        self.model.removeRows(self.model.indexFromItem(self.rc_item).row(), 1)

    def handleDuplicate(self, boolean):
        dup_item = QtGui.QStandardItem(self.rc_item.text())
        dup_item.setData(ParametersItemData(getItemData(self.rc_item).parameters.copy()))
        #dup_qitem.setData(ParametersItemData(getItemData(self.rc_item).parameters))
        row = self.model.indexFromItem(self.rc_item).row()
        self.model.insertRow(row, dup_item)

    def handleEdit(self, boolean):
        # You can only edit the current parameters.
        self.editParameters.emit(getItemData(self.current_item).parameters)

    def handleSave(self, boolean):
        data = getItemData(self.rc_item)
        self.saveParameters.emit(data.parameters)
        data.stale = False
    
    def handleSelectionChange(self, new_selection, old_selection):
        """
        Heh, new_selection and old_selection are the same so we
        need to keep track of what was previously selected ourselves.
        """
        new_item = self.getSelectedItem(new_selection)
        if (self.current_item != new_item):
            getItemData(self.current_item).checked = False
            getItemData(new_item).checked = True
            self.previous_item = self.current_item
            self.current_item = new_item
            self.newParameters.emit(getItemData(new_item).parameters)

    def mousePressEvent(self, event):
        if (event.button() == QtCore.Qt.RightButton):
            rc_index = self.indexAt(event.pos())

            # Check that the user actually clicked on an item.
            if (rc_index.row() > -1):
                self.rc_item = self.model.itemFromIndex(rc_index)
                if (self.rc_item == self.current_item):
                    popup_menu = QtWidgets.QMenu()
                    popup_menu.addAction(self.duplicateAction)
                    popup_menu.addAction(self.editAction)
                    if getItemData(self.rc_item).stale:
                        popup_menu.addAction(self.saveAction)
                else:
                    popup_menu = QtWidgets.QMenu()
                    popup_menu.addAction(self.deleteAction)
                    popup_menu.addAction(self.duplicateAction)
                    if getItemData(self.rc_item).stale:
                        popup_menu.addAction(self.saveAction)
                popup_menu.exec_(event.globalPos())
                
        else:
            super().mousePressEvent(event)

    def setCurrentParameters(self, item, always_emit_new_parameters = False):
        self.setCurrentIndex(self.model.indexFromItem(item))

        # If we are modifying the current and always_emit_new_parameter is
        # True then we have to emit the newParameters signal here because
        # handleSelectionChange will not do this.
        if (item == self.current_item) and always_emit_new_parameters:
            self.newParameters.emit(getItemData(item).parameters)

    def setItemParameters(self, item, parameters):
        getItemData(item).parameters = parameters




class ParametersStandardItemModel(QtGui.QStandardItemModel):

    def flags(self, index):
        """
        This blocks overwriting items during drag and drop re-ordering.
        """
        if index.isValid(): 
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled| \
            QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled        

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
