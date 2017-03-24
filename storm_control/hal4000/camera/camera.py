#!/usr/bin/env python
"""
Handles a single camera. 

Notes:
 1. There is one of these per camera.

 2. The name of the camera is the name of the module.


Responsibilities:
 
 1. Operate the camera.
 
 2. Return the camera configuration when requested. This includes
    things like the camera maximum value, whether it has a shutter,
    temperature control, EM gain, etc..

Hazen 02/17
"""

import importlib

from PyQt5 import QtCore


import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class Camera(halModule.HalModuleBuffered):
    """
    Controller for a single camera.

    This sends the following messages:
     'camera stopped'
     'camera temperature'
     'current camera'
     'film complete'
     'new frame'
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.film_length = None

        camera_params = module_params.get("camera")
        a_module = importlib.import_module("storm_control.hal4000." + camera_params.get("module_name"))
        a_class = getattr(a_module, camera_params.get("class_name"))
        self.camera_control = a_class(camera_name = self.module_name,
                                      config = camera_params.get("parameters"))
        self.camera_control.addToHWConfig("master", camera_params.get("master"))

        self.camera_control.finished.connect(self.handleFinished)
        self.camera_control.newData.connect(self.handleNewData)

        # Sent when the camera stops.
        halMessage.addMessage("camera stopped", check_exists = False)

        # The temperature data from this camera.
        halMessage.addMessage("camera temperature", check_exists = False)

        # Information about this camera if it is the 'current camera', i.e. 
        # the camera shown in the main viewer and the parameters display.
        halMessage.addMessage("current camera", check_exists = False)

        # Sent when filming and we have reached the desired number of frames.
        halMessage.addMessage("film complete")
        
        # Sent each time there is a new frame from the camera.
        halMessage.addMessage("new frame", check_exists = False)

    def broadcastParameters(self):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "current parameters",
                                                   data = self.camera_control.getCameraConfig()))
        
    def cleanUp(self, qt_settings):
        self.camera_control.cleanUp()

    def handleFinished(self):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "camera stopped"))

    def handleNewData(self, frames):
        for frame in frames:
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "new frame",
                                                       level = 2,
                                                       data = {"frame" : frame}))
            #
            # If possible the camera should stop when it has recorded the
            # expected number of frames, but not all camera supports this.
            #
            if self.film_length is not None:
                if (frame.frame_number == self.film_length):
                    self.newMessage.emit(halMessage.HalMessage(source = self,
                                                               m_type = "film complete"))
                    break
                
    def processMessage(self, message):
        
        if (message.level == 1):
                    
            if (message.getType() == "configure1"):

                # Broadcast initial parameters and configuration.
                self.broadcastParameters()

            # This message comes from display.cameraDisplay to get information about a camera.
            elif (message.getType() == "get feed config"):
                if (message.getData()["camera"] == self.module_name):
                    message.addResponse(halMessage.HalMessageResponse(source = self,
                                                                      m_type = message.getType(),
                                                                      response_data = self.camera_control.getCameraConfig()))

            # This message comes from settings.settings.
            elif (message.getType() == "new parameters"):
                p = message.getData().get(self.module_name)
                self.camera_control.newParameters(p)
                self.broadcastParameters()

            #
            # This message comes from display.cameraDisplay when the feed is changed. The
            # response is broadcast because display.paramsDisplay also needs this information.
            #
            # FIXME: Should also broadcast current temperature?
            #
            elif (message.getType() == "set current camera"):
                if (message.getData()["camera"] == self.module_name):
                    self.newMessage.emit(halMessage.HalMessage(source = self,
                                                               m_type = "current camera",
                                                               data = self.camera_control.getCameraConfig()))
                    
            # This message comes from display.paramsDisplay.
            #
            # FIXME: Should broadcast the gain after it is set.
            #
            elif (message.getType() == "set emccd gain"):
                if (message.getData()["camera"] == self.module_name):
                    self.camera_control.setEMCCDGain(message.getData()["gain"])

            # This message comes from the shutter button.
            #
            # FIXME: Should broadcast the updated shutter state.
            #
            elif (message.getType() == "set shutter"):
                if (message.getData()["camera"] == self.module_name):
                    self.camera_control.setShutter(message.getData()["state"])

            # This message comes from film.film, it is camera specific as
            # slave cameras need to be started before master camera(s).
            elif (message.getType() == "start camera"):
                if (message.getData()["camera"] == self.module_name):

                    # Broadcast the camera temperature, if available. We do this here because at least
                    # with some cameras this can only be measured when the camera is not running.
                    if self.camera_control.haveTemperature():
                        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                                   m_type = "camera temperature",
                                                                   data = self.camera_control.getTemperature()))

                    # Start the camera.
                    self.camera_control.startCamera()

            # This message comes from film.film, it goes to all cameras at once.
            elif (message.getType() == "start film"):
                film_settings = message.getData()["film_settings"]
                self.camera_control.startFilm(film_settings)
                if (self.module_name == "camera1") and (film_settings["acq_mode"] == "fixed_length"):
                    self.film_length = film_settings["frames"] - 1

            # This message comes from film.film. Once the camera actually
            # stops we send the 'camera stopped' message.
            elif (message.getType() == "stop camera"):
                if (message.getData()["camera"] == self.module_name):
                    self.camera_control.stopCamera()

            # This message comes from film.film, it goes to all camera at once.
            elif (message.getType() == "stop film"):
                self.camera_control.stopFilm()
                
        super().processMessage(message)


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
