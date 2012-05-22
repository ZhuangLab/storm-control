#!/usr/bin/python
#
# Handles viewing the mosaic.
#
# Hazen 06/11
#

import os

from PyQt4 import QtCore, QtGui

import qtMultifieldView as multiView


#
# Create a grid position array
#
def createGrid(nx, ny):
    direction = 0
    positions = []
    if (nx > 1) or (ny > 1):
        half_x = int(nx/2)
        half_y = int(ny/2)
        for i in range(ny):
            for j in range(nx):
                if ((direction%2)==0):
                    positions.append([j-half_x,i-half_y])
                else:
                    positions.append([nx-j-half_x-1,i-half_y])
            direction += 1
    return positions


#
# Create a spiral position array
#
def createSpiral(number):
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


#
# Handles user interaction with the mosaic.
#
# All coordinates are in pixels.
#
class MosaicView(multiView.MultifieldView):
    def __init__(self, parameters, parent = None):
        super(MosaicView, self).__init__(parameters, parent)

        # class variables
        self.extrapolate_count = parameters.extrapolate_picture_count
        self.extrapolate_start = None
        self.magnification = parameters.magnification
        self.number_x = 5
        self.number_y = 3
        self.pixels_to_um = parameters.pixels_to_um
        self.pointf = 0
        self.rectangle_size = parameters.rectangle_size/self.pixels_to_um
        self.setup_name = parameters.setup_name
        self.x_sign = parameters.x_sign
        self.xoffset = 0.0
        self.y_sign = parameters.y_sign
        self.yoffset = 0.0

        self.pen = QtGui.QPen(self.pen_color)
        self.pen.setWidth(self.pen_width)

        pen = QtGui.QPen(QtGui.QColor(0, 0, 255))
        pen.setWidth(self.pen_width)
        self.selectionRect = self.addRectangle(0,
                                               0,
                                               self.rectangle_size,
                                               self.rectangle_size,
                                               pen,
                                               2000.0)

        # popup menu initializiation
        self.pictAct = QtGui.QAction(self.tr("Take Picture"), self)
        self.posAct = QtGui.QAction(self.tr("Record Position"), self)
        self.gotoAct = QtGui.QAction(self.tr("Goto Position"), self)
        self.removeAct = QtGui.QAction(self.tr("Remove Last Picture"), self)
        self.extrapolateAct = QtGui.QAction(self.tr("Extrapolate"), self)

        self.popup_menu = QtGui.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.posAct)
        self.popup_menu.addAction(self.gotoAct)
        self.popup_menu.addAction(self.removeAct)
        self.popup_menu.addAction(self.extrapolateAct)

        # signals
        self.connect(self.pictAct, QtCore.SIGNAL("triggered()"), self.handlePict)
        self.connect(self.posAct, QtCore.SIGNAL("triggered()"), self.handlePos)
        self.connect(self.gotoAct, QtCore.SIGNAL("triggered()"), self.handleGoto)
        self.connect(self.removeAct, QtCore.SIGNAL("triggered()"), self.handleRemoveLastItem)
        self.connect(self.extrapolateAct, QtCore.SIGNAL("triggered()"), self.handleExtrapolate)

    def addPixmap(self, pixmap, x_um, y_um):
        x_pix = x_um / self.pixels_to_um - pixmap.width() * 0.5 * self.x_sign / self.magnification + self.xoffset
        y_pix = y_um / self.pixels_to_um - pixmap.height() * 0.5 * self.y_sign / self.magnification + self.yoffset
        mapped_pos = self.mapPosition(x_pix, y_pix)
        self.addViewPixmapItem(pixmap, 
                               mapped_pos.x(),
                               mapped_pos.y(),
                               x_um,
                               y_um,
                               self.magnification,
                               "new",
                               self.currentz)
        self.currentz += 0.01

    def addPositionRectangle(self, x_um, y_um):
        mapped_pos = self.mapPosition(x_um / self.pixels_to_um, 
                                      y_um / self.pixels_to_um)
        return self.addRectangle(mapped_pos.x(),
                                 mapped_pos.y(),
                                 self.rectangle_size,
                                 self.rectangle_size,
                                 self.pen,
                                 1000.0)

    def changeMagnification(self, newMag, xoffset, yoffset):
        self.magnification = newMag
        self.xoffset = xoffset/self.pixels_to_um
        self.yoffset = yoffset/self.pixels_to_um

    def gridChange(self, xnum, ynum):
        self.number_x = xnum
        self.number_y = ynum

    def handleExtrapolate(self):
        self.extrapolate_start = self.pointf

    def handleExtrapolatePict(self):
        pict_x = self.pointf.x() + (self.pointf.x() - self.extrapolate_start.x())
        pict_y = self.pointf.y() + (self.pointf.y() - self.extrapolate_start.y())
        self.extrapolate_start = None
        self.emit(QtCore.SIGNAL("takePictures(float, float, PyQt_PyObject)"),
                  pict_x * self.pixels_to_um,
                  pict_y * self.pixels_to_um,
                  createSpiral(self.extrapolate_count))

    def handleGoto(self):
        self.emit(QtCore.SIGNAL("gotoPosition(float, float)"),
                  (self.pointf.x() - self.xoffset) * self.pixels_to_um,
                  (self.pointf.y() - self.yoffset) * self.pixels_to_um)

    def handlePict(self):
        self.handlePictures([])

    def handlePictures(self, positions):
        self.emit(QtCore.SIGNAL("takePictures(float, float, PyQt_PyObject)"),
                  (self.pointf.x() - self.xoffset) * self.pixels_to_um,
                  (self.pointf.y() - self.yoffset) * self.pixels_to_um,
                  positions)

    def handlePos(self):
        self.emit(QtCore.SIGNAL("addPosition(float, float)"),
                  self.pointf.x() * self.pixels_to_um,
                  self.pointf.y() * self.pixels_to_um)

    def keyPressEvent(self, event):
        event_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        self.pointf = self.mapPosition(self.mapToScene(event_pos))

        # picture taking
        if event.key() == QtCore.Qt.Key_Space:
            self.handlePictures([])
        if event.key() == 51: # 3
            self.handlePictures(createSpiral(3))
        if event.key() == 53: # 5
            self.handlePictures(createSpiral(5))
        if event.key() == 55: # 7
            self.handlePictures(createSpiral(7))
        if event.key() == 57: # 9
            self.handlePictures(createSpiral(9))
        if event.key() == 71: # g
            self.handlePictures(createGrid(self.number_x, self.number_y))

        super(MosaicView, self).keyPressEvent(event)

    def mapPosition(self, x, y = None):
        if (type(x) == type(QtCore.QPointF())):
            y = x.y()
            x = x.x()
        if self.setup_name == "storm3":
            return QtCore.QPointF(y * self.x_sign, x * self.y_sign)
        elif self.setup_name == "prism2":
            return QtCore.QPointF(x * self.x_sign, y * self.y_sign)
        elif self.setup_name == "storm2":
            return QtCore.QPointF(y * self.x_sign, x * self.y_sign)
        elif self.setup_name == "storm4":
            return QtCore.QPointF(y * self.x_sign, x * self.y_sign)
        else:
            return QtCore.QPointF(x, y)

    def mouseMoveEvent(self, event):
        pointf = self.mapPosition(self.mapToScene(event.pos()))
        self.emit(QtCore.SIGNAL("mouseMove(float, float)"),
                  pointf.x() * self.pixels_to_um,
                  pointf.y() * self.pixels_to_um)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))
        elif event.button() == QtCore.Qt.RightButton:
            self.pointf = self.mapPosition(self.mapToScene(event.pos()))
            if self.extrapolate_start:
                self.handleExtrapolatePict()
            else:
                self.popup_menu.exec_(event.globalPos())

    def moveRectangle(self, rect, x_um, y_um):
        x_pix = x_um / self.pixels_to_um
        y_pix = y_um / self.pixels_to_um
        rect.setPos(self.mapPosition(x_pix, y_pix))

    def moveSelectionRectangle(self, x_um, y_um):
        x_pix = x_um / self.pixels_to_um - self.rectangle_size * 0.5 * self.x_sign
        y_pix = y_um / self.pixels_to_um - self.rectangle_size * 0.5 * self.y_sign
        self.selectionRect.setPos(self.mapPosition(x_pix, y_pix))


#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
