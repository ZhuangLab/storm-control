# George Emanuel
#
# 2015

from PyQt4 import QtCore
import numpy
import os
import sys
import platform
import traceback

# Debugging
import sc_library.hdebug as hdebug

import camera.frame as frame
import camera.cameraControl as cameraControl
import sc_hardware.andor.zylacontroller as zyla

## ACameraControl
#
# The CameraControl class specialized to control a Andor Zyla camera.
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

    ## getAcquisitionTimings
    #
    # Stop the camera and get the acquisition timings (basically the exposure
    #  time)
    #
    @hdebug.debug
    def getAcquisitionTimings(self):
        self.stopCamera()
        if self.got_camera:
            return [self.camera.getExposureTime(), 1.0, 1.0]
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
            return [self.camera.getTemperature(), "unstable"]
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
        return False 

    ## havePreamp
    #
    # Returns that the camera has a pre-amplifier.
    #
    # @return True, this camera has a pre-amplifier.
    #
    @hdebug.debug
    def havePreamp(self):
        return False

    ## haveShutter
    #
    # Returns that the camera has a shutter.
    #
    # @return True, this camera has a shutter.
    #
    @hdebug.debug
    def haveShutter(self):
        return False

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
    # This assumes that the directory containing atcore.dll is
    # C:/Program Files/Andor SDK3/
    # This directory is added to the path so that other required dlls can
    # be found.
    #
    # @param cameraID (Optional) The ID of the camera
    #
    @hdebug.debug
    def initCamera(self, cameraID = 0):
        if not self.camera:
            hdebug.logText("Initializing Andor Camera", False)
	    os.environ['PATH'] = "C:/Program Files/Andor SDK3/" + ';' + os.environ['PATH']
	    zyla.loadZylaDLL()
	    self.camera = zyla.ZylaCamera(cameraID)

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
                        self.camera.setCycleMode("Continuous")
                    else:
                        self.camera.setCycleMode("Fixed") 
			self.camera.setFrameCount(self.frames_to_take)

                else:
                    self.camera.setCycleMode("Continuous")

            else:
                self.filming = False
                self.acq_mode = "run_till_abort"
                self.camera.setCycleMode("Continuous")

            # This is for testing whether the camera fan is shaking the
            # the camera, adding noise to the images.
            if p.get("off_during_filming"):
                if self.filming:
                    self.camera.setFanMode("Off") # fan off
                else:
                    self.camera.setFanMode("On") # fan on full

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
            hdebug.logText("Setting Trigger Mode", False)
            self.camera.setTriggerMode("Internal")

	    self.camera.coolerOn();

            hdebug.logText("Setting ROI and Binning", False)
            cam_roi = p.get("ROI")
            cam_binning = p.get("binning")

            self.camera.setROIAndBinning(cam_roi, cam_binning)

            hdebug.logText("Setting Cycle Mode", False)
            self.camera.setCycleMode("Continuous")

            hdebug.logText("Setting Exposure Time", False)
            self.camera.setExposureTime(p.get("exposure_time"))

            hdebug.logText("Setting Frame Rate", False)
            self.camera.setFrameRate(p.get("frame_rate"))

            p.model = self.camera.getCameraModel()

            hdebug.logText("Camera Initialized", False)
            self.got_camera = True
        except:
            hdebug.logText("andorCameraControl: Bad camera settings")
            print traceback.format_exc()
            self.got_camera = False
        self.newFilmSettings(parameters, None)
        self.parameters = parameters

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

                if (len(frames) > 0):

	            # Create frame objects.
	            frame_data = []

		    for raw_frame in frames:
		        aframe = frame.Frame(numpy.fromstring(raw_frame, 
				             dtype = numpy.uint16),
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
				    if (self.frame_number <= 
						    self.frames_to_take):
					self.daxfile.saveFrame(aframe)
				else:
			            self.daxfile.saveFrame(aframe)

		            if (self.acq_mode == "fixed_length") and (
					    self.frame_number ==
					    self.frames_to_take):
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


