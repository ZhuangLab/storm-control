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
    Hmm.. Apparently Qt clones items when dragging and dropping
    making it very difficult use customized QStandardItems in
    a re-orderable list. So instead we store the data in an object
    and store the object in a QStandardItem.
    """
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.parameters = parameters
        self.stale = False  # Edited but not saved.

    
class ParametersListViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    This lets us draw items that look like radio buttons.
    """
    def paint(self, painter, option, index):
        p_item = index.model().itemFromIndex(index)
        p_data = getItemData(p_item)
        
        opt = QtWidgets.QStyleOptionButton()
        opt.state = QtWidgets.QStyle.State_Enabled
        if (p_item.checkState() == QtCore.Qt.Checked):
            opt.state = QtWidgets.QStyle.State_On | opt.state
        if p_data.stale:
            opt.palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255,0,0))
        opt.rect = option.rect
        opt.text = p_item.text()

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
    """
    This class handles the actual display of the various parameter choices in a
    QListView. It also keeps track of the current selected item and the 
    previously selected item.
    """
    editParameters = QtCore.pyqtSignal()
    newParameters = QtCore.pyqtSignal(object)
    saveParameters = QtCore.pyqtSignal(object)

    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.model = ParametersStandardItemModel(self)
        self.rc_item = None # This is the right item that was right clicked.
        self.selected_items = [None, None] # Keeps track of the last two selected items.
        self.setModel(self.model)

        # This enables the user to re-order the items by dragging them.
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDragDropOverwriteMode(False)

        # Custom drawing of the items.
        self.setItemDelegate(ParametersListViewDelegate())

        self.clicked.connect(self.handleClicked)

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
        q_item = QtGui.QStandardItem(name)
        q_item.setData(ParametersItemData(parameters = parameters))
        q_item.setCheckable(True)
        
        self.setToolTip(q_item)
        self.model.insertRow(0, q_item)

        # The first parameter in is the default parameters
        # and are selected by default.
        if (self.model.rowCount() == 1):
            self.selected_items[0] = q_item
            q_item.setCheckState(QtCore.Qt.Checked)

    def getCurrentItem(self):
        """
        Return the currently selected item.
        """
        return self.selected_items[0]

    def getCurrentParameters(self):
        """
        Return the currently selected items parameters.
        """
        return self.getItemParameters(self.getCurrentItem())

    def getItemParameters(self, q_item):
        return getItemData(q_item).parameters
        
    def getPreviousItem(self):
        return self.selected_items[1]

    def getPreviousParameters(self):
        q_item = self.getPreviousItem()
        if q_item is not None:
            return self.getItemParameters(q_item)

    def getQItemByValue(self, value):
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
                raise halExceptions.HalException("Found " + str(len(items)) + " parameter files with the requested name!")
            elif (len(items) == 1):
                return items[0]
        else:
            return self.model.item(value)
        
    def handleClicked(self, index):
        if (self.model.itemFromIndex(index).checkState() == QtCore.Qt.Checked):
            return

        for i in range(self.model.rowCount()):
            q_item = self.model.item(i)
            if (i == index.row()):
                q_item.setCheckState(QtCore.Qt.Checked)
                self.selected_items[0] = q_item
            else:
                # Check if this was the previously selected item.
                if (q_item.checkState() == QtCore.Qt.Checked):
                    self.selected_items[1] = q_item
                q_item.setCheckState(QtCore.Qt.Unchecked)
        self.newParameters.emit(self.getCurrentParameters())
        
    def handleDelete(self, boolean):
        self.model.removeRows(self.model.indexFromItem(self.rc_item).row(), 1)

    def handleDuplicate(self, boolean):
        dup_item = QtGui.QStandardItem(self.rc_item.text())
        dup_item.setData(ParametersItemData(getItemData(self.rc_item).parameters.copy()))
        self.setToolTip(dup_item)
        row = self.model.indexFromItem(self.rc_item).row()
        self.model.insertRow(row, dup_item)

    def handleEdit(self, boolean):
        # You can only edit the current parameters.
        self.editParameters.emit()

    def handleSave(self, boolean):
        #
        # Why do we need to emit a signal instead of just doing everything
        # here? Not sure, but it we throw up a QFileDialog here the colors
        # are all funny..
        #
        data = getItemData(self.rc_item)
        self.saveParameters.emit(data.parameters)

    def mousePressEvent(self, event):
        if (event.button() == QtCore.Qt.RightButton):
            rc_index = self.indexAt(event.pos())

            # Check that the user actually clicked on an item.
            if (rc_index.row() > -1):
                self.rc_item = self.model.itemFromIndex(rc_index)
                if (self.rc_item == self.getCurrentItem()):
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

    def printItems(self):
        for i in range(self.model.rowCount()):
            print(i, self.model.item(i))

    def revertToPreviousItem(self):
        """
        Set the previously selected item as the current item.
        """
        self.setCurrentItem(self.getPreviousItem())
        
    def setCurrentItem(self, q_item):
        self.handleClicked(self.model.indexFromItem(q_item))

    def setRCParametersName(self, name):
        self.rc_item.setText(name)
                
    def setRCParametersStale(self, is_stale):
        getItemData(self.rc_item).stale = is_stale

    def setItemParameters(self, q_item, parameters):
        getItemData(q_item).parameters = parameters

    def setToolTip(self, q_item):
        parameters = self.getItemParameters(q_item)

        ttip = "Right click to edit"
        if (parameters.has("parameters_file")):
            ttip += "\n" + parameters.get("parameters_file")
        q_item.setToolTip(ttip)

    def updateRCToolTip(self):
        self.setToolTip(self.rc_item)
        

class ParametersStandardItemModel(QtGui.QStandardItemModel):

    def flags(self, index):
        """
        This blocks overwriting items during drag and drop re-ordering.
        """
        default_flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

        if index.isValid():
            return default_flags | QtCore.Qt.ItemIsDragEnabled
        else:
            return default_flags | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled


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
