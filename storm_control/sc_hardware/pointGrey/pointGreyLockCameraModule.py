#!/usr/bin/env python
"""
Point Grey AF Camera functionality.

Hazen 09/19
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.baseClasses.lockModule as lockModule
import storm_control.sc_hardware.pointGrey.pointGreyLockCamera as pointGreyLockCamera


class PGQPDAutoFocusFunctionality(hardwareModule.HardwareFunctionality, lockModule.QPDAutoFocusFunctionalityMixin):
    qpdUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, camera = None, **kwds):
        super().__init__(**kwds)
        self.camera = camera
        self.camera.cameraUpdate.connect(self.handleCameraUpdate)
        self.started = False

    def adjustAOI(self, dx, dy):
        self.camera.adjustAOI(dx, dy)
        
    def adjustZeroDist(self, inc):
        self.camera.adjustZeroDist(inc)

    def handleCameraUpdate(self, qpd_dict):
        #
        # We are bouncing the signal here so that we can adjust the offset value. Like
        # with the Thorlabs cameras this may also improve the update speed, but this
        # was not tested.
        #
        qpd_dict["offset"] = qpd_dict["offset"] * self.units_to_microns
        self.qpdUpdate.emit(qpd_dict)

    def getMinimumInc(self):
        #
        # The minimum step size of AOI adjustments for these cameras is 8 pixels.
        #
        return 8
        
    def getOffset(self):
        #
        # lockControl.LockControl will call this each time the qpdUpdate signal
        # is emitted, but we only want to start the camera once.
        #
        if not self.started:
            self.camera.startCamera()
            self.started = True
            
    def wait(self):
        super().wait()
        self.camera.stopCamera()
            

class PointGreyLockCamera(hardwareModule.HardwareModule):
    """
    HAL module that interfaces with a Point Grey camera (for a focus lock).
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.camera = None
        self.camera_functionality = None

        configuration = module_params.get("configuration")
        uc480Camera.loadDLL(configuration.get("uc480_dll"))

        #
        # This is sort of generalized as at some point we might also want to use these
        # cameras for a QPD style focus lock. In order to do this some work would be
        # required including writing the correct functionality and camera classes
        # specifically for this purpose.
        #
        if (configuration.get("auto_focus", False)):
            self.camera = pointGreyLockCamera.AFLockCamera(camera_id = configuration.get("camera_id"),
                                                           parameters = configuration.get("camera_parameters"))

        self.camera_functionality = PGQPDAutoFocusFunctionality(camera = self.camera)

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
