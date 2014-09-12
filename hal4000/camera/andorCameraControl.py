#!/usr/bin/python
#
## @file
#
# Camera control specialized for a Andor camera.
#
# Hazen 10/13
#

from PyQt4 import QtCore
import numpy
import os
import platform
import traceback

# Debugging
import sc_library.hdebug as hdebug

import camera.frame as frame
import camera.cameraControl as cameraControl
import sc_hardware.andor.andorcontroller as andor

## ACameraControl
#
# The CameraControl class specialized to control a Andor camera.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create the CameraControl class.
    #
    # @param hardware Camera hardware settings.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parent = None):
        cameraControl.CameraControl.__init__(self, hardware, parent)
        
        if hasattr(hardware, "pci_card"):
            self.initCamera(hardware.pci_card)
        else:
            self.initCamera()

    ## closeShutter
    #
    # Stop the camera and close the shutter.
    #
    @hdebug.debug
    def closeShutter(self):
        self.shutter = False
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.openShutter()
            else:
                self.camera.closeShutter()

    ## getAcquisitionTimings
    #
    # Stop the camera and get the acquisition timings (basically the frame rate)
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        self.stopCamera()
        if self.got_camera:
            return self.camera.getAcquisitionTimings()
        else:
            return [1.0, 1.0, 1.0]

    ## getTemperature
    #
    # Stop the camera and get the camera temperature.
    #
    @hdebug.debug
    def getTemperature(self):
        self.stopCamera()
        if self.got_camera:
            return self.camera.getTemperature()
        else:
            return [50, "unstable"]

    ## haveEMCCD
    #
    # Returns that this is a EMCCD camera.
    #
    # @return True, this is a EMCCD camera.
    #
    @hdebug.debug
    def haveEMCCD(self):
        return True

    ## havePreamp
    #
    # Returns that the camera has a pre-amplifier.
    #
    # @return True, this camera has a pre-amplifier.
    #
    @hdebug.debug
    def havePreamp(self):
        return True

    ## haveShutter
    #
    # Returns that the camera has a shutter.
    #
    # @return True, this camera has a shutter.
    #
    @hdebug.debug
    def haveShutter(self):
        return True

    ## haveTemperature
    #
    # Returns that this camera can measure its sensor temperature.
    #
    # @return True, this camera can measure its sensor temperature.
    #
    @hdebug.debug
    def haveTemperature(self):
        return True

    ## initCamera
    #
    # This tries to find the right driver file to operate the camera
    # based on the OS type (32 or 64bit) and a search of the common
    # Andor directory names.
    #
    # @param pci_card (Optional) The ID of the PC card to use.
    #
    @hdebug.debug
    def initCamera(self, pci_card = 0):
        if not self.camera:
            hdebug.logText("Initializing Andor Camera", False)

            if (platform.architecture()[0] == "32bit"):
                path = "c:/Program Files/Andor Solis/"
                driver = "atmcd32d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files/Andor iXon/Drivers/"
                driver = "atmcd32d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

            else:
                path = "c:/Program Files/Andor Solis/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

                path = "c:/Program Files (x86)/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver, pci_card)
                    return

            hdebug.logText("Can't find Andor Camera drivers")

    ## initCameraHelperFn
    #
    # Given the path, driver and pci_card ID this creates a Andor
    # camera controller class.
    #
    # @param path The path to the Andor camera DLL.
    # @param driver The name of the Andor camera DLL.
    # @param pci_card The ID of the PCI card.
    #
    @hdebug.debug
    def initCameraHelperFn(self, path, driver, pci_card):
        andor.loadAndorDLL(path + driver)
        handle = andor.getCameraHandles()[pci_card]
        self.camera = andor.AndorCamera(path, handle)

    ## newFilmSettings
    #
    # This is called at the start of a acquisition to get the camera
    # running in the right mode (fixed length or run till abort) and
    # to set the camera fan speed. Fixed length is only used for films
    # that are less than 1000 frames in length, otherwise they are
    # generally too large to easily store in RAM.
    #
    # @param parameters The current camera settings object.
    # @param film_settings A film settings object or None.
    #
    @hdebug.debug
    def newFilmSettings(self, parameters, film_settings):
        self.stopCamera()
        self.mutex.lock()
        p = parameters
        if self.got_camera:
            self.reached_max_frames = False

            if film_settings:
                self.filming = True
                self.acq_mode = film_settings.acq_mode
                self.frames_to_take = film_settings.frames_to_take

                if (self.acq_mode == "fixed_length"):

                    # If the film is really long then we use a software stop, otherwise 
                    # we tell the camera to take the number of frames that was requested.
                    if (self.frames_to_take > 1000):
                        self.camera.setACQMode("run_till_abort")
                    else:
                        self.camera.setACQMode("fixed_length", number_frames = self.frames_to_take)

                else:
                    self.camera.setACQMode("run_till_abort")

            else:
                self.filming = False
                self.acq_mode = "run_till_abort"
                self.camera.setACQMode("run_till_abort")

            # Due to what I can only assume is a bug in some of the
            # older Andor software you need to reset the frame
            # transfer mode after setting the aquisition mode.
            self.camera.setFrameTransferMode(p.frame_transfer_mode)

            # Set camera fan to low. This is overriden by the off option
            if p.get("low_during_filming"):
                if self.filming:
                    self.camera.setFanMode(1) # fan on low
                else:
                    self.camera.setFanMode(0) # fan on full

            # This is for testing whether the camera fan is shaking the
            # the camera, adding noise to the images.
            if p.get("off_during_filming"):
                if self.filming:
                    self.camera.setFanMode(2) # fan off
                else:
                    self.camera.setFanMode(0) # fan on full

        self.mutex.unlock()

    ## newParameters
    #
    # Called when the user selects a new parameters file.
    #
    # @param parameters The new parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        #self.initCamera()
        p = parameters
        self.reversed_shutter = p.get("reversed_shutter")
        try:
            hdebug.logText("Setting Read Mode", False)
            self.camera.setReadMode(4)

            hdebug.logText("Setting Temperature", False)
            self.camera.setTemperature(p.get("temperature"))

            hdebug.logText("Setting Trigger Mode", False)
            self.camera.setTriggerMode(0)

            hdebug.logText("Setting ROI and Binning", False)
            self.camera.setROIAndBinning(p.get("ROI"), p.get("binning"))

            hdebug.logText("Setting Horizontal Shift Speed", False)
            self.camera.setHSSpeed(p.get("hsspeed"))

            hdebug.logText("Setting Vertical Shift Amplitude", False)
            self.camera.setVSAmplitude(p.get("vsamplitude"))

            hdebug.logText("Setting Vertical Shift Speed", False)
            self.camera.setVSSpeed(p.get("vsspeed"))

            hdebug.logText("Setting EM Gain Mode", False)
            self.camera.setEMGainMode(p.get("emgainmode"))

            hdebug.logText("Setting Advanced EM Gain Control", False)
            self.camera.setEMAdvanced(p.get("emccd_advanced", False))

            hdebug.logText("Setting EM Gain", False)
            self.camera.setEMCCDGain(p.get("emccd_gain"))

            hdebug.logText("Setting Baseline Clamp", False)
            self.camera.setBaselineClamp(p.get("baselineclamp"))

            hdebug.logText("Setting Preamp Gain", False)
            self.camera.setPreAmpGain(p.get("preampgain"))

            hdebug.logText("Setting Acquisition Mode", False)
            self.camera.setACQMode("run_till_abort")

            hdebug.logText("Setting Frame Transfer Mode", False)
            self.camera.setFrameTransferMode(p.get("frame_transfer_mode"))

            hdebug.logText("Setting Exposure Time", False)
            self.camera.setExposureTime(p.get("exposure_time"))

            hdebug.logText("Setting Kinetic Cycle Time", False)
            self.camera.setKineticCycleTime(p.get("kinetic_cycle_time"))

            hdebug.logText("Setting ADChannel", False)
            self.camera.setADChannel(p.get("adchannel"))

            p.head_model = self.camera.getHeadModel()

            [p.em_gain_low, p.em_gain_high] = self.camera.getEMGainRange()

            hdebug.logText("Camera Initialized", False)
            self.got_camera = True
        except:
            hdebug.logText("andorCameraControl: Bad camera settings")
            print traceback.format_exc()
            self.got_camera = False
        self.newFilmSettings(parameters, None)
        self.parameters = parameters

    ## openShutter
    #
    # Stops the camera and opens the camera shutter.
    #
    @hdebug.debug
    def openShutter(self):
        self.shutter = True
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter:
                self.camera.closeShutter()
            else:
                self.camera.openShutter()

    ## quit
    #
    # Stops the camera thread and closes the connection to the camera.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        if self.got_camera:
            self.camera.shutdown()

    ## run
    #
    # This is the thread loop that handles getting the new frames from 
    # the camera, saving them in filming mode and signaling that the
    # camera has new data, or that the camera is idle.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:

                # Get data from camera and create frame objects.
                [frames, frame_size, state] = self.camera.getImages16()

                # Check if we got new frame data.
                if (len(frames) > 0):

                    # Create frame objects.
                    frame_data = []
                    for raw_frame in frames:
                        aframe = frame.Frame(numpy.fromstring(raw_frame, dtype = numpy.uint16),
                                             self.frame_number,
                                             frame_size[0],
                                             frame_size[1],
                                             "camera1",
                                             True)
                        frame_data.append(aframe)
                        self.frame_number += 1

                        if self.filming:
                            if self.daxfile:
                                if (self.acq_mode == "fixed_length"):
                                    if (self.frame_number <= self.frames_to_take):
                                        self.daxfile.saveFrame(aframe)
                                else:
                                    self.daxfile.saveFrame(aframe)
            
                            if (self.acq_mode == "fixed_length") and (self.frame_number == self.frames_to_take):
                                self.reached_max_frames = True
                                break
                            
                    # Emit new data signal.
                    self.newData.emit(frame_data, self.key)

                    # Emit max frames signal.
                    #
                    # The signal is emitted here because if it is emitted before
                    # newData then you never see that last frame in the movie, which
                    # is particularly problematic for single frame movies.
                    #
                    if self.reached_max_frames:
                        self.max_frames_sig.emit()

            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(5)

    ## setEMCCDGain
    #
    # Set the EMCCD gain of the camera.
    #
    # @param gain The desired EMCCD gain value.
    #
    @hdebug.debug
    def setEMCCDGain(self, gain):
        self.stopCamera()
        if self.got_camera:
            self.camera.setEMCCDGain(gain)

    ## startCamera
    #
    # Start a new camera acquisition. The key parameter is to
    # ensure that camera frames taken with older parameters
    # are ignored. This can be a problem due to thread
    # synchronization issues.
    #
    # @param key The ID to use for the frames from this acquisition series.
    #
    @hdebug.debug        
    def startCamera(self, key):
        #if self.have_paused:
        self.mutex.lock()
        self.acquire.go()
        self.key = key
        self.frame_number = 0
        self.max_frames_sig.reset()
        if self.got_camera:
            self.camera.startAcquisition()
        self.mutex.unlock()

    ## stopCamera
    #
    # Stop the current acquisition series.
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

