#!/usr/bin/python
#
## @file
#
# Base class for handling the control and display of the
# data from one (or more) cameras.
#
# Classes that sub-class this also need to include a 
# separate function getMode() which should return
# one of the following strings, depending on what sort
# of UI is appropriate for the camera:
# 
# 1. "single" - classic single window HAL UI.
# 2. "detached" - the camera window is separate.
# 3. "dual" - the camera window is separate and there
#             are two cameras.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

## Camera
#
# The generic base class. Classes designed for a particular 
# set-up need to be modified as appropriate.
#
class Camera(QtGui.QDialog):
    reachedMaxFrames = QtCore.pyqtSignal()
    newFrames = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

    ## cameraInit
    #
    # This is called once HAL has finished initializing.
    #
    def cameraInit(self):
        pass

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "newCycleLength"):
                signal[2].connect(self.setSyncMax)

    ## getCameraDisplay
    #
    # Return the camera display frame for the purposes of
    # getting the correct lay-out in classic single camera
    # display mode.
    #
    # @return False, The default camera has no display.
    #
    def getCameraDisplay(self):
        return False

    ## getFilmSize
    #
    # Return the total size of the film(s) the camera(s)
    # is/are taking.
    #
    # Return 0, The default camera cannot record anything.
    #
    def getFilmSize(self):
        return 0

    ## getRecordButton
    #
    # Return the record button. This is a property of the
    # camera display frame, but it is needed by HAL in
    # classic single camera display mode.
    #
    # @return False, The default camera has no record button.
    #
    def getRecordButton(self):
        return False

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return []

    ## newParameters
    #
    # Update camera parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        pass

    ## quit
    #
    # Clean up in preparation for shutting down.
    #
    def quit(self):
        pass

    ## setSyncMax
    #
    # Set the sync max (this is based on the shutters file)
    #
    def setSyncMax(self, sync_max):
        pass

    ## showCamera1
    #
    # Show UI window for camera 1
    #
    # @param boolean Dummy parameter.
    #
    def showCamera1(self, boolean):
        pass

    ## showCamera2
    #
    # Show UI window for camera 2
    #
    # @param boolean Dummy parameter.
    #
    def showCamera2(self, boolean):
        pass

    ## startCamera
    #
    # Start the camera(s).
    #
    def startCamera(self):
        pass

    ## startFilm
    #
    # Setup for recording data from the camera(s) to a file(s).
    #
    # @param writer This is a image writing object (halLib/imagewriters).
    # @param film_setting A film setting object.
    #
    def startFilm(self, writer, film_settings):
        pass

    ## stopCamera
    #
    # Stop the camera(s).
    #
    def stopCamera(self):
        pass

    ## stopFilm
    #
    # Stop recording the camera(s) data.
    #
    def stopFilm(self):
        pass


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

