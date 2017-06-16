#!/usr/bin/env python
"""
Uses a NI counter functionality to create a pulse delay.

Hazen 06/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class PulseDelay(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.ct_fn = None
        self.ct_fn_name = module_params.get("configuration.counter_functionality")

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.ct_fn = response.getData()["functionality"]
    
    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.ct_fn_name}))


class PulseDelayCamera(PulseDelay):
    """
    Pulse delay where the task is armed when we see 
    the 'start camera' message for the specified camera.
    """
    def __init__(self, module_params = None, **kwds):
        kwds["module_params"] = module_params
        super().__init__(**kwds)
        self.camera_name = module_params.get("configuration.camera")

    def processMessage(self, message):
        super().processMessage(message)

        if message.isType("start camera") and self.ct_fn is not None:
            if (message.getData()["camera"] == self.camera_name):
                self.ct_fn.pwmOutput(cycles = 1)
