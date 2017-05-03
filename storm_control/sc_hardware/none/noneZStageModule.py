#!/usr/bin/env python
"""
Emulated Z stage functionality

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class NoneZStageFunctionality(hardwareModule.HardwareFunctionality, lockModule.ZStageFunctionalityMixin):
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.maximum = self.getParameter("maximum")
        self.minimum = self.getParameter("minimum")
        self.z_position = 0.5 * (self.maximum - self.minimum)

    def goAbsolute(self, z_pos):
        if (z_pos < self.minimum):
            z_pos = self.minimum
        if (z_pos > self.maximum):
            z_pos = self.maximum
        self.z_position = z_pos
        self.zStagePosition.emit(self.z_position)

    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)


class NoneZStageModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.z_stage_functionality = None

        configuration = module_params.get("configuration")
        self.z_stage_functionality = NoneZStageFunctionality(parameters = configuration.get("parameters"))

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.z_stage_functionality}))
            
    def processMessage(self, message):
        
        if message.isType("get functionality"):
            self.getFunctionality(message)
