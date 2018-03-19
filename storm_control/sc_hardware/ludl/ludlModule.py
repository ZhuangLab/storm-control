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
    positionUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, update_interval = None, **kwds):
        super().__init__(**kwds)
        self.am_moving = False
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

        # We need a 'relay' signal because when self.position() is called
        # in the context of a HardwareWorker it will have stale information,
        # in particular it might think the stage is not moving when it
        # actually is. If the stage is moving we don't want to return
        # whatever position the stage thinks it is at as this will likely
        # be wrong.
        self.positionUpdate.connect(self.handlePositionUpdate)

    def goAbsolute(self, x, y):
        # Notify that the stage is moving.
        self.am_moving = True
        self.isMoving.emit(True)

        # Stop the position update timer. Note that this alone is not
        # sufficient to stop stale stage position information. This
        # timer might have gone off just before self.goAbsolute() was
        # called so there could be a position request queued up in
        # the BufferedFunctionality().
        #
        self.update_timer.stop()
        
        # Tell the stage to move.
        super().goAbsolute(x, y)

        # Figure out how far we have to move in microns. Assume we can move
        # 10mm / second. We add an extra second as this seems to be how long
        # it takes for the command to get to the stage and for the stage to
        # settle after the move.
        #
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
        self.stagePosition.emit(self.pos_dict)
        
    def handleMovingTimer(self):
        self.isMoving.emit(False)
        self.am_moving = False
        
        # Restart the position update timer.
        self.update_timer.start()

    def handlePositionUpdate(self, pos_dict):
        # Only update and pass on the current stage position if we
        # are not in the middle of a move.
        if not self.am_moving:
            self.pos_dict = pos_dict
            self.stagePosition.emit(self.pos_dict)
            
    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.positionUpdate)

    def position(self):
        return self.stage.position()
        
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

