#!/usr/bin/env python
"""
QGraphicsView customized for displaying camera images.

Hazen 3/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class QtCameraGraphicsView(QtWidgets.QGraphicsView):
    """
    This is responsible for handling the camera transforms
    (flip_horizontal, flip_vertical, transpose). Hopefully
    this makes rendering a lot simpler for us as we don't 
    have keep track of all these details.
    """
    dragMove = QtCore.pyqtSignal(int, int)
    dragStart = QtCore.pyqtSignal()
    newCenter = QtCore.pyqtSignal(int, int)
    newScale = QtCore.pyqtSignal(int)
    
    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.can_drag = False
        self.chip_max = 100
        self.center_x = 0
        self.center_y = 0
        self.ctrl_key_down = False
        self.display_scale = 0
        self.drag_mode = False
        self.drag_scale = 1.0
        self.drag_x = 0
        self.drag_y = 0
        self.frame_size = 0
        self.max_scale = 8
        self.min_scale = -8
        self.transform = QtGui.QTransform()
        self.viewport_min = 100

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

    def calcScale(self, size):
        if (size < self.viewport_min):
            return int(self.viewport_min/size) -1
        else:
            return -int(size/self.viewport_min)

    def enableStageDrag(self, enabled):
        self.can_drag = enabled

    def getCurrentCenter(self):
        center = self.mapToScene(self.viewport().rect().center())
        self.center_x = center.x()
        self.center_y = center.y()
        self.newCenter.emit(self.center_x, self.center_y)
        
    def keyPressEvent(self, event):
        if self.can_drag and (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = True
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def keyReleaseEvent(self, event):
        if self.can_drag and (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = False
            self.drag_mode = False
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def mouseMoveEvent(self, event):
        if self.drag_mode:
            dx = (event.x() - self.drag_x) * self.drag_scale
            dy = (event.y() - self.drag_y) * self.drag_scale            
            self.dragMove.emit(dx, dy)
        else:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.center_x = pos.x()
        self.center_y = pos.y()
        self.newCenter.emit(self.center_x, self.center_y)
        self.centerOn(self.center_x, self.center_y)

        if self.ctrl_key_down:
            self.drag_mode = True
            self.drag_x = event.x()
            self.drag_y = event.y()
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
            self.dragStart.emit()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_mode:
            self.drag_mode = False
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
        else:
            super().mouseReleaseEvent(event)

    def newConfiguration(self, camera_functionality, feed_parameters):
        """
        This is called when the camera or frame size may have changed.
        """
        self.chip_max = camera_functionality.getChipMax()

        # Calculate transform matrix.
        [cx, cy] = camera_functionality.getChipSize()

        if camera_functionality.getParameter("flip_horizontal"):
            flip_lr = QtGui.QTransform(-1.0, 0.0, 0.0,
                                       0.0, 1.0, 0.0,
                                       cx, 0.0, 1.0)
        else:
            flip_lr = QtGui.QTransform()

        if camera_functionality.getParameter("flip_vertical"):
            flip_ud = QtGui.QTransform(1.0, 0.0, 0.0,
                                       0.0, -1.0, 0.0,
                                       0.0, cy, 1.0)
        else:
            flip_ud = QtGui.QTransform()

        if camera_functionality.getParameter("transpose"):
            flip_xy = QtGui.QTransform(0.0, 1.0, 0.0,
                                       1.0, 0.0, 0.0,
                                       0.0, 0.0, 1.0)
        else:
            flip_xy = QtGui.QTransform()            

        self.transform = flip_lr * flip_ud * flip_xy
        self.setTransform(self.transform)

        # Calculate initial zoom and center position.
        if feed_parameters.get("initialized"):
            self.display_scale = feed_parameters.get("scale")
            self.center_x = feed_parameters.get("center_x")
            self.center_y = feed_parameters.get("center_y")
        else:
            self.display_scale = self.calcScale(camera_functionality.getFrameMax())
            [self.center_x, self.center_y] = camera_functionality.getFrameCenter()
            self.newCenter.emit(self.center_x, self.center_y)
            feed_parameters.set("initialized", True)

        # Calculate max zoom out.
        self.min_scale = self.calcScale(self.chip_max)

        #
        # Among other possible issues, this solves the problem that at startup
        # self.display_scale will get set to the wrong value this GraphicsView
        # will not have the correct size the first time we come through this
        # method, then on the second pass initialized will be set and we'll
        # locked in on a self.display_scale value that is out of range and cannot
        # be changed using the scroll wheel.
        #
        if (self.display_scale < self.min_scale):
            self.display_scale = self.min_scale

        self.rescale(self.display_scale)

    def resizeEvent(self, event):
        #
        # Use the GraphicsView contentsRect size and not it's viewport
        # contentsRect size because depending on the zoom scroll bars
        # will appear and disappear throwing off the calculation.
        #
        #viewport_rect = self.viewport().contentsRect()
        viewport_rect = self.contentsRect()
        self.viewport_min = viewport_rect.width() if (viewport_rect.width() < viewport_rect.height())\
                            else viewport_rect.height()

        self.min_scale = self.calcScale(self.chip_max)
        if (self.display_scale < self.min_scale):
            self.display_scale = self.min_scale
        
        super().resizeEvent(event)
        
    def rescale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """
        if (scale < self.min_scale) or (scale > self.max_scale):
            return

        self.display_scale = scale
        self.newScale.emit(self.display_scale)

        if (self.display_scale == 0):
            flt_scale = 1.0
        elif (self.display_scale > 0):
            flt_scale = float(self.display_scale + 1)
        else:
            flt_scale = 1.0/(-self.display_scale + 1)

        self.drag_scale = 1.0/flt_scale
        transform = QtGui.QTransform()
        transform.scale(flt_scale, flt_scale)
        self.setTransform(self.transform * transform)
        self.centerOn(self.center_x, self.center_y)

    def wheelEvent(self, event):
        """
        Zoom in/out with the mouse wheel.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.rescale(self.display_scale + 1)
            else:
                self.rescale(self.display_scale - 1)
            event.accept()
