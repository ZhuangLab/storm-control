#!/usr/bin/env python
"""
Mad City Labs Z stage functionality.

Hazen 05/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule
import storm_control.sc_hardware.baseClasses.madCityLabs.mclController as mclController

class MCLZStageFunctionality(hardwareModule.HardwareFunctionality, lockModule.ZStageFunctionalityMixin):
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, mcl_stage = None, **kwds):
        super().__init__(**kwds)
        self.maximum = self.getParameter("maximum")
        self.mcl_stage = mcl_stage
        self.minimum = self.getParameter("minimum")
        self.recenter()

    def goAbsolute(self, z_pos):
        if (z_pos < self.minimum):
            z_pos = self.minimum
        if (z_pos > self.maximum):
            z_pos = self.maximum
        self.z_position = z_pos
        self.mcl_stage.zMoveTo(self.z_position)
        self.zStagePosition.emit(self.z_position)

    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)


class MCLZStage(hardwareModule.HardwareModule):
    """
    This is a Mad City Labs stage in USB control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.z_stage_functionality = None

        configuration = module_params.get("configuration")
        serial_number = configuration.get("serial_number", 0)
        if (serial_number == 0):
            serial_number = None
        self.mcl_stage = mclController.MCLStage(mcl_lib = configuration.get("mcl_lib"),
                                                serial_number = serial_number)

        if self.mcl_stage.getStatus():
            # FIXME? Query stage for the actual maximum Z?
            self.z_stage_functionality = MCLZStageFunctionality(mcl_stage = self.mcl_stage,
                                                                parameters = configuration.get("parameters"))
                                                            
    def cleanUp(self, qt_settings):
        if self.z_stage_functionality is not None:
            self.mcl_stage.shutDown()
        
    def processMessage(self, message):
        
        if message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.z_stage_functionality is not None:
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.z_stage_functionality}))
