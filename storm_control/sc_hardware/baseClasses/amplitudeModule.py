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

    Note that illumination uses sliders to control the amplitude
    minimum and maximum must be integers.
    """
    def __init__(self, display_normalized = True, minimum = 0, maximum = 10, used_during_filming = True, **kwds):
        super().__init__(**kwds)

        assert isinstance(display_normalized, bool)
        assert isinstance(minimum, int)
        assert isinstance(maximum, int)
        assert isinstance(used_during_filming, bool)
        
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

    def onOff(self, power, state):
        """
        This is usually called when the illumination channel check box is toggled. Devices
        like lasers and AOTFs are expected to go to 'power' and then not respond to further
        power changes if state is False. Others devices like filter wheels will likely
        just ignore this as they are usually not used to also turn the channel on/off.
        """
        assert False
        
    def output(self, power):
        """
        This is usually called when the illumination channel slider is moved. Some
        channels will ignore this when they are turned off, others like filter wheels
        might still move.
        """
        assert False
        
    
class AmplitudeFunctionality(hardwareModule.HardwareFunctionality, AmplitudeMixin):
    """
    Base class for an amplitude functionality.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        
class AmplitudeFunctionalityBuffered(hardwareModule.BufferedFunctionality, AmplitudeMixin):
    """
    Base class for a buffered amplitude functionality.
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
