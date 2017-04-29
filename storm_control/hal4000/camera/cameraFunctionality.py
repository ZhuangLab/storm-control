#!/usr/bin/env python
"""
Provides the functionality of camera. Basically this is everything
another module would need to know to display and/or save the
output of the camera.

Hazen 4/17
"""

import copy

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halFunctionality as halFunctionality


class CameraFunctionality(halFunctionality.HalFunctionality):
    """
    Camera functionality in a form that other modules can interact with. 

    There is one of these per camera and it will exist for the lifetime of 
    HAL. When the camera changes it's parameters a parametersChanged
    signal is emitted.

    During a parameter change feed.feed and display.display disconnect
    from camera functionalities and then request new ones.
    """
    emccdGain = QtCore.pyqtSignal(int)
    newFrame = QtCore.pyqtSignal(object)
    parametersChanged = QtCore.pyqtSignal()
    shutter = QtCore.pyqtSignal(bool)
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    temperature = QtCore.pyqtSignal(dict)

    def __init__(self,
                 camera_name = "",
                 have_emccd = False,
                 have_preamp = False,
                 have_shutter = False,
                 have_temperature = False,
                 is_master = False,
                 parameters = None,
                 **kwds):
        super().__init__(**kwds)

        # The name of the camera (i.e. 'camera1').
        self.camera_name = camera_name

        # This is an EMCCD camera.
        self.have_emccd = have_emccd

        # The camera has adjustable pre-amp gain.
        self.have_preamp = have_preamp

        # The camera has a shutter.
        self.have_shutter = have_shutter

        # The camera has temperature control.
        self.have_temperature = have_temperature

        # The camera provides it own timing.
        self.is_master = is_master

        # Camera parameters.
        self.parameters = parameters

        # Current state of the camera shutter.
        self.shutter_state = False

    def copy(self):
        # Not used, kept because it may be useful for enforcing invalid functionalities?
        return copy.deepcopy(self)

    def getCameraName(self):
        return self.camera_name

    def getChipMax(self):
        xm = self.parameters.get("x_chip")
        ym = self.parameters.get("y_chip")
        return xm if (xm > ym) else ym

    def getChipSize(self):
        return [self.parameters.get("x_chip"),
                self.parameters.get("y_chip")]

    def getFrameCenter(self):
        xc = self.getParameter("x_bin") * (self.getParameter("x_start") + int(0.5 * self.getParameter("x_pixels")))
        yc = self.getParameter("y_bin") * (self.getParameter("y_start") + int(0.5 * self.getParameter("y_pixels")))
        return [xc, yc]
    
    def getFrameMax(self):
        xm = self.getParameter("x_bin") * self.getParameter("x_pixels")
        ym = self.getParameter("y_bin") * self.getParameter("y_pixels")
        return xm if (xm > ym) else ym
    
    def getFrameScale(self):
        return [self.getParameter("x_bin"),
                self.getParameter("y_bin")]

    def getFrameZeroZero(self):
        """
        Where to place the frame in the display.
        """
        zx = self.getParameter("x_bin") * self.getParameter("x_start")
        zy = self.getParameter("y_bin") * self.getParameter("y_start")
        return [zx, zy]

    def getParameter(self, pname):
        return self.parameters.get(pname)

    def getParameterObject(self, pname):
        return self.parameters.getp(pname)

    def getShutterState(self):
        return self.shutter_state
    
    def hasEMCCD(self):
        return self.have_emccd

    def hasParameter(self, pname):
        return self.parameters.has(pname)
        
    def hasPreamp(self):
        return self.have_preamp

    def hasShutter(self):
        return self.have_shutter

    def hasTemperature(self):
        return self.have_temperature

    def isCamera(self):
        return True
    
    def isMaster(self):
        return self.is_master

    def isSaved(self):
        return self.getParameter("saved")

    def setEMCCDGain(self, gain):
        pass

    def toggleShutter(self):
        pass

    def transformChipToFrame(self, cx, cy):
        """
        Go from chip coodinates to frame coordinates. Typically frame 
        will only be part of the camera chip not the entire chip.
        """
        cx -= self.getParameter("x_start")
        cy -= self.getParameter("y_start")
        cx = int(cx/self.getParameter("x_bin"))
        cy = int(cy/self.getParameter("y_bin"))
        return [cx, cy]

