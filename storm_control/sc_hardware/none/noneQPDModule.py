#!/usr/bin/env python
"""
Emulated QPD functionality

Hazen 04/17
"""
import math
import time

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class NoneQPDFunctionality(hardwareModule.BufferedFunctionality, lockModule.QPDFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)
    _update_ = QtCore.pyqtSignal(list)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.z_offset = 0.0

        self._update_.connect(self.handleUpdate)

    def getOffset(self):
        self.mustRun(task = self.scan,
                     ret_signal = self._update_)

    def handleUpdate(self, qpd_data):
        update_dict = {"offset" : qpd_data[0],
                       "sum" : qpd_data[1],
                       "x" : qpd_data[2],
                       "y" : qpd_data[3]}
        self.qpdUpdate.emit(update_dict)

    def scan(self):
        time.sleep(0.1)
        self.z_offset = 0.01 * math.sin(2.0 * time.time())
        return([self.z_offset, 600.0, 600.0 * self.z_offset, 100.0 * self.z_offset])


class NoneQPDModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.qpd_functionality = None

        configuration = module_params.get("configuration")
        self.qpd_functionality = NoneQPDFunctionality(parameters = configuration.get("parameters"),
                                                      units_to_microns = configuration.get("units_to_microns"))

    def cleanUp(self, qt_settings):
        if self.qpd_functionality is not None:
            self.qpd_functionality.wait()

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.qpd_functionality}))

    def processMessage(self, message):
        
        if message.isType("get functionality"):
            self.getFunctionality(message)            
