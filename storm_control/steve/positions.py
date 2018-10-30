#!/usr/bin/env python
"""
Handles the list of positions, including manipulation and 
display in graphics scene.

This is displayed in the mosaic tab, but is technically an 
independent SteveModule() like object.

Hazen 10/18
"""

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.coord as coord
import storm_control.steve.steveItems as steveItems


class PositionItem(steveItems.SteveItem):
    """
    These are the square boxes that are used for displaying
    positions of interest
    """
    brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
    deselected_pen = QtGui.QPen(QtGui.QColor(0,0,255))
    rectangle_size = 1
    selected_pen = QtGui.QPen(QtGui.QColor(255,0,0))

    def __init__(self, a_point = None, **kwds):
        super().__init__(**kwds)

        self.a_point = None
        self.text = None
        self.x_size = coord.umToPix(self.rectangle_size)
        self.y_size = coord.umToPix(self.rectangle_size)
        
        self.graphics_item = QtWidgets.QGraphicsRectItem(0, 0, self.x_size, self.y_size)
        self.graphics_item.setPen(self.deselected_pen)
        self.graphics_item.setBrush(self.brush)
        self.graphics_item.setZValue(1000.0)
        self.setLocation(a_point)

    def getText(self):
        """
        The current position of the object in microns as a text string.
        """
        return self.text

    def movePosition(self, dx_um, dy_um):
        a_point = coord.Point(self.a_point.x_um + dx_um,
                              self.a_point.y_um + dy_um,
                              "um")
        self.setLocation(a_point)

    def setLocation(self, a_point):
        self.a_point = a_point
        self.text = "{0:.2f},{1:.2f}".format(a_point.x_um, a_point.y_um)
        self.graphics_item.setPos(a_point.x_pix - 0.5 * self.x_size,
                                  a_point.y_pix - 0.5 * self.y_size)

    def setSelected(self, selected):
        """
        If the object is selected, increase it's z value and change the pen
        color, otherwise set the object's z value and pen color back to the
        unselected values.
        """
        if selected:
            self.graphics_item.setZValue(2000.0)
            self.graphics_item.setPen(self.selected_pen)
        else:
            self.graphics_item.setZValue(1000.0)
            self.graphics_item.setPen(self.deselected_pen)


class Positions(QtWidgets.QListView):
    """
    The position list view, this is what the user actually interacts with.

    This duck types a steveModule.SteveModule() object.
    """
    def __init__(self, item_store = None, parameters = None, **kwds):
        super().__init__(**kwds)

        self.context_menu_coord = None
        self.item_store = item_store
        self.step_size = parameters.get("step_size")
        self.title_bar = None

        PositionItem.deselected_pen.setWidth(parameters.get("pen_width"))
        PositionItem.selected_pen.setWidth(parameters.get("pen_width"))
        PositionItem.rectangle_size = parameters.get("rectangle_size")
                
        self.position_list_model = QtGui.QStandardItemModel()
        self.setModel(self.position_list_model)

    def addPosition(self, pos):

        # Add to our item store.
        position_item = PositionItem(pos)
        self.item_store.addItem(position_item)

        # Also add to this views model.
        positions_standard_item = PositionsStandardItem(position_item = position_item)
        self.position_list_model.appendRow(positions_standard_item)

        self.updateTitle()

    def currentChanged(self, current, previous):
        """
        Called when the currently selected item in the list changes.
        """
        previous_item = self.position_list_model.itemFromIndex(previous)
        if isinstance(previous_item, PositionsStandardItem):
            previous_item.setSelected(False)

        current_item = self.position_list_model.itemFromIndex(current)
        if isinstance(current_item, PositionsStandardItem):
            current_item.setSelected(True)

    def handleRecordPosition(self, ignored):
        self.addPosition(self.context_menu_coord)
            
    def keyPressEvent(self, event):
        current_item = self.position_list_model.itemFromIndex(self.currentIndex())
        if isinstance(current_item, PositionsStandardItem):
            current_pos_item = current_item.getPositionItem()
            which_key = event.key()

            # Delete current item.
            if (which_key == QtCore.Qt.Key_Backspace) or (which_key == QtCore.Qt.Key_Delete):
                self.position_list_model.removeRow(self.currentIndex().row())
                self.item_store.removeItem(current_pos_item.getItemID())
                self.updateTitle()
                
            elif (which_key == QtCore.Qt.Key_W):
                current_pos_item.movePosition(0.0, -self.step_size)
            elif (which_key == QtCore.Qt.Key_S):
                current_pos_item.movePosition(0.0, self.step_size)
            elif (which_key == QtCore.Qt.Key_A):
                current_pos_item.movePosition(-self.step_size, 0.0)
            elif (which_key == QtCore.Qt.Key_D):
                current_pos_item.movePosition(self.step_size, 0.0)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def loadPositions(self, filename):
        pos_fp = open(filename, "r")
        while 1:
            line = pos_fp.readline()
            if not line: break
            [x, y] = line.split(",")
            self.addPosition(coord.Point(float(x), float(y), "um"))

    def mosaicLoaded(self):
        for position_item in self.item_store.itemIterator(item_type = PositionItem):
            positions_standard_item = PositionsStandardItem(position_item = position_item)
            self.position_list_model.appendRow(positions_standard_item)
    
    def savePositions(self, filename):
        fp = open(filename, "w")
        for position_item in self.plist_model.getPositionItems():
            fp.write(position_item.text + "\r\n")
        fp.close()

    def setContextMenuCoord(self, a_coord):
        self.context_menu_coord = a_coord
        
    def setTitleBar(self, title_bar):
        self.title_bar = title_bar
        
#    def setSceneItemsVisible(self, visible):
#        ScenePositionItem.visible = visible

    def updateTitle(self):
        if self.title_bar is not None:
            n = self.position_list_model.rowCount()
            if (n == 0):
                self.title_bar.setTitle("Positions")
            else:
                self.title_bar.setTitle("Positions ({0:d} total)".format(n))


class PositionsStandardItem(QtGui.QStandardItem):

    def __init__(self, position_item = None, **kwds):
        super().__init__(**kwds)

        self.position_item = position_item

        self.setText(position_item.getText())
        
    def getPositionItem(self):
        return self.position_item
        
    def setSelected(self, selected):
        self.position_item.setSelected(selected)


#
# The MIT License
#
# Copyright (c) 2018 Zhuang Lab, Harvard University
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
