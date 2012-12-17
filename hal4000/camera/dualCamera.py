#!/usr/bin/python
#
# Dual camera control.
#
# Hazen 12/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs
import qtdesigner.camera_detached_ui as cameraDetachedUi
import qtdesigner.camera_display_ui as cameraDisplayUi
import qtdesigner.camera_params_detached_ui as cameraParamsUi

import camera.genericCamera as genericCamera
import camera.cameraDisplay as cameraDisplay
import camera.cameraParams as cameraParams

#
# Dialog that displays data from camera1/2 & and associated controls.
#
class CameraDialog(QtGui.QDialog):
    
    @hdebug.debug
    def __init__(self, parameters, name, which_camera, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = cameraDetachedUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(name)

        camera_display_ui = cameraDisplayUi.Ui_Frame()
        self.camera_display = cameraDisplay.CameraDisplay(parameters,
                                                          camera_display_ui,
                                                          which_camera,
                                                          show_record_button = False,
                                                          show_shutter_button = True,
                                                          parent = self.ui.cameraFrame)

        camera_params_ui = cameraParamsUi.Ui_GroupBox()
        self.camera_params = cameraParams.CameraParams(camera_params_ui,
                                                       parent = self.ui.cameraParamsFrame)

        layout = QtGui.QGridLayout(self.ui.cameraParamsFrame)
        layout.setMargin(0)
        layout.addWidget(self.camera_params)
            
        # Connect ui elements.
        self.ui.okButton.setText("Close")
        self.ui.okButton.clicked.connect(self.handleOk)

    @hdebug.debug
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    @hdebug.debug
    def handleOk(self):
        self.hide()


#
# Interface between the cameras and HAL.
#
class DualCamera(genericCamera.Camera):

    @hdebug.debug
    def __init__(self, parameters, parent = None):
        genericCamera.Camera.__init__(self, parent)
        self.hide()

        # Class variables
        self.cycle_length = 1
        self.filming = False
        self.frame_cam1 = False
        self.frame_cam2 = False
        self.key = 0
        self.parameters = parameters

        # Setup UI
        self.camera1 = CameraDialog(parameters.camera1,
                                    parameters.setup_name + " Camera1",
                                    "camera1",
                                    parent)

        self.camera2 = CameraDialog(parameters.camera1,
                                    parameters.setup_name + " Camera2",
                                    "camera2",
                                    parent)

        # Setup camera control.
        camera_type = parameters.camera1.camera_type.lower()

        cameraControl = __import__('camera.' + camera_type + 'CameraControl', globals(), locals(), [camera_type], -1)
        self.camera_control = cameraControl.ACameraControl(parameters, parent = self)

        self.camera_control.idleCamera.connect(self.handleIdleCamera)
        self.camera_control.newData.connect(self.handleNewFrames)

        # Connect ui elements.
        self.camera1.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutterCamera1)
        self.camera1.camera_params.gainChange.connect(self.handleGainChangeCamera1)

        self.camera2.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutterCamera2)
        self.camera2.camera_params.gainChange.connect(self.handleGainChangeCamera2)

    @hdebug.debug
    def cameraInit(self):
        self.camera_control.cameraInit()

    @hdebug.debug
    def handleGainChangeCamera1(self, gain):
        self.stopCamera()
        self.parameters.camera1.emccd_gain = gain
        self.camera_control.setEMCCDGain(0, self.parameters.camera1.emccd_gain)
        self.startCamera()

    @hdebug.debug
    def handleGainChangeCamera2(self, gain):
        self.stopCamera()
        self.parameters.camera2.emccd_gain = gain
        self.camera_control.setEMCCDGain(1, self.parameters.camera2.emccd_gain)
        self.startCamera()

    @hdebug.debug
    def handleIdleCamera(self):
        self.idleCamera.emit()

    def handleNewFrames(self, frames, key):
        if (key == self.key):
            self.camera1.camera_display.newFrames(frames)
            self.camera2.camera_display.newFrames(frames)
            self.newFrames.emit(frames)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        p = self.parameters
        self.camera_control.newParameters(parameters)

        #
        # These values are used by the shutterControl class to figure out how fast 
        # to run the shutter timers. As written the shutters are driven by camera1.
        #
        [p.exposure_value, p.accumulate_value, p.kinetic_value] = self.camera_control.getAcquisitionTimings(0)

        [p.camera1.exposure_value, p.camera1.accumulate_value, p.camera1.kinetic_value] = self.camera_control.getAcquisitionTimings(0)
        self.camera1.camera_display.newParameters(parameters.camera1)
        self.camera1.camera_params.newParameters(parameters.camera1)

        [p.camera2.exposure_value, p.camera2.accumulate_value, p.camera2.kinetic_value] = self.camera_control.getAcquisitionTimings(1)
        self.camera2.camera_display.newParameters(parameters.camera2)
        self.camera2.camera_params.newParameters(parameters.camera2)

    @hdebug.debug
    def quit(self):
        self.camera_control.quit()

    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.cycle_length = sync_max
        self.camera1.camera_display.setSyncMax(sync_max)
        self.camera2.camera_display.setSyncMax(sync_max)

    @hdebug.debug
    def showCamera1(self):
        self.camera1.show()

    @hdebug.debug
    def showCamera2(self):
        self.camera2.show()
    
    @hdebug.debug
    def startCamera(self):
        self.key += 1
        self.updateTemperature()
        self.camera_control.startCamera(self.key)

    @hdebug.debug
    def startFilm(self, writer):
        self.camera_control.startFilm(writer)
        self.camera1.camera_display.startFilm()
        self.camera2.camera_display.startFilm()
        self.filming = True

    @hdebug.debug
    def stopCamera(self):
        self.updateTemperature()

    @hdebug.debug
    def stopFilm(self):
        self.camera_control.stopFilm()
        self.camera1.camera_display.stopFilm()
        self.camera2.camera_display.stopFilm()
        self.filming = False

    @hdebug.debug        
    def toggleShutterCamera1(self):
        open = self.camera_control.toggleShutter(0)
        if open:
            self.camera1.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera1.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera1.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera1.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    @hdebug.debug        
    def toggleShutterCamera2(self):
        open = self.camera_control.toggleShutter(1)
        if open:
            self.camera2.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera2.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera2.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera2.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    @hdebug.debug
    def updateTemperature(self):

        # Get camera1 temperature
        cur_temp = self.camera_control.getTemperature(0)
        self.parameters.camera1.actual_temperature = cur_temp[0]
        self.camera1.camera_params.newTemperature(cur_temp)

        # Get camera2 temperature
        cur_temp = self.camera_control.getTemperature(1)
        self.parameters.camera2.actual_temperature = cur_temp[0]
        self.camera2.camera_params.newTemperature(cur_temp)

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

