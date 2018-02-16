'''
Ludl (voltage controlled) Z stage functionality

George 02/18
'''

from PyQt5 import QtCore

import storm_control.sc_hardware.baseClasses.voltageZModule as voltageZModule


class LudlVoltageZ(voltageZModule.VoltageZ):
    """
    This is a Mad City Labs stage in analog control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(module_params, qt_settings, **kwds)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.z_stage_functionality = voltageZModule.VoltageZFunctionality(
                  ao_fn = response.getData()["functionality"],
                  parameters = self.configuration.get("parameters"),
                  microns_to_volts = self.configuration.get("microns_to_volts"),
                  invert_signal = True)

