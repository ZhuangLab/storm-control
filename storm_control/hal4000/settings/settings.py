#!/usr/bin/env python
"""

Handles all interaction / communication with the parameters widget.

This widget is responsible for keeping track of the various
different parameter files that the user has loaded as well as
editting and saving these parameters.

Unlike in Python2/PyQt4 HAL there is no longer a single current 
parameter object that is shared across all the modules.

The 'parameters of record' are those that are stored by each
module, though they are expected to match this modules
parameters.

Hazen 01/17
"""

from PyQt5 import QtWidgets

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.settings.parametersBox as parametersBox


class Settings(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.view = parametersBox.ParametersBox()

        self.configure_dict = {"ui_order" : module_params.get("ui_order"),
                               "ui_parent" : module_params.get("ui_parent"),
                               "ui_widget" : self.view}
        
    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            if (message.m_type == "configure"):
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = self.configure_dict))

