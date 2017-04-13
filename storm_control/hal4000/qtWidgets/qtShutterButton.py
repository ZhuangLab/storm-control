#!/usr/bin/env python
"""
QPushButton specialized to be a shutter button.

Hazen 4/17
"""

from PyQt5 import QtWidgets


class QtShutterButton(QtWidgets.QPushButton):

    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)
        self.cam_fn = None
        self.clicked.connect(self.handleClick)

    def handleClick(self):
        if self.cam_fn is not None:
            self.cam_fn.toggleShutter()
        
    def handleShutter(self, state):
        if state:
            self.setText("Close Shutter")
            self.setStyleSheet("QPushButton { color: green }")
        else:
            self.setText("Open Shutter")
            self.setStyleSheet("QPushButton { color: black }")    

    def setCameraFunctionality(self, camera_functionality):
        if self.cam_fn is not None:
            self.cam_fn.shutter.disconnect(self.handleShutter)
        self.cam_fn = camera_functionality
        self.cam_fn.shutter.connect(self.handleShutter)
        self.setVisible(self.cam_fn.hasShutter())
        
    def startFilm(self):
        self.setEnabled(False)

    def stopFilm(self):
        self.setEnabled(True)

        
