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


class UC480QPDCameraFunctionality(QtCore.QThread, lockModule.QPDCameraFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, camera = None, reps = None, **kwds):
        super().__init__(**kwds)
        self.camera = camera
        self.device_mutex = QtCore.QMutex()
        self.reps = reps
        self.running = False

        #self.scan_worker = hardwareModule.HardwareWorker(task = self.run,
        #                                                 args = [self.scan, [], self.qpdUpdate])
        #self.scan_worker.setAutoDelete(False)

    def adjustAOI(self, dx, dy):
        return
        self.maybeRun(task = self.camera.adjustAOI,
                      args = [dx, dy])

    def adjustZeroDist(self, inc):
        return
        self.maybeRun(task = self.camera.adjustZeroDist,
                      args = [inc])

    def changeFitMode(self, mode):
        return
        self.mustRun(task = self.camera.changeFitMode,
                     args = [mode])
        
    def getOffset(self):
        if not self.running:
            self.start(QtCore.QThread.NormalPriority)
#        self.startWorker(self.scan_worker)

    def run(self):
        self.running = True
        while(self.running):
            self.device_mutex.lock()
            [power, offset] = self.camera.qpdScan(reps = self.reps)[:2]
            [image, x_off1, y_off1, x_off2, y_off2, sigma] = self.camera.getImage()
            self.device_mutex.unlock()
            self.qpdUpdate.emit({"offset" : offset * self.units_to_microns,
                                 "sum" : power,
                                 "image" : image,
                                 "sigma" : sigma,
                                 "x_off1" : x_off1,
                                 "y_off1" : y_off1,
                                 "x_off2" : x_off2,
                                 "y_off2" : y_off2})

    def wait(self):
        self.running = False
        super().wait()
        

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
