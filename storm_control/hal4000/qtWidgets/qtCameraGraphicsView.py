#!/usr/bin/env python
"""
QGraphicsView customized for displaying camera images.

Hazen 3/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class QtCameraGraphicsView(QtWidgets.QGraphicsView):

    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)

        self.frame_size = 0
        self.max_scale = 2.0
        self.min_scale = 0.5
        
        self.view_scale = 1.0
        self.zoom_in = 1.2
        self.zoom_out = 1.0 / self.zoom_in

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))

    def newConfiguration(self, feed_info):
        """
        This is called when the camera or frame size might change.
        """
        # Figure out the maximum dimension of the frame.
        self.frame_size = feed_info.getParameter("x_pixels")
        if (self.frame_size < feed_info.getParameter("y_pixels")):
            self.frame_size = feed_info.getParameter("y_pixels")

        # Calculate new scales.
        self.updateScaleRange()

        # Change the scale, which we maybe don't want to do.
        self.rescale(self.min_scale)

    def resizeEvent(self, event):
        self.updateScaleRange()
        super().resizeEvent(event)
        
    def rescale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """
        if (scale < self.min_scale) or (scale > self.max_scale):
            return
            
        self.view_scale = scale
        transform = QtGui.QTransform()
        transform.scale(scale, scale)
        self.setTransform(transform)
        
    def updateScaleRange(self):
        """
        Given the view and camera size, this figures 
        out the range of scales to allow.
        """
        
        # Figure out the minimum dimension of the viewport.
        viewport_rect = self.viewport().contentsRect()
        viewport_size = viewport_rect.width()
        if (viewport_size > viewport_rect.height()):
            viewport_size = viewport_rect.height()

        # This sets how far we can zoom out (and also the starting size).
        self.min_scale = float(viewport_size)/float(self.frame_size + 10)

        # This sets how far we can zoom in (~32 pixels).
        self.max_scale = float(viewport_size)/32.0

        # For those really small cameras.
        if (self.max_scale < self.min_scale):
            self.max_scale = 2.0 * self.min_scale

        if (self.view_scale < self.min_scale):
            self.view_scale = self.min_scale

        if (self.view_scale > self.max_scale):
            self.view_scale = self.max_scale

        print(self.frame_size, viewport_size, self.min_scale, self.max_scale)

    def wheelEvent(self, event):
        """
        Zoom in/out with the mouse wheel.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.rescale(self.view_scale * self.zoom_in)
            else:
                self.rescale(self.view_scale * self.zoom_out)
            event.accept()
