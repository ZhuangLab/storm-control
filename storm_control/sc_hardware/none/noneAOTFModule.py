#!/usr/bin/env python
"""
HAL module for emulating an AOTF.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_library.parameters as params

class NoneAOTFFunctionality(amplitudeModule.AmplitudeFunctionality):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.on = True
        
    def onOff(self, power, state):
        pass
    
    def output(self, power):
        pass


class NoneAOTFModule(amplitudeModule.AmplitudeModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")

        # Create functionalities that we will provide.
        self.aotf_channel_fns = {}
        for pname in configuration.getAttrs():
            pvalue = configuration.getp(pname)
            if isinstance(pvalue, params.StormXMLObject):
                fn_name = self.module_name + "." + pname
                self.aotf_channel_fns[fn_name] = NoneAOTFFunctionality(maximum = pvalue.get("maximum"))
        
    def getFunctionality(self, message):
        fn_name = message.getData()["name"]
        if (fn_name in self.aotf_channel_fns):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.aotf_channel_fns[fn_name]}))


            
