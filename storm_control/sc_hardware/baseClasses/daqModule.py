#!/usr/bin/env python
"""
Basic DAQ module functionality.

Hazen 04/17
"""

import numpy
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_library.halExceptions as halExceptions


class DaqModuleException(halExceptions.HardwareException):
    pass


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

    #
    # If the daq needs this functionality during a film it will send this
    # signal at the start of the film with 'True' and at the end of the
    # film with 'False'.
    #
    # Note that by the time this signal is received this functionality
    # may already be in use by the daq, so at least at the start of filming
    # any modules that use this functionality need to act *before* they
    # get the signal.
    #
    filming = QtCore.pyqtSignal(bool)
    
    def __init__(self, source = None, **kwds):
        super().__init__(**kwds)
        self.am_filming = False
        self.source = source

    def amFilming(self):
        return self.am_filming
        
    def getSource(self):
        return self.source

    def output(self, value):
        if self.am_filming:
            raise DaqModuleException("Attempt to use '" + self.getSource() + "' when it is in use for filming.")

    def setFilming(self, start):
        """
        start is True/False if filming is starting/stopping.
        """
        self.am_filming = start
        self.filming.emit(start)


class DaqModule(hardwareModule.HardwareModule):
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.run_shutters = False

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
            # Let film.film know that it needs to wait for us
            # to get ready before starting the cameras.
            self.sendMessage(halMessage.HalMessage(m_type = "wait for",
                                                   data = {"module names" : ["film"]}))
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
        self.run_shutters = message.getData()["film settings"].runShutters()

        # Sub-classes must provide a "ready to film" response when they
        # are ready to film otherwise film.film will hang.
        if not self.run_shutters:
            self.sendMessage(halMessage.HalMessage(m_type = "ready to film"))

    def stopFilm(self, message):
        self.oversampling = 0
        self.analog_waveforms = []
        self.digital_waveforms = []
