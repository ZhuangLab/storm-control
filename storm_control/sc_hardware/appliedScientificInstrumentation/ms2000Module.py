#!/usr/bin/env python
"""
HAL module for controlling a MS2000 stage.

Aaron 10/19

Adapted from Ludl Module
"""
import math
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.appliedScientificInstrumentation.ms2000 as ms2000


class ASIStageFunctionality(stageModule.StageFunctionalityNF):

    def calculateMoveTime(self, dx, dy):
        """
        According to the MS2000 manual
        We assume that this stage can move at 7.5mm / second.  We add an extra 
        second as this seems to be how long it takes for the command to get to 
        the stage and for the stage to settle after the move.
        """
        time_estimate = math.sqrt(dx*dx + dy*dy)/7500.0 + 1.0
        print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate
    

class ASIStageRS232(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        configuration = module_params.get("configuration")
        self.stage = ms2000.MS2000(port = configuration.get("com_port"))

        if self.stage.getStatus():
            self.stage.setVelocity(7.5,7.5)
            self.stage_functionality = ASIStageFunctionality(device_mutex = QtCore.QMutex(),
                                                              stage = self.stage,
                                                              update_interval = 500)
        else:
            self.stage = None