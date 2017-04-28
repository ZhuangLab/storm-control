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

    def getWaveformLength(self):
        return self.waveform.size
    
    def isAnalog(self):
        return self.is_analog

    
class DaqFunctionality(hardwareModule.HardwareFunctionality):

    def __init__(self, source = None, used_during_filming = True, **kwds):
        super().__init__(**kwds)
        self.source = source
        self.used_during_filming = used_during_filming

    def getSource(self):
        return self.source

    def getUsedDuringFilming(self):
        return self.used_during_filming    


class DaqModule(hardwareModule.HardwareModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)

        # These are the waveforms to output during a film.
        self.analog_waveforms = []
        self.digital_waveforms = []
        
        self.oversampling = 0
        self.waveform_len = 0

        # The message for passing waveforms to a Daq module.
        #
        # FIXME: Replace with a configuration message?
        #
        halMessage.addMessage("daq waveforms",
                              validator = {"data" : {"waveforms" : [True, list]},
                                           "resp" : None})

    def configure1(self, message):
        pass

    def daqWaveforms(self, message):
        waveforms = message.getData()["waveforms"]
        for waveform in waveforms:
            assert isinstance(waveform, DaqWaveform)

            print(waveform.getSource())

            # Check that all the waveforms are the same
            # length with the same oversampling.
            if (self.oversampling == 0):
                self.oversampling = waveform.getOversampling()
                self.waveform_len = waveform.getWaveformLength()
            else:
                assert (self.oversampling == waveform.getOversampling())
                assert (self.waveform_len == waveform.getWaveformLength())
                
            if waveform.isAnalog():
                self.analog_waveforms.append(waveform)
            else:
                self.digital_waveforms.append(waveform)

    def filmTiming(self, message):
        pass

    def getFunctionality(self, message):
        pass
    
    def processMessage(self, message):

        if message.isType("configuration") and message.sourceIs("timing"):
            self.filmTiming(message)
            
        elif message.isType("configure1"):
            self.configure1(message)

        elif message.isType("daq waveforms"):
            self.daqWaveforms(message)

        elif message.isType("get functionality"):
            self.getFunctionality(message)
            
        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

    def startFilm(self, message):
        pass

    def stopFilm(self, message):
        self.oversampling = 0
        self.analog_waveforms = []
        self.digital_waveforms = []
