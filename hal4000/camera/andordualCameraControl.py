#!/usr/bin/python
#
## @file
#
# Camera control specialized for controlling two Andor cameras.
#
# Hazen 12/13
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
# The CameraControl class specialized to control two Andor cameras at once.
#
class ACameraControl(cameraControl.CameraControl):

    ## __init__
    #
    # Create a Andor dual camera control object.
    #
    # @param hardware A hardware object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parent = None):
        cameraControl.CameraControl.__init__(self, hardware, parent)

        self.cameras = [False, False]
        self.frame_number = [0, 0]
        self.reversed_shutter = [False, False]
        self.shutter = [False, False]
        self.initCamera()

    ## closeShutter
    #
    # Close the shutter of one of the Andor cameras.
    #
    # @param which_camera Which camera to close the shutter of.
    #
    @hdebug.debug
    def closeShutter(self, which_camera):
        self.shutter[which_camera] = False
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter[which_camera]:
                self.cameras[which_camera].openShutter()
            else:
                self.cameras[which_camera].closeShutter()

    ## getAcquisitionTimings
    #
    # Get the acquisition timings of one of the cameras.
    #
    # @param which_camera Which camera to get the acquisition timings from.
    #
    # @return A python array containing the acquisition timings.
    #
    @hdebug.debug
    def getAcquisitionTimings(self, which_camera):
        self.stopCamera()
        if self.got_camera:
            return self.cameras[which_camera].getAcquisitionTimings()
        else:
            return [1.0, 1.0, 1.0]

    ## getTemperature
    #
    # Get the temperature of one of the cameras.
    #
    # @param which_camera Which camera to get the temperature of.
    #
    @hdebug.debug
    def getTemperature(self, which_camera):
        self.stopCamera()
        if self.got_camera:
            return self.cameras[which_camera].getTemperature()
        else:
            return [50, "unstable"]

    ## haveEMCCD
    #
    # Returns that these are EMCCD cameras.
    #
    # @return True, these are EMCCD cameras.
    #
    @hdebug.debug
    def haveEMCCD(self):
        return True

    ## havePreamp
    #
    # Returns that these cameras have a pre-amplifier.
    #
    # @return True, these cameras have a pre-amplifier.
    #
    @hdebug.debug
    def havePreamp(self):
        return True

    ## haveShutter
    #
    # Returns that these cameras have a shutter.
    #
    # @return True, these cameras have a shutter.
    #
    @hdebug.debug
    def haveShutter(self):
        return True

    ## haveTemperature
    #
    # Returns that these cameras can measure their sensor temperature.
    #
    # @return True, these cameras can measure their sensor temperature.
    #
    @hdebug.debug
    def haveTemperature(self):
        return True

    ## initCamera
    #
    # Find the Andor DLL and open the connections to the cameras.
    #
    # FIXME:
    #   Update to match andorCameraControl or change both to call the same function..
    #
    @hdebug.debug
    def initCamera(self):
        if not self.cameras[0]:
            hdebug.logText(" Initializing Andor Cameras", False)

            if (platform.architecture()[0] == "32bit"):
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
                
            else:
                path = "c:/Program Files/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver)
                    return

                path = "c:/Program Files (x86)/Andor Solis/Drivers/"
                driver = "atmcd64d.dll"
                if os.path.exists(path + driver):
                    self.initCameraHelperFn(path, driver)
                    return

            print "Can't find Andor Camera drivers"

    ## initCameraHelperFn
    #
    # Given the path to the Andor DLL and the name of the DLL, start
    # communication with the two cameras.
    #
    # @param path The path to the Andor DLL.
    # @param driver The name of the Andor DLL.
    #
    @hdebug.debug
    def initCameraHelperFn(self, path, driver):
        andor.loadAndorDLL(path + driver)
        handles = andor.getCameraHandles()
        for i in range(2):
            self.cameras[i] = andor.AndorCamera(path, handles[i])

    ## newFilmSettings
    #
    # This is called at the start of acquisition to configure the cameras correctly.
    #
    # @param parameters The current parameters object.
    # @param film_settings A film settings object or False.
    #
    @hdebug.debug
    def newFilmSettings(self, parameters, film_settings):
        self.stopCamera()
        self.mutex.lock()
        if self.got_camera:
            self.reached_max_frames = False

            if film_settings:
                self.filming = True
                self.acq_mode = film_settings.acq_mode
                self.frames_to_take = film_settings.frames_to_take

                if (self.acq_mode == "fixed_length"):
                    if (self.frames_to_take > 1000):
                        self.cameras[0].setACQMode("run_till_abort")
                    else:
                        self.cameras[0].setACQMode("fixed_length", number_frames = self.frames_to_take)
                else:
                    self.cameras[0].setACQMode("run_till_abort")

                self.cameras[1].setACQMode("run_till_abort")

            else:
                self.filming = False
                self.acq_mode = "run_till_abort"
                for i in range(2):
                    self.cameras[i].setACQMode("run_till_abort")

            for i in range(2):
                p = parameters.get("camera" + str(i+1))
                # Due to what I can only assume is a bug in some of the
                # older Andor software you need to reset the frame
                # transfer mode after setting the aquisition mode.
                self.cameras[i].setFrameTransferMode(p.frame_transfer_mode)
                # Set camera fan to low. This is overriden by the off option
                if p.get("low_during_filming"):
                    if filming:
                        self.cameras[i].setFanMode(1) # fan on low
                    else:
                        self.cameras[i].setFanMode(0) # fan on full
                # This is for testing whether the camera fan is shaking the
                # the camera, adding noise to the images.
                if p.get("off_during_filming"):
                    if filming:
                        self.cameras[i].setFanMode(2) # fan off
                    else:
                        self.cameras[i].setFanMode(0) # fan on full

        self.mutex.unlock()

    ## newParameters
    #
    # Change the camera settings for both cameras.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.initCamera()
        self.got_camera = True
        for i in range(2):
            p = parameters.get("camera" + str(i+1))
            self.reversed_shutter[i] = p.get("reversed_shutter")
            try:
                hdebug.logText("Setting Read Mode", False)
                self.cameras[i].setReadMode(4)

                hdebug.logText("Setting Temperature", False)
                self.cameras[i].setTemperature(p.get("temperature"))
                
                hdebug.logText("Setting Trigger Mode", False)
                if p.external_trigger:
                    self.cameras[i].setTriggerMode(p.get("external_trigger"))
                else:
                    self.cameras[i].setTriggerMode(0)

                hdebug.logText("Setting ROI and Binning", False)
                self.cameras[i].setROIAndBinning(p.get("ROI"), p.get("binning"))

                hdebug.logText("Setting Horizontal Shift Speed", False)
                self.cameras[i].setHSSpeed(p.get("hsspeed"))

                hdebug.logText("Setting Vertical Shift Amplitude", False)
                self.cameras[i].setVSAmplitude(p.get("vsamplitude"))

                hdebug.logText("Setting Vertical Shift Speed", False)
                self.cameras[i].setVSSpeed(p.get("vsspeed"))

                hdebug.logText("Setting EM Gain Mode", False)
                self.cameras[i].setEMGainMode(p.get("emgainmode"))

                hdebug.logText("Setting EM Gain", False)
                self.cameras[i].setEMCCDGain(p.get("emccd_gain"))

                hdebug.logText("Setting Baseline Clamp", False)
                self.cameras[i].setBaselineClamp(p.get("baselineclamp"))

                hdebug.logText("Setting Preamp Gain", False)
                self.cameras[i].setPreAmpGain(p.get("preampgain"))

                hdebug.logText("Setting Acquisition Mode", False)
                self.cameras[i].setACQMode("run_till_abort")

                hdebug.logText("Setting Frame Transfer Mode", False)
                self.cameras[i].setFrameTransferMode(p.get("frame_transfer_mode"))

                hdebug.logText("Setting Exposure Time", False)
                self.cameras[i].setExposureTime(p.get("exposure_time"))

                hdebug.logText("Setting Kinetic Cycle Time", False)
                self.cameras[i].setKineticCycleTime(p.get("kinetic_cycle_time"))

                hdebug.logText("Setting ADChannel", False)
                self.cameras[i].setADChannel(p.get("adchannel"))

                p.head_model = self.cameras[i].getHeadModel()

                hdebug.logText("Camera Initialized", False)
            except:
                hdebug.logText("andordualCameraControl: Bad camera settings")
                print traceback.format_exc()
                self.got_camera = False
        self.newFilmSettings(parameters, False)
        self.parameters = parameters

    ## openShutter
    # 
    # Open the shutter of the specified camera.
    #
    # @param which_camera Which camera to open the shutter of.
    #
    @hdebug.debug
    def openShutter(self, which_camera):
        self.shutter[which_camera] = True
        self.stopCamera()
        if self.got_camera:
            if self.reversed_shutter[which_camera]:
                self.cameras[which_camera].closeShutter()
            else:
                self.cameras[which_camera].openShutter()

    ## quit
    #
    # Stop the camera control thread and shutdown the cameras.
    #
    @hdebug.debug
    def quit(self):
        self.stopThread()
        self.wait()
        if self.got_camera:
            for i in range(2):
                self.cameras[i].shutdown()

    ## run
    #
    # The camera control thread. This gets new frames from the camera,
    # saves them if we are filming and signals the new data to the
    # main process. It also signals if the camera is idle as it might
    # be at the end of a fixed length acquisition.
    #
    def run(self):
        while(self.running):
            self.mutex.lock()
            if self.acquire.amActive() and self.got_camera:

                for i in range(2):
                    # Get data from camera and create frame objects.
                    [frames, frame_size, state] = self.cameras[i].getImages16()

                    # Check if we got new frame data.
                    if (len(frames) > 0):

                        # Create frame objects.
                        # The first camera is considered to be the master camera.
                        if (i==0):
                            master = True
                        else:
                            master = False

                        frame_data = []
                        for raw_frame in frames:
                            aframe = frame.Frame(numpy.fromstring(raw_frame, dtype = numpy.uint16),
                                                 self.frame_number[i],
                                                 frame_size[0],
                                                 frame_size[1],
                                                 "camera" + str(i+1),
                                                 master)
                            frame_data.append(aframe)
                            self.frame_number[i] += 1

                            if self.filming:
                                if self.daxfile:
                                    if (self.acq_mode == "fixed_length"):
                                        if (self.frame_number[i] <= self.frames_to_take):
                                            self.daxfile.saveFrame(aframe)
                                    else:
                                        self.daxfile.saveFrame(aframe)
            
                                if (self.acq_mode == "fixed_length") and (self.frame_number[0] == self.frames_to_take):
                                    self.reached_max_frames = True
                                    break

                        # Emit new data signal.
                        self.newData.emit(frame_data, self.key)

                        # Emit max frames signal.
                        if self.reached_max_frames:
                            self.max_frames_sig.emit()

            else:
                self.acquire.idle()

            self.mutex.unlock()
            self.msleep(5)

    ## setEMCCDGain
    #
    # Set the EMCCDGain of one of the cameras.
    #
    # @param which_camera The camera to set the gain of.
    # @param gain The desired EMCCD gain value for that camera.
    #
    @hdebug.debug
    def setEMCCDGain(self, which_camera, gain):
        self.stopCamera()
        if self.got_camera:
            self.cameras[which_camera].setEMCCDGain(gain)

    ## startCamera
    #
    # Tell the camera control thread to start the cameras. The key 
    # parameter is used to identify frames that came from this acquisition. 
    # This is way to handle thread synchronization issues, the main
    # process ignores frames that do not have the correct key.
    #
    # @param key The ID to use for frames from the current acquisition sequence.
    #
    @hdebug.debug        
    def startCamera(self, key):
        self.mutex.lock()
        self.acquire.go()
        self.key = key
        self.frame_number = [0, 0]
        self.max_frames_sig.reset()
        if self.got_camera:
            self.cameras[1].startAcquisition()
            self.cameras[0].startAcquisition()
        self.mutex.unlock()

    ## stopCamera
    #
    # Tells the camera control thread to stop the cameras.
    #
    @hdebug.debug
    def stopCamera(self):
        if self.acquire.amActive():
            self.mutex.lock()
            if self.got_camera:
                self.cameras[0].stopAcquisition()
                self.cameras[1].stopAcquisition()
            self.acquire.stop()
            self.mutex.unlock()
            while not self.acquire.amIdle():
                self.usleep(50)

    ## toggleShutter
    #
    # Open/close the shutter of the specified camera.
    #
    # @param which_camera The camera to open/close the shutter of.
    #
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

