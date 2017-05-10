#!/usr/bin/env python
"""
HAL interface to Crystal Technologies AOTFs.

Hazen 04/17
"""
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.crystalTechnologies.AOTF as AOTF
import storm_control.sc_library.parameters as params


class AOTFFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):

    def __init__(self, aotf = None, channel = None, frequencies = None, **kwds):
        super().__init__(**kwds)
        self.aotf = aotf
        self.on = False
        self.channel = channel
        self.aotf.setFrequencies(self.channel, frequencies)

    def onOff(self, power, state):
        self.mustRun(task = self.aotf.setAmplitude,
                     args = [self.channel, power])
        self.on = state

    def output(self, power):
        if self.on:
            self.maybeRun(task = self.aotf.setAmplitude,
                          args = [self.channel, power])
        

class AOTFModule(amplitudeModule.AmplitudeModule):
    """
    The sub-class should connect to the AOTF, then call super().
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.aotf_fns = {}
        self.aotf_mutex = QtCore.QMutex()

        if self.aotf is not None:
            configuration = module_params.get("configuration")
            fsk_mode = configuration.get("fsk_mode")
            use_fsk = configuration.get("use_fsk")

            if use_fsk:
                self.aotf.analogModulationOn()
            else:
                self.aotf.analogModulationOff()

            for fn_name in configuration.getAttrs():
                fn_params = configuration.get(fn_name)
                if isinstance(fn_params, params.StormXMLObject):
                    aotf_fn_name = self.module_name + "." + fn_name
                    channel = fn_params.get("channel")

                    # Configure frequencies.
                    frequencies = [fn_params.get("off_frequency"),
                                   fn_params.get("off_frequency"),
                                   fn_params.get("off_frequency"),
                                   fn_params.get("off_frequency")]

                    # FIXME: This won't work unless fsk_mode is 1.
                    if use_fsk:
                        frequencies[1] = fn_params.get("on_frequency")
                        self.aotf.fskOn(channel, fsk_mode)
                    else:
                        frequencies[0] = fn_params.get("on_frequency")
                        self.aotf.fskOff(channel)

                    self.aotf_fns[aotf_fn_name] = AOTFFunctionality(aotf = self.aotf,
                                                                    channel = channel,
                                                                    device_mutex = self.aotf_mutex,
                                                                    frequencies = frequencies,
                                                                    maximum = fn_params.get("maximum"))

    def cleanUp(self, qt_settings):
        if self.aotf is not None:
            for aotf_fn in self.aotf_fns.values():
                aotf_fn.wait()
            self.aotf.shutDown()

    def getFunctionality(self, message):
        aotf_fn_name = message.getData()["name"]
        if aotf_fn_name in self.aotf_fns:
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.aotf_fns[aotf_fn_name]}))


class AOTF64BitModule(AOTFModule):
                                
    def __init__(self, module_params = None, **kwds):
        kwds["module_params"] = module_params
        self.aotf = AOTF.AOTF64Bit(python32_exe = module_params.get("configuration").get("python32_exe"))
        if not self.aotf.getStatus():
            self.aotf = None

        super().__init__(**kwds)


class AOTFTelnet(AOTFModule):
                                
    def __init__(self, module_params = None, **kwds):
        kwds["module_params"] = module_params
        self.aotf = AOTF.AOTFTelnet(ip_address = module_params.get("configuration").get("ip_address"))
        if not self.aotf.getStatus():
            self.aotf = None

        super().__init__(**kwds)
        
