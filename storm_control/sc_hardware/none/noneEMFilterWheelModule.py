#!/usr/bin/env python
"""
HAL module for emulating an emission filter wheel.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.filterWheelModule as filterWheelModule


class NoneEMFilterWheelFunctionality(filterWheelModule.FilterWheelFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def setCurrentPosition(self, position):
        self.checkPosition(position)
        self.current_position = position


class NoneEMFilterWheelModule(filterWheelModule.FilterWheelModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.em_wheel_functionality = NoneEMFilterWheelFunctionality(maximum = 6)
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.em_wheel_functionality}))
