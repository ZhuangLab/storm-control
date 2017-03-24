#!/usr/bin/env python
"""
This is the customized Listview, model, etc.

Hazen 03/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class ParametersMVC(QtWidgets.QListView):
    
    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.model = ParametersStandardItemModel(self)
        self.setModel(self.model)

        # This enables the user to re-order the items by dragging them.
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        for name in ["setting 1", "setting 2", "setting 3"]:
            self.model.appendRow(ParametersStandardItem(name))
            

class ParametersStandardItem(QtGui.QStandardItem):
    pass

    
class ParametersStandardItemModel(QtGui.QStandardItemModel):
    pass

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
