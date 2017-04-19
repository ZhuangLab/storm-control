#!/usr/bin/env python
"""
Base class / functionality for an (illumination) amplitude control device.

Hazen 04/17
"""

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class AmplitudeWorker(hardwareModule.HardwareWorker):
    pass


class AmplitudeMixin(object):
    """
    These are the methods that illumination.illumination will 
    expect an amplitude functionality to have.
    """
    def __init__(self, display_normalized = True, minimum = 0, maximum = 10, **kwds):
        super().__init__(**kwds)
        self.display_normalized = display_normalized
        self.maximum = maximum
        self.minimum = minimum

    def getDisplayNormalized(self):
        return self.display_normalized
    
    def getMaximum(self):
        return self.maximum
        
    def getMinimum(self):
        return self.minimum
        
    def output(self, power):
        self.processRequest(power)

    def processRequest(self, power):
        # This is where the command to the hardware is supposed to go.
        assert False
        
    
class AmplitudeFunctionality(hardwareModule.HardwareFunctionality, AmplitudeMixin):
    """
    Base class for a amplitude functionality. The sub-class must override processRequest().
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        
class AmplitudeFunctionalityBuffered(hardwareModule.BufferedFunctionality, AmplitudeMixin):
    """
    Base class for a buffered laser functionality. The sub-class must override processRequest().
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
    def output(self, power):
        self.maybeProcess(power)
    
    
class AmplitudeModule(hardwareModule.HardwareModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)

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
