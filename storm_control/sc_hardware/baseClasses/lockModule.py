#!/usr/bin/env python
"""
The core functionality for a QPD, QPD/Camera or z stage.

Hazen 04/17
"""

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class LockFunctionalityMixin(object):
    """
    Combine this with either a HardwareFunctionality or a
    BufferedFunctionality depending on how responsive the 
    device is. Most of these are to help the focus lock GUI
    render the output of the device properly.
    """
    def __init__(self,
                 has_center_bar = False,
                 maximum = None,
                 minimum = None,
                 warning_high = None,
                 warning_low = None,
                 **kwds):
        super().__init__(**kwds)
        self.has_center_bar = has_center_bar
        self.maximum = maximum
        self.minimum = minimum
        self.warning_high = warning_high
        self.warning_low = warning_low

    def getMaximum(self):
        return self.maximum

    def getMinimum(self):
        return self.minimum

    def getWarningHigh(self):
        return self.warning_high
        
    def getWarningLow(self):
        return self.warning_low
        
    def hasCenterBar(self):
        return self.has_center_bar


class QPDFunctionalityMixin(LockFunctionalityMixin):
    pass


class ZStageFunctionalityMixin(LockFunctionalityMixin):
    """
    Z stages are expected to work in units of microns.

    A Z stage will emit two signals:
    (1) zStageJump() - One of the clients requested a stage jump.
    (2) zStagePosition() - The current z stage position.
    """
    def __init__(self, jump_size = None, **kwds):
        super().__init__(**kwds)
        self.center = 0.5 * (self.maximum - self.minimum)
        self.jump_size = jump_size
        self.z_position = 0.0

    def getCurrentPosition(self):
        return self.z_position
        
    def goAbsolute(self, z_pos):
        pass

    def goRelative(self, z_delta):
        pass
        
    def jump(self, delta):
        """
        Users will call this to move the stage. If focus lock
        is engaged then the lock target will need to change.
        """
        pass

    def recenter(self):
        pass
    

class LockModule(hardwareModule.HardwareModule):
    pass

        
