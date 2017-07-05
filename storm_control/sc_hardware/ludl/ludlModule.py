#!/usr/bin/env python
"""
HAL module for controlling a LUDL stage.

Hazen 05/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.ludl.ludl as ludl


class LudlStageFunctionality(stageModule.StageFunctionality):

    def __init__(self, update_interval = None, **kwds):
        super().__init__(**kwds)
        self.pos_dict = self.stage.position()

        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(update_interval)
        self.updateTimer.timeout.connect(self.handleUpdateTimer)
        self.updateTimer.start()

    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.stagePosition)

    def position(self):
        self.pos_dict = self.stage.position()
        return self.pos_dict
        
    def wait(self):
        self.updateTimer.stop()
        super().wait()


class LudlStageTCP(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        configuration = module_params.get("configuration")
        self.stage = ludl.LudlTCP(ip_address = configuration.get("ip_address"))

        if self.stage.getStatus():
            self.stage.setVelocity(10000,10000)
            self.stage_functionality = LudlStageFunctionality(stage = self.stage,
                                                              update_interval = 500)
        else:
            self.stage = None

