#!/usr/bin/env python
"""
Mad City Labs Z stage functionality.

Hazen 05/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageZModule as stageZModule

import storm_control.sc_hardware.madCityLabs.mclController as mclController

class MCLZStageFunctionality(stageZModule.ZStageFunctionality):

    def __init__(self, z_stage = None, **kwds):
        super().__init__(**kwds)

        # FIXME? Query stage for the actual maximum Z?
        self.maximum = self.getParameter("maximum")
        self.minimum = self.getParameter("minimum")

        self.recenter()


class MCLZStage(stageZModule.ZStage):
    """
    This is a Mad City Labs stage in USB control mode.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        serial_number = self.configuration.get("serial_number", 0)
        if (serial_number == 0):
            serial_number = None
        self.z_stage = mclController.MCLStage(mcl_lib = self.configuration.get("mcl_lib"),
                                              serial_number = serial_number)

        if self.z_stage.getStatus():
            self.z_stage_functionality = MCLZStageFunctionality(z_stage = self.z_stage,
                                                                parameters = self.configuration.get("parameters"))
