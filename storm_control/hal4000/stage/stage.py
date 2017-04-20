3#!/usr/bin/env python
"""
The stage GUI.

Hazen 04/17
"""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.stage_ui as stageUi


class MotionButton(QtCore.QObject):
    """
    Encapsulate the handling and display of the motion buttons.
    """
    motionClicked = QtCore.pyqtSignal(float, float)
    
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
        self.motionClicked.emit(self.xval * self.step_size, self.yval * self.step_size)

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
        self.directory = ""
        self.parameters = params.StormXMLObject()
        self.stage_functionality = None

        # Add stage UI parameters.
        self.parameters.add(params.ParameterRangeFloat(description = "Large step size (microns)",
                                                       name = "large_step_size",
                                                       value = 25.0,
                                                       min_value = 1.0,
                                                       max_value = 500.0))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Small step size (microns)",
                                                       name = "small_step_size",
                                                       value = 5.0,
                                                       min_value = 1.0,
                                                       max_value = 50.0))
        
        # UI setup.
        self.ui = stageUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Configure all the stage movement buttons.
        icon_path = os.path.join(os.path.dirname(__file__),"../icons/")
        print(icon_path)
        self.motion_buttons = [MotionButton(button = self.ui.leftSButton,
                                            icon = os.path.join(icon_path, "1leftarrow-128.png"),
                                            button_type = "small",
                                            xval = 1,
                                            yval = 0),
                               MotionButton(button = self.ui.leftLButton,
                                            icon = os.path.join(icon_path, "2leftarrow-128.png"),
                                            button_type = "large",
                                            xval = 1,
                                            yval = 0),
                               MotionButton(button = self.ui.rightSButton,
                                            icon = os.path.join(icon_path, "1rightarrow-128.png"),
                                            button_type = "small",
                                            xval = -1,
                                            yval = 0),
                               MotionButton(button = self.ui.rightLButton,
                                            icon = os.path.join(icon_path, "2rightarrow-128.png"),
                                            button_type = "large",
                                            xval = -1,
                                            yval = 0),
                               MotionButton(button = self.ui.upSButton,
                                            icon = os.path.join(icon_path, "1uparrow-128.png"),
                                            button_type = "small",
                                            xval = 0,
                                            yval = 1),
                               MotionButton(button = self.ui.upLButton,
                                            icon = os.path.join(icon_path, "2uparrow-128.png"),
                                            button_type = "large",
                                            xval = 0,
                                            yval = 1),
                               MotionButton(button = self.ui.downSButton,
                                            icon = os.path.join(icon_path, "1downarrow1-128.png"),
                                            button_type = "small",
                                            xval = 0,
                                            yval = -1),
                               MotionButton(button = self.ui.downLButton,
                                            icon = os.path.join(icon_path, "2dowarrow-128.png"),
                                            button_type = "large",
                                            xval = 0,
                                            yval = -1)]
        for button in self.motion_buttons:
            button.motionClicked.connect(self.handleMotionClicked)

        self.newParameters(self.parameters)
        
        # Disable UI until we get a stage functionality.
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters
        
    def handleMotionClicked(self, dx, dy):
        self.stage_functionality.goRelative(dx, dy)
        
    def handleStagePosition(self, stage_x, stage_y, stage_z):
        self.ui.xposText.setText("{0:.3f}".format(stage_x))
        self.ui.yposText.setText("{0:.3f}".format(stage_y))

    def newParameters(self, parameters):
        small_step = parameters.get("small_step_size")
        large_step = parameters.get("large_step_size")
        self.parameters.setv("small_step_size", small_step)
        self.parameters.setv("large_step_size", large_step)
        for button in self.motion_buttons:
            button.setStepSize(small_step, large_step)

    def setDirectory(self, directory):
        self.directory = directory
        
    def setStageFunctionality(self, stage_functionality):
        self.stage_functionality = stage_functionality
        self.stage_functionality.stagePosition.connect(self.handleStagePosition)
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

        elif message.isType("new directory"):
            self.view.setDirectory(message.getData()["directory"])
            
        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))
            
        elif message.isType("show stage"):
            self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()            
