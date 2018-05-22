#!/usr/bin/env python
"""
The z stage UI.

Hazen Babcock 05/18
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets

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

        icon_path = os.path.join(os.path.dirname(__file__),"../icons/")
        self.ui.upLButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "2uparrow-128.png")))
        self.ui.upLButton.clicked.connect(self.handleUpLButton)
        self.ui.upSButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "1uparrow-128.png")))
        self.ui.upSButton.clicked.connect(self.handleUpSButton)
        self.ui.downSButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "1downarrow-128.png")))
        self.ui.downSButton.clicked.connect(self.handleDownSButton)                
        self.ui.downLButton.setIcon(QtGui.QIcon(os.path.join(icon_path, "2downarrow-128.png")))
        self.ui.downLButton.clicked.connect(self.handleDownLButton)

        self.ui.homeButton.clicked.connect(self.handleHomeButton)
        self.ui.retractButton.clicked.connect(self.handleRetractButton)
        self.ui.zeroButton.clicked.connect(self.handleZeroButton)

        self.ui.goButton.clicked.connect(self.handleGoButton)
        
        # Set to minimum size & fix.
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        # Add parameters.
        self.parameters.add(params.ParameterRangeFloat(description ="Z Stage large step size",
                                                       name = "z_large_step",
                                                       value = configuration.get("large_step"),
                                                       min_value = 0.001,
                                                       max_value = 100.0))        
        self.parameters.add(params.ParameterRangeFloat(description ="Z Stage small step size",
                                                       name = "z_small_step",
                                                       value = configuration.get("small_step"),
                                                       min_value = 0.001,
                                                       max_value = 10.0))
        
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters

    def handleDownLButton(self, boolean):
        self.z_stage_fn.goRelative(-1.0*self.parameters.get("z_large_step"))

    def handleDownSButton(self, boolean):
        self.z_stage_fn.goRelative(-1.0*self.parameters.get("z_small_step"))

    def handleGoButton(self, boolean):
        self.z_stage_fn.goAbsolute(self.ui.goSpinBox.value())
        
    def handleHomeButton(self, boolean):
        self.z_stage_fn.goAbsolute(0.0)

    def handleRetractButton(self, boolean):
        self.z_stage_fn.goAbsolute(self.retracted_z)

    def handleUpLButton(self, boolean):
        self.z_stage_fn.goRelative(self.parameters.get("z_large_step"))

    def handleUpSButton(self, boolean):
        self.z_stage_fn.goRelative(self.parameters.get("z_small_step"))        

    def handleZeroButton(self, boolean):
        self.z_stage_fn.zero()

    def handleZStagePosition(self, z_value):
        self.ui.zPosLabel.setText("{0:.2f}".format(z_value))
        
#    def handleZValueChanged(self, z_value):
#        self.z_stage_fn.goAbsolute(z_value)

    def newParameters(self, parameters):
        self.parameters.setv("z_large_step", parameters.get("z_large_step"))
        self.parameters.setv("z_small_step", parameters.get("z_small_step"))

    def setFunctionality(self, z_stage_fn):
        self.z_stage_fn = z_stage_fn
        self.z_stage_fn.zStagePosition.connect(self.handleZStagePosition)
        self.ui.goSpinBox.setMinimum(self.z_stage_fn.getMinimum())
        self.ui.goSpinBox.setMaximum(self.z_stage_fn.getMaximum())
        self.setEnabled(True)


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


