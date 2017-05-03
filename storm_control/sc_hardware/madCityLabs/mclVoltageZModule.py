#!/usr/bin/env python
"""
Mad City Labs (voltage controlled) Z stage functionality.

Hazen 05/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class MCLVoltageZFunctionality(hardwareModule.HardwareFunctionality, lockModule.ZStageFunctionalityMixin):
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, ao_fn = None, microns_to_volts = None, **kwds):
        super().__init__(**kwds)
        self.ao_fn = ao_fn
        self.maximum = self.getParameter("maximum")
        self.microns_to_volts = microns_to_volts
        self.minimum = self.getParameter("minimum")
        self.recenter()

    def goAbsolute(self, z_pos):
        if (z_pos < self.minimum):
            z_pos = self.minimum
        if (z_pos > self.maximum):
            z_pos = self.maximum
        self.z_position = z_pos
        self.ao_fn.output(self.z_position * self.microns_to_volts)
        self.zStagePosition.emit(self.z_position)
        
    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)

    def haveHardwareTiming(self):
        return True

    def rescaleWaveform(self, waveform):
        return waveform * self.microns_to_volts
    

class MCLVoltageZ(hardwareModule.HardwareModule):
    """
    This is a Mad City Labs stage in analog control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.z_stage_functionality = None

    def cleanUp(self, qt_settings):
        if self.z_stage_functionality is not None:
            self.z_stage_functionality.recenter()
        
    def handleResponse(self, message):
        if message.isType("get functionality"):
            self.z_stage_functionality = MCLVoltageZFunctionality(ao_fn = response.getData()["functionality"],
                                                                  parameters = self.configuration.get("parameters"),
                                                                  microns_to_volts = self.configuration.get("microns_to_volts"))

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("ao_fn_name")}))
                                                           "extra data" : "ir_laser"}))
        
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.z_stage_functionality is not None:
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.z_stage_functionality}))

