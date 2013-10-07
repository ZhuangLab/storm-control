#!/usr/bin/python
#
# Camera control specialized for controlling two Andor cameras.
#
# Hazen 12/12
#

from PyQt4 import QtCore
import numpy
import os

# Debugging
import halLib.hdebug as hdebug

import camera.frame as frame
import camera.cameraControl as cameraControl
import andor.andorcontroller as andor

class ACameraControl(cameraControl.CameraControl):
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        cameraControl.CameraControl.__init__(self, parameters, parent)

        self.cameras = [False, False]
        self.frame_number = [0, 0]
        self.reversed_shutter = [False, False]
        self.shutter = [False, False]
        self.initCamera()

    @hdebug.debug
    def closeShutter(self, which_camera):
        self.shutter[which_camera] = False
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter[which_camera]:
                self.cameras[which_camera].openShutter()
            else:
                self.cameras[which_camera].closeShutter()

    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        self.stopCamera()
        if self.got_camera:
            return self.cameras[which_camera].getAcquisitionTimings()
        else:
            return [1.0, 1.0, 1.0]

    @hdebug.debug
    def getTemperature(self, which_camera):
        self.stopCamera()
        if self.got_camera:
            return self.cameras[which_camera].getTemperature()
        else:
            return [50, "unstable"]

    #
    # FIXME:
    #   Update to match andorCameraControl or change both to call the same function..
    #
    @hdebug.debug
    def initCamera(self):
        if not self.cameras[0]:
            if hdebug.getDebug():
                print " Initializing Andor Camera"

            path = "c:/Program Files/Andor iXon/Drivers/"
            driver = "atmcd32d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver)
                return

            path = "c:/Program Files/Andor Solis/"
            driver = "atmcd32d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver)
                return

            path = "c:/Program Files (x86)/Andor Solis/Drivers/"
            driver = "atmcd64d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver)
                return

            print "Can't find Andor Camera drivers"

    @hdebug.debug
    def initCameraHelperFn(self, path, driver):
        andor.loadAndorDLL(path + driver)
        handles = andor.getCameraHandles()
        for i in range(2):
            self.cameras[i] = andor.AndorCamera(path, handles[i])

    @hdebug.debug
    def newFilmSettings(self, parameters, filming = 0):
        self.stopCamera()
        self.mutex.lock()
        self.parameters = parameters
        if self.got_camera:
            if filming:
                self.cameras[0].setACQMode(parameters.acq_mode, number_frames = parameters.frames)
                self.cameras[1].setACQMode("run_till_abort")
            else:
                for i in range(2):
                    self.cameras[i].setACQMode("run_till_abort")

            for i in range(2):
                p = getattr(parameters, "camera" + str(i+1))
                # Due to what I can only assume is a bug in some of the
                # older Andor software you need to reset the frame
                # transfer mode after setting the aquisition mode.
                self.cameras[i].setFrameTransferMode(p.frame_transfer_mode)
                # Set camera fan to low. This is overriden by the off option
                if p.low_during_filming:
                    if filming:
                        self.cameras[i].setFanMode(1) # fan on low
                    else:
                        self.cameras[i].setFanMode(0) # fan on full
                # This is for testing whether the camera fan is shaking the
                # the camera, adding noise to the images.
                if p.off_during_filming:
                    if filming:
                        self.cameras[i].setFanMode(2) # fan off
                    else:
                        self.cameras[i].setFanMode(0) # fan on full

        self.filming = filming
        self.mutex.unlock()

    @hdebug.debug
    def newParameters(self, parameters):
        self.initCamera()
        self.got_camera = True
        for i in range(2):
            p = getattr(parameters, "camera" + str(i+1))
            self.reversed_shutter[i] = p.reversed_shutter
            try:
                if hdebug.getDebug():
                    print "  Setting Read Mode"
                self.cameras[i].setReadMode(4)
                if hdebug.getDebug():
                    print "  Setting Temperature"
                self.cameras[i].setTemperature(p.temperature)
                if hdebug.getDebug():
                    print "  Setting Trigger Mode"
                if p.external_trigger:
                    self.cameras[i].setTriggerMode(p.external_trigger)
                    #self.cameras[1].setFastExtTrigger(1)
                else:
                    self.cameras[i].setTriggerMode(0)
                if hdebug.getDebug():
                    print "  Setting ROI and Binning"
                self.cameras[i].setROIAndBinning(p.ROI, p.binning)
                if hdebug.getDebug():
                    print "  Setting Horizontal Shift Speed"
                self.cameras[i].setHSSpeed(p.hsspeed)
                if hdebug.getDebug():
                    print "  Setting Vertical Shift Amplitude"
                self.cameras[i].setVSAmplitude(p.vsamplitude)
                if hdebug.getDebug():
                    print "  Setting Vertical Shift Speed"
                self.cameras[i].setVSSpeed(p.vsspeed)
                if hdebug.getDebug():
                    print "  Setting EM Gain Mode"
                self.cameras[i].setEMGainMode(p.emgainmode)
                if hdebug.getDebug():
                    print "  Setting EM Gain"
                self.cameras[i].setEMCCDGain(p.emccd_gain)
                if hdebug.getDebug():
                    print "  Setting Baseline Clamp"
                self.cameras[i].setBaselineClamp(p.baselineclamp)
                if hdebug.getDebug():
                    print "  Setting Preamp Gain"
                self.cameras[i].setPreAmpGain(p.preampgain)
                if hdebug.getDebug():
                    print "  Setting Acquisition Mode"
                self.cameras[i].setACQMode("run_till_abort")
                if hdebug.getDebug():
                    print "  Setting Frame Transfer Mode"
                self.cameras[i].setFrameTransferMode(p.frame_transfer_mode)
                if hdebug.getDebug():
                    print "  Setting Exposure Time"
                self.cameras[i].setExposureTime(p.exposure_time)
                if hdebug.getDebug():
                    print "  Setting Kinetic Cycle Time"
                self.cameras[i].setKineticCycleTime(p.kinetic_cycle_time)
                if hdebug.getDebug():
                    print "  Setting ADChannel"
                self.cameras[i].setADChannel(p.adchannel)
                p.head_model = self.cameras[i].getHeadModel()
                if hdebug.getDebug():
                    print " Camera Initialized"
            except:
                #if hdebug.getDebug():
                print "QCameraThread: Bad camera settings"
                self.got_camera = False
        self.newFilmSettings(parameters)

    @hdebug.debug
    def openShutter(self, which_camera):
        self.shutter[which_camera] = True
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter[which_camera]:
                self.cameras[which_camera].closeShutter()
            else:
                self.cameras[which_camera].openShutter()

    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        if self.got_camera:
            for i in range(2):
                self.cameras[i].shutdown()

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.should_acquire and self.got_camera:

                for i in range(2):
                    # Get data from camera and create frame objects.
                    [frames, frame_size, state] = self.cameras[i].getImages16()

                    # Check if we got new frame data.
                    if (len(frames) > 0):

                        #
                        # Create frame objects.
                        # The first camera is considered to be the master camera.
                        #
                        if (i==0):
                            master = True
                        else:
                            master = False
                        frame_data = []
                        for raw_frame in frames:
                            frame_data.append(frame.Frame(numpy.fromstring(raw_frame, dtype = numpy.uint16),
                                                          self.frame_number[i],
                                                          frame_size[0],
                                                          frame_size[1],
                                                          "camera" + str(i+1),
                                                          master))
                            self.frame_number[i] += 1

                        # Save frames if we are filming.
                        if self.filming:
                            for aframe in frame_data:
                                self.daxfile.saveFrame(aframe)

                        # Emit new data signal
                        self.newData.emit(frame_data, self.key)

                    # Emit idle signal if camera 0 is idle.
                    if (i == 0) and (state == "idle"):
                        # Signal that camera 0 is idle, but only once.
                        if not(self.forced_idle):
                            self.idleCamera.emit()
                            self.forced_idle = True

            else:
                self.have_paused = 1
            self.mutex.unlock()
            self.msleep(5)

    @hdebug.debug
    def setEMCCDGain(self, which_camera, gain):
        self.stopCamera()
        if self.got_camera:
            self.cameras[which_camera].setEMCCDGain(gain)

    @hdebug.debug        
    def startCamera(self, key):
        if self.have_paused:
            self.mutex.lock()
            self.key = key
            self.forced_idle = False
            self.frame_number = [0, 0]
            self.should_acquire = 1
            self.have_paused = 0
            if self.got_camera:
                self.cameras[1].startAcquisition()
                self.cameras[0].startAcquisition()
            self.mutex.unlock()

    @hdebug.debug
    def stopCamera(self):
        if self.should_acquire:
            self.mutex.lock()
            self.forced_idle = True
            if self.got_camera:
                self.cameras[0].stopAcquisition()
                self.cameras[1].stopAcquisition()
            self.should_acquire = 0
            self.mutex.unlock()
            while not self.have_paused:
                self.usleep(50)

    @hdebug.debug
    def toggleShutter(self, which_camera):
        if self.shutter[which_camera]:
            self.closeShutter(which_camera)
            return False
        else:
            self.openShutter(which_camera)
            return True
        
#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

