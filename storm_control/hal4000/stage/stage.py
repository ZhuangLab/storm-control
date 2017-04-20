3#!/usr/bin/env python
"""
The stage GUI.

Hazen 04/17
"""

from PyQt5 import QtCore, QtWidgets

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.stage_ui as stageUi


class MotionButton(QtCore.QObject):
    """
    Encapsulate the handling and display of the motion buttons.
    """
    buttonClicked = QtCore.pyqtSignal(float, float)
    
    def __init__(self,
                 button = None,
                 icon = None,
                 button_type = None,
                 xval = None,
                 yval = None,
                 **kwds):
        super().__init__(**kwds)

        self.step_size = 1.0
        self.button_type = button_type
        self.xval = float(xval)
        self.yval = float(yval)

        self.button = button
        self.button.setIcon(QtGui.QIcon(icon))
        self.button.setIconSize(QtCore.QSize(56, 56))
        self.button.clicked.connect(self.handleClicked)

    def handleClicked(self, boolean):
        self.buttonClicked.emit(self.xval * self.step_size, self.yval * self.step_size)

    def setStepSize(self, small_step_size, large_step_size):
        if (self.button_type == "small"):
            self.step_size = small_step_size
        else:
            self.step_size = large_step_size
            

class StageView(halDialog.HalDialog):
    """
    Manages the stage GUI.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.stage_functionality = None

        # UI setup.
        self.ui = stageUi.Ui_Dialog()
        self.ui.setupUi(self)

        #
        
        # Disable UI until we get a stage functionality.
        self.setEnabled(False)
        
    def setStageFunctionality(self, stage_functionality):
        self.stage_functionality = stage_functionality
        self.setEnabled(True)

    def show(self):
        super().show()
        self.setFixedSize(self.width(), self.height())


class Stage(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.stage_fn_name = module_params.get("configuration.stage_functionality")
        
        self.view = StageView(module_name = self.module_name)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " stage control")

        # Unhide stage control.
        halMessage.addMessage("show stage",
                              validator = {"data" : None, "resp" : None})
        
    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setStageFunctionality(response.getData()["functionality"])
            
    def processMessage(self, message):
            
        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Stage",
                                                           "item msg" : "show stage"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.stage_fn_name}))

        elif message.isType("show stage"):
            self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()            
