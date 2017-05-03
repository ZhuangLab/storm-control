#!/usr/bin/env python
"""
Phresh photonics QPD functionality

Hazen 05/17
"""
import numpy

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class PhreshQPDFunctionality(hardwareModule.BufferedFunctionality, lockModule.QPDFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, ai_fn = None, **kwds):
        super().__init__(**kwds)
        self.ai_fn = ai_fn

    def getOffset(self):
        self.mustRun(task = self.scan,
                     ret_signal = self.qpdUpdate)

    def scan(self):
        qpd_data = self.ai_fn.getData()
        x_minus = numpy.mean(qpd_data[:,0])
        x_plus = numpy.mean(qpd_data[:,1])
        qpd_diff = x_plus - x_minus
        qpd_sum = x_plus + x_minux
        offset = qpd_diff/qpd_sum * self.units_to_microns
        return {"offset" : offset,
                "sum" : qpd_sum,
                "x" : qpd_diff,
                "y" : 0.0}


class PhreshQPDModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")
        self.qpd_functionality = None

    def cleanUp(self, qt_settings):
        if self.qpd_functionality is not None:
            self.qpd_functionality.wait()

    def handleResponse(self, message):
        if message.isType("get functionality"):
            self.qpd_functionality = PhreshQPDFunctionality(ai_fn = response.getData()["functionality"],
                                                            parameters = self.configuration.get("parameters"),
                                                            microns_to_volts = self.configuration.get("microns_to_volts"))

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("ai_fn_name")}))
        
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                if self.qpd_functionality is not None:
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.qpd_functionality}))
