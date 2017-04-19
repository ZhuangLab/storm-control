#!/usr/bin/env python
"""
HAL module for Coherent laser control.

Hazen 04/17
"""

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule


class CoherentLaserFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):

    def __init__(self, laser = None, **kwds):
        super().__init__(**kwds)
        self.laser = laser

    def processRequest(self, power):
        # This will be called inside a mutex so we don't have to
        # worry about locking this ourselves.
        self.laser.setPower(0.01 * power)
    
    
class CoherentModule(amplitudeModule.AmplitudeModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.laser = None

    def cleanUp(self):
        if self.laser:
            self.laser.shutDown()
   
    def processMessage(self, message):

        if message.isType("get functionality"):
            self.getFunctionality(message)
            
        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

    def setExtControl(self, state):
        self.device_mutex.lock()
        self.laser.setExtControl(state)
        self.device_mutex.unlock()
        
    def startFilm(self, message):
        if self.laser is not None:
            amplitudeModule.AmplitudeWorker(task = self.setExtControl,
                                            args = [True])

    def stopFilm(self, message):
        if self.laser is not None:
            amplitudeModule.AmplitudeWorker(task = self.setExtControl,
                                            args = [False])
