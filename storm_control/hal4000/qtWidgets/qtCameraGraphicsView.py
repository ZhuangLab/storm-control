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
    newCenter = QtCore.pyqtSignal(int, int)
    newScale = QtCore.pyqtSignal(int)
    
    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.chip_max = 0
        self.center_x = 0
        self.center_y = 0
        self.ctrl_key_down = False
        self.frame_size = 0
        self.max_scale = 8
        self.min_scale = -8
        self.scale = 0
        self.transform = QtGui.QTransform()
        self.viewport_min = 100

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = True
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.ctrl_key_down = False
            if not self.drag_mode:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.center_x = pos.x()
        self.center_y = pos.y()
        self.newCenter.emit(self.center_x, self.center_y)
        self.centerOn(self.center_x, self.center_y)
        
    def newConfiguration(self, feed_info, feed_parameters):
        """
        This is called when the camera or frame size may have changed.
        """
        self.chip_max = feed_info.getChipMax()

        # Calculate transform matrix.
        [cx, cy] = feed_info.getChipSize()

        if feed_info.getParameter("flip_horizontal"):
            flip_lr = QtGui.QTransform(-1.0, 0.0, 0.0,
                                       0.0, 1.0, 0.0,
                                       cx, 0.0, 1.0)
        else:
            flip_lr = QtGui.QTransform()

        if feed_info.getParameter("flip_vertical"):
            flip_ud = QtGui.QTransform(1.0, 0.0, 0.0,
                                       0.0, -1.0, 0.0,
                                       0.0, cy, 1.0)
        else:
            flip_ud = QtGui.QTransform()

        if feed_info.getParameter("transpose"):
            flip_xy = QtGui.QTransform(0.0, 1.0, 0.0,
                                       1.0, 0.0, 0.0,
                                       0.0, 0.0, 1.0)
        else:
            flip_xy = QtGui.QTransform()            

        self.transform = flip_lr * flip_ud * flip_xy
        self.setTransform(self.transform)

        # Calculate max zoom out.
        self.min_scale = -int(self.chip_max/self.viewport_min) - 1

        # Calculate initial zoom and center position.
        if feed_parameters.get("initialized"):
            self.scale = feed_parameters.get("scale")
            self.center_x = feed_parameters.get("center_x")
            self.center_y = feed_parameters.get("center_y")
        else:
            if (feed_info.getFrameMax() < self.viewport_min):
                self.scale = int(self.viewport_min/feed_info.getFrameMax()) - 1
            else:
                self.scale = -int(feed_info.getFrameMax()/self.viewport_min)

            [self.center_x, self.center_y] = feed_info.getFrameCenter()
            feed_parameters.set("initialized", True)

        self.centerOn(self.center_x, self.center_y)
        self.rescale(self.scale)

    def resizeEvent(self, event):
        viewport_rect = self.viewport().contentsRect()
        self.viewport_min = viewport_rect.width() if (viewport_rect.width() < viewport_rect.height())\
                            else viewport_rect.height()

        self.min_scale = -int(self.chip_max/self.viewport_min) - 1
        if (self.scale < self.min_scale):
            self.scale = self.min_scale
        
        super().resizeEvent(event)
        
    def rescale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """
        if (scale <= self.min_scale) or (scale >= self.max_scale):
            print("scale out of range", scale, self.min_scale, self.max_scale)
            return

        self.scale = scale
        self.newScale.emit(self.scale)

        if (self.scale == 0):
            flt_scale = 1.0
        elif (self.scale > 0):
            flt_scale = float(self.scale + 1)
        else:
            flt_scale = 1.0/(-self.scale + 1)
            
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
                self.rescale(self.scale + 1)
            else:
                self.rescale(self.scale - 1)
            event.accept()
