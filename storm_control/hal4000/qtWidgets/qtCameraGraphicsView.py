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

        # Prefix everything is prefixed with hal_ here to try
        # not to collide with Qt class attributes.
        self.hal_chip_max = 0
        self.hal_center_x = 0
        self.hal_center_y = 0
        self.hal_ctrl_key_down = False
        self.hal_display_scale = 0
        self.hal_drag_mode = False
        self.hal_frame_size = 0
        self.hal_max_scale = 8
        self.hal_min_scale = -8
        self.hal_scale = 0
        self.hal_transform = QtGui.QTransform()
        self.hal_viewport_min = 100

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))

    def calcScale(self, size):
        if (size < self.hal_viewport_min):
            return int(self.hal_viewport_min/size) -1
        else:
            return -int(size/self.hal_viewport_min)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.hal_ctrl_key_down = True
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Control):
            self.hal_ctrl_key_down = False
            if not self.hal_drag_mode:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.hal_center_x = pos.x()
        self.hal_center_y = pos.y()
        self.newCenter.emit(self.hal_center_x, self.hal_center_y)
        self.centerOn(self.hal_center_x, self.hal_center_y)
        
    def newConfiguration(self, feed_info, feed_parameters):
        """
        This is called when the camera or frame size may have changed.
        """
        self.hal_chip_max = feed_info.getChipMax()

        print(">nc", self.hal_scale, feed_parameters.get("initialized"))
        
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

        self.hal_transform = flip_lr * flip_ud * flip_xy
        self.setTransform(self.hal_transform)

        # Calculate initial zoom and center position.
        if feed_parameters.get("initialized"):
            self.hal_scale = feed_parameters.get("scale")
            self.hal_center_x = feed_parameters.get("center_x")
            self.hal_center_y = feed_parameters.get("center_y")
        else:
            self.hal_scale = self.calcScale(feed_info.getFrameMax())
            [self.hal_center_x, self.hal_center_y] = feed_info.getFrameCenter()
            feed_parameters.set("initialized", True)

        # Calculate max zoom out.
        self.hal_min_scale = self.calcScale(self.hal_chip_max)

        #
        # Among other possible issues, this solves the problem that at startup
        # self.scale will get set to the wrong value this GraphicsView will
        # not have the correct size the first time we come through this method,
        # then on the second pass initialized will be set and we'll locked in
        # on a self.scale value that is out of range and cannot be changed
        # using the scroll wheel.
        #
        if (self.hal_scale < self.hal_min_scale):
            self.hal_scale = self.hal_min_scale
    
        self.centerOn(self.hal_center_x, self.hal_center_y)
        self.rescale(self.hal_scale)

    def resizeEvent(self, event):
        print(">resize")
        viewport_rect = self.viewport().contentsRect()
        self.hal_viewport_min = viewport_rect.width() if (viewport_rect.width() < viewport_rect.height())\
                            else viewport_rect.height()

        self.hal_min_scale = self.calcScale(self.hal_chip_max)
        if (self.hal_scale < self.hal_min_scale):
            self.hal_scale = self.hal_min_scale
        
        super().resizeEvent(event)
        
    def rescale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """
        if (scale < self.hal_min_scale) or (scale > self.hal_max_scale):
            print("scale out of range", scale, self.hal_min_scale, self.hal_max_scale)
            return

        self.hal_scale = scale
        print(">rs emit")
        self.newScale.emit(self.hal_scale)

        if (self.hal_scale == 0):
            flt_scale = 1.0
        elif (self.hal_scale > 0):
            flt_scale = float(self.hal_scale + 1)
        else:
            flt_scale = 1.0/(-self.hal_scale + 1)
            
        transform = QtGui.QTransform()
        transform.scale(flt_scale, flt_scale)
        self.setTransform(self.hal_transform * transform)
        self.centerOn(self.hal_center_x, self.hal_center_y)

    def wheelEvent(self, event):
        """
        Zoom in/out with the mouse wheel.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.rescale(self.hal_scale + 1)
            else:
                self.rescale(self.hal_scale - 1)
            event.accept()
