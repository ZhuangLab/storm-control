#!/usr/bin/env python
"""
HAL module for emulating an illumination filter wheel.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule


class NoneFilterWheelFunctionality(amplitudeModule.AmplitudeFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.on = True
        
    def onOff(self, power, state):
        pass
    
    def output(self, power):
        pass


class NoneFilterWheelModule(amplitudeModule.AmplitudeModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.wheel_functionality = NoneFilterWheelFunctionality(display_normalized = False,
                                                                minimum = 1,
                                                                maximum = 6,
                                                                used_during_filming = False)
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.wheel_functionality}))
