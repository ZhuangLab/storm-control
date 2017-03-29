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

        self.view_scale = 1.0
        self.zoom_in = 1.2
        self.zoom_out = 1.0 / self.zoom_in

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))

    def handleRectChanged(self, rect):
        print(rect)
        
    def setScale(self, scale):
        """
        Rescale the view so that it looks like we have zoomed in/out.
        """        
        self.view_scale = scale
        transform = QtGui.QTransform()
        transform.scale(scale, scale)
        self.setTransform(transform)
        
    def wheelEvent(self, event):
        """
        Zoom in/out with the mouse wheel.
        """
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.view_scale = self.view_scale * self.zoom_in
                self.setScale(self.view_scale)
            else:
                self.view_scale = self.view_scale * self.zoom_out
                self.setScale(self.view_scale)
            event.accept()
