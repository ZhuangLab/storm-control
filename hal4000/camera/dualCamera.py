#!/usr/bin/python
#
## @file
#
# Basic dual camera control.
#
# Hazen 01/14
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


## CameraDialog
#
# Dialog that displays data from camera1 or 2 and the associated controls
# and camera parameters. Each camera has a shutter button (if relevant),
# but no record button.
#
class CameraDialog(QtGui.QDialog):

    ## __init__
    #
    # Create a camera dialog object.
    #
    # @param display_module The python module that implements the camera display widget.
    # @param parameters A parameters object.
    # @param name The name of to use on the UI window.
    # @param which_camera The camera this window is associated with ("camera1" or "camera2")
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, display_module, parameters, name, which_camera, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = cameraDetachedUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(name)

        # Set up camera display.
        camera_display_ui = cameraDisplayUi.Ui_Frame()
        self.camera_display = cameraDisplay.CameraDisplay(display_module,
                                                          parameters,
                                                          camera_display_ui,
                                                          which_camera,
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

        # Connect ui elements.
        self.ui.okButton.setText("Close")
        self.ui.okButton.clicked.connect(self.handleOk)

    ## closeEvent
    #
    # Handles the user clicking on the "X" to close the window.
    #
    # @param event The PyQt close event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    ## handleOk
    #
    # Handles the user clicking on the close button.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()


## DualCamera
#
# This is the interface between HAL and (1) the camera control object that
# runs both the cameras (2) The UI windows that display the data from
# the cameras & (some of) the current camera parameters.
#
class DualCamera(genericCamera.Camera):

    ## __init__
    #
    # Create a DualCamera object.
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
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
        self.camera1 = CameraDialog(hardware.display,
                                    parameters.camera1,
                                    parameters.setup_name + " Camera1",
                                    "camera1",
                                    parent)

        self.camera2 = CameraDialog(hardware.display,
                                    parameters.camera1,
                                    parameters.setup_name + " Camera2",
                                    "camera2",
                                    parent)

        # Setup camera control.
        cameraControl = __import__('camera.' + hardware.control, globals(), locals(), [hardware.control], -1)
        self.camera_control = cameraControl.ACameraControl(hardware, parent = self)

        self.camera_control.reachedMaxFrames.connect(self.handleMaxFrames)
        self.camera_control.newData.connect(self.handleNewFrames)

        # Setup what is displayed in the parameters. This assumes that the
        # two cameras are more or less identical.
        self.camera1.camera_params.showEMCCD(self.camera_control.haveEMCCD())
        self.camera1.camera_params.showPreamp(self.camera_control.havePreamp())
        self.camera1.camera_params.showTemperature(self.camera_control.haveTemperature())

        self.camera2.camera_params.showEMCCD(self.camera_control.haveEMCCD())
        self.camera2.camera_params.showPreamp(self.camera_control.havePreamp())
        self.camera2.camera_params.showTemperature(self.camera_control.haveTemperature())

        # Connect ui elements.
        self.camera1.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutterCamera1)
        self.camera1.camera_params.gainChange.connect(self.handleGainChangeCamera1)

        self.camera2.camera_display.ui.cameraShutterButton.clicked.connect(self.toggleShutterCamera2)
        self.camera2.camera_params.gainChange.connect(self.handleGainChangeCamera2)

    ## cameraInit
    #
    # Initialize the communication with the two cameras.
    #
    @hdebug.debug
    def cameraInit(self):
        self.camera_control.cameraInit()

    ## getFilmSize
    #
    # Returns the size of the current film.
    #
    # @return The size of the current film (in bytes).
    #
    def getFilmSize(self):
        return self.camera_control.getFilmSize()

    ## handleGainChangeCamera1
    #
    # Handles changing the EMCCD gain of camera 1.
    #
    # @param gain The desired EMCCD gain.
    #
    @hdebug.debug
    def handleGainChangeCamera1(self, gain):
        self.stopCamera()
        self.parameters.camera1.emccd_gain = gain
        self.camera_control.setEMCCDGain(0, self.parameters.camera1.emccd_gain)
        self.startCamera()

    ## handleGainChangeCamera2
    #
    # Handles changing the EMCCD gain of camera 2.
    #
    # @param gain The desired EMCCD gain.
    #
    @hdebug.debug
    def handleGainChangeCamera2(self, gain):
        self.stopCamera()
        self.parameters.camera2.emccd_gain = gain
        self.camera_control.setEMCCDGain(1, self.parameters.camera2.emccd_gain)
        self.startCamera()

    ## handleMaxFrames
    #
    # Handles emitting a signal when the camera has acquired the
    # desired number of frames.
    #
    @hdebug.debug
    def handleMaxFrames(self):
        self.reachedMaxFrames.emit()

    ## handleNewFrames
    #
    # This passes frame data recieved from the camera control to UIs
    # for display. It also passes the frame data up to HAL.
    #
    # @param frames A python array of frame objects.
    # @param key The ID of these frames.
    #
    def handleNewFrames(self, frames, key):
        if (key == self.key):
            self.camera1.camera_display.newFrames(frames)
            self.camera2.camera_display.newFrames(frames)
            self.newFrames.emit(frames)

    ## newParameters
    #
    # Handles a change in acquisition parameters.
    #
    # @param parameters A parameters object.
    #
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

    ## quit
    #
    # Shut down communication with the cameras.
    #
    @hdebug.debug
    def quit(self):
        self.camera_control.quit()

    ## setSyncMax
    #
    # Sets the maximum value for the shutter synchronization element
    # of the camera UIs.
    #
    # @param sync_max The new maximum value for the sync parameter.
    #
    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.cycle_length = sync_max
        self.camera1.camera_display.setSyncMax(sync_max)
        self.camera2.camera_display.setSyncMax(sync_max)

    ## showCamera1
    #
    # Show the UI for camera1. This is called when the user 
    # selects camera1 from the file menu.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def showCamera1(self, boolean):
        self.camera1.show()

    ## showCamera2
    #
    # Show the UI for camera2. This is called when the user
    # selects camera2 from the file menu.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def showCamera2(self, boolean):
        self.camera2.show()

    ## startCamera
    #
    # Tells the camera control object to start the cameras.
    #
    @hdebug.debug
    def startCamera(self):
        self.key += 1
        self.updateTemperature()
        self.camera_control.startCamera(self.key)

    ## startFilm
    #
    # Tells the camera control object to start filming &
    # tells the UIs to update themselves accordingly.
    #
    # @param writer This is a image writing object (halLib/imagewriters).
    # @param film_setting A film setting object.
    #
    @hdebug.debug
    def startFilm(self, writer, film_settings):
        self.camera_control.startFilm(writer, film_settings)
        self.camera1.camera_display.startFilm()
        self.camera2.camera_display.startFilm()
        self.filming = True

    ## stopCamera
    #
    # Tells the camera control object to stop the cameras.
    #
    @hdebug.debug
    def stopCamera(self):
        self.updateTemperature()

    ## stopFilm
    #
    # Tell the camera control object to stop filming &
    # tell the UIs to update themselves accordingly.
    #
    @hdebug.debug
    def stopFilm(self):
        self.camera_control.stopFilm()
        self.camera1.camera_display.stopFilm()
        self.camera2.camera_display.stopFilm()
        self.filming = False

    ## toggleShutterCamera1
    #
    # Toggles the shutter of camera 1.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug        
    def toggleShutterCamera1(self, bool):
        open = self.camera_control.toggleShutter(0)
        if open:
            self.camera1.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera1.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera1.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera1.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    ## toggleShutterCamera2
    #
    # Toggles the shutter of camera 2.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def toggleShutterCamera2(self, bool):
        open = self.camera_control.toggleShutter(1)
        if open:
            self.camera2.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera2.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera2.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera2.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    ## updateTemperature
    #
    # Get the sensor temperature from camera 1 and camera 2 and uses
    # this to update the corresponding UI elements.
    #
    @hdebug.debug
    def updateTemperature(self):
        if self.camera_control.haveTemperature():

            # Get camera1 temperature
            cur_temp = self.camera_control.getTemperature(0)
            self.parameters.camera1.actual_temperature = cur_temp[0]
            self.camera1.camera_params.newTemperature(cur_temp)

            # Get camera2 temperature
            cur_temp = self.camera_control.getTemperature(1)
            self.parameters.camera2.actual_temperature = cur_temp[0]
            self.camera2.camera_params.newTemperature(cur_temp)


## ACamera
#
# This is just DualCamera in a form so that it can used 
# directly by HAL without needing to be wrapped.
#
class ACamera(DualCamera):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        DualCamera.__init__(self, hardware, parameters, parent)


## getMode
#
# @return The UI mode to use with this camera.
#
def getMode():
    return "dual"

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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

