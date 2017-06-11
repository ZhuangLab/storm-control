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

import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality
import storm_control.hal4000.camera.frame as frame
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class Camera(halModule.HalModule):
    """
    Controller for a single camera.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.film_settings = None

        camera_params = module_params.get("camera")
        a_module = importlib.import_module(camera_params.get("module_name"))
        a_class = getattr(a_module, camera_params.get("class_name"))
        self.camera_control = a_class(camera_name = self.module_name,
                                      config = camera_params.get("parameters"),
                                      is_master = camera_params.get("master"))
                                   
    def cleanUp(self, qt_settings):
        self.camera_control.cleanUp()
        super().cleanUp(qt_settings)

    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("timing"):
                timing_fn = message.getData()["properties"]["functionality"]
                is_time_base = (timing_fn.getTimeBase() == self.module_name)
                halModule.runWorkerTask(self,
                                        message, 
                                        lambda : self.startFilm(is_time_base))

        elif message.isType("configure1"):
            # Broadcast initial parameters.
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.camera_control.getParameters()}))


        elif message.isType("current parameters"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.camera_control.getParameters().copy()}))
            
        elif message.isType("get functionality"):
            # This message comes from display.cameraDisplay among others.
            if (message.getData()["name"] == self.module_name):
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.camera_control.getCameraFunctionality()}))

        elif message.isType("new parameters"):
            # This message comes from settings.settings
            halModule.runWorkerTask(self,
                                    message,
                                    lambda : self.updateParameters(message))

        elif message.isType("shutter clicked"):
            # This message comes from the shutter button.
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self,
                                        message,
                                        self.toggleShutter)

        elif message.isType("start camera"):
            # This message comes from film.film, it is camera specific as
            # slave cameras need to be started before master camera(s).
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self, message, self.startCamera)

        elif message.isType("start film"):
            # This message comes from film.film, we save the film settings
            # but don't actually do anything until we get a 'configuration'
            # message from timing.timing.
            self.film_settings = message.getData()["film settings"]

        elif message.isType("stop camera"):
            # This message comes from film.film.
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self, message, self.stopCamera)

        elif message.isType("stop film"):
            # This message comes from film.film, it goes to all camera at once.
            self.film_length = None
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.camera_control.getParameters()}))
            halModule.runWorkerTask(self, message, self.stopFilm)

    def startCamera(self):
        self.camera_control.startCamera()

    def startFilm(self, is_time_base):
        self.camera_control.startFilm(self.film_settings, is_time_base)

    def stopCamera(self):
        self.camera_control.stopCamera()

    def stopFilm(self):
        self.camera_control.stopFilm()

    def toggleShutter(self):
        self.camera_control.toggleShutter()
        
    def updateParameters(self, message):
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"old parameters" : self.camera_control.getParameters().copy()}))
        p = message.getData()["parameters"].get(self.module_name)
        self.camera_control.newParameters(p)
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"new parameters" : self.camera_control.getParameters()}))


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
