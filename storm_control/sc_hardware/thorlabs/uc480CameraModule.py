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
        self.scan_thread = UC480ScanThread(camera = self.camera,
                                           device_mutex = self.device_mutex,
                                           qpd_update_signal = self.qpdUpdate,
                                           reps = reps,
                                           units_to_microns = self.units_to_microns)

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
        #
        # lockControl.LockControl will call this each time the qpdUpdate signal
        # is emitted, but we only want the thread to get started once.
        #
        if not self.scan_thread.isRunning():
            self.scan_thread.startScan()

    def wait(self):
        super().wait()
        self.scan_thread.stopScan()


class UC480ScanThread(QtCore.QThread):
    """
    Handles periodic polling of the camera to determine the current offset. 
    In testing this approach appeared more performant than starting a new
    QRunnable for each scan.
    """
    def __init__(self,
                 camera = None,
                 device_mutex = None,
                 qpd_update_signal = None,
                 reps = None,
                 units_to_microns = None,
                 **kwds):
        super().__init__(**kwds)
        self.camera = camera
        self.device_mutex = device_mutex
        self.qpd_update_signal = qpd_update_signal
        self.reps = reps
        self.running = False
        self.units_to_microns = units_to_microns

    def isRunning(self):
        return self.running
        
    def run(self):
        self.running = True
        while(self.running):
            self.device_mutex.lock()
            [power, offset] = self.camera.qpdScan(reps = self.reps)[:2]
            [image, x_off1, y_off1, x_off2, y_off2, sigma] = self.camera.getImage()
            self.device_mutex.unlock()
            self.qpd_update_signal.emit({"is_good" : (power > 0),
                                         "image" : image,
                                         "offset" : offset * self.units_to_microns,
                                         "sigma" : sigma,
                                         "sum" : power,
                                         "x_off1" : x_off1,
                                         "y_off1" : y_off1,
                                         "x_off2" : x_off2,
                                         "y_off2" : y_off2})

    def startScan(self):
        self.start(QtCore.QThread.NormalPriority)

    def stopScan(self):
        self.running = False
        self.wait()
            

class UC480Camera(hardwareModule.HardwareModule):
    """
    HAL module that interfaces with a Thorlabs UC480 camera.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.camera = None
        self.camera_functionality = None

        configuration = module_params.get("configuration")
        uc480Camera.loadDLL(configuration.get("uc480_dll"))

        # Use the storm-analysis project for fitting. This is hopefully both faster
        # and more accurate than the Numpy/Scipy fitter.
        #
        if (configuration.get("use_storm_analysis", False)):
            print("> using storm-analysis for fitting.")
            self.camera = uc480Camera.CameraQPDSAFit(allow_single_fits = configuration.get("allow_single_fits", False),
                                                     background = configuration.get("background"),
                                                     camera_id = configuration.get("camera_id"),
                                                     ini_file = configuration.get("ini_file"),
                                                     offset_file = configuration.get("offset_file"),
                                                     pixel_clock = configuration.get("pixel_clock", 30),
                                                     sigma = configuration.get("sigma"),
                                                     x_width = configuration.get("x_width"),
                                                     y_width = configuration.get("y_width"))
        # Use the Numpy/Scipy fitter.
        else:
            print("> using numpy/scipy for fitting.")
            self.camera = uc480Camera.CameraQPDScipyFit(allow_single_fits = configuration.get("allow_single_fits", False),
                                                        background = configuration.get("background"),
                                                        camera_id = configuration.get("camera_id"),
                                                        ini_file = configuration.get("ini_file"),
                                                        offset_file = configuration.get("offset_file"),
                                                        pixel_clock = configuration.get("pixel_clock", 30),
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
