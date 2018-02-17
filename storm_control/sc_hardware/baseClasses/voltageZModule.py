#!/usr/bin/env python
"""
Voltage controlled Z stage functionality.

Hazen 05/17

George 02/18 - Abstracted from mclVoltageZModule.py
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.daqModule as daqModule
import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class VoltageZFunctionality(hardwareModule.HardwareFunctionality, lockModule.ZStageFunctionalityMixin):
    """
    This supports hardware timed z scans. These work by passing control of the
    analog line that this functionality is using back to the DAQ at the start
    of filming. A focuslock.lockModes.LockMode that uses this should *not* use
    the analog line during filming. We're blocking this by checking if the
    line is being used for filming before we try and set a voltage on it.

    Note: This will remember the current z position at the start of the film
          and return to it at the end of the film, which might not be what
          we want?

    FIXME: The stage will appear to stop moving during filming.
    """
    zStagePosition = QtCore.pyqtSignal(float)

    def __init__(self, invert_signal = False, ao_fn = None, 
            microns_to_volts = None, **kwds):
        super().__init__(**kwds)
        self.ao_fn = ao_fn
        self.film_z = None
        self.maximum = self.getParameter("maximum")
        self.microns_to_volts = microns_to_volts
        self.minimum = self.getParameter("minimum")
        self.invert_signal = invert_signal

        self.ao_fn.filming.connect(self.handleFilming)
        
        self.recenter()

    def getDaqWaveform(self, waveform):
        waveform = waveform * self.microns_to_volts
        if self.invert_signal:
            waveform = 10-waveform
        return daqModule.DaqWaveform(source = self.ao_fn.getSource(),
                                     waveform = waveform)
            
    def goAbsolute(self, z_pos, invert = False):
        if self.ao_fn.amFilming():
            return
        
        if (z_pos < self.minimum):
            z_pos = self.minimum
        if (z_pos > self.maximum):
            z_pos = self.maximum
        self.z_position = z_pos
        if self.invert_signal:
            self.ao_fn.output(10 - self.z_position * self.microns_to_volts)
        else:
            self.ao_fn.output(self.z_position * self.microns_to_volts)
        self.zStagePosition.emit(self.z_position)
        
    def goRelative(self, z_delta):
        z_pos = self.z_position + z_delta
        self.goAbsolute(z_pos)

    def handleFilming(self, filming):
        
        # Record current z position at the start of the film.
        if filming:
            self.film_z = self.z_position

        # Return to the current z position at the end of the film.
        else:
            self.goAbsolute(self.film_z)

    def haveHardwareTiming(self):
        return True


class VoltageZ(hardwareModule.HardwareModule):
    """
    This is a Z-piezo stage in analog control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.z_stage_functionality = None

    def cleanUp(self, qt_settings):
        if self.z_stage_functionality is not None:
            self.z_stage_functionality.goAbsolute(
                    self.z_stage_functionality.getMinimum())
        
    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.z_stage_functionality = VoltageZFunctionality(
                  ao_fn = response.getData()["functionality"],
                  parameters = self.configuration.get("parameters"),
                  microns_to_volts = self.configuration.get("microns_to_volts"))

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(
               m_type = "get functionality",
               data = {"name" : self.configuration.get("ao_fn_name")}))
        
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.z_stage_functionality is not None:
                    message.addResponse(
                        halMessage.HalMessageResponse(source = self.module_name,
                        data = {"functionality" : self.z_stage_functionality}))

