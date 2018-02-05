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
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
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

    The stage orientation settings have been dropped in this version of
    HAL, at least until we remember why we thought they were useful.
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

        # Connect the rest of the UI elements.
        self.ui.addButton.clicked.connect(self.handleAddButton)
        self.ui.clearButton.clicked.connect(self.handleClearButton)
        self.ui.goButton.clicked.connect(self.handleGoButton)
        self.ui.homeButton.clicked.connect(self.handleHomeButton)
        self.ui.loadButton.clicked.connect(self.handleLoadButton)
        self.ui.saveButton.clicked.connect(self.handleSaveButton)
        self.ui.saveComboBox.activated.connect(self.handleSaveComboBox)
        self.ui.zeroButton.clicked.connect(self.handleZeroButton)

        self.newParameters(self.parameters)
        
        # Disable UI until we get a stage functionality.
        self.setEnabled(False)


    def getParameters(self):
        return self.parameters

    def handleAddButton(self, boolean):
        [x, y, z] = self.stage_functionality.getCurrentPosition()
        self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(x, y), [x, y])
        self.ui.saveComboBox.setCurrentIndex(self.ui.saveComboBox.count()-1)

    def handleClearButton(self, boolean):
        self.ui.saveComboBox.clear()

    def handleGoButton(self, boolean):
        self.stage_functionality.goAbsolute(self.ui.xmoveDoubleSpinBox.value(),
                                            self.ui.ymoveDoubleSpinBox.value())

    def handleHomeButton(self, boolean):
        self.stage_functionality.goAbsolute(0, 0)

    def handleLoadButton(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.directory,
                                                                   "*.txt")[0]
        if positions_filename:
            self.ui.saveComboBox.clear()
            with open(positions_filename, "r") as fp:
                for line in fp:
                    [x, y] = map(float, line.split(","))
                    self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(x, y),
                                                 [x, y])
            self.ui.saveComboBox.setCurrentIndex(self.ui.saveComboBox.count()-1)
        
    def handleMotionClicked(self, dx, dy):
        self.stage_functionality.goRelative(dx, dy)

    def handleSaveButton(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.directory, 
                                                                   "*.txt")[0]
        if positions_filename and (self.ui.saveComboBox.count() > 0):
            with open(positions_filename, "w") as fp:
                for i in range(self.ui.saveComboBox.count()):
                    [x, y] = self.ui.saveComboBox.itemData(i)
                    fp.write("{0:.2f}, {1:.2f}\r\n".format(x, y))

    def handleSaveComboBox(self, index):
        [x, y] = self.ui.saveComboBox.itemData(index)
        self.ui.xmoveDoubleSpinBox.setValue(x)
        self.ui.ymoveDoubleSpinBox.setValue(y)
        
    def handleStagePosition(self, pos_dict):
        self.ui.xposText.setText("{0:.3f}".format(pos_dict["x"]))
        self.ui.yposText.setText("{0:.3f}".format(pos_dict["y"]))

    def handleZeroButton(self, boolean):
        resp = halMessageBox.halMessageBoxResponse(self,
                                                   "Confirm Stage Zero",
                                                   "Are you sure that you want to zero the stage position?")
        if (resp == QtWidgets.QMessageBox.Yes):
            self.stage_functionality.zero()

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
        
    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setStageFunctionality(response.getData()["functionality"])
            
    def processMessage(self, message):

        if message.isType("change directory"):
            self.view.setDirectory(message.getData()["directory"])

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Stage",
                                                           "item data" : "stage"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.stage_fn_name}))

            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))

            self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : {"stage functionality name" : self.stage_fn_name}}))
            
        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))
            
        elif message.isType("show"):
            if (message.getData()["show"] == "stage"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("stop film"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters()}))
            
