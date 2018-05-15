#!/usr/bin/env python
"""
Motorized or piezo Z stage functionality (software control, see
voltageZModule for DAQ control). 

Hazen 04/18
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class ZStageFunctionality(hardwareModule.HardwareFunctionality, lockModule.ZStageFunctionalityMixin):
    """
    This is the functionality you'd want to use with the focus lock. It is
    designed to be used with z stages the respond essentially instanteously.
    """
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, z_stage = None, **kwds):
        super().__init__(**kwds)
        self.z_stage = z_stage

    def goAbsolute(self, z_pos):
        if (z_pos < self.minimum):
            z_pos = self.minimum
        if (z_pos > self.maximum):
            z_pos = self.maximum
        self.z_position = z_pos
        self.z_stage.zMoveTo(self.z_position)
        self.zStagePosition.emit(self.z_position)

    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)

        
class ZStageFunctionalityBuffered(hardwareModule.BufferedFunctionality, lockModule.ZStageFunctionalityMixin):
    """
    This functionality is less idea for a focus lock. It is designed for
    use with z stages that respond more slowly. Maybe they are motorized,
    or communication is slow.
    """
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, z_stage = None, **kwds):
        super().__init__(**kwds)
        self.z_stage = z_stage

    def goAbsolute(self, z_pos):
        if (z_pos != self.z_position):
            if (z_pos < self.minimum):
                z_pos = self.minimum
            if (z_pos > self.maximum):
                z_pos = self.maximum
            self.maybeRun(task = self.zMoveTo,
                          args = [z_pos],
                          ret_signal = self.zStagePosition)

    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)

    def zMoveTo(self, z_pos):
        self.z_stage.zMoveTo(z_pos)
        self.z_position = z_pos
        return z_pos
        

class ZStage(hardwareModule.HardwareModule):
    """
    This is a Z stage under software control.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.z_stage_functionality = None
        self.z_stage = None
                                                            
    def cleanUp(self, qt_settings):
        if self.z_stage_functionality is not None:
            self.z_stage.shutDown()

    def processMessage(self, message):
        
        if message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.z_stage_functionality is not None:
                    message.addResponse(
                        halMessage.HalMessageResponse(source = self.module_name,
                                                      data = {"functionality" : self.z_stage_functionality}))
