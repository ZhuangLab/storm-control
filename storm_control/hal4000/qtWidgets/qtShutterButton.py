#!/usr/bin/env python
"""
QPushButton specialized to be a shutter button.

Hazen 4/17
"""

from PyQt5 import QtWidgets


class QtShutterButton(QtWidgets.QPushButton):

    def setShutter(self, state):
        if state:
            self.setText("Close Shutter")
            self.setStyleSheet("QPushButton { color: green }")
        else:
            self.setText("Open Shutter")
            self.setStyleSheet("QPushButton { color: black }")    

    def startFilm(self):
        self.setEnabled(False)

    def stopFilm(self):
        self.setEnabled(True)

        
