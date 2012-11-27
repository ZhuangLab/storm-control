#!/usr/bin/python
#
# Qt Thread for handling camera data capture and recording. 
# All communication with the camera should go through this 
# class (of which there should only be one instance). This
# is a generic class and should be specialized for control
# of particular camera types.
#
# Hazen 11/09
#

from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

#
# Camera update thread. All camera control is done by this thread.
# Classes for controlling specific cameras should be subclasses
# of this class that implement at least the following methods:
#
# getAcquisitionTimings()
#    Returns the current acquisition timings as a triple:
#    [time, time, time]
#
# initCamera()
#    Initializes the camera.
#
# newParameters()
#    Setup the camera with the new acquisition parameters.
#
# run()
#    This is the main thread loop that gets data from the
#    camera and sends signals to the control program that
#    data is available, etc.
#
# See noneCameraControl.py or andorCameraControl.py for examples.
#
#
# This class generates two kinds of Qt signals:
#
# 1. idleCamera() when the camera has stop acquiring without
#    being explicitly commanded to do so. This happens for
#    example when at the end of a fixed_length acquisition.
#
# 2. newData() when new data has been received from the camera.
#    Data is supplied as a list of frame objects as part of
#    the signal.
#
class CameraControl(QtCore.QThread):
    idleCamera = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(object, int)

    @hdebug.debug
    def __init__(self, parameters, type = "camera1", parent = None):
        QtCore.QThread.__init__(self, parent)

        p = parameters

        # other class initializations
        self.daxfile = 0
        self.filming = 0
        self.forced_idle = False
        self.frame_number = 0
        self.have_paused = 1
        self.key = -1
        self.mode = "run_till_abort"
        self.mutex = QtCore.QMutex()
        self.running = 1
        self.should_acquire = 0
        self.shutter = 0
        self.type = type

        # camera initialization
        self.camera = 0
        self.got_camera = 0
        self.reversed_shutter = 0

        self.initCamera()

    def cameraInit(self):
        self.start(QtCore.QThread.NormalPriority)

    @hdebug.debug
    def closeShutter(self):
        self.shutter = 0

    @hdebug.debug
    def getTemperature(self):
        return [50, "unstable"]

    @hdebug.debug
    def newFilmSettings(self, parameters, filming = 0):
        self.mutex.lock()
        self.parameters = parameters
        p = parameters
        if filming:
            self.acq_mode = p.acq_mode
        else:
            self.acq_mode = "run_till_abort"
        self.frames = []
        self.acquired = 0
        self.filming = filming
        self.mutex.unlock()

    @hdebug.debug
    def openShutter(self):
        self.shutter = 1

    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()

    @hdebug.debug
    def setEMCCDGain(self, gain):
        pass

    @hdebug.debug        
    def startCamera(self, key):
        self.mutex.lock()
        self.frame_number = 0
        self.key = key
        self.should_acquire = 1
        self.mutex.unlock()

    @hdebug.debug
    def startFilm(self, daxfile):
        if daxfile:
            self.daxfile = daxfile
            self.newFilmSettings(self.parameters, filming = 1)
        else:
            self.newFilmSettings(self.parameters)

    @hdebug.debug
    def stopCamera(self):
        self.mutex.lock()
        self.should_acquire = 0
        self.mutex.unlock()

    @hdebug.debug
    def stopThread(self):
        self.running = 0

    @hdebug.debug
    def stopFilm(self):
        self.newFilmSettings(self.parameters)
        self.daxfile = 0

    @hdebug.debug
    def toggleShutter(self):
        if self.shutter:
            self.closeShutter()
            return 0
        else:
            self.openShutter()
            return 1


        
#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

