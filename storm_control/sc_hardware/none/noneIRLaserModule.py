#!/usr/bin/env python
"""
HAL module for emulating a (IR) laser for the focus lock.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule


class NoneIRLaserFunctionality(amplitudeModule.AmplitudeFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.scale = 1.0/(self.maximum - self.minimum + 1.0)

    def hasPowerAdjustment(self):
        return True
    
    def onOff(self, power, state):
        pass
    
    def output(self, power):
        duty_cycle = (power - self.minimum)*self.scale


class NoneIRLaserModule(amplitudeModule.AmplitudeModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.ir_laser_functionality = NoneIRLaserFunctionality(minimum = 0,
                                                               maximum = 100,
                                                               used_during_filming = False)
        
    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.ir_laser_functionality}))
