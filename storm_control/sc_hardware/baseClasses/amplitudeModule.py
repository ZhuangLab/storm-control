#!/usr/bin/env python
"""
Base class / functionality for an (illumination) amplitude control device.

Hazen 04/17
"""
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class AmplitudeWorker(hardwareModule.HardwareWorker):
    pass


class AmplitudeMixin(object):
    """
    These are the methods that illumination.illumination will 
    expect an amplitude functionality to have.
    """
    def __init__(self, display_normalized = True, minimum = 0, maximum = 10, used_during_filming = True, **kwds):
        super().__init__(**kwds)
        self.display_normalized = display_normalized
        self.maximum = maximum
        self.minimum = minimum
        self.used_during_filming = used_during_filming

    def getDisplayNormalized(self):
        return self.display_normalized
    
    def getMaximum(self):
        return self.maximum
        
    def getMinimum(self):
        return self.minimum

    def getUsedDuringFilming(self):
        return self.used_during_filming
    
    def output(self, power):
        assert False
        
    
class AmplitudeFunctionality(hardwareModule.HardwareFunctionality, AmplitudeMixin):
    """
    Base class for an amplitude functionality. The sub-class must override processRequest().
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        
class AmplitudeFunctionalityBuffered(hardwareModule.BufferedFunctionality, AmplitudeMixin):
    """
    Base class for a buffered amplitude functionality. The sub-class must override processRequest().
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
    
    
class AmplitudeModule(hardwareModule.HardwareModule):
    """
    These modules will always provide a single functionality with the 
    name 'module_name.amplitude_modulation'. This functionality is
    primarily used by illumination.illumination.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.device_mutex = QtCore.QMutex()

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
        pass

    def stopFilm(self, message):
        pass
