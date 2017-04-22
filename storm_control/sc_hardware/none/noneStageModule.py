#!/usr/bin/env python
"""
HAL module for emulating a stage.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule


class NoneStage(object):
    """
    Emulates a stage hardware object.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.x = 0.0
        self.y = 0.0

    def getStatus(self):
        return True
    
    def goAbsolute(self, x, y):
        self.x = x
        self.y = y

    def goRelative(self, dx, dy):
        self.x += dx
        self.y += dy

    def jog(self, xs, ys):
        pass
    
    def joystickOnOff(self, flag):
        pass

    def position(self):
        return [self.x, self.y]

    def setVelocity(self, vx, vy):
        pass

    def shutDown(self):
        pass

    def zero(self):
        self.x = 0.0
        self.y = 0.0


class NoneStageFunctionality(stageModule.StageFunctionality):
    pass


class NoneStageModule(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        self.stage = NoneStage()

        # Set (maximum) stage velocity.
        velocity = configuration.get("velocity")
        self.stage.setVelocity(velocity, velocity)
        
        self.stage_functionality = NoneStageFunctionality(stage = self.stage,
                                                          update_interval = 500)

