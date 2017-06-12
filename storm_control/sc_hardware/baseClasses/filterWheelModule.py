#!/usr/bin/env python
"""
Base class / functionality for a filter wheel.

Hazen 06/17
"""
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class FilterWheelWorker(hardwareModule.HardwareWorker):
    pass


class FilterWheelMixin(object):
    """
    These are the methods that miscControl.filterWheel will 
    expect a filter wheel functionality to have.
    """
    def __init__(self, maximum = 6, **kwds):
        super().__init__(**kwds)

        assert isinstance(maximum, int)

        self.current_position = 0
        self.maximum = maximum

    def checkPosition(self, position):
        assert (position >= 0)
        assert (position < self.maximum)
        
    def getCurrentPosition(self):
        return self.current_position

    def setCurrentPosition(self, position):
        assert False


class FilterWheelFunctionality(hardwareModule.HardwareFunctionality, FilterWheelMixin):
    """
    Base class for a filter wheel functionality.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)


class FilterWheelFunctionalityBuffered(hardwareModule.BufferedFunctionality, FilterWheelMixin):
    """
    Base class for a filter wheel functionality.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
    

class FilterWheelModule(hardwareModule.HardwareModule):
    """
    Base class for control of stand-alone filter wheel, as opposed
    to one that is controlled in combination with another device
    such as a XY stage.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def getFunctionality(self, message):
        pass

    def processMessage(self, message):

        if message.isType("get functionality"):
            self.getFunctionality(message)
