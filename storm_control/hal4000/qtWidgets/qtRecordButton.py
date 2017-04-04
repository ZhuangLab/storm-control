#!/usr/bin/env python
"""
QPushButton specialized to be a record button.

Hazen 4/17
"""

from PyQt5 import QtWidgets

import storm_control.hal4000.film.filmRequest as filmRequest
import storm_control.hal4000.halLib.halMessage as halMessage


class QtRecordButton(QtWidgets.QPushButton):

    def __init__(self, parent = None, **kwds):
        kwds["parent"] = parent
        super().__init__(**kwds)
        self.filming = False

    def getHalMessage(self):
        if self.filming:
            return halMessage.HalMessage(source = self,
                                         m_type = "stop film request")
        else:
            return halMessage.HalMessage(source = self,
                                         m_type = "start film request",
                                         data = {"request" : filmRequest.FilmRequest()})

    def startFilm(self, film_settings):
        self.setText("Stop")
        self.setEnabled(not film_settings.isTCPRequest())
        if film_settings.isSaved():
            self.setStyleSheet("QPushButton { color: red }")
        else:
            self.setStyleSheet("QPushButton { color: orange }")
        self.filming = True

    def stopFilm(self):
        self.setEnabled(True)
        self.setText("Record")
        self.setStyleSheet("QPushButton { color: black }")
        self.filming = False
