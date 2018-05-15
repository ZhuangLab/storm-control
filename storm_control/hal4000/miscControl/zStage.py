#!/usr/bin/env python
"""
The z stage UI.

Hazen Babcock 05/18
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.z_stage_ui as zStageUi


class ZStageView(halDialog.HalDialog):
    """
    Manages the z stage GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.parameters = params.StormXMLObject()
        self.retracted_z = configuration.get("retracted_z")
        self.z_stage_fn = None

        # Load UI
        self.ui = zStageUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.homeButton.clicked.connect(self.handleHomeButton)
        self.ui.retractButton.clicked.connect(self.handleRetractButton)
        self.ui.zeroButton.clicked.connect(self.handleZeroButton)
        self.ui.zPosDoubleSpinBox.valueChanged.connect(self.handleZValueChanged)

        self.setZStep(configuration.get("single_step"))
        
        # Set to minimum size & fix.
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        # Add parameters.
        self.parameters.add(params.ParameterRangeFloat(description ="Z Stage step size",
                                                       name = "z_stage_step",
                                                       value = configuration.get("single_step"),
                                                       min_value = 0.001,
                                                       max_value = 1.0))
        
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters

    def handleHomeButton(self, boolean):
        self.z_stage_fn.goAbsolute(0.0)

    def handleRetractButton(self, boolean):
        self.z_stage_fn.goAbsolute(self.retracted_z)

    def handleZeroButton(self, boolean):
        self.z_stage_fn.zero()

    def handleZStagePosition(self, z_value):
        self.ui.zPosDoubleSpinBox.setValue(z_value)
        
    def handleZValueChanged(self, z_value):
        self.z_stage_fn.goAbsolute(z_value)

    def newParameters(self, parameters):
        self.parameters = parameters
        self.setZStep(parameters.get("single_step"))

    def setFunctionality(self, z_stage_fn):
        self.z_stage_fn = z_stage_fn
        self.z_stage_fn.zStagePosition.connect(self.handleZStagePosition)
        self.ui.zPosDoubleSpinBox.setMinimum(self.z_stage_fn.getMinimum())
        self.ui.zPosDoubleSpinBox.setMaximum(self.z_stage_fn.getMaximum())
        self.setEnabled(True)

    def setZStep(self, z_step):
        self.ui.zPosDoubleSpinBox.setSingleStep(z_step)


class ZStage(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = ZStageView(module_name = self.module_name,
                               configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " z stage")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Z Stage",
                                                           "item data" : "z stage"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("z_stage_fn")}))

            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))            

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("show"):
            if (message.getData()["show"] == "z stage"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()


