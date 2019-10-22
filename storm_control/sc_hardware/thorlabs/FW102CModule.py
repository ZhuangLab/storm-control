#!/usr/bin/env python
"""
HAL module for controlling a Thorlabs filter wheel.

Hazen 04/18
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.thorlabs.FW102C as FW102C


# FIXME: Should be amplitudeModule.AmplitudeFunctionalityBuffered?
#
class FW102CFilterWheelFunctionality(amplitudeModule.AmplitudeFunctionality):

    def __init__(self, filter_wheel = None, **kwds):
        super().__init__(**kwds)
        self.filter_wheel = filter_wheel
        #self.on = True

    def onOff(self, power, state):
        pass
    
    def output(self, power):
        self.filter_wheel.setPosition(power)

    def startFilm(self, power):
        pass


class FW102CFilterWheelModule(amplitudeModule.AmplitudeModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.filter_wheel_functionality = None

        configuration = module_params.get("configuration")
        filter_wheel = FW102C.FW102C(baudrate = configuration.get("baudrate"),
                                     port = configuration.get("port"))

        if filter_wheel.getStatus():
            self.filter_wheel_functionality = FW102CFilterWheelFunctionality(display_normalized = False,
                                                                             filter_wheel = filter_wheel,
                                                                             maximum = configuration.get("maximum"),
                                                                             used_during_filming = False)
        
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            if self.filter_wheel_functionality is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.filter_wheel_functionality}))
            
