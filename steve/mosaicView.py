#!/usr/bin/python
#
# Handles viewing the mosaic.
#
# Hazen 07/13
#

import os

from PyQt4 import QtCore, QtGui

import qtMultifieldView as multiView
import coord

#
# Create a grid position array
#
def createGrid(nx, ny):
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
    addPosition = QtCore.pyqtSignal(object)
    addSection = QtCore.pyqtSignal(object)
    gotoPosition = QtCore.pyqtSignal(object)
    mouseMove = QtCore.pyqtSignal(object)
    takePictures = QtCore.pyqtSignal(object)

    def __init__(self, parameters, parent = None):
        multiView.MultifieldView.__init__(self, parameters, parent)

        # class variables
        self.extrapolate_count = parameters.extrapolate_picture_count
        self.extrapolate_start = None
        self.number_x = 5
        self.number_y = 3
        self.pointf = 0
        self.xoffset = 0.0
        self.yoffset = 0.0

        # popup menu initializiation
        self.pictAct = QtGui.QAction(self.tr("Take Picture"), self)
        self.posAct = QtGui.QAction(self.tr("Record Position"), self)
        self.secAct = QtGui.QAction(self.tr("Add Section"), self)
        self.gotoAct = QtGui.QAction(self.tr("Goto Position"), self)
        self.removeAct = QtGui.QAction(self.tr("Remove Last Picture"), self)
        self.extrapolateAct = QtGui.QAction(self.tr("Extrapolate"), self)

        self.popup_menu = QtGui.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.posAct)
        self.popup_menu.addAction(self.secAct)
        self.popup_menu.addAction(self.gotoAct)
        self.popup_menu.addAction(self.removeAct)
        self.popup_menu.addAction(self.extrapolateAct)

        # signals
        self.pictAct.triggered.connect(self.handlePict)
        self.posAct.triggered.connect(self.handlePos)
        self.secAct.triggered.connect(self.handleSec)
        self.gotoAct.triggered.connect(self.handleGoto)
        self.removeAct.triggered.connect(self.handleRemoveLastItem)
        self.extrapolateAct.triggered.connect(self.handleExtrapolate)

    def addImage(self, image, objective, magnification, offset):
        x_pix = image.x_pix - (image.width * 0.5 / magnification)
        y_pix = image.y_pix - (image.height * 0.5 / magnification)
        self.addViewImageItem(image,
                              x_pix,
                              y_pix,
                              offset.x_pix,
                              offset.y_pix,
                              objective,
                              magnification,
                              self.currentz)
        self.currentz += 0.01

    def changeMagnification(self, objective, new_magnification):
        self.changeImageMagnifications(objective, new_magnification)

    def changeXOffset(self, objective, x_offset_pix):
        self.changeImageXOffsets(objective, x_offset_pix)

    def changeYOffset(self, objective, y_offset_pix):
        self.changeImageYOffsets(objective, y_offset_pix)

    def getScene(self):
        return self.scene

    def gridChange(self, xnum, ynum):
        self.number_x = xnum
        self.number_y = ynum

    def handleExtrapolate(self, boolean):
        self.extrapolate_start = self.pointf

    def handleExtrapolatePict(self):
        pict_x = self.pointf.x() + (self.pointf.x() - self.extrapolate_start.x())
        pict_y = self.pointf.y() + (self.pointf.y() - self.extrapolate_start.y())
        self.extrapolate_start = None
        pic_list = [coord.Point(pict_x, pict_y, "pix")]
        pic_list.extend(createSpiral(self.extrapolate_count))
        self.takePictures.emit(pic_list)

    def handleGoto(self, boolean):
        self.gotoPosition.emit(coord.Point(self.pointf.x(), self.pointf.y(), "pix"))

    def handlePict(self, boolean):
        self.handlePictures([])

    def handlePictures(self, positions):
        pic_list = [coord.Point(self.pointf.x(), self.pointf.y(), "pix")]
        pic_list.extend(positions)
        self.takePictures.emit(pic_list)

    def handlePos(self, boolean):
        self.addPosition.emit([coord.Point(self.pointf.x(), self.pointf.y(), "pix")])

    def handleSec(self, boolean):
        self.addSection.emit(coord.Point(self.pointf.x(), self.pointf.y(), "pix"))

    def keyPressEvent(self, event):
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
            self.handlePos()

        # create section
        elif (event.key() == QtCore.Qt.Key_S):
            self.handleSec()

        multiView.MultifieldView.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        pointf = self.mapToScene(event.pos())
        self.mouseMove.emit(coord.Point(pointf.x(), pointf.y(), "pix"))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))
        elif event.button() == QtCore.Qt.RightButton:
            self.pointf = self.mapToScene(event.pos())
            if self.extrapolate_start:
                self.handleExtrapolatePict()
            else:
                self.popup_menu.exec_(event.globalPos())


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
