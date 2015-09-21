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
# Hazen 09/15
#

from PyQt4 import QtCore

# Debugging
import sc_library.hdebug as hdebug

import camera.frame as frame

## CameraControl
#
# Camera update thread. All camera control is done by this thread.
# Classes for controlling specific cameras should be subclasses
# of this class that implement at least the following methods:
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
        self.acquire = IdleActive()
        self.frame_number = 0
        self.key = -1
        self.mutex = QtCore.QMutex()
        self.parameters = None
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
    # @param which_camera The camera to get the timing information for.
    #
    # @return A Python array containing the time it takes to take a frame.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        return [0.1, 0.1]

    ## getNumberOfCameras
    #
    # @return The number of cameras that this module controls.
    #
    @hdebug.debug
    def getNumberOfCameras(self):
        return 1
    
    ## getProperties
    #
    # @return The properties of the cameras as a dict.
    #
    @hdebug.debug
    def getProperties(self):
        return {"camera1" : frozenset()}

    ## getShutterStage
    #
    # @return The current state of the shutter (True - Open, False - Closed).
    #
    @hdebug.debug
    def getShutterState(self, which_camera):
        return self.shutter

    ## getTemperature
    #
    # Get the current camera temperature.
    #
    # @param which_camera Which camera to get the temperature of.
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def getTemperature(self, which_camera, parameters):
        if (which_camera == "camera1"):
            temp = [50, "unstable"]
            parameters.set(which_camera + ".actual_temperature", temp[0])
            parameters.set(which_camera + ".temperature_control", temp[1])
            
    ## initCamera
    #
    # Initializes the camera.
    #
    @hdebug.debug
    def initCamera(self):
        pass

    ## newParameters
    #
    # Update the camera based on a new set of parameters.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
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
    # @param which_camera The camera to set the gain of.
    # @param gain The desired EMCCD gain.
    #
    @hdebug.debug
    def setEMCCDGain(self, which_camera, gain):
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
        self.mutex.unlock()

    ## startFilm
    #
    # Called before filming in case the camera needs to do any setup.
    #
    # @param film_settings A film settings object.
    #
    @hdebug.debug
    def startFilm(self, film_settings):
        pass

    ## stopCamera
    #
    # Signal the camera control thread to stop the current acquisition.
    #
    @hdebug.debug
    def stopCamera(self):
        self.mutex.lock()
        self.acquire.stop()
        self.mutex.unlock()
        
    ## stopFilm
    #
    # Called before filming in case the camera needs to do any teardown.
    #
    @hdebug.debug
    def stopFilm(self):
        pass
    
    ## stopThread
    #
    # Signal the camera control thread to stop running.
    #
    @hdebug.debug
    def stopThread(self):
        self.running = False

    ## toggleShutter
    #
    # Open/Close the shutter depending on the shutters current state.
    #
    # @param which_camera The camera to open the shutter of.
    #
    @hdebug.debug
    def toggleShutter(self, which_camera):
        if self.shutter:
            self.closeShutter()
            return False
        else:
            self.openShutter()
            return True


## HWCameraControl
#
# This class implements what is common to all of the "hardware"
# cameras.
#
class HWCameraControl(CameraControl):

    ## quit
    #
    # Stops the camera thread and shuts down the camera.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        self.camera.shutdown()

    ## run
    #
    # The camera thread. This gets images from the camera, turns
    # them into frames and sends them out using the newData signal.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:

                # Get data from camera and create frame objects.
                [frames, frame_size] = self.camera.getFrames()

                # Check if we got new frame data.
                if (len(frames) > 0):

                    # Create frame objects.
                    frame_data = []
                    for cam_frame in frames:
                        aframe = frame.Frame(cam_frame.getData(),
                                             self.frame_number,
                                             frame_size[0],
                                             frame_size[1],
                                             "camera1",
                                             True)
                        frame_data.append(aframe)
                        self.frame_number += 1
                            
                    # Emit new data signal.
                    self.newData.emit(frame_data, self.key)
            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(5)

    ## startCamera
    #
    # Start the camera. The key parameter is for synchronizing the main
    # process and the camera thread.
    #
    # @param key The ID value to use for frames from the current acquisition.
    #
    @hdebug.debug        
    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.key = key
        self.frame_number = 0
        if self.got_camera:
            self.camera.startAcquisition()
        self.mutex.unlock()

    ## stopCamera
    #
    # Stops the camera
    #
    @hdebug.debug
    def stopCamera(self):
        if self.acquire.amActive():
            self.mutex.lock()
            if self.got_camera:
                self.camera.stopAcquisition()
            self.acquire.stop()
            self.mutex.unlock()
            while not self.acquire.amIdle():
                self.usleep(50)


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


#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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

