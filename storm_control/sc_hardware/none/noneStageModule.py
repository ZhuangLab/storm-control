#!/usr/bin/env python
"""
HAL module for emulating a stage.

Hazen 04/17
"""
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule


class NoneStage(QtCore.QObject):
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
        self.goAbsolute(self.x + dx, self.y + dy)

    def jog(self, xs, ys):
        pass
    
    def joystickOnOff(self, flag):
        pass

    def position(self):
        return {"x" : self.x,
                "y" : self.y}

    def setVelocity(self, vx, vy):
        pass

    def shutDown(self):
        pass

    def zero(self):
        self.x = 0.0
        self.y = 0.0


class NoneStageFunctionality(stageModule.StageFunctionality):
    
    def __init__(self, update_interval = None, **kwds):
        """
        update_interval - How frequently to update in milli-seconds, something 
                          like 500 is usually good.
        """
        super().__init__(**kwds)
        self.pos_dict = self.stage.position()

        self.moveTimer = QtCore.QTimer()
        self.moveTimer.setInterval(200)
        self.moveTimer.setSingleShot(True)
        self.moveTimer.timeout.connect(self.handleMoveTimer)
        
        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(update_interval)
        self.updateTimer.timeout.connect(self.handleUpdateTimer)
        self.updateTimer.start()

    def goAbsolute(self, x, y):
        super().goAbsolute(x, y)
        
        # This is for TCP testing, so we don't have to
        # wait for the (position) update timer to fire.
        self.pos_dict = {"x" : x, "y" : y}
        
        self.isMoving.emit(True)
        self.moveTimer.start()

    def handleMoveTimer(self):
        self.isMoving.emit(False)

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


class NoneStageFunctionalityBroken(NoneStageFunctionality):
    """
    This is in testing to verify that the watchdog timer
    functionality is working.
    """
    def handleMoveTimer(self):
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


class NoneStageModuleBroken(NoneStageModule):
    """
    This is in testing to verify that the watchdog timer
    functionality is working.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.stage_functionality = NoneStageFunctionalityBroken(stage = self.stage,
                                                                update_interval = 500)

        self.watchdog_timeout = 100
