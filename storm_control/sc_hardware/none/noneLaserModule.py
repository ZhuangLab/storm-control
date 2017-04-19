#!/usr/bin/env python
"""
HAL module for emulating a laser.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule


class NoneLaserFunctionality(amplitudeModule.AmplitudeFunctionality):

    def output(self, power):
        pass


class NoneLaserModule(amplitudeModule.AmplitudeModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        self.used_during_filming = configuration.get("used_during_filming")        

        self.laser_functionality = NoneLaserFunctionality(display_normalized = True,
                                                          minimum = 0,
                                                          maximum = 1000,
                                                          used_during_filming = self.used_during_filming)
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.laser_functionality}))
