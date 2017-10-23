#!/usr/bin/env python
"""
Base class for controlling a camera.

See noneCameraControl.py or andorCameraControl.py for specific examples.

Note that "slave" cameras are assumed to always be hardware timed.

Hazen 2/17
"""

from PyQt5 import QtCore
import time

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.frame as frame


class CameraException(halExceptions.HardwareException):
    pass


class CameraControl(QtCore.QThread):
    newData = QtCore.pyqtSignal(object)

    def __init__(self, camera_name = None, config = None, **kwds):
        """
        camera_name - This is the name of this camera's section in the config XML file.        
        config - These are the values in the parameters section as a StormXMLObject().
        """
        super().__init__(**kwds)

        # This is the hardware module that will actually control the camera.
        self.camera = None

        # Sub-classes should set this to a CameraFunctionality object.
        self.camera_functionality = None

        self.camera_name = camera_name

        # This is a flag for whether or not the camera is in a working state.
        # It might not be if for example the parameters were bad.
        self.camera_working = True

        # The length of a fixed length film.
        self.film_length = None
        
        # The current frame number, this gets reset by startCamera().
        self.frame_number = 0

        # The camera parameters.
        self.parameters = params.StormXMLObject()

        # This is how we tell the thread that is handling actually talking
        # to the camera hardware to stop.
        self.running = False

        # This is how we know that the camera thread that is talking to the
        # camera actually started.
        self.thread_started = False

        #
        # These are the minimal parameters that every camera must provide
        # to work with HAL.
        #

        # The exposure time.
        self.parameters.add(params.ParameterFloat(description = "Exposure time (seconds)", 
                                                  name = "exposure_time", 
                                                  value = 1.0))
        
        # This is frames per second as reported by the camera. It is used
        # for hardware timed waveforms (if any).
        self.parameters.add(params.ParameterFloat(name = "fps",
                                                  value = 0,
                                                  is_mutable = False))

        #
        # Chip size, ROI of the chip and the well depth.
        #
        x_size = 256
        y_size = 256
        self.parameters.add(params.ParameterInt(name = "x_chip",
                                                value = x_size,
                                                is_mutable = False,
                                                is_saved = False))
        
        self.parameters.add(params.ParameterInt(name = "y_chip",
                                                value = y_size,
                                                is_mutable = False,
                                                is_saved = False))

        self.parameters.add(params.ParameterInt(name = "max_intensity",
                                                value = 128,
                                                is_mutable = False,
                                                is_saved = False))

        #
        # Note: These are all expected to be in units of binned pixels. For
        # example if the camera is 512 x 512 and we are binning by 2s then
        # the maximum value of these would 256 x 256.
        #
        self.parameters.add(params.ParameterRangeInt(description = "AOI X start",
                                                     name = "x_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = x_size))
        
        self.parameters.add(params.ParameterRangeInt(description = "AOI X end",
                                                     name = "x_end",
                                                     value = x_size,
                                                     min_value = 1,
                                                     max_value = x_size))
        
        self.parameters.add(params.ParameterRangeInt(description = "AOI Y start",
                                                     name = "y_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = y_size))
        
        self.parameters.add(params.ParameterRangeInt(description = "AOI Y end",
                                                     name = "y_end",
                                                     value = y_size,
                                                     min_value = 1,
                                                     max_value = y_size))
        
        self.parameters.add(params.ParameterInt(name = "x_pixels",
                                                value = 0,
                                                is_mutable = False))
        
        self.parameters.add(params.ParameterInt(name = "y_pixels",
                                                value = 0,
                                                is_mutable = False))

        self.parameters.add(params.ParameterRangeInt(description = "Binning in X",
                                                     name = "x_bin",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = 4))
        
        self.parameters.add(params.ParameterRangeInt(description = "Binning in Y",
                                                     name = "y_bin",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = 4))

        # Frame size in bytes.
        self.parameters.add(params.ParameterInt(name = "bytes_per_frame",
                                                value = x_size * y_size * 2,
                                                is_mutable = False,
                                                is_saved = False))

        #
        # How/if data from this camera is saved.
        #
        self.parameters.add(params.ParameterString(description = "Camera save filename extension",
                                                   name = "extension",
                                                   value = ""))
        
        self.parameters.add(params.ParameterSetBoolean(description = "Save data from this camera when filming",
                                                       name = "saved",
                                                       value = True))
        
        self.parameters.set("extension", config.get("extension", ""))
        self.parameters.set("saved", config.get("saved", True))

        #
        # Camera display orientation. Values can only be changed by
        # changing the config.xml file.
        #
        self.parameters.add(params.ParameterSetBoolean(name = "flip_horizontal",
                                                       value = False,
                                                       is_mutable = False))
                            
        self.parameters.add(params.ParameterSetBoolean(name = "flip_vertical",
                                                       value = False,
                                                       is_mutable = False))

        self.parameters.add(params.ParameterSetBoolean(name = "transpose",
                                                       value = False,
                                                       is_mutable = False))
        
        self.parameters.set("flip_horizontal", config.get("flip_horizontal", False))
        self.parameters.set("flip_vertical", config.get("flip_vertical", False))
        self.parameters.set("transpose", config.get("transpose", False))

        #
        # Camera default display minimum and maximum.
        #
        # These are the values the display will use by default. They can
        # only be changed by changing the config.xml file.
        #
        self.parameters.add(params.ParameterInt(name = "default_max",
                                                value = 2000,
                                                is_mutable = False))
        
        self.parameters.add(params.ParameterInt(name = "default_min",
                                                value = 100,
                                                is_mutable = False))
        
        self.parameters.set("default_max", config.get("default_max", 2000))
        self.parameters.set("default_min", config.get("default_min", 100))

        self.finished.connect(self.handleFinished)
        self.newData.connect(self.handleNewData)

    def cleanUp(self):
        self.running = False
        self.wait()

    def closeShutter(self):
        """
        Close the shutter.
        """
        self.camera_functionality.shutter_state = False
        self.camera_functionality.shutter.emit(False)

    def getCameraFunctionality(self):
        if (self.camera_functionality.parameters != self.parameters):
            msg = "The parameters in the camera functionality are different from the actual camera parameters."
            raise CameraException(msg)
        return self.camera_functionality

    def getParameters(self):
        return self.parameters

    def getTemperature(self):
        """
        Non-sensical defaults. Cameras that have this 
        feature should override this method.
        """
        self.camera_functionality.temperature.emit({"camera" : self.camera_name,
                                                    "temperature" : 50.0,
                                                    "state" : "unstable"})

    def handleFinished(self):
        self.camera_functionality.stopped.emit()
        
    def handleNewData(self, frames):
        """
        Data from the camera should go through this method on it's
        way to the camera functionality object.
        """
        for frame in frames:
            if self.film_length is not None:

                # Stop the camera (if it has not already stopped).
                if (frame.frame_number > self.film_length):
                    self.stopCamera()

                # This keeps us from emitting more than the expected number
                # of newFrame signals.
                if (frame.frame_number >= self.film_length):
                    break
                
            self.camera_functionality.newFrame.emit(frame)

    def newParameters(self, parameters):
        """
        Notes: (1) The parameters that the camera receives are already
                   a copy so there is no need to make another copy.

               (2) It is up to the sub-class whether or not the camera
                   needs to be stopped to make the parameter changes. If
                   the camera needs to be stopped, then it must also be
                   re-started by the sub-class. And care should be taken
                   that the camera is not accidentally starting at
                   initialization. See noneCameraControl.py.
        """
        #
        # This restriction is necessary because in order to display
        # pictures as QImages they need to 32 bit aligned.
        #
        if ((parameters.get("x_pixels")%4) != 0):
            raise CameraException("The x size of the camera ROI must be a multiple of 4!")

        # Update parameter ranges based on binning.
        #
        # FIXME: For most cameras these parameters are not even relevant,
        #        so setting there range is not going to do anything. In
        #        the parameters editor they won't even be shown.
        #
        max_x = self.parameters.get("x_chip") / parameters.get("x_bin")
        for attr in ["x_start", "x_end"]:
            self.parameters.getp(attr).setMaximum(max_x)

        max_y = self.parameters.get("y_chip") / parameters.get("y_bin")
        for attr in ["y_start", "y_end"]:
            self.parameters.getp(attr).setMaximum(max_y)

        # Update parameters that are also used for the display.
        for pname in ["x_bin", "x_pixels", "x_start", "y_bin", "y_pixels", "y_start"]:
            self.parameters.setv(pname, parameters.get(pname))

        # Update parameters that are used for filming.
        self.parameters.setv("extension", parameters.get("extension"))
        self.parameters.setv("saved", parameters.get("saved"))

    def openShutter(self):
        """
        Open the shutter.
        """
        self.camera_functionality.shutter_state = True
        self.camera_functionality.shutter.emit(True)
        
    def setEMCCDGain(self, gain):
        """
        Cameras that have EMCCD gain should override this. This method must 
        also set the 'emccd_gain' parameter.
        """
        self.parameters.set("emccd_gain", gain)
        self.camera_functionality.emccdGain.emit(gain)
        
    def startCamera(self):

        # Update the camera temperature, if available.
        if self.camera_functionality.hasTemperature():
            self.getTemperature()
        
        self.frame_number = 0

        # Start the thread to handle data from the camera.
        self.thread_started = False
        self.start(QtCore.QThread.NormalPriority)

        # Wait until the thread has actually started the camera.
        #
        # Why not just use self.running? Because this creates a race condition
        # with short films where the camera gets started and stopped during the
        # time we are sleeping in the while loop so we never know that the camera
        # even started.
        #
        while not self.thread_started:
            time.sleep(0.01)

        self.camera_functionality.started.emit()

    def startFilm(self, film_settings, is_time_base):
        """
        If this is a fixed length film and this camera is the time
        base for the film, then set the film_length attribute.
        """
        if film_settings.isFixedLength() and is_time_base:
            self.film_length = film_settings.getFilmLength()

    def stopCamera(self):
        if self.running:

            # Stop the thread.
            self.running = False
            self.wait()

        self.camera_functionality.stopped.emit()

    def stopFilm(self):
        self.film_length = None

    def toggleShutter(self):
        if self.camera_functionality.getShutterState():
            self.closeShutter()
        else:
            self.openShutter()


class HWCameraControl(CameraControl):
    """
    This class implements what is common to all of the 'hardware' cameras.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.camera_mutex = QtCore.QMutex()

    def cleanUp(self):
        super().cleanUp()
        self.camera.shutdown()

    def run(self):
        #
        # Note: The order is important here, we need to start the camera and
        #       only then set self.running. Otherwise HAL might think the
        #       camera is running when it is not.
        #
        self.camera.startAcquisition()
        self.running = True
        self.thread_started = True
        while(self.running):

            # Get data from camera and create frame objects.
            self.camera_mutex.lock()
            [frames, frame_size] = self.camera.getFrames()
            self.camera_mutex.unlock()

            # Check if we got new frame data.
            if (len(frames) > 0):

                # Create frame objects.
                frame_data = []
                for cam_frame in frames:
                    aframe = frame.Frame(cam_frame.getData(),
                                         self.frame_number,
                                         frame_size[0],
                                         frame_size[1],
                                         self.camera_name)
                    frame_data.append(aframe)
                    self.frame_number += 1

                    if self.film_length is not None:                    
                        if (self.frame_number == self.film_length):
                            self.running = False
                            
                # Emit new data signal.
                self.newData.emit(frame_data)
            self.msleep(5)

        self.camera.stopAcquisition()
            
#    def startCamera(self):
#        print(">start", self.camera_name, self.running)
#        if self.camera_working:
#            self.camera.startAcquisition()
#        super().startCamera()

#    def stopCamera(self):
#        print(">stop", self.camera_name, self.running)
#        if self.camera_working and self.running:
#            self.camera_mutex.lock()
#
#            self.camera_mutex.unlock()
#        super().stopCamera()
            

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

