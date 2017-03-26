#!/usr/bin/env python
"""
Base class for controlling a camera.

See noneCameraControl.py or andorCameraControl.py for specific examples.

Hazen 2/17
"""

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.frame as frame


class CameraException(halExceptions.HardwareException):
    pass


class CameraControl(QtCore.QThread):
    configured = QtCore.pyqtSignal()
    newData = QtCore.pyqtSignal(object)
    stopped = QtCore.pyqtSignal()

    def __init__(self, camera_name = None, config = None, **kwds):
        super().__init__(**kwds)

        self.camera = False
        self.camera_name = camera_name
        self.camera_working = True
        self.frame_number = 0
        self.parameters = params.StormXMLObject()
        self.running = False
        self.shutter_state = False  # True = open

        # Default (hardware) configuration. The remaining values
        # for the camera are stored in it's parameters.
        self.hw_dict = {"camera" : self.camera_name,
                        "have_emccd" : False,
                        "have_preamp" : False,
                        "have_shutter" : False,
                        "have_temp" : False}

        # Parameters common to every camera.

        # This is frames per second as reported by the camera. It is used
        # by the illumination module for timing the shutters.
        self.parameters.add(params.ParameterFloat(name = "fps",
                                                  value = 0,
                                                  is_mutable = False))

        # Camera AOI size.
        x_size = 512
        y_size = 512
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
                                                value = x_size,
                                                is_mutable = False))
        
        self.parameters.add(params.ParameterInt(name = "y_pixels",
                                                value = y_size,
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
                                                   name = "filename_ext",
                                                   value = ""))
        
        self.parameters.add(params.ParameterSetBoolean(description = "Save data from this camera when filming",
                                                       name = "is_saved",
                                                       value = True))
        
        self.parameters.set("filename_ext", config.get("filename_ext", ""))
        self.parameters.set("is_saved", config.get("is_saved", True))

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

    def addToHWConfig(self, key, value):
        self.hw_dict[key] = value

    def cleanUp(self):
        self.running = False
        self.wait()

    def getCameraConfig(self):
        self.hw_dict["shutter_state"] = self.shutter_state
        self.hw_dict["parameters"] = self.parameters.copy()
        return self.hw_dict

    def getParameters(self):
        return self.parameters

    def getTemperature(self):
        """
        Non-sensical defaults. Cameras that have this 
        feature should override this method.
        """
        return {"camera" : self.hw_dict["camera"],
                "temperature" : 50.0,
                "state" : "unstable"}

    def haveTemperature(self):
        return self.hw_dict["have_temp"]

    def newParameters(self, parameters):
        """
        Note: (1) The sub-class must emit 'configured' at the
                  end of this method()!

              (2) The parameters that the camera receives are already
                  a copy so there is no need to make another copy.
        """
        #
        # This restriction is necessary because in order to display
        # pictures as QImages they need to 32 bit aligned.
        #
        if parameters.has("x_end"):
            x_pixels = parameters.get("x_end") - parameters.get("x_start") + 1
            if((x_pixels % 4) != 0):
                raise CameraException("The camera ROI must be a multiple of 4 in x!")

        self.parameters.set("filename_ext", parameters.get("filename_ext"))
        self.parameters.set("is_saved", parameters.get("is_saved"))

    def setEMCCDGain(self, gain):
        pass
    
    def setShutter(self, shutter_state):
        self.shutter_state = shutter_state

    def startCamera(self):
        self.frame_number = 0
        self.start(QtCore.QThread.NormalPriority)

    def startFilm(self, film_settings):
        pass

    def stopCamera(self):

        # If we are running then we'll get the finished
        # signal when the thread stops.
        if self.running:
            self.running = False
            self.wait()

        # Otherwise we need to send it ourselves, or the 'camera stopped'
        # message will never get sent. Other classes depend on this message
        # to know when the camera has actually stopped running.
        else:
            self.finished.emit()

    def stopFilm(self):
        pass

    # FIXME: Is this used? How many different ways to control the shutter do we need?
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
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.camera_mutex = QtCore.QMutex()

    def cleanUp(self):
        self.stopCamera()
        self.camera.shutdown()

    def run(self):
        self.running = True
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
                            
                # Emit new data signal.
                self.newData.emit(frame_data)

        self.msleep(5)

    def startCamera(self):
        super().startCamera()
        if self.camera_working:
            self.camera.startAcquisition()

    def stopCamera(self):
        if self.camera_working:
            self.camera_mutex.lock()
            self.camera.stopAcquisition()
            self.camera_mutex.unlock()
        super().stopCamera()
        

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

