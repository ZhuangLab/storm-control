#!/usr/bin/env python
"""
The handles all the UI elements in the Mosaic tab.

Hazen 10/18
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.hdebug as hdebug

import storm_control.steve.qtdesigner.sections_ui as sectionsUi
import storm_control.steve.steveModule as steveModule


class Sections(steveModule.SteveModule):

    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.ui = sectionsUi.Ui_Form()
        self.ui.setupUi(self)
