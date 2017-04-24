#!/usr/bin/env python
"""
focus lock.

Hazen 04/17
"""

from PyQt5 import QtCore, QtWidgets

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.focusLock.lockDisplay as lockDisplay

# UI.
import storm_control.hal4000.qtdesigner.focuslock_ui as focuslockUi


class FocusLockView(halDialog.HalDialog):
    """
    Manages the focus lock GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)

        self.ui = focuslockUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Set up lock display.
        self.lock_display = lockDisplay.LockDisplay(configuration = configuration,
                                                    parent = self)
        layout = QtWidgets.QGridLayout(self.ui.lockDisplayWidget)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.lock_display)

    def setFunctionality(self, name, functionality):
        self.lock_display.setFunctionality(name, functionality)

    def show(self):
        super().show()
        self.setFixedSize(self.width(), self.height())
        
        
class FocusLock(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = FocusLockView(module_name = self.module_name,
                                  configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " focus lock")

        # Unhide focus lock control.
        halMessage.addMessage("show focus lock",
                              validator = {"data" : None, "resp" : None})

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(message.getData()["extra data"],
                                       response.getData()["functionality"])
            
    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Focus Lock",
                                                           "item msg" : "show focus lock"}))

            # Get functionalities.
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("ir_laser"),
                                                           "extra data" : "ir_laser"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("qpd"),
                                                           "extra data" : "qpd"}))
            
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("z_stage"),
                                                           "extra data" : "z_stage"}))

        elif message.isType("show focus lock"):
            self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()            
