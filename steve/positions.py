#!/usr/bin/python
#
# Handles the list of positions.
#
# Hazen 03/13
#

from PyQt4 import QtCore, QtGui

import coord

#
# List of Positions
#
class Positions(QtGui.QListWidget):
    addPositionSig = QtCore.pyqtSignal(object)
    currentPositionChange = QtCore.pyqtSignal(object)
    deletePosition = QtCore.pyqtSignal(int)

    def __init__(self, parent = None):
        QtGui.QListWidget.__init__(self, parent)

        # ui initialization
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.currentRowChanged.connect(self.handleRowChange)

    def addPosition(self, a_point):
        self.addItem("{0:.2f}, {1:.2f}".format(a_point.x_um, a_point.y_um))

    def handleRowChange(self, row):
        if (row > -1):
            [x, y] = str(self.item(row).text()).split(",")
            self.currentPositionChange.emit(coord.Point(float(x), float(y), "um"))
        else:
            self.currentPositionChange.emit(coord.Point(0.0, 0.0, "um"))

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Backspace) or (event.key() == QtCore.Qt.Key_Delete):
            if (self.count() > 0):
                current = self.currentRow()
                self.takeItem(current)
                self.deletePosition.emit(current)
        else:
            QtGui.QListWidget.keyPressEvent(self, event)

    def loadPositions(self, filename):
        pos_fp = open(filename, "r")
        while 1:
            line = pos_fp.readline()
            if not line: break
            [x, y] = line.split(",")
            self.addPositionSig.emit([coord.Point(float(x), float(y), "um")])

    def savePositions(self, filename):
        fp = open(filename, "w")
        for i in range(self.count()):
            fp.write(str(self.item(i).text()) + "\r\n")
        fp.close()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
