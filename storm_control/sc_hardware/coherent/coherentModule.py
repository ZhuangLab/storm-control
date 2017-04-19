#!/usr/bin/env python
"""
HAL module for Coherent laser control.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.sc_hardware.baseClasses.laserModule as laserModule


class CoherentLaserFunctionality(laserModule.LaserFunctionalityBuffered):

    def __init__(self, laser = None, **kwds):
        super().__init__(**kwds)
        self.laser = laser

    def processRequest(self, power):
        # This will be called inside a mutex so we don't have to
        # worry about locking this ourselves.
        self.laser.setPower(0.01 * power)
    
    
class CoherentModule(hardwareModule.HardwareModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.device_mutex = QtCore.QMutex()
        self.laser_functionality = None
        
    def getFunctionality(self, message):
        pass
    
    def processMessage(self, message):

        if message.isType("get functionality"):
            self.getFunctionality(message)
            
        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

    def startFilm(self, message):
        if self.laser_functionality is not None:
        pass

    def stopFilm(self, message):
        pass
