#!/usr/bin/python
#
## @file
#
# Camera class for controlling a single "detached" camera.
# The camera has it's own window.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs
import qtdesigner.camera_detached_ui as cameraDetachedUi
import qtdesigner.camera_display_ui as cameraDisplayUi
import qtdesigner.camera_params_detached_ui as cameraParamsUi

import camera.singleCamera as singleCamera
import camera.cameraDisplay as cameraDisplay
import camera.cameraParams as cameraParams

## DetachedSingleCamera
#
# Camera class for the UI of single "detached" camera.
# The camera has it's own window with a shutter button
# and camera parameters, but no record button.
#
class DetachedSingleCamera(singleCamera.SingleCamera):

    ## __init__
    #
    # Create a detached single camera object.
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        singleCamera.SingleCamera.__init__(self, hardware, parameters, parent)

        self.ui = cameraDetachedUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Camera")

        # Set up camera display.
        camera_display_ui = cameraDisplayUi.Ui_Frame()
        self.camera_display = cameraDisplay.CameraDisplay(hardware.display,
                                                          parameters,
                                                          camera_display_ui,
                                                          "camera1",
                                                          show_record_button = False,
                                                          show_shutter_button = True,
                                                          parent = self.ui.cameraFrame)
        layout = QtGui.QGridLayout(self.ui.cameraFrame)
        layout.setMargin(0)
        layout.addWidget(self.camera_display)

        # Set up camera parameters display.
        camera_params_ui = cameraParamsUi.Ui_GroupBox()
        self.camera_params = cameraParams.CameraParams(camera_params_ui,
                                                       parent = self.ui.cameraParamsFrame)

        layout = QtGui.QGridLayout(self.ui.cameraParamsFrame)
        layout.setMargin(0)
        layout.addWidget(self.camera_params)
            
        self.camera_params.showEMCCD(self.camera_control.haveEMCCD())
        self.camera_params.showPreamp(self.camera_control.havePreamp())
        self.camera_params.showTemperature(self.camera_control.haveTemperature())

        # Connect ui elements.
        self.ui.okButton.setText("Close")
        self.ui.okButton.clicked.connect(self.handleOk)

        self.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutter)
        self.camera_params.gainChange.connect(self.handleGainChange)

    ## closeEvent
    #
    # Handles hiding the window when the user presses the X in
    # the upper right corner of the window.
    #
    # @param event The PyQt close event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    ## handleOk
    #
    # Handles when the user presses on the close button.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## showCamera1
    #
    # Handles displaying the UI when the user selects
    # "camera" from the file menu.
    #
    # @param boolean Dummy parameter.
    @hdebug.debug
    def showCamera1(self, boolean):
        self.show()


## ACamera
#
# This is just DetachedSingleCamera in a form so that it can used 
# directly by HAL without needing to be wrapped.
#
class ACamera(DetachedSingleCamera):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        DetachedSingleCamera.__init__(self, hardware, parameters, parent)


## getMode
#
# @return The UI mode to use with this camera.
#
def getMode():
    return "detached"

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

