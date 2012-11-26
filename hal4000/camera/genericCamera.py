#!/usr/bin/python
#
# Base class for handling the control and display of the
# data from one (or more) cameras.
#
# Hazen 11/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

#
# The generic base class. Classes designed for a particular 
# set-up need to be modified as appropriate.
#
class Camera(QtGui.QWidget):
    idleCamera = QtCore.pyqtSignal()
    newFrames = QtCore.pyqtSignal(object)

    @hdebug.debug
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

    # Called once HAL has finished initializing.
    def cameraInit(self):
        pass

    # Return the camera display frame for the purposes of
    # getting the correct lay-out in classic single camera
    # display mode.
    def getCameraDisplay(self):
        return False

    # Return the sub-region of the camera display where the
    # camera images are actually shown. This is used by the
    # misc controls on some setups.
    def getCameraDisplayArea(self):
        return False

    # Return the record button. This is a property of the
    # camera display frame, but it is needed by HAL in
    # classic single camera display mode.
    def getRecordButton(self):
        return False

    # Update camera parameters.
    def newParameters(self, parameters):
        pass

    # Clean up in preparation for shutting down.
    def quit(self):
        pass

    # Set the sync max (this is based on the shutters file)
    def setSyncMax(self, sync_max):
        pass

    # Start the camera(s).
    def startCamera(self):
        pass

    # Setup for recording data from the camera(s) to a file(s).
    def startFilm(self, writer):
        pass

    # Stop the camera(s).
    def stopCamera(self):
        pass

    # Stop recording the camera(s) data.
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

