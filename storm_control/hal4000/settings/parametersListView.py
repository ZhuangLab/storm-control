#!/usr/bin/env python
"""
This is the customized Listview, model, etc.

Hazen 03/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets


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
        self.initialized = False
        self.parameters = parameters

    def getChecked(self):
        return self.checked

    def getParameters(self):
        return self.parameters

    
class ParametersListViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    This lets us draw items that look like radio buttons.
    """
    def __init__(self, model = None, **kwds):
        super().__init__(**kwds)
        self.model = model

    def paint(self, painter, option, index):
        note = self.model.itemFromIndex(index)
        print(type(getItemData(note)))
        
        opt = QtWidgets.QStyleOptionButton()
        opt.rect = option.rect
        opt.text = note.text()
        
        style = option.widget.style()
        style.drawControl(QtWidgets.QStyle.CE_RadioButton, opt, painter, option.widget)
        
        
class ParametersMVC(QtWidgets.QListView):
    
    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.model = ParametersStandardItemModel(self)
        self.setModel(self.model)

        # This enables the user to re-order the items by dragging them.
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        self.setItemDelegate(ParametersListViewDelegate(model = self.model))

        for name in ["setting 1", "setting 2", "setting 3"]:
            qitem = QtGui.QStandardItem(name)
            qitem.setData(ParametersItemData())
            self.model.appendRow(qitem)
    
    
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
