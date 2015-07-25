#!/usr/bin/python
#
## @file
#
# Handles the list of positions, including manipulation and display in graphics scene.
#
# Hazen 07/13
#

from PyQt4 import QtCore, QtGui


## PositionItem
#
# This class encapsulates a position item.
#
class PositionItem():

    brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
    deselected_pen = QtGui.QPen(QtGui.QColor(0,0,255))
    rectangle_size = 1
    selected_pen = QtGui.QPen(QtGui.QColor(255,0,0))

    ## __init__
    #
    # @param a_point A coord.Point object.
    #
    def __init__(self, a_point):
        self.a_point = a_point

        self.x_size = self.rectangle_size / a_point.pixels_to_um
        self.y_size = self.rectangle_size / a_point.pixels_to_um
        self.scene_position_item = ScenePositionItem(self.x_size,
                                                     self.y_size,
                                                     self.deselected_pen,
                                                     self.brush)
        self.text = "NA"
        self.scene_position_item.setZValue(1000.0)
        self.setLocation(self.a_point)

    ## getText
    #
    # @return The current position of the object in microns as a text string.
    #
    def getText(self):
        return self.text

    ## getScenePositionItem
    #
    # @return The QGraphicsScene object associated with this object.
    #
    def getScenePositionItem(self):
        return self.scene_position_item

    ## movePosition
    #
    # @param dx_um Amount to move in x in microns.
    # @param dy_um Amount to move in y in microns.
    #
    def movePosition(self, dx_um, dy_um):
        self.a_point = coord.Point(self.a_point.x_um + dx_um,
                                   self.a_point.y_um + dy_um,
                                   "um")
        self.setLocation(self.a_point)

    ## setLocation
    #
    # @param a_point A coord.Point object specifying the location of this object.
    #
    def setLocation(self, a_point):
        self.text = "{0:.2f}, {1:.2f}".format(a_point.x_um, a_point.y_um)
        self.scene_position_item.setPos(a_point.x_pix - 0.5 * self.x_size,
                                        a_point.y_pix - 0.5 * self.y_size)

    ## setSelected
    #
    # If the object is selected, increase it's z value and change the pen
    # color, otherwise set the object's z value and pen color back to the
    # unselected values.
    #
    # @param selected True/False if the object is currently selected.
    #
    def setSelected(self, selected):
        if selected:
            self.scene_position_item.setZValue(2000.0)
            self.scene_position_item.setPen(self.selected_pen)
        else:
            self.scene_position_item.setZValue(1000.0)
            self.scene_position_item.setPen(self.deselected_pen)
            

## PositionListModel
#
# This object handles the position list model associated with the position list view.
#
class PositionListModel(QtCore.QAbstractListModel):

    ## __init__
    #
    # @param parent The PyQt parent of this object, defaults to None.
    #
    def __init__(self, parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)

        self.group_box = None
        if parent is not None:
            self.group_box = parent.parentWidget()
            
        self.positions = []

    ## addPosition
    #
    # @param a_position A PositionItem object.
    # @param parent (Optional) Defaults to QtCore.QModelIndex().
    #
    def addPosition(self, a_position, parent = QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount()+1)
        self.positions.append(a_position)
        self.endInsertRows()
        self.updateTitle()
        
    ## data
    #
    # @param index The index of the item to get the data of.
    # @param role What we want the data for?
    #
    # @return If role == QtCore.Qt.DisplayRole then return the items text field as a QtCore.QVariant, otherwise return a empty QtCore.QVariant.
    #
    def data(self, index, role):
        if index.isValid() and (role == QtCore.Qt.DisplayRole):
            return QtCore.QVariant(self.positions[index.row()].text)
        else:
            return QtCore.QVariant()

    ## getPositionItems
    #
    # @return An array containing all of the position items.
    #
    def getPositionItems(self):
        return self.positions

    ## movePosition
    #
    # @param q_index A QModelIndex specifying which item to move.
    # @param dx_um The amount to move in x in microns.
    # @param dy_um The amount to move in y in microns.
    #
    def movePosition(self, q_index, dx_um, dy_um):
        self.positions[q_index.row()].movePosition(dx_um, dy_um)
        self.dataChanged.emit(q_index, q_index)

    ## removePosition
    #
    # @param index The index of the item to remove.
    # @param parent (Optional) Defaults to QtCore.QModelIndex.
    #
    # @return The item that was removed from the list model.
    #
    def removePosition(self, index, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, index, index + 1)
        a_scene_position_item = self.positions[index].getScenePositionItem()
        del self.positions[index]
        self.endRemoveRows()
        self.updateTitle()
        return a_scene_position_item

    ## rowCount
    #
    # @param parent (Optional) Defaults to QtCore.QModelIndex.
    #
    # @return The number of items in the list model.
    #
    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.positions)

    ## setSelected
    #
    # @param index The index to set the selection state of.
    # @param selected True/False if this item is selected/unselected.
    #
    def setSelected(self, index, selected):
        self.positions[index].setSelected(selected)

    ## updateTitle
    #
    # Updates the title with the current number of positions.
    #
    def updateTitle(self):
        if self.group_box is not None:
            n = len(self.positions)
            if (n == 0):
                self.group_box.setTitle("Positions")
            else:
                self.group_box.setTitle("Positions (" + str(n) + " total)")

                
## Positions
#
# The position list view, this is what the user actually interacts with.
#
class Positions(QtGui.QListView):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param scene A QGraphicsScene object.
    # @param parent (Optional) The PyQt parent of this object, defaults to None.
    #
    def __init__(self, parameters, scene, parent = None):
        QtGui.QListView.__init__(self, parent)

        self.plist_model = PositionListModel(parent)
        self.scene = scene
        self.step_size = parameters.step_size

        PositionItem.deselected_pen.setWidth(parameters.get("pen_width"))
        PositionItem.selected_pen.setWidth(parameters.get("pen_width"))
        PositionItem.rectangle_size = parameters.get("rectangle_size")

        self.setModel(self.plist_model)

    ## addPosition
    #
    # Add a position to the list.
    #
    # @param a_point A coord.Point object specifying the location of the position to add.
    #
    def addPosition(self, a_point):
        a_position = PositionItem(a_point)
        self.plist_model.addPosition(a_position)
        self.scene.addItem(a_position.getScenePositionItem())

    ## currentChanged
    #
    # Called when the currently selected item in the list changes.
    #
    # @param current A QtCore.QModelIndex object specifying the currently selected item.
    # @param previous A QtCore.QModelIndex object specifying the previously selected item.
    #
    def currentChanged(self, current, previous):
        if (previous.row() >= 0):
            self.plist_model.setSelected(previous.row(), False)
        if (current.row() >= 0):
            self.plist_model.setSelected(current.row(), True)

    ## keyPressEvent
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        which_key = event.key()
        if (which_key == QtCore.Qt.Key_Backspace) or (which_key == QtCore.Qt.Key_Delete):
            current_index = self.currentIndex().row()
            if (current_index >= 0):
                self.scene.removeItem(self.plist_model.removePosition(current_index))
        elif (which_key == QtCore.Qt.Key_W):
            self.plist_model.movePosition(self.currentIndex(), 0.0, -self.step_size)
        elif (which_key == QtCore.Qt.Key_S):
            self.plist_model.movePosition(self.currentIndex(), 0.0, self.step_size)
        elif (which_key == QtCore.Qt.Key_A):
            self.plist_model.movePosition(self.currentIndex(), -self.step_size, 0.0)
        elif (which_key == QtCore.Qt.Key_D):
            self.plist_model.movePosition(self.currentIndex(), self.step_size, 0.0)
        else:
            QtGui.QListView.keyPressEvent(self, event)

    ## loadFromMosaicFileData
    #
    # This is called when we are loading a previously saved mosaic.
    #
    # @param data A data element from the mosaic file.
    # @param directory The directory in which the mosaic file is located.
    #
    # @return True/False if the data element described a position item.
    #
    def loadFromMosaicFileData(self, data, directory):
        if (data[0] == "position"):
            self.addPosition(coord.Point(float(data[1]), float(data[2]), "um"))
            return True
        else:
            return False

    ## loadPositions
    #
    # Add positions to the current list from a positions.txt file.
    #
    # @param filename The name of the text file containing the positions.
    #
    def loadPositions(self, filename):
        pos_fp = open(filename, "r")
        while 1:
            line = pos_fp.readline()
            if not line: break
            [x, y] = line.split(",")
            self.addPosition(coord.Point(float(x), float(y), "um"))

    ## saveToMosaicFile
    #
    # Save the current position items into a mosaic file.
    #
    # @param file_ptr The file pointer of the file to save the positions to.
    # @param filename The name of the file to save the positions to (not used).
    #
    def saveToMosaicFile(self, file_ptr, filename):
        for position in self.plist_model.getPositionItems():
            file_ptr.write("position," + position.getText() + "\r\n")

    ## savePositions
    #
    # Save the current positions in a text file such as might be used by Dave.
    #
    # @param filename The name of the text file to save the positions in.
    #
    def savePositions(self, filename):
        fp = open(filename, "w")
        for position_item in self.plist_model.getPositionItems():
            fp.write(position_item.text + "\r\n")
        fp.close()

    ## setSceneItemsVisible
    #
    # Sets the visibility field of all the scenePositionItems in the QGraphicsScene.
    #
    # @param visible True/False if the items should be visible/invisible in the QGraphicsScene.
    #
    def setSceneItemsVisible(self, visible):
        ScenePositionItem.visible = visible


## ScenePositionItem
#
# This class handles the display of the PositionItems in a QGraphicsScene.
#
class ScenePositionItem(QtGui.QGraphicsRectItem):

    visible = True

    ## __init__
    #
    # @param x_size The x size in pixels of the PositionItem rectangle.
    # @param y_size The y size in pixels of the PositionItem rectangle.
    # @param pen The QPen to use when rendering this ScenePositionItem in the scene.
    # @param brush The QBrush to use when rendering this ScenePositionItem in the scene.
    #
    def __init__(self, x_size, y_size, pen, brush):
        QtGui.QGraphicsRectItem.__init__(self,
                                         0,
                                         0,
                                         x_size,
                                         y_size)
        self.setPen(pen)
        self.setBrush(brush)
        self.setZValue(1000.0)

    ## paint
    #
    # Called when the ScenePositionItem needs to be updated. If the class variable
    # visible is False then the ScenePositionItem is not displayed.
    #
    # @param painter A QPainter object.
    # @param options A QStyleOptionGraphicsItem object.
    # @param widget A QWidget object.
    #
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
