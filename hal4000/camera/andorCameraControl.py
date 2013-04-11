#!/usr/bin/python
#
# Camera control specialized for a Andor camera.
#
# Hazen 11/09
#

from PyQt4 import QtCore
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
        if hasattr(parameters, "pci_card"):
            self.initCamera(parameters.pci_card)
        else:
            self.initCamera()

    @hdebug.debug
    def closeShutter(self):
        self.shutter = 0
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.openShutter()
            else:
                self.camera.closeShutter()

    @hdebug.debug
    def getAcquisitionTimings(self):
        self.stopCamera()
        if self.got_camera:
            return self.camera.getAcquisitionTimings()
        else:
            return [1.0, 1.0, 1.0]

    @hdebug.debug
    def getTemperature(self):
        self.stopCamera()
        if self.got_camera:
            return self.camera.getTemperature()
        else:
            return [50, "unstable"]

    @hdebug.debug
    def initCamera(self, pci_card = 0):
        if not self.camera:
            if hdebug.getDebug():
                print " Initializing Andor Camera"

            path = "c:/Program Files/Andor iXon/Drivers/"
            driver = "atmcd32d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver, pci_card)
                return

            path = "c:/Program Files/Andor Solis/Drivers/"
            driver = "atmcd64d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver, pci_card)
                return

            path = "c:/Program Files/Andor Solis/"
            driver = "atmcd32d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver, pci_card)
                return

            path = "c:/Program Files (x86)/Andor Solis/Drivers/"
            driver = "atmcd64d.dll"
            if os.path.exists(path + driver):
                self.initCameraHelperFn(path, driver, pci_card)
                return

            print "Can't find Andor Camera drivers"

    @hdebug.debug
    def initCameraHelperFn(self, path, driver, pci_card):
        andor.loadAndorDLL(path + driver)
        handle = andor.getCameraHandles()[pci_card]
        self.camera = andor.AndorCamera(path, handle)

    @hdebug.debug
    def newFilmSettings(self, parameters, filming = 0):
        self.stopCamera()
        self.mutex.lock()
        self.parameters = parameters
        p = parameters
        if self.got_camera:
            if filming:
                self.camera.setACQMode(p.acq_mode, number_frames = p.frames)
            else:
                self.camera.setACQMode("run_till_abort")
            # Due to what I can only assume is a bug in some of the
            # older Andor software you need to reset the frame
            # transfer mode after setting the aquisition mode.
            self.camera.setFrameTransferMode(p.frame_transfer_mode)
            # Set camera fan to low. This is overriden by the off option
            if p.low_during_filming:
                if filming:
                    self.camera.setFanMode(1) # fan on low
                else:
                    self.camera.setFanMode(0) # fan on full
            # This is for testing whether the camera fan is shaking the
            # the camera, adding noise to the images.
            if p.off_during_filming:
                if filming:
                    self.camera.setFanMode(2) # fan off
                else:
                    self.camera.setFanMode(0) # fan on full
        self.filming = filming
        self.mutex.unlock()

    @hdebug.debug
    def newParameters(self, parameters):
        self.initCamera()
        p = parameters
        self.reversed_shutter = p.reversed_shutter
        try:
            if hdebug.getDebug():
                print "  Setting Read Mode"
            self.camera.setReadMode(4)
            if hdebug.getDebug():
                print "  Setting Temperature"
            self.camera.setTemperature(p.temperature)
            if hdebug.getDebug():
                print "  Setting Trigger Mode"
            self.camera.setTriggerMode(0)
            if hdebug.getDebug():
                print "  Setting ROI and Binning"
            self.camera.setROIAndBinning(p.ROI, p.binning)
            if hdebug.getDebug():
                print "  Setting Horizontal Shift Speed"
            self.camera.setHSSpeed(p.hsspeed)
            if hdebug.getDebug():
                print "  Setting Vertical Shift Amplitude"
            self.camera.setVSAmplitude(p.vsamplitude)
            if hdebug.getDebug():
                print "  Setting Vertical Shift Speed"
            self.camera.setVSSpeed(p.vsspeed)
            if hdebug.getDebug():
                print "  Setting EM Gain Mode"
            self.camera.setEMGainMode(p.emgainmode)
            if hdebug.getDebug():
                print "  Setting EM Gain"
            self.camera.setEMCCDGain(p.emccd_gain)
            if hdebug.getDebug():
                print "  Setting Baseline Clamp"
            self.camera.setBaselineClamp(p.baselineclamp)
            if hdebug.getDebug():
                print "  Setting Preamp Gain"
            self.camera.setPreAmpGain(p.preampgain)
            if hdebug.getDebug():
                print "  Setting Acquisition Mode"
            self.camera.setACQMode("run_till_abort")
            if hdebug.getDebug():
                print "  Setting Frame Transfer Mode"
            self.camera.setFrameTransferMode(p.frame_transfer_mode)
            if hdebug.getDebug():
                print "  Setting Exposure Time"
            self.camera.setExposureTime(p.exposure_time)
            if hdebug.getDebug():
                print "  Setting Kinetic Cycle Time"
            self.camera.setKineticCycleTime(p.kinetic_cycle_time)
            if hdebug.getDebug():
                print "  Setting ADChannel"
            self.camera.setADChannel(p.adchannel)
            p.head_model = self.camera.getHeadModel()
            if hdebug.getDebug():
                print " Camera Initialized"
            self.got_camera = 1
        except:
            #if hdebug.getDebug():
            print "QCameraThread: Bad camera settings"
            self.got_camera = 0
        self.newFilmSettings(parameters)

    @hdebug.debug
    def openShutter(self):
        self.shutter = 1
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.closeShutter()
            else:
                self.camera.openShutter()

    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        if self.got_camera:
            self.camera.shutdown()

    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.should_acquire and self.got_camera:

                # Get data from camera and create frame objects.
                [frames, frame_size, state] = self.camera.getImages16()

                # Check if we got new frame data.
                if (len(frames) > 0):

                    # Create frame objects.
                    frame_data = []
                    for raw_frame in frames:
                        frame_data.append(frame.Frame(raw_frame,
                                                      self.frame_number,
                                                      frame_size[0],
                                                      frame_size[1],
                                                      "camera1",
                                                      True))
                        self.frame_number += 1

                    # Save frames if we are filming.
                    if self.filming:
                        for aframe in frame_data:
                            self.daxfile.saveFrame(aframe)

                    # Emit new data signal
                    self.newData.emit(frame_data, self.key)

                # Emit idle signal if the camera is idle.
                if (state == "idle"):
                    # Signal that the camera is idle, but only once.
                    if not(self.forced_idle):
                        self.idleCamera.emit()
                        self.forced_idle = True

            else:
                self.have_paused = 1
            self.mutex.unlock()
            self.msleep(5)

    @hdebug.debug
    def setEMCCDGain(self, gain):
        self.stopCamera()
        if self.got_camera:
            self.camera.setEMCCDGain(gain)

    @hdebug.debug        
    def startCamera(self, key):
        if self.have_paused:
            self.mutex.lock()
            self.key = key
            self.forced_idle = False
            self.frame_number = 0
            self.should_acquire = 1
            self.have_paused = 0
            if self.got_camera:
                self.camera.startAcquisition()
            self.mutex.unlock()

    @hdebug.debug
    def stopCamera(self):
        if self.should_acquire:
            self.mutex.lock()
            self.forced_idle = True
            if self.got_camera:
                self.camera.stopAcquisition()
            self.should_acquire = 0
            self.mutex.unlock()
            while not self.have_paused:
                self.usleep(50)

        
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

