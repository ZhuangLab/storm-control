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

Hazen 03/17
"""
import os

from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
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
        # They should be initialized since this what we are starting with..
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
        #
        # Data includes a copy of the desired new parameters. Other modules
        # should at least check if the new parameters are okay. They may
        # defer actually re-configuring until they receive the
        # 'updated parameters' message.
        #
        # Other modules that respond should send two response:
        #  1. A response with a copy of their old parameter as "old parameters".
        #  2. A response with their updated parameters as "new parameters".
        #
        # The response is structured this way so that if an error occurs
        # during the parameter update we still have a record of the last
        # good state in "old parameters".
        #
        halMessage.addMessage("new parameters",
                              validator = {"data" : {"parameters" : [True, params.StormXMLObject],
                                                     "is_edit" : [True, bool]},
                                           "resp" : {"new parameters" : [False, params.StormXMLObject],
                                                     "old parameters" : [False, params.StormXMLObject]}})

        # The updated parameters.
        #
        # These are the updated values of parameters of all of the modules.
        # This is sent immediately after all of the modules respond to
        # the 'new parameters' message.
        #
        halMessage.addMessage("updated parameters",
                              validator = {"data" : {"parameters" : [True, params.StormXMLObject]},
                                           "resp" : None})

    def handleError(self, message, m_error):

        # We can hopefully handle all 'new parameters' errors by reverting
        # to the previous good parameters. The actual reversion happens in
        # handleResponses.
        if message.isType("new parameters"):
            return True

    def handleNewParameters(self, parameters, is_edit):
        """
        Sends the 'new parameters' message. 

        The updated parameters could be a modified form of the current parameters or
        it could be a different set. We use the is_edit flag to record which of these
        two it is.
        """
        # Disable the UI so the user can't change the parameters again while we
        # are processing the current change.
        self.view.enableUI(False)
        
        # is_edit means we are sending a modified version of the current parameters.
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "new parameters",
                                                   data = {"parameters" : parameters.copy(),
                                                           "is_edit" : is_edit}))

    def handleResponses(self, message):
        
        if message.isType("new parameters"):

            # Check if we got any errors.
            if message.hasErrors():
                
                # Create a message box with the first error.
                msg = "New Parameters:\n\n"
                for m_error in message.getErrors():
                    msg += "Got an error from '" + m_error.source + "' of type '" + m_error.message + "'!\n\n"
                msg += "Attempting to revert to the last known good parameters."
                halMessageBox.halMessageBoxInfo(msg)

                # Attempt reversion.

                # Replace the 'bad' parameters with their previous 'good' values.
                if message.getData()["is_edit"]:
                    for response in message.getResponses():
                        data = response.getData()
                        if "old parameters" in data:
                            self.view.updateCurrentParameters(response.source, data["old parameters"])
                    self.handleNewParameters(self.view.getCurrentParameters(), True)
                            
                # Otherwise set the current selection back to previous selection.
                # This will automatically send a 'new parameters' message.
                else:
                    self.view.revertSelection()
                
            else:
                # If this is in response to a 'new parameters' message triggered by
                # the editor then we don't want to update the previous parameters.
                if not ("is_edit" in message.getData()):
                    for response in message.getResponses():
                        data = response.getData()
                        if "old parameters" in data:
                            self.view.updatePreviousParameters(response.source, data["old parameters"])

                for response in message.getResponses():
                    data = response.getData()
                    if "new parameters" in data:
                        self.view.updateCurrentParameters(response.source, data["new parameters"].copy())

                # Mark the new parameters as initialized.
                self.view.markCurrentAsInitialized()
                    
                # Let modules, such as feeds.feeds known that all of the modules
                # have updated their parameters.
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "updated parameters",
                                                           data = {"parameters" : self.view.getCurrentParameters().copy()}))

                # Renable the UI
                self.view.enableUI(True)

    def processL1Message(self, message):
        
        if message.isType("configure1"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to ui",
                                                       data = self.configure_dict))

        elif message.isType("configure2"):
            self.view.copyDefaultParameters()
            
        elif message.isType("initial parameters"):
            #
            # It is okay for other modules to just send their parameters as we make
            # a copy before storing them in this module.
            #
            self.view.updateCurrentParameters(message.getSourceName(),
                                              message.getData()["parameters"].copy())

        elif message.isType("get parameters"):
            p = self.view.getParameters(message.getData()["index_or_name"])
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : p}))
            
        elif message.isType("new parameters file"):

            # Ignore this message if the UI is disabled and send a warning.
            if not self.view.getEnabled():
                msg = "Parameters files cannot be added during editting / filming" 
                message.addError(halMessage.HalMessageError(source = self.module_name,
                                                            message = msg))
                return
            
            data = message.getData()

            # Check if these parameters should be default parameters. For now
            # anyway this should only be possible at initialization.
            is_default = False
            if "is_default" in data:
                is_default = data["is_default"]

            # Process new parameters file.
            self.view.newParametersFile(data["filename"], is_default)

        elif message.isType("start film"):
            self.view.enableUI(False)
            
        elif message.isType("stop film"):
            self.view.enableUI(True)




