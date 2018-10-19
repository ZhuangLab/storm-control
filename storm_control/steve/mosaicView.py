#!/usr/bin/env python
"""
The mosaic QGraphicsView, associated SteveItems and functions.

Hazen 10/18
"""
from PyQt5 import QtCore, QtGui, QtWidgets

#import storm_control.steve.qtMultifieldView as multiView
import storm_control.steve.coord as coord
import storm_control.steve.steveItems as steveItems


def createGrid(nx, ny):
    """
    Create a grid position array.
    """
    direction = 0
    positions = []
    if (nx > 1) or (ny > 1):
        half_x = int(nx/2)
        half_y = int(ny/2)
        for i in range(-half_y, half_y+1):
            for j in range(-half_x, half_x+1):
                if not ((i==0) and (j==0)):
                    if ((direction%2)==0):
                        positions.append([j,i])
                    else:
                        positions.append([-j,i])
            direction += 1
    return positions

def createSpiral(number):
    """
    Create a spiral position array.
    """
    number = number * number
    positions = []
    if (number > 1):
        # spiral outwards
        tile_x = 0.0
        tile_y = 0.0
        tile_count = 1
        spiral_count = 1
        while(tile_count < number):
            i = 0
            while (i < spiral_count) and (tile_count < number):
                if (spiral_count % 2) == 0:
                    tile_y -= 1.0
                else:
                    tile_y += 1.0
                i += 1
                tile_count += 1
                positions.append([tile_x, tile_y])
            i = 0
            while (i < spiral_count) and (tile_count < number):
                if (spiral_count % 2) == 0:
                    tile_x -= 1.0
                else:
                    tile_x += 1.0
                i += 1
                tile_count += 1
                positions.append([tile_x, tile_y])
            spiral_count += 1
    return positions


class Crosshair(QtWidgets.QGraphicsItem):
    """
    The cross-hair item to indicate the current stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ch_size = 15.0
        self.r_size = self.ch_size
        self.visible = False

        self.setZValue(1001.0)

    def boundingRect(self):
        return QtCore.QRectF(-self.r_size,
                              -self.r_size,
                              2.0 * self.r_size,
                              2.0 * self.r_size)

    def paint(self, painter, options, widget):
        if self.visible:
            painter.setPen(QtGui.QPen(QtGui.QColor(0,0,255)))
            painter.drawLine(-self.r_size, 0, self.r_size, 0)
            painter.drawLine(0, -self.r_size, 0, self.r_size)
            painter.drawEllipse(-0.5 * self.r_size,
                                 -0.5 * self.r_size,
                                 self.r_size,
                                 self.r_size)

    def setScale(self, scale):
        """
        Resizes the cross-hair based on the current view scale.
        """
        self.r_size = round(self.ch_size/scale)

    def setVisible(self, is_visible):
        """
        True/False if the cross-haur should be visible.
        """
        if is_visible:
            self.visible = True
        else:
            self.visible = False
        self.update()


class MosaicView(QtWidgets.QGraphicsView):
    """
    Handles user interaction with the mosaic.

    All coordinates are in pixels.
    """
    mouseMove = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def keyPressEvent(self, event):
        """
        Handles key press events. Valid events are:
        'space' Take a picture.
        '3' Take a 3 picture spiral.
        '5' Take a 5 picture spiral.
        '7' Take a 7 picture spiral.
        '9' Take a 9 picture spiral.
        'g' Take a grid of pictures.
        'p' Add the current cursor position to the list of positions.
        's' Add the current cursor position to the list of sections.
        """        
        event_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        self.pointf = self.mapToScene(event_pos)

        # picture taking
        if (event.key() == QtCore.Qt.Key_Space):
            self.handlePictures([])
        elif (event.key() == QtCore.Qt.Key_3):
            self.handlePictures(createSpiral(3))
        elif (event.key() == QtCore.Qt.Key_5):
            self.handlePictures(createSpiral(5))
        elif (event.key() == QtCore.Qt.Key_7):
            self.handlePictures(createSpiral(7))
        elif (event.key() == QtCore.Qt.Key_9):
            self.handlePictures(createSpiral(9))
        elif (event.key() == QtCore.Qt.Key_G):
            self.handlePictures(createGrid(self.number_x, self.number_y))

        # record position
        elif (event.key() == QtCore.Qt.Key_P):
            self.handlePos(False)

        # create section
        elif (event.key() == QtCore.Qt.Key_S):
            self.handleSec(False)

        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Tracks mouse movements across the view.
        """
        pointf = self.mapToScene(event.pos())
        self.mouseMove.emit(coord.Point(pointf.x(), pointf.y(), "pix"))

    def mousePressEvent(self, event):
        """
        If the left mouse button is pressed then the view is centered on the current cursor position.
        If the right mouse button is pressed then the current location of the cursor in the scene
        is recorded. If self.extrapolate_start exists then self.handleExtrapolatePict() is called,
        otherwise the popup menu is displayed.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))
        elif event.button() == QtCore.Qt.RightButton:
            self.pointf = self.mapToScene(event.pos())
            if self.extrapolate_start:
                self.handleExtrapolatePict()
            else:
                self.popup_menu.exec_(event.globalPos())

    def setCrosshairPosition(self, x_pos, y_pos):
        self.cross_hair.setPos(x_pos, y_pos)

    def showCrosshair(self, is_visible):
        """
        True/False to show or hide the current stage position cross-hair.
        """
        self.cross_hair.setVisible(is_visible)

    def wheelEvent(self, event):
        """
        Resizes the stage tracking cross-hair based on the current scale.
        """
        #multiView.MultifieldView.wheelEvent(self, event)
        self.cross_hair.setScale(self.view_scale)


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
