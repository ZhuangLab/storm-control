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

Note this module makes a copy of any parameters it receives
before storing. Similarly it only broadcasts a copy of the
parameters that it has stored.

Hazen 03/17
"""
import os

from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.settings.parametersBox as parametersBox


class Settings(halModule.HalModule):
    
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.view = parametersBox.ParametersBox()
        self.view.newParameters.connect(self.handleNewParameters)

        p = params.StormXMLObject()
        p.set("parameters_file", os.path.join(module_params.get("directory"), "default.xml"))
        
        #
        # Add parameter to record whether or not these parameters have actually
        # been used (as opposed to just appearing in the list view).
        #
        p.add(params.ParameterSetBoolean(name = "initialized",
                                         value = False,
                                         is_mutable = False,
                                         is_saved = False))

        self.view.addParameters(p, is_default = True)

        self.configure_dict = {"ui_order" : 0,
                               "ui_parent" : "hal.containerWidget",
                               "ui_widget" : self.view}

        # The current parameters have changed.
        halMessage.addMessage("new parameters")

    def handleError(self, message, m_error):
        print("setting error handler")
        if (message.getType() == "new parameters"):
            print("Errors in the default parameters are not handled.")
            return False
        return False
        
    def handleNewParameters(self, parameters, is_edit):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "new parameters",
                                                   data = {"parameters" : parameters,
                                                           "is_edit" : is_edit}))

    def handleResponses(self, message):
        if (message.getType() == "new parameters"):

            # If this is in response to a 'new parameters' message triggered by
            # the editor then we don't want to update the previous parameters.
            if not ("is_edit" in message.getData()):
                for response in message.getResponses():
                    data = response.getData()
                    self.view.updatePreviousParameters(response.source, data["parameters"].copy())

    def processL1Message(self, message):
        
        if (message.m_type == "configure1"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to ui",
                                                       data = self.configure_dict))

        elif (message.getType() == "current parameters"):
            self.view.updateCurrentParameters(message.getSourceName(),
                                              message.getData()["parameters"].copy())

        elif (message.getType() == "new parameters file"):
            data = message.getData()

            #
            # Check if these parameters should be default parameters. For now
            # anyway this should only be possible at initialization.
            #
            is_default = False
            if "is_default" in data:
                is_default = data["is_default"]
            self.view.newParametersFile(data["filename"], is_default)
                                        


#        elif (message.getType() == 'start'):
#            self.view.addParameters("default", self.default_parameters)
#            self.current_parameters = self.


