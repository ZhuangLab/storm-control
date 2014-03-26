#!/usr/bin/python
#
## @file
#
# Qt Thread for handling camera data capture and recording. 
# All communication with the camera should go through this 
# class (of which there should only be one instance). This
# is a generic class and should be specialized for control
# of particular camera types.
#
# Hazen 09/13
#

from PyQt4 import QtCore

# Debugging
import sc_library.hdebug as hdebug

## CameraControl
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
# newFilmSettings()
#    Setup the camera to take the appropriate type of film.
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
# 1. reachedMaxFrames() when the camera has acquired the
#    number of frames it was told to acquire by the
#    parameters.frames.
#
# 2. newData() when new data has been received from the camera.
#    Data is supplied as a list of frame objects as part of
#    the signal.
#
class CameraControl(QtCore.QThread):
    reachedMaxFrames = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(object, int)

    ## __init__
    #
    # Create a CameraControl object.
    #
    # @param hardware A hardware object.
    # @param parent (Optional) The PyQt parent of this CameraControl object.
    #
    @hdebug.debug
    def __init__(self, hardware, parent = None):
        QtCore.QThread.__init__(self, parent)

        # other class initializations
        self.acq_mode = "run_till_abort"
        self.acquire = IdleActive()
        self.daxfile = False
        self.filming = False
        self.frame_number = 0
        self.frames_to_take = 0
        self.key = -1
        self.max_frames_sig = SingleShotSignal(self.reachedMaxFrames)
        self.mutex = QtCore.QMutex()
        self.reached_max_frames = False
        self.running = True
        self.shutter = False

        # camera initialization
        self.camera = False
        self.got_camera = False
        self.reversed_shutter = False

    ## cameraInit
    #
    # Starts the camera control thread.
    #
    def cameraInit(self):
        self.start(QtCore.QThread.NormalPriority)

    ## closeShutter
    #
    # Sets the shutter (open) flag to False.
    #
    @hdebug.debug
    def closeShutter(self):
        self.shutter = False

    ## getAcquisitionTimings
    #
    # Returns how fast the camera is running.
    #
    # @return A Python array containing the time it takes to take a frame.
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        return [0.1, 0.1, 0.1]
    
    ## getFilmSize
    #
    # Returns the current size of the film that is being recorded.
    #
    # @return The size of the film (in bytes?).
    #
    def getFilmSize(self):
        film_size = 0
        if self.daxfile:
            self.mutex.lock()
            film_size = self.daxfile.totalFilmSize()
            self.mutex.unlock()
        return film_size

    ## getTemperature
    #
    # Return the default temperature.
    #
    # @return A two element array, [current temperature, "stable" / "unstable"]
    #
    @hdebug.debug
    def getTemperature(self):
        return [50, "unstable"]

    ## haveEMCCD
    #
    # Return if the camera has a EMCCD.
    #
    # @return False, the default is that there is no EMCCD.
    #
    @hdebug.debug
    def haveEMCCD(self):
        return False

    ## havePreamp
    #
    # Return if the camera has a preamp.
    #
    # @return False, the default is that there is no pre-amplifier.
    @hdebug.debug
    def havePreamp(self):
        return False

    ## haveShutter
    #
    # Return if the camera has a shutter.
    #
    # @return False, the default is that there is no temperature.
    @hdebug.debug
    def haveShutter(self):
        return False

    ## haveTemperature
    #
    # Return if the camera can measure its sensor temperature.
    #
    # @return False, the default is that the camera cannot measure it's sensor temperature.
    #
    @hdebug.debug
    def haveTemperature(self):
        return False

    ## initCamera
    #
    # Initializes the camera.
    #
    @hdebug.debug
    def initCamera(self):
        pass

    ## newFilmSettings
    #
    # This is called at the start of a acquisition to get the camera configured properly.
    #
    # @param parameters A parameters object.
    # @param film_settings A film settings object or None.
    #
    @hdebug.debug
    def newFilmSettings(self, parameters, film_settings):
        pass

    ## openShutter
    #
    # Sets the shutter (open) flag to true.
    #
    @hdebug.debug
    def openShutter(self):
        self.shutter = True

    ## quit
    #
    # Stops the camera control thread.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()

    ## setEMCCDGain
    #
    # This is a place-holder, it should be sub-classed to set
    # the EMCCD gain.
    #
    # @param gain The desired EMCCD gain.
    #
    @hdebug.debug
    def setEMCCDGain(self, gain):
        pass

    ## startCamera
    #
    # Starts an acquisition. The key value is used to identify
    # the frames that are associated with current acquisition.
    # This is necessary for multi-process synchronization.
    #
    # @param key The ID number to use for frames in the current acquisition.
    #
    @hdebug.debug        
    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.frame_number = 0
        self.key = key
        self.max_frames_sig.reset()
        self.mutex.unlock()

    ## startFilm
    #
    # This is called prior to startCamera when the acquisition is
    # to be recorded. If daxfile is False then the user has
    # requested to take the film but not to save it.
    #
    # @param daxfile This is a image writing object (halLib/imagewriters).
    # @param film_settings A film settings object.
    #
    @hdebug.debug
    def startFilm(self, daxfile, film_settings):
        if daxfile:
            self.daxfile = daxfile
        self.newFilmSettings(self.parameters, film_settings)

    ## stopCamera
    #
    # Signal the camera control thread to stop the current acquisition.
    #
    @hdebug.debug
    def stopCamera(self):
        self.mutex.lock()
        self.acquire.stop()
        self.mutex.unlock()

    ## stopThread
    #
    # Signal the camera control thread to stop running.
    #
    @hdebug.debug
    def stopThread(self):
        self.running = False

    ## stopFilm
    #
    # This is called when we are done filming.
    #
    @hdebug.debug
    def stopFilm(self):
        self.newFilmSettings(self.parameters, None)
        self.daxfile = False

    ## toggleShutter
    #
    # Open/Close the shutter depending on the shutters current state.
    #
    @hdebug.debug
    def toggleShutter(self):
        if self.shutter:
            self.closeShutter()
            return False
        else:
            self.openShutter()
            return True

## IdleActive
#
# A traffic light class.
#
# This class handles signaling between the thread run function and the
# rest of the thread. If "go" then the run method performs the
# requested operations. If "stop" then the run method acknowledges
# that it is idling.
#
class IdleActive():

    ## __init__
    #
    # Create idleActive object
    #
    def __init__(self):
        self.idling = False
        self.running = False

    ## amActive
    #
    # Returns true if thread should be operating (as opposed to idling).
    #
    # @return True/False should the thread be operating.
    #
    def amActive(self):
        return self.running

    ## amIdle
    #
    # Returns true if the thread is currently idling.
    #
    # @return True/False is the thread idling.
    #
    def amIdle(self):
        return self.idling

    ## go
    #
    # Tells the thread that it should be operating.
    #
    def go(self):
        self.idling = False
        self.running = True

    ## idle
    #
    # Tells the main process that the thread is idling.
    #
    def idle(self):
        self.idling = True

    ## stop
    #
    # Tells the thread that is should stop operating.
    #
    def stop(self):
        self.running = False

## SingleShotSignal
#
# Single shot signal class.
#
# This class creates a signal that needs to be reset each time it is 
# emitted. This is used in the camera control thread, which might
# otherwise signal multiple times that the camera is idle before
# the main process has a chance to respond.
#
class SingleShotSignal():

    ## __init__
    #
    # Create a SingleShotSignal object.
    #
    # @param pyqt_signal The PyQt signal the object should emit.
    #
    def __init__(self, pyqt_signal):
        self.emitted = False
        self.pyqt_signal = pyqt_signal

    ## emit
    #
    # Emit the PyQt signal, but only if it has not already been emitted.
    #
    def emit(self):
        if not self.emitted:
            self.pyqt_signal.emit()
            self.emitted = True

    ## reset
    #
    # Reset the emitted flag so that the signal can be emitted again.
    #
    def reset(self):
        self.emitted = False

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

