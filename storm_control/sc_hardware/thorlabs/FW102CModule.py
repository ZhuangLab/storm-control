#!/usr/bin/env python
"""
HAL module for controlling a Thorlabs filter wheel.

Hazen 04/18
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.filterWheelModule as filterWheelModule
import storm_control.sc_hardware.thorlabs.FW102C as FW102C


class FW102CFilterWheelFunctionality(filterWheelModule.FilterWheelFunctionality):

    def __init__(self, filter_wheel = None, **kwds):
        super().__init__(**kwds)
        self.filter_wheel = filter_wheel

        # FIXME: Query filter wheel instead of just setting it's position.
        self.setCurrentPosition(0)

    def setCurrentPosition(self, position):
        self.checkPosition(position)
        self.current_position = position
        self.filter_wheel.setPosition(position + 1)


class FW102CFilterWheelModule(filterWheelModule.FilterWheelModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        filter_wheel = FW102C(baud_rate = configuration.get("baud_rate"),
                              port = configuration.get("port"))

        self.filter_wheel_functionality = FW102CFilterWheelFunctionality(filter_wheel = filter_wheel,
                                                                         maximum = configuration.get("maximum"))
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.filter_wheel_functionality}))
            
