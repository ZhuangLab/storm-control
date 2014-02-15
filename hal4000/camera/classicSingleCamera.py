#!/usr/bin/python
#
## @file
#
# Camera class for controlling a single (non-detached) camera.
#
# Hazen 12/13
#

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# UIs
import qtdesigner.camera_display_ui as cameraDisplayUi
import qtdesigner.camera_params_ui as cameraParamsUi

import camera.singleCamera as singleCamera
import camera.cameraDisplay as cameraDisplay
import camera.cameraParams as cameraParams


## ClassicSingleCamera
#
# This displays and control a single camera. The display is classic
# in that it is the original HAL configuration, a single window that 
# shows the picture from the camera, along with parameters, film 
# settings, etc.
#
class ClassicSingleCamera(singleCamera.SingleCamera):

    @hdebug.debug
    def __init__(self, hardware, parameters, camera_frame, camera_params_frame, parent = None):
        singleCamera.SingleCamera.__init__(self, hardware, parameters, parent)

        # Set up camera display.
        camera_display_ui = cameraDisplayUi.Ui_Frame()
        self.camera_display = cameraDisplay.CameraDisplay(hardware.display,
                                                          parameters,
                                                          camera_display_ui,
                                                          "camera1",
                                                          show_record_button = True,
                                                          show_shutter_button = self.camera_control.haveShutter(),
                                                          parent = camera_frame)

        layout = QtGui.QGridLayout(camera_frame)
        layout.setMargin(0)
        layout.addWidget(self.camera_display)

        # Set up camera parameters display.
        camera_params_ui = cameraParamsUi.Ui_GroupBox()
        self.camera_params = cameraParams.CameraParams(camera_params_ui,
                                                       parent = camera_params_frame)

        layout = QtGui.QGridLayout(camera_params_frame)
        layout.setMargin(0)
        layout.addWidget(self.camera_params)

        self.camera_params.showEMCCD(self.camera_control.haveEMCCD())
        self.camera_params.showPreamp(self.camera_control.havePreamp())
        self.camera_params.showTemperature(self.camera_control.haveTemperature())

        # Connect ui elements.
        self.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutter)
        self.camera_params.gainChange.connect(self.handleGainChange)


## ACamera
#
# This is just ClassicSingleCamera in a form so that it can used 
# directly by HAL without needing to be wrapped.
#
class ACamera(ClassicSingleCamera):
    @hdebug.debug
    def __init__(self, hardware, parameters, camera_frame, camera_params_frame, parent = None):
        ClassicSingleCamera.__init__(self, hardware, parameters, camera_frame, camera_params_frame, parent)


## getMode
#
# @return The UI mode to use with this camera.
#
def getMode():
    return "single"

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

