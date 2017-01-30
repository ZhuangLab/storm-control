#!/usr/bin/env python
"""

Handles mosaic related functionality.

This module is responsible for keeping track of the current
objective.

Hazen 01/17
"""

from PyQt5 import QtWidgets

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtdesigner.mosaic_ui as mosaicUi


class MosaicBox(QtWidgets.QGroupBox):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ui = mosaicUi.Ui_GroupBox()
        self.ui.setupUi(self)
        
    
class Mosaic(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.ui_parent = module_params.get("ui_parent")

        self.view = MosaicBox()

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            if (message.m_type == "configure"):
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = {"ui_parent" : self.ui_parent,
                                                                   "ui_widget" : self.view}))

