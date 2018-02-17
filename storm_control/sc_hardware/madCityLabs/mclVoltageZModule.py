#!/usr/bin/env python
"""
Mad City Labs (voltage controlled) Z stage functionality.

Hazen 05/17
"""

import storm_control.sc_hardware.baseClasses.voltageZModule as voltageZModule


class MCLVoltageZ(voltageZModule.VoltageZ):
    """
    This is a Mad City Labs stage in analog control mode.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(module_params, qt_settings, **kwds)
