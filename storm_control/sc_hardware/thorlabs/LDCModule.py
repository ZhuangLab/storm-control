#!/usr/bin/env python
"""
HAL module for controlling a Thorlabs laser diode. The
actual control is done by a DAQ card.

Hazen 05/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class LDCIRLaserAdjustableFunctionality(amplitudeModule.AmplitudeFunctionality):

    def __init__(self, ct_task = None, **kwds):
        super().__init__(**kwds)
        self.ct_task = ct_task
        self.scale = 1.0/(self.maximum - self.minimum + 1.0)

    def hasPowerAdjustment(self):
        return True
    
    def onOff(self, power, state):
        self.output(power)
    
    def output(self, power):
        duty_cycle = (power - self.minimum)*self.scale
        self.ct_task.pwmOutput(duty_cycle = duty_cycle)


class LDCIRLaserModule(hardwareModule.HardwareModule):
    """
    Thorlabs diode laser control module with power controlled by PWM.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.ir_laser_functionality = None

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.ir_laser_functionality = LDCIRLaserAdjustableFunctionality(ct_task = response.getData()["functionality"],
                                                                            minimum = 0,
                                                                            maximum = 100)

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("ct_fn_name")}))
        
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.ir_laser_functionality is not None:
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.ir_laser_functionality}))
        
