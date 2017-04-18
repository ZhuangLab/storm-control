#!/usr/bin/env python
"""
Basic DAQ module functionality.

Hazen 04/17
"""

import numpy

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class DaqWaveform(object):

    def __init__(self, is_analog = True, source = None, waveform = None, oversampling = 1, **kwds):
        super().__init__(**kwds)

        assert isinstance(is_analog, bool)
        assert isinstance(oversampling, int)
        assert isinstance(source, str)
        assert isinstance(waveform, numpy.ndarray)
        
        self.is_analog = is_analog
        self.oversampling = oversampling # This is relative to the camera speed.
        self.waveform = waveform
        self.source = source

    def getOversampling(self):
        return self.oversampling
        
    def getSource(self):
        return self.source
        
    def getWaveform(self):
        return self.waveform
    
    def isAnalog(self):
        return self.is_analog

    
class DaqFunctionality(hardwareModule.HardwareFunctionality):
    pass


class DaqModule(hardwareModule.HardwareModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)

        # The message for passing waveforms to a Daq module.
        halMessage.addMessage("daq waveform",
                              validator = {"data" : {"waveform" : [True, DaqWaveform]},
                                           "resp" : None})

        
