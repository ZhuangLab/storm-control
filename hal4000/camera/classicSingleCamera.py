#!/usr/bin/python
#
# Camera class for controlling a single camera.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

import camera.genericCamera as genericCamera
import camera.cameraDisplay as cameraDisplay
import camera.cameraParams as cameraParams

class ClassicSingleCamera(genericCamera.Camera):

    @hdebug.debug
    def __init__(self, parameters, camera_frame, camera_params_frame, parent = None):
        genericCamera.Camera.__init__(self, parent)

        # Class variables
        self.cycle_length = 1
        self.display_timer = QtCore.QTimer(self)
        self.filming = False
        self.frame = False
        self.key = 0
        self.parameters = parameters

        # Setup camera control & display stuff.
        camera_type = parameters.camera_type.lower()

        cameraControl = __import__('camera.' + camera_type + 'CameraControl', globals(), locals(), [camera_type], -1)
        self.camera_control = cameraControl.ACameraControl(parameters, parent = self)
        self.camera_display = cameraDisplay.CameraDisplay(parameters,
                                                          show_record_button = True,
                                                          show_shutter_button = True,
                                                          parent = camera_frame)
        self.camera_params = cameraParams.CameraParams(parent = camera_params_frame)
            
        # Connect ui elements.
        self.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutter)

        # Connect control and display signal.
        self.camera_control.idleCamera.connect(self.handleIdleCamera)
        self.camera_control.newData.connect(self.handleNewFrames)
        self.camera_display.syncChange.connect(self.handleSyncChange)
        self.camera_params.gainChange.connect(self.handleGainChange)

        # Display timer
        self.display_timer.setInterval(100)
        self.display_timer.timeout.connect(self.displayFrame)

    @hdebug.debug
    def cameraInit(self):
        self.camera_control.cameraInit()

    def displayFrame(self):
        self.camera_display.updateImage(self.frame)

    @hdebug.debug
    def getCameraDisplay(self):
        return self.camera_display

    @hdebug.debug
    def getCameraDisplayArea(self):
        return self.camera_display.camera_widget
    
    @hdebug.debug
    def getRecordButton(self):
        return self.camera_display.getRecordButton()

    @hdebug.debug
    def handleGainChange(self, gain):
        self.stopCamera()
        self.parameters.emccd_gain = gain
        self.camera_control.setEMCCDGain(self.parameters.emccd_gain)
        self.startCamera()

    @hdebug.debug
    def handleIdleCamera(self):
        self.idleCamera.emit()

    def handleNewFrames(self, frames, key):
        if (key == self.key):
            for frame in frames:
                if self.filming:
                    if((frame.number % self.cycle_length) == (self.parameters.sync - 1)):
                        self.frame = frame
                else:
                    self.frame = frame
            self.newFrames.emit(frames)

    @hdebug.debug
    def handleSyncChange(self, sync):
        self.parameters.sync = sync

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        p = self.parameters
        self.camera_control.newParameters(parameters)
        [p.exposure_value, p.accumulate_value, p.kinetic_value] = self.camera_control.getAcquisitionTimings()        
        self.camera_display.newParameters(parameters)
        self.camera_params.newParameters(parameters)

    @hdebug.debug
    def quit(self):
        self.camera_control.quit()

    @hdebug.debug
    def startCamera(self):
        self.key += 1
        self.updateTemperature()
        self.camera_control.startCamera(self.key)
        self.display_timer.start()

    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.cycle_length = sync_max
        self.camera_display.setSyncMax(sync_max)

    @hdebug.debug
    def startFilm(self, writer):
        self.camera_control.startFilm(writer)
        self.camera_display.startFilm()
        self.filming = True

    @hdebug.debug
    def stopCamera(self):
        self.display_timer.stop()
        self.updateTemperature()

    @hdebug.debug
    def stopFilm(self):
        self.camera_control.stopFilm()
        self.camera_display.stopFilm()
        self.filming = False

    @hdebug.debug        
    def toggleShutter(self):
        open = self.camera_control.toggleShutter()
        if open:
            self.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    @hdebug.debug
    def updateTemperature(self):
        cur_temp = self.camera_control.getTemperature()
        self.parameters.actual_temperature = cur_temp[0]
        self.camera_params.newTemperature(cur_temp)

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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

