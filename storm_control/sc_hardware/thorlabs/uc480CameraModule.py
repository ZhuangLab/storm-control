#!/usr/bin/env python
"""
UC480 Camera QPD functionality.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule
import storm_control.sc_hardware.thorlabs.uc480Camera as uc480Camera


class UC480QPDCameraFunctionality(hardwareModule.BufferedFunctionality, lockModule.QPDCameraFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, camera = None, reps = None, **kwds):
        super().__init__(**kwds)
        self.camera = camera
        self.reps = reps

    def adjustAOI(self, dx, dy):
        self.maybeRun(task = self.camera.adjustAOI,
                      args = [dx, dy])

    def adjustZeroDist(self, inc):
        self.maybeRun(task = self.camera.adjustZeroDist,
                      args = [inc])

    def changeFitMode(self, mode):
        self.mustRun(task = self.camera.changeFitMode,
                     args = [mode])
        
    def getOffset(self):
        self.mustRun(task = self.scan,
                     ret_signal = self.qpdUpdate)

    def scan(self):
        [power, offset] = self.camera.qpdScan(reps = self.reps)[:2]
        [image, x_off1, y_off1, x_off2, y_off2, sigma] = self.camera.getImage()
        return {"offset" : offset * self.units_to_microns,
                "sum" : power,
                "image" : image,
                "sigma" : sigma,
                "x_off1" : x_off1,
                "y_off1" : y_off1,
                "x_off2" : x_off2,
                "y_off2" : y_off2}


class UC480Camera(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.camera = None
        self.camera_functionality = None

        configuration = module_params.get("configuration")
        uc480Camera.loadDLL(configuration.get("uc480_dll"))
        self.camera = uc480Camera.CameraQPD(background = configuration.get("background"),
                                            camera_id = configuration.get("camera_id"),
                                            ini_file = configuration.get("ini_file"),
                                            offset_file = configuration.get("offset_file"),
                                            sigma = configuration.get("sigma"),
                                            x_width = configuration.get("x_width"),
                                            y_width = configuration.get("y_width"))
        self.camera_functionality = UC480QPDCameraFunctionality(camera = self.camera,
                                                                parameters = configuration.get("parameters"),
                                                                reps = configuration.get("reps", 4),
                                                                units_to_microns = configuration.get("units_to_microns"))

    def cleanUp(self, qt_settings):
        self.camera_functionality.wait()
        self.camera.shutDown()

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.camera_functionality}))

    def processMessage(self, message):
        
        if message.isType("get functionality"):
            self.getFunctionality(message)            
