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

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        camera_params = module_params.get("camera")
        a_module = importlib.import_module("storm_control.hal4000." + camera_params.get("module_name"))
        a_class = getattr(a_module, camera_params.get("class_name"))
        self.camera_control = a_class(camera_params.get("parameters"))
        self.camera_control.addToHWConfig("camera", self.module_name)
        self.camera_control.addToHWConfig("master", camera_params.get("master"))

        self.camera_control.newFrame.connect(self.handleNewFrame)

        halMessage.addMessage("camera config", check_exists = False)
        halMessage.addMessage("camera temperature", check_exists = False)

    def cleanUp(self, qt_settings):
        self.camera_control.cleanUp()

    def handleNewFrame(self, frame, key):
        if (key == self.key):
            self.newFrame.emit(frame)

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
                    
            if (message.getType() == "configure"):

                # Start the camera control thread.
                self.camera_control.cameraInit()

                # Broadcast initial parameters and configuration.
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "default parameters",
                                                           data = self.camera_control.getCameraConfig()))
                
            # This message comes from display.cameraDisplay when the feed is changed. The
            # response is broadcast because display.paramsDisplay also needs this information.
            #
            # FIXME: Should also broadcast current temperature?
            #
            elif (message.getType() == "get camera config"):
                if (message.getData()["camera"] == self.module_name):
                    self.newMessage.emit(halMessage.HalMessage(source = self,
                                                               m_type = "camera config",
                                                               data = self.camera_control.getCameraConfig()))


            # This message comes from settings.settings.
            elif (message.getType() == "new parameters"):
                p = message.getData().get(self.module_name).copy()
                self.camera_control.newParameters(p)

            # This message comes from display.paramsDisplay.
            elif (message.getType() == "set emccd gain"):
                if (message.getData()["camera"] == self.module_name):
                    self.camera_control.setEMCCDGain(message.getData()["gain"])

            # This message comes from the shutter button.
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
                    self.camera_control.startCamera(message.getData()["key"])

            # This message comes from film.film, it goes to all cameras at once.
            elif (message.getType() == "start film"):
                self.camera_control.startCamera(message.getData()["film_settings"])

            # This message comes from film.film.
            elif (message.getType() == "stop camera"):
                if (message.getData()["camera"] == self.module_name):
                    self.camera_control.stopCamera()

            # This message comes from film.film, it goes to all camera at once.
            elif (message.getType() == "stop film"):
                self.camera_control.stopFilm()

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
