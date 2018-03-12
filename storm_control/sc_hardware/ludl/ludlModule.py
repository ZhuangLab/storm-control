#!/usr/bin/env python
"""
HAL module for controlling a LUDL stage.

Hazen 05/17
"""
import math
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
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(update_interval)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        self.update_timer.start()

        # Moving timer for absolute moves. We use this as polling these stages
        # for their position is ridiculously slow.
        self.moving_timer = QtCore.QTimer()
        self.moving_timer.setSingleShot(True)
        self.moving_timer.timeout.connect(self.handleMovingTimer)

    def goAbsolute(self, x, y):
        # Notify that the stage is moving.
        self.isMoving.emit(True)

        # Tell the stage to move.
        super().goAbsolute(x, y)

        # Figure out how far we have to move in microns. Assume we can move
        # 10mm / second. Add an additional fixed amount.
        dx = x - self.pos_dict["x"]
        dy = y - self.pos_dict["y"]
        time_estimate = math.sqrt(dx*dx + dy*dy)/10000.0 + 1.0
        print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))

        # Set interval and start the timer.
        self.moving_timer.setInterval(time_estimate * 1.0e+3)
        self.moving_timer.start()

        # Pretend we already got there..
        self.pos_dict["x"] = x
        self.pos_dict["y"] = y
        
    def handleMovingTimer(self):
        self.isMoving.emit(False)
        
    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.stagePosition)

    def position(self):
        # Don't update the position if the move timer is active. When we were
        # told to move we set the stage position to the final position and we
        # don't want to change that in the middle of the move. Why? If we get
        # a position during the move, then arrive at the final position and
        # don't manage to poll the stage again before saving the movie the
        # movie position will be incorrect. This assumes that the stage does
        # finally arrive at the requested position..
        #
        if not self.moving_timer.isActive():
            self.pos_dict = self.stage.position()
        return self.pos_dict
        
    def wait(self):
        self.update_timer.stop()
        super().wait()


class LudlStageRS232(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        configuration = module_params.get("configuration")
        self.stage = ludl.LudlRS232(port = configuration.get("com_port"))

        if self.stage.getStatus():
            self.stage.setVelocity(10000,10000)
            self.stage_functionality = LudlStageFunctionality(stage = self.stage,
                                                              update_interval = 500)
        else:
            self.stage = None

            
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

