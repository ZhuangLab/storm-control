#!/usr/bin/env python
"""
HAL module for controlling a Marzhauser stage.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.marzhauser.marzhauser as marzhauser


class MarzhauserStageFunctionality(stageModule.StageFunctionality):
    pass


class MarzhauserStage(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        self.stage = marzhauser.MarzhauserRS232(port = configuration.get("port"))
        if self.stage.getStatus():

            # Set (maximum) stage velocity.
            velocity = configuration.get("velocity")
            self.stage.setVelocity(velocity, velocity)
            self.stage_functionality = MarzhauserStageFunctionality(stage = self.stage,
                                                                    update_interval = 500)

