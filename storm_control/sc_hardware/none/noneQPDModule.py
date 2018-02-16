#!/usr/bin/env python
"""
Emulated QPD functionality

Hazen 04/17
"""
import math
import random
import time

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule


class NoneQPDFunctionality(hardwareModule.BufferedFunctionality, lockModule.QPDFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, noise = 0.0, tilt = 0.0, **kwds):
        super().__init__(**kwds)
        self.first_scan = True
        self.noise = noise
        self.tilt = tilt
        self.xy_stage_fn = None
        self.z_offset = 0.0
        self.z_stage_center = None
        self.z_stage_fn = None
        self.z_stage_max = None
        self.z_stage_min = None

    def getOffset(self):
        self.mustRun(task = self.scan,
                     ret_signal = self.qpdUpdate)

    def scan(self):
        if self.first_scan:
            self.first_scan = False
        else:
            time.sleep(0.1)

        #
        # Determine current z offset. This is the offset of the z stage from
        # it's center position adjusted by xy stage tilt (if any).
        #
        z_offset = 0.0
        if (self.xy_stage_fn is not None) and (self.z_stage_fn is not None):
            z_center = self.z_stage_center
            
            pos_dict = self.xy_stage_fn.getCurrentPosition()
            if pos_dict is not None:
                dx = pos_dict["x"]
                #dy = pos_dict["y"]
                #dd = math.sqrt(dx*dx + dy*dy)
                z_center += self.tilt * dx

            if (z_center > self.z_stage_max):
                z_center = self.z_stage_max
            elif (z_center < self.z_stage_min):
                z_center = self.z_stage_min
                
            z_offset = self.z_stage_fn.getCurrentPosition() - z_center

        if (self.noise > 0.0):
            z_offset += random.gauss(0.0, self.noise)

        power = 600.0 * math.exp(-0.250 * (z_offset * z_offset))
        
        if (power < (0.5 * self.getParameter("sum_warning_low"))):
            z_offset = 0.0
            
        return {"is_good" : True,
                "offset" : z_offset,
                "sum" : power,
                "x" : 100.0 * z_offset,
                "y" : 0.0}

    def setFunctionality(self, name, functionality):
        if (name == "xy_stage"):
            self.xy_stage_fn = functionality
        elif (name == "z_stage"):
            self.z_stage_fn = functionality
            self.z_stage_center = self.z_stage_fn.getCenterPosition()
            self.z_stage_max = self.z_stage_fn.getMaximum()
            self.z_stage_min = self.z_stage_fn.getMinimum()
        else:
            print(">> Warning unknown function", name)

class NoneQPDModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.qpd_functionality = None

        self.configuration = module_params.get("configuration")
        self.qpd_functionality = NoneQPDFunctionality(parameters = self.configuration.get("parameters"),
                                                      noise = self.configuration.get("noise", 0.0),
                                                      tilt = self.configuration.get("tilt", 0.0),
                                                      units_to_microns = self.configuration.get("units_to_microns"))

    def cleanUp(self, qt_settings):
        if self.qpd_functionality is not None:
            self.qpd_functionality.wait()

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.qpd_functionality}))

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.qpd_functionality.setFunctionality(message.getData()["extra data"],
                                                    response.getData()["functionality"])
            
    def processMessage(self, message):

        if message.isType("configure2"):
            #
            # The xy and z stage functionalities are used so that the none focus lock
            # can more realistically simulate the behavior of a real focus lock.
            #
            if self.configuration.has("xy_stage_fn"):
                self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                       data = {"name" : self.configuration.get("xy_stage_fn"),
                                                               "extra data" : "xy_stage"}))

            if self.configuration.has("z_stage_fn"):
                self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                       data = {"name" : self.configuration.get("z_stage_fn"),
                                                               "extra data" : "z_stage"}))

        elif message.isType("get functionality"):
            self.getFunctionality(message)            
