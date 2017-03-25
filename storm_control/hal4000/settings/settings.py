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

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.settings.parametersBox as parametersBox


class Settings(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.current_parameters = None
        self.default_parameters = params.StormXMLObject()

        self.view = parametersBox.ParametersBox()

        self.configure_dict = {"ui_order" : 0,
                               "ui_parent" : "hal.containerWidget",
                               "ui_widget" : self.view}
        
    def processL1Message(self, message):
        
        if (message.m_type == "configure1"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to ui",
                                                       data = self.configure_dict))

        elif (message.getType() == "current parameters"):                
            section = message.getSourceName()

            # The display module handles all the displays, so figure
            # out which display these are the parameters for.
            if (section == "display"):
                section = message.getData()["display_name"]
                    
            parameters = message.getData()["parameters"]
                
            #
            # If we don't have default parameters then we must be in start-up and
            # the parameters that we get from the modules will be the defaults.
            #
            if (self.default_parameters == None):
                self.default_parameters.addSubSection(section,
                                                      parameters)

            #
            # Otherwise update current parameters with parameters from the module.
            #
            else:
                print("s", section)

        elif (message.getType() == 'start'):
            self.view.addParameters("default", self.default_parameters)


