#!/usr/bin/python
#
## @file
#
# Base camera class for controlling a single camera,
# detached or otherwise. This class is missing key
# functionality that must be provided by a sub-class
# to work properly.
#
# Example sub-classes:
#  camera.classicSingleCamera
#  camera.detachedSingleCamera
#
# Note: This should not be confused with the parameter 
# setting "single" which is handled by the sub-class 
# camera.classicSingleCamera.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

import camera.genericCamera as genericCamera

## SingleCamera
#
# This is the interface between HAL and (1) the camera control 
# object that runs the camera (2) the UI window that display 
# the data from the camera & (some of) the current camera 
# parameters.
#
class SingleCamera(genericCamera.Camera):

    ## __init__
    #
    # Create a single camera object.
    #
    # @param hardware A camera hardware object
    # @param parameters A camera parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        genericCamera.Camera.__init__(self, parent)

        # Class variables
        self.cycle_length = 1
        self.filming = False
        self.key = 0
        self.parameters = parameters

        # Setup camera control.
        cameraControl = __import__('camera.' + hardware.control, globals(), locals(), [hardware.control], -1)
        self.camera_control = cameraControl.ACameraControl(hardware, parent = self)

        self.camera_control.reachedMaxFrames.connect(self.handleMaxFrames)
        self.camera_control.newData.connect(self.handleNewFrames)

    ## cameraInit
    #
    # Initialize the camera.
    #
    @hdebug.debug
    def cameraInit(self):
        self.camera_control.cameraInit()

    ## closeEvent
    #
    # Shut down communication with the camera.
    #
    # @param event A QEvent object.
    #
    @hdebug.debug
    def closeEvent(self, event):
        self.camera_control.quit()

    ## getCameraDisplay
    #
    # @return The camera display object.
    #
    @hdebug.debug
    def getCameraDisplay(self):
        return self.camera_display

    ## getCameraDisplayArea
    #
    # @return The UI widget where images from the camera are rendered.
    #
    @hdebug.debug
    def getCameraDisplayArea(self):
        return self.camera_display.camera_widget

    ## getFilmSize
    #
    # @return The size of the current film.
    #
    def getFilmSize(self):
        return self.camera_control.getFilmSize()

    ## getRecordButton
    #
    # @return The record button of the camera display UI.
    #
    @hdebug.debug
    def getRecordButton(self):
        return self.camera_display.getRecordButton()

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [["camera", "cameraROISelection", self.camera_display.cameraROISelection],
                ["camera", "dragStart", self.camera_display.cameraDragStart],
                ["camera", "dragMove", self.camera_display.cameraDragMove]]

    ## handleGainChange
    #
    # Handles changing the EMCCD gain.
    #
    # @param gain The desired EMCCD gain.
    #
    @hdebug.debug
    def handleGainChange(self, gain):
        self.stopCamera()
        self.parameters.emccd_gain = gain
        self.camera_control.setEMCCDGain(self.parameters.emccd_gain)
        self.startCamera()

    ## handleMaxFrames
    #
    # Handles passing the reachedMaxFrames signal through from the
    # camera control object to HAL.
    #
    @hdebug.debug
    def handleMaxFrames(self):
        self.reachedMaxFrames.emit()

    ## handleNewFrames
    #
    # Handles passing the newFrames from the camera control object
    # to camera display object. It also signals the new frames
    # to HAL if they are from the current acquisition.
    #
    # @param frames A python array of frame objects.
    # @param key The ID of the frames from the camera control object.
    #
    def handleNewFrames(self, frames, key):
        if (key == self.key):
            self.camera_display.newFrames(frames)
            self.newFrames.emit(frames)

    ## newParameters
    #
    # Updates the setting of the camera control object, the camera
    # display UI and the camera params UI.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        p = self.parameters
        self.camera_control.newParameters(parameters)
        [p.exposure_value, p.accumulate_value, p.kinetic_value] = self.camera_control.getAcquisitionTimings()        
        self.camera_display.newParameters(parameters)
        self.camera_params.newParameters(parameters)

    ## startCamera
    #
    # Tell the camera control thread to start the camera.
    #
    @hdebug.debug
    def startCamera(self):
        self.key += 1
        self.updateTemperature()
        self.camera_control.startCamera(self.key)

    ## setSyncMax
    #
    # Sets the max for the shutter synchronization spin box element of
    # the camera display UI based the length of the shutter sequence.
    #
    # @param sync_max The maximum value of the synchronization spin box.
    #
    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.cycle_length = sync_max
        self.camera_display.setSyncMax(sync_max)

    ## startFilm
    #
    # Tell the camera control object to start filming. Tell the
    # camera display object to update the UI accordingly.
    #
    # @param writer This is a image writing object (halLib/imagewriters).
    # @param film_setting A film setting object.
    #
    @hdebug.debug
    def startFilm(self, writer, film_settings):
        self.camera_control.startFilm(writer, film_settings)
        self.camera_display.startFilm()
        self.filming = True

    ## stopCamera
    #
    # Tell the camera control object to stop the camera. This is
    # also updates the temperature for those microscopes that
    # support this.
    #
    @hdebug.debug
    def stopCamera(self):
        self.camera_control.stopCamera()
        self.updateTemperature()

    ## stopFilm
    #
    # Tell the camera control object to stop filming. Tell the
    # camera display widget to update it's UI accordingly.
    #
    @hdebug.debug
    def stopFilm(self):
        self.camera_control.stopFilm()
        self.camera_display.stopFilm()
        self.filming = False

    ## toggleShutter
    #
    # Tell the camera control object to toggle the camera shutter. Update
    # the camera_display UI accordingly.
    #
    # FIXME: Instead of updating the UI directly we should make this
    #    a call to a method of the camera display widget.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug        
    def toggleShutter(self, bool):
        open = self.camera_control.toggleShutter()
        if open:
            self.camera_display.ui.cameraShutterButton.setText("Close Shutter")
            self.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.camera_display.ui.cameraShutterButton.setText("Open Shutter")
            self.camera_display.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    ## updateTemperature
    #
    # Get the current temperature from the camera control object. Update
    # the parameters and camera parameters display with this object.
    #
    @hdebug.debug
    def updateTemperature(self):
        if self.camera_control.haveTemperature():
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

