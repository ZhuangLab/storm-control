#!/usr/bin/env python
"""
QPushButton specialized to be a record button.

Hazen 4/17
"""

from PyQt5 import QtWidgets


class QtRecordButton(QtWidgets.QPushButton):

    def startFilm(self, film_settings):
        self.setText("Stop")
        if film_settings["save_film"]:
            self.setStyleSheet("QPushButton { color: red }")
        else:
            self.setStyleSheet("QPushButton { color: orange }")

    def stopFilm(self):
        self.setText("Record")
        self.setStyleSheet("QPushButton { color: black }")
