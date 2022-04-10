#!/usr/bin/env python
"""
The mosaic QGraphicsView. This is QGraphicsView in the mosaic
UI tab.

Hazen 10/18
Jeff 3/22
"""
import os
from PyQt5 import QtCore, QtGui, QtWidgets

#import storm_control.steve.qtMultifieldView as multiView
import storm_control.steve.coord as coord
import storm_control.steve.steveItems as steveItems


class Crosshair(QtWidgets.QGraphicsItem):
    """
    The cross-hair item to indicate the current stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ch_pen = QtGui.QPen(QtGui.QColor(0,0,255))
        self.ch_size = 15.0
        self.r_size = self.ch_size

        self.ch_pen.setWidth(0)
        self.setZValue(1001.0)

    def boundingRect(self):
        return QtCore.QRectF(-self.r_size,
                              -self.r_size,
                              2.0 * self.r_size,
                              2.0 * self.r_size)

    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.ch_pen)
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


class MosaicView(QtWidgets.QGraphicsView):
    """
    Handles user interaction with the mosaic.

    All coordinates are in pixels.
    """
    extrapolateTakeMovie = QtCore.pyqtSignal(object)
    mosaicViewContextMenuEvent = QtCore.pyqtSignal(object, object)
    mosaicViewDropEvent = QtCore.pyqtSignal(list)
    mosaicViewKeyPressEvent = QtCore.pyqtSignal(object, object)
    mosaicViewKeyReleaseEvent = QtCore.pyqtSignal(object)
    mouseMove = QtCore.pyqtSignal(object)
    scaleChange = QtCore.pyqtSignal(float)
    mosaicViewSelectionChange = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.bg_brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.cross_hair = Crosshair()
        self.currentz = 0.0
        self.extrapolate_start = None
        self.view_scale = 1.0
        self.zoom_in = 1.2
        self.zoom_out = 1.0 / self.zoom_in

        self.showCrossHair(False)
        
        self.setAcceptDrops(True)
        self.setMinimumSize(QtCore.QSize(200, 200))
        self.setBackgroundBrush(self.bg_brush)
        self.setMouseTracking(True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.setInteractive(True)
        self.setRubberBandSelectionMode(QtCore.Qt.IntersectsItemShape)
        self.setToolTip("Hot keys are 'space','3','5','7','9','g','p','s','h','y','n'")

        self.cursor_mode = 'Pointer' # The cursor mode controls how the mouse modifies the view. Possible values are Pointer, Drag, Select

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()            

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            
        # Initialize filenames variable
        filenames = []

        # Tranfer urls to filenames
        for url in event.mimeData().urls():
            filenames.append(str(url.toLocalFile()))

        # Sort file names
        filenames = sorted(filenames)

        # Identify first type
        firstType = os.path.splitext(filenames[0])[1]

        # Check to see if all types are the same
        sameType = []
        for filename in filenames:
            fileType = os.path.splitext(filename)[1]
            sameType.append(fileType == firstType)

        # If not, raise an error and abort load
        if not all(sameType):
            QtGui.QMessageBox.information(self,
                                          "Too many file types",
                                          "")
            return

        self.mosaicViewDropEvent.emit(filenames)
            
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
        'h' Toggle drag mode
        'y' Toggle select mode
        'n' Add current position to the center position for position generation
        """        
        event_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        pointf = self.mapToScene(event_pos)
        a_coord = coord.Point(pointf.x(), pointf.y(), "pix")

        if event.key() == QtCore.Qt.Key_H:
            if not (self.cursor_mode == 'Drag'):
                self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
                self.cursor_mode = 'Drag'
            else:
                self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                self.cursor_mode = 'Pointer'
        elif event.key() == QtCore.Qt.Key_Y:
            if not self.cursor_mode == 'Select':
                self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
                self.cursor_mode = 'Select'
            else:
                self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                self.cursor_mode = 'Pointer'

        self.mosaicViewKeyPressEvent.emit(event, a_coord)

        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Tracks mouse movements across the view.
        """
        pointf = self.mapToScene(event.pos())
        self.mouseMove.emit(coord.Point(pointf.x(), pointf.y(), "pix"))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """
        If the left mouse button is pressed then the view is centered on the current cursor position in Pointer mode, 
        dragged in drag mode, or items are selected in select mode.
        If the right mouse button is pressed then the current location of the cursor in the scene
        is recorded. If self.extrapolate_start exists then self.handleExtrapolatePict() is called,
        otherwise the popup menu is displayed.
        """
        if event.button() == QtCore.Qt.LeftButton:                
            if self.cursor_mode == 'Pointer':
                self.centerOn(self.mapToScene(event.pos()))
            elif self.cursor_mode == 'Drag':
                self.drag_start_pos = self.mapToScene(event.pos())
        elif event.button() == QtCore.Qt.RightButton:
            pointf = self.mapToScene(event.pos())
            a_coord = coord.Point(pointf.x(), pointf.y(), "pix")
            if self.extrapolate_start:
                self.extrapolateTakeMovie.emit(a_coord)
            else:
                self.mosaicViewContextMenuEvent.emit(event, a_coord)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.cursor_mode == 'Select':
                bounding_rect = self.scene().selectionArea().boundingRect()
                selected_items = self.items(self.mapFromScene(bounding_rect))
                self.mosaicViewSelectionChange.emit(selected_items) # Emit the selected items so that steve can pass these back to the positions

    def setCrossHairPosition(self, x_pos_um, y_pos_um):
        x_pos = coord.umToPix(x_pos_um)
        y_pos = coord.umToPix(y_pos_um)
        self.cross_hair.setPos(x_pos, y_pos)

    def setScale(self, scale):
        self.view_scale = scale
        transform = QtGui.QTransform()
        transform.scale(scale, scale)
        self.setTransform(transform)
        self.cross_hair.setScale(scale)

    def setScene(self, scene):
        super().setScene(scene)
        scene.addItem(self.cross_hair)

    def showCrossHair(self, is_visible):
        """
        True/False to show or hide the current stage position cross-hair.
        """
        if (self.cross_hair.isVisible() != is_visible):
            self.cross_hair.setVisible(is_visible)

    def wheelEvent(self, event):
        """
        Resizes the stage tracking cross-hair based on the current scale.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.view_scale = self.view_scale * self.zoom_in
                self.setScale(self.view_scale)
            else:
                self.view_scale = self.view_scale * self.zoom_out
                self.setScale(self.view_scale)
            self.scaleChange.emit(self.view_scale)
            event.accept()
        #multiView.MultifieldView.wheelEvent(self, event)
        #self.cross_hair.setScale(self.view_scale)


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
