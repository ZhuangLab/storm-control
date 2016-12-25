#!/usr/bin/python
#
## @file
#
# Handles viewing the mosaic.
#
# Hazen 06/14
#

import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.qtMultifieldView as multiView
import storm_control.steve.coord as coord

## createGrid
#
# Create a grid position array.
#
# @param nx Size of the grid in x.
# @param ny Size of the grid in y.
#
# @return An array of positions, [[0,1],[1,1],..]
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

## createSpiral
#
# Create a spiral position array.
#
# @param number The number of images in the spiral.
#
# @return An array of positions, [[0,0],[0,1],[1,1]..]
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


## Crosshair
#
# The cross-hair item to indicate the current stage position.
#
class Crosshair(QtWidgets.QGraphicsItem):

    ## __init__
    #
    # Create a Crosshair object.
    #
    def __init__(self):
        QtWidgets.QGraphicsItem.__init__(self)

        self.ch_size = 15.0
        self.r_size = self.ch_size
        self.visible = False

        self.setZValue(1001.0)

    ## boundingRect
    #
    # @return The bounding rectangle (as a QRectF)
    #
    def boundingRect(self):
        return QtCore.QRectF(-self.r_size,
                              -self.r_size,
                              2.0 * self.r_size,
                              2.0 * self.r_size)

    ## paint
    #
    # @param painter A QPainter object.
    # @param options A QStyleOptionGraphicsItem object.
    # @param widget A QWidget object.
    #
    def paint(self, painter, options, widget):
        if self.visible:
            painter.setPen(QtGui.QPen(QtGui.QColor(0,0,255)))
            painter.drawLine(-self.r_size, 0, self.r_size, 0)
            painter.drawLine(0, -self.r_size, 0, self.r_size)
            painter.drawEllipse(-0.5 * self.r_size,
                                 -0.5 * self.r_size,
                                 self.r_size,
                                 self.r_size)
    
    ## setScale
    #
    # Resizes the cross-hair based on the current view scale.
    #
    # @param scale The current scale of the view.
    #
    def setScale(self, scale):
        self.r_size = round(self.ch_size/scale)

    ## setVisible
    #
    # @param is_visible True/False if the cross-haur should be visible.
    #
    def setVisible(self, is_visible):
        if is_visible:
            self.visible = True
        else:
            self.visible = False
        self.update()

        
## MosaicView
#
# Handles user interaction with the mosaic.
#
# All coordinates are in pixels.
#
class MosaicView(multiView.MultifieldView):
    addPosition = QtCore.pyqtSignal(object)
    addSection = QtCore.pyqtSignal(object)
    getObjective = QtCore.pyqtSignal()
    gotoPosition = QtCore.pyqtSignal(object)
    mouseMove = QtCore.pyqtSignal(object)
    takePictures = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQy parent of this object, defaults to none.
    #
    def __init__(self, parameters, parent = None):
        multiView.MultifieldView.__init__(self, parameters, parent)

        # class variables
        self.cross_hair = Crosshair()
        self.extrapolate_count = parameters.get("extrapolate_picture_count")
        self.extrapolate_start = None
        self.number_x = 5
        self.number_y = 3
        self.pointf = 0
        self.xoffset = 0.0
        self.yoffset = 0.0

        # popup menu initializiation
        self.extrapolateAct = QtWidgets.QAction(self.tr("Extrapolate"), self)
        self.getObjAct = QtWidgets.QAction(self.tr("Query Objective"), self)
        self.gotoAct = QtWidgets.QAction(self.tr("Goto Position"), self)
        self.pictAct = QtWidgets.QAction(self.tr("Take Picture"), self)
        self.posAct = QtWidgets.QAction(self.tr("Record Position"), self)
        self.removeAct = QtWidgets.QAction(self.tr("Remove Last Picture"), self)
        self.secAct = QtWidgets.QAction(self.tr("Add Section"), self)

        self.popup_menu = QtWidgets.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.gotoAct)
        self.popup_menu.addAction(self.posAct)
        self.popup_menu.addAction(self.secAct)
        self.popup_menu.addAction(self.getObjAct)
        self.popup_menu.addAction(self.removeAct)
        self.popup_menu.addAction(self.extrapolateAct)

        # signals
        self.extrapolateAct.triggered.connect(self.handleExtrapolate)
        self.getObjAct.triggered.connect(self.handleGetObjective)
        self.gotoAct.triggered.connect(self.handleGoto)
        self.pictAct.triggered.connect(self.handlePict)
        self.posAct.triggered.connect(self.handlePos)
        self.secAct.triggered.connect(self.handleSec)
        self.removeAct.triggered.connect(self.handleRemoveLastItem)

        # crosshair
        self.scene.addItem(self.cross_hair)

    ## addImage
    #
    # Add a capture.Image object to the graphics scene.
    #
    # @param image The capture.Image object.
    # @param objective The name of the current objective (a string).
    # @param magnification The magnification of the objective.
    # @param offset The offset of the current objective to the reference objective (a coord.Point object).
    #
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

    ## changeMagnification
    #
    # This changes the magnification of all the viewImageItems in the scene that are associated with a particular objective.
    #
    # @param objective The name of the objective (a string).
    # @param new_magnification The magnification to use when rendering these images.
    #
    def changeMagnification(self, objective, new_magnification):
        self.changeImageMagnifications(objective, new_magnification)

    ## changeXOffset
    #
    # This changes the x offset of all the viewImageItems in the scene that are associated with a particular objective.
    #
    # @param objective The name of the objective (a string).
    # @param x_offset_pix The new x offset (relative to the reference objective) to use when rendering these images.
    #
    def changeXOffset(self, objective, x_offset_pix):
        self.changeImageXOffsets(objective, x_offset_pix)

    ## changeYOffset
    #
    # This changes the y offset of all the viewImageItems in the scene that are associated with a particular objective.
    #
    # @param objective The name of the objective (a string).
    # @param y_offset_pix The new y offset (relative to the reference objective) to use when rendering these images.
    #
    def changeYOffset(self, objective, y_offset_pix):
        self.changeImageYOffsets(objective, y_offset_pix)

    ## getScene
    #
    # @return The QGraphicsScene associated with this QGraphicsView.
    #
    def getScene(self):
        return self.scene

    ## gridChange
    #
    # Change the size of the grid to return when asked to generate a grid of positions.
    #
    # @param xnum The new size of the grid in x.
    # @param ynum The new size of the grid in y.
    #
    def gridChange(self, xnum, ynum):
        self.number_x = xnum
        self.number_y = ynum

    ## handleExtrapolate
    #
    # Handles the extrapolate action. Records the current mouse position in the QGraphicsView
    # when the action was generated in the class variable self.extrapolate_start
    #
    # @param boolean Dummy parameter.
    #
    def handleExtrapolate(self, boolean):
        self.extrapolate_start = self.pointf

    ## handleExtrapolatePict
    #
    # Takes a series of pictures at a location calculated from where the user clicked
    # to start the extrapolation action and the next place the user clicked. The
    # extrapolation is linear.
    #
    # Emits the takePictures signal.
    #
    def handleExtrapolatePict(self):
        pict_x = self.pointf.x() + (self.pointf.x() - self.extrapolate_start.x())
        pict_y = self.pointf.y() + (self.pointf.y() - self.extrapolate_start.y())
        self.extrapolate_start = None
        pic_list = [coord.Point(pict_x, pict_y, "pix")]
        pic_list.extend(createSpiral(self.extrapolate_count))
        self.takePictures.emit(pic_list)

    ## handleGetObjective
    #
    # Handles querying the current objective.
    #
    # @param boolean Dummy parameter.
    #
    def handleGetObjective(self, boolean):
        self.getObjective.emit()
        
    ## handleGoto
    #
    # Handles the goto (i.e. move the stage) action.
    #
    # Emits the gotoPosition signal.
    #
    # @param boolean Dummy parameter.
    #
    def handleGoto(self, boolean):
        self.gotoPosition.emit(coord.Point(self.pointf.x(), self.pointf.y(), "pix"))

    ## handlePict
    #
    # Handles the take picture at a given location action.
    #
    # @param boolean Dummy parameter.
    #
    def handlePict(self, boolean):
        self.handlePictures([])

    ## handlePictures
    #
    # Handles taking pictures. This constructs an array structured like this:
    # [coord.Point() from self.pointf, [offset x 1, offset y 1], [offset x 2, offset y 2], ..]
    #
    # Emits the takePictures signal.
    #
    # @param positions A array of position offsets to take the pictures at.
    #
    def handlePictures(self, positions):
        pic_list = [coord.Point(self.pointf.x(), self.pointf.y(), "pix")]
        pic_list.extend(positions)
        self.takePictures.emit(pic_list)

    ## handlePos
    #
    # Handles the add position action.
    #
    # Emits the addPosition signal.
    #
    # @param boolean Dummy parameter.
    #
    def handlePos(self, boolean):
        self.addPosition.emit([coord.Point(self.pointf.x(), self.pointf.y(), "pix")])

    ## handleSec
    #
    # Handles the add section action.
    #
    # Emits the addSection signal.
    #
    # @param boolean Dummy parameter.
    #
    def handleSec(self, boolean):
        self.addSection.emit(coord.Point(self.pointf.x(), self.pointf.y(), "pix"))

    ## keyPressEvent
    #
    # Handles key press events. Valid events are:
    # 'space' Take a picture.
    # '3' Take a 3 picture spiral.
    # '5' Take a 5 picture spiral.
    # '7' Take a 7 picture spiral.
    # '9' Take a 9 picture spiral.
    # 'g' Take a grid of pictures.
    # 'p' Add the current cursor position to the list of positions.
    # 's' Add the current cursor position to the list of sections.
    #
    # Records the current cursor location in the scene in self.pointf.
    #
    # @param event A PyQt key press event.
    #
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
            self.handlePos(False)

        # create section
        elif (event.key() == QtCore.Qt.Key_S):
            self.handleSec(False)

        multiView.MultifieldView.keyPressEvent(self, event)

    ## mouseMoveEvent
    #
    # Tracks mouse movements across the view.
    #
    # Emits the mouseMove signal.
    #
    # @param event A PyQt mouse move event.
    #
    def mouseMoveEvent(self, event):
        pointf = self.mapToScene(event.pos())
        self.mouseMove.emit(coord.Point(pointf.x(), pointf.y(), "pix"))

    ## mousePressEvent
    #
    # If the left mouse button is pressed then the view is centered on the current cursor position.
    # If the right mouse button is pressed then the current location of the cursor in the scene
    # is recorded. If self.extrapolate_start exists then self.handleExtrapolatePict() is called,
    # otherwise the popup menu is displayed.
    #
    # @param event A PyQt mouse press event.
    #
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))
        elif event.button() == QtCore.Qt.RightButton:
            self.pointf = self.mapToScene(event.pos())
            if self.extrapolate_start:
                self.handleExtrapolatePict()
            else:
                self.popup_menu.exec_(event.globalPos())

    ## setCrosshairPosition
    #
    # @param x_pos The x position of the cross-hair.
    # @param y_pos The y position of the cross-hair.
    #
    def setCrosshairPosition(self, x_pos, y_pos):
        self.cross_hair.setPos(x_pos, y_pos)

    ## showCrosshair
    #
    # @param is_visible True/False to show or hide the current stage position cross-hair.
    #
    def showCrosshair(self, is_visible):
        self.cross_hair.setVisible(is_visible)

    ## wheelEvent
    #
    # Resizes the stage tracking cross-hair based on the current scale.
    #
    # @param event A PyQt mouse wheel event.
    #
    def wheelEvent(self, event):
        multiView.MultifieldView.wheelEvent(self, event)
        self.cross_hair.setScale(self.view_scale)


#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
