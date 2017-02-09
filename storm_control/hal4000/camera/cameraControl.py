#!/usr/bin/env python
"""
Base class for controlling a camera.

See noneCameraControl.py or andorCameraControl.py for specific examples.

Hazen 2/17
"""

from PyQt5 import QtCore

import storm_control.sc_library.parameters as params
import storm_control.hal4000.camera.frame as frame


class CameraControl(QtCore.QThread):
    newFrame = QtCore.pyqtSignal(object, int)

    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Other class initializations
        self.acquire = IdleActive()
        self.frame_number = 0
        self.key = -1
        self.mutex = QtCore.QMutex()
        self.running = True
        self.shutter = False

        # Camera initialization
        self.camera = False
        self.camera_working = False

    def cameraInit(self):
        self.start(QtCore.QThread.NormalPriority)

    def cleanUp(self):
        self.running = False
        self.wait()
        
    def closeShutter(self):
        self.shutter = False

    def getAcquisitionTimings(self):
        """
        Return the time that it takes to capture a frame in seconds.
        """
        return 0.1

    def getShutterState(self, which_camera):
        return self.shutter

#    def getTemperature(self, which_camera, parameters):
#        if (which_camera == "camera1"):
#            temp = [50, "unstable"]
#            parameters.set(which_camera + ".actual_temperature", temp[0])
#            parameters.set(which_camera + ".temperature_control", temp[1])
    def initCamera(self):
        pass

    def newParameters(self, parameters):
        pass

    def openShutter(self):
        self.shutter = True

    def setEMCCDGain(self, which_camera, gain):
        pass

    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.frame_number = 0
        self.key = key
        self.mutex.unlock()

    def startFilm(self, film_settings):
        pass

    def stopCamera(self):
        self.mutex.lock()
        self.acquire.stop()
        self.mutex.unlock()

    def stopFilm(self):
        pass
    
    def toggleShutter(self, which_camera):
        if self.shutter:
            self.closeShutter()
            return False
        else:
            self.openShutter()
            return True


class HWCameraControl(CameraControl):
    """
    This class implements what is common to all of the 'hardware' cameras.
    """
    def cleanUp(self):
        self.stopThread()
        self.wait()
        self.camera.shutdown()

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.camera_working:

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
                    self.newFrame.emit(frame_data, self.key)
            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(5)

    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.key = key
        self.frame_number = 0
        if self.got_camera:
            self.camera.startAcquisition()
        self.mutex.unlock()

    def stopCamera(self):
        if self.acquire.amActive():
            self.mutex.lock()
            if self.got_camera:
                self.camera.stopAcquisition()
            self.acquire.stop()
            self.mutex.unlock()
            while not self.acquire.amIdle():
                self.usleep(50)


class IdleActive(object):
    """
    This class handles signaling between the thread run function and the
    rest of the thread. If "go" then the run method performs the
    requested operations. If "stop" then the run method acknowledges
    that it is idling.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.idling = False
        self.running = False

    def amActive(self):
        """
        Returns true if thread should be operating (as opposed to idling).
        """
        return self.running

    def amIdle(self):
        """
        Returns true if the thread is currently idling.
        """
        return self.idling

    def go(self):
        """
        Tells the thread that it should be operating.
        """
        self.idling = False
        self.running = True

    def idle(self):
        """
        Tells the main process that the thread is idling.
        """
        self.idling = True

    def stop(self):
        """
        Tells the thread that is should stop operating.
        """
        self.running = False


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

