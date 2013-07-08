#!/usr/bin/python
#
# Handles the list of positions.
#
# Hazen 07/13
#

from PyQt4 import QtCore, QtGui

import coord


#
# Position item.
#
class PositionItem():

    brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
    deselected_pen = QtGui.QPen(QtGui.QColor(0,0,255))
    selected_pen = QtGui.QPen(QtGui.QColor(255,0,0))
    x_size = 1
    y_size = 1

    def __init__(self, a_point):
        self.scene_position_item = ScenePositionItem(self.x_size,
                                                     self.y_size,
                                                     self.deselected_pen,
                                                     self.brush)
        self.scene_position_item.setZValue(1000.0)
        self.setLocation(a_point)

    def getText(self):
        return self.text

    def getScenePositionItem(self):
        return self.scene_position_item
    
    def setLocation(self, a_point):
        self.text = "{0:.2f}, {1:.2f}".format(a_point.x_um, a_point.y_um)
        self.scene_position_item.setPos(a_point.x_pix - 0.5 * self.x_size,
                                        a_point.y_pix - 0.5 * self.y_size)

    def setSelected(self, selected):
        if selected:
            self.scene_position_item.setZValue(2000.0)
            self.scene_position_item.setPen(self.selected_pen)
        else:
            self.scene_position_item.setZValue(1000.0)
            self.scene_position_item.setPen(self.deselected_pen)
            

#
# Position list model.
#
class PositionListModel(QtCore.QAbstractListModel):

    def __init__(self, parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)

        self.positions = []

    def addPosition(self, a_position, parent = QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount()+1)
        self.positions.append(a_position)
        self.endInsertRows()

    def data(self, index, role):
        if index.isValid() and (role == QtCore.Qt.DisplayRole):
            return QtCore.QVariant(self.positions[index.row()].text)
        else:
            return QtCore.QVariant()

    def getPositionItems(self):
        return self.positions

    def removePosition(self, index, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, index, index + 1)
        a_scene_position_item = self.positions[index].getScenePositionItem()
        del self.positions[index]
        self.endRemoveRows()
        return a_scene_position_item
        
    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.positions)

    def setSelected(self, index, selected):
        self.positions[index].setSelected(selected)

    
#
# Position list view.
#
class Positions(QtGui.QListView):

    def __init__(self, parameters, scene, parent = None):
        QtGui.QListView.__init__(self, parent)

        self.plist_model = PositionListModel(parent)
        self.scene = scene

        PositionItem.deselected_pen.setWidth(parameters.pen_width)
        PositionItem.selected_pen.setWidth(parameters.pen_width)
        rectangle_size = parameters.rectangle_size/parameters.pixels_to_um
        PositionItem.x_size = rectangle_size
        PositionItem.y_size = rectangle_size

        self.setModel(self.plist_model)

    def addPosition(self, a_point):
        a_position = PositionItem(a_point)
        self.plist_model.addPosition(a_position)
        self.scene.addItem(a_position.getScenePositionItem())

    def currentChanged(self, current, previous):
        if (previous.row() >= 0):
            self.plist_model.setSelected(previous.row(), False)
        if (current.row() >= 0):
            self.plist_model.setSelected(current.row(), True)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Backspace) or (event.key() == QtCore.Qt.Key_Delete):
            current_index = self.currentIndex().row()
            if (current_index >= 0):
                self.scene.removeItem(self.plist_model.removePosition(current_index))
        else:
            QtGui.QListView.keyPressEvent(self, event)

    def loadFromMosaicFileData(self, data, directory):
        if (data[0] == "position"):
            self.addPosition(coord.Point(float(data[1]), float(data[2]), "um"))
            return True
        else:
            return False

    def loadPositions(self, filename):
        pos_fp = open(filename, "r")
        while 1:
            line = pos_fp.readline()
            if not line: break
            [x, y] = line.split(",")
            self.addPosition(coord.Point(float(x), float(y), "um"))

    def saveToMosaicFile(self, file_ptr, filename):
        for position in self.plist_model.getPositionItems():
            file_ptr.write("position," + position.getText() + "\r\n")

    def savePositions(self, filename):
        fp = open(filename, "w")
        for position_item in self.plist_model.getPositionItems():
            fp.write(position_item.text + "\r\n")
        fp.close()

    def setSceneItemsVisible(self, visible):
        ScenePositionItem.visible = visible


#
# Position rectangle rendering.
#
class ScenePositionItem(QtGui.QGraphicsRectItem):

    visible = True

    def __init__(self, x_size, y_size, pen, brush):
        QtGui.QGraphicsRectItem.__init__(self,
                                         0,
                                         0,
                                         x_size,
                                         y_size)
        self.setPen(pen)
        self.setBrush(brush)
        self.setZValue(1000.0)

    def paint(self, painter, options, widget):
        if self.visible:
            QtGui.QGraphicsRectItem.paint(self, painter, options, widget)


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
