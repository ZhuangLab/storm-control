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
        
        camera_params = module_params.get("camera")
        a_module = importlib.import_module("storm_control.hal4000." + camera_params.get("module_name"))
        a_class = getattr(a_module, camera_params.get("class_name"))
        self.camera_control = a_class(camera_name = self.module_name,
                                      config = camera_params.get("parameters"),
                                      is_master = camera_params.get("master"))

        # Other modules will send this to get a camera/feed functionality.
        halMessage.addMessage("get camera functionality",
                              check_exists = False,
                              validator = {"data" : {"camera" : [True, str],
                                                     "extra data" : [False, str]},
                                           "resp" : {"functionality" : [True, cameraFunctionality.CameraFunctionality]}})
                                   
    def cleanUp(self, qt_settings):
        self.camera_control.cleanUp()
        super().cleanUp(qt_settings)

    def processMessage(self, message):

        if message.isType("configure1"):

            # Broadcast initial parameters.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "initial parameters",
                                                       data = {"parameters" : self.camera_control.getParameters()}))

        # This message comes from settings.settings.
        elif message.isType("new parameters"):
            halModule.runWorkerTask(self,
                                    message,
                                    lambda : self.updateParameters(message))

        # This message comes from display.cameraDisplay among others.
        elif message.isType("get camera functionality"):
            if (message.getData()["camera"] == self.module_name):
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.camera_control.getCameraFunctionality()}))

        # This message comes from the shutter button.
        elif message.isType("shutter clicked"):
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self,
                                        message,
                                        self.toggleShutter)

        # This message comes from film.film, it is camera specific as
        # slave cameras need to be started before master camera(s).
        elif message.isType("start camera"):
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self, message, self.startCamera)

        # This message comes from film.film, it goes to all cameras at once.
        elif message.isType("start film"):
            film_settings = message.getData()["film settings"]
            self.camera_control.startFilm(film_settings)
#            if (self.module_name == "camera1") and film_settings.isFixedLength():
#                self.film_length = film_settings.getFilmLength()

        # This message comes from film.film.
        elif message.isType("stop camera"):
            if (message.getData()["camera"] == self.module_name):
                halModule.runWorkerTask(self, message, self.stopCamera)

        # This message comes from film.film, it goes to all camera at once.
        elif message.isType("stop film"):
            self.film_length = None
            self.camera_control.stopFilm()
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.camera_control.getParameters()}))

    def startCamera(self):
        self.camera_control.startCamera()

    def stopCamera(self):
        self.camera_control.stopCamera()
        
    def toggleShutter(self):
        self.camera_control.toggleShutter()
        
    def updateParameters(self, message):
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"old parameters" : self.camera_control.getParameters().copy()}))
        p = message.getData()["parameters"].get(self.module_name)
        self.camera_control.newParameters(p)
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"new parameters" : self.camera_control.getParameters()}))






        
#        state = self.camera_control.toggleShutter()
#        self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "camera shutter",
#                                                   data = {"camera" : self.module_name,
#                                                           "state" : state}))
        
        # Broadcast the camera temperature, if available. We do this here because at least
        # with some cameras this can only be measured when the camera is not running.
#        if self.camera_control.haveTemperature():
#            self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                       m_type = "camera temperature",
#                                                       data = self.camera_control.getTemperature()))
        
#    def setEMCCDGain(self, new_gain):
#        gain = self.camera_control.setEMCCDGain(new_gain)
#        self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "camera emccd gain",
#                                                   data = {"camera" : self.module_name,
#                                                           "emccd gain" : gain}))        
        # This message comes from display.paramsDisplay.
        #
        # FIXME: Need to broadcast the emccd gain after it is set.
        #
#        elif message.isType("set emccd gain"):
#            if (message.getData()["camera"] == self.module_name):
#                halModule.runWorkerTask(self,
#                                        message,
#                                        lambda : self.setEMCCDGain(message.getData()["emccd gain"]))
        

#            # Broadcast configuration.
#            self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                       m_type = "camera configuration",
#                                                       data = {"camera" : self.module_name,
#                                                               "config" : self.camera_control.getCameraConfiguration()}))
        
#        self.camera_control.finished.connect(self.handleFinished)
#        self.camera_control.newData.connect(self.handleNewData)


        # This is sent at start-up so that other modules, in particular
        # feeds.feeds, get the information they need about the camera(s)
#        halMessage.addMessage("camera configuration",
#                              check_exists = False,
#                              validator = {"data" : {"camera" : [True, str],
#                                                     "config" : [True, cameraControl.CameraConfiguration]},
#                                           "resp" : {}})

#        # Sent each time the camera emccd gain changes.
#        halMessage.addMessage("camera emccd gain",
#                              check_exists = False,
#                              validator = {"data" : {"camera" : [True, str],
#                                                     "emccd gain" : [True, int]},
#                                           "resp" : None})

#        # Sent when filming and we have reached the desired number of frames.
#        halMessage.addMessage("camera film complete",
#                              check_exists = False,
#                              validator = {"data" : None, "resp" : None})
                        
#        # Sent each time the camera shutter stage changes.
#        halMessage.addMessage("camera shutter",
#                              check_exists = False,
#                              validator = {"data" : {"camera" : [True, str],
#                                                     "state" : [True, bool]},
#                                           "resp" : None})
        
#        # Sent when the camera stops.
#        halMessage.addMessage("camera stopped",
#                              check_exists = False,
#                              validator = {"data" : None, "resp" : None})

#        # The temperature data from this camera.
#        halMessage.addMessage("camera temperature",
#                              check_exists = False,
#                              validator = {"data" : {"camera" : [True, str],
#                                                     "state" : [True, str],
#                                                     "temperature" : [True, float]},
#                                           "resp" : None})

#        # Sent each time there is a new frame from the camera.
#        halMessage.addMessage("new frame",
#                              check_exists = False,
#                              validator = {"data" : {"frame" : [True, frame.Frame]},
#                                           "resp" : None})

#    def addParametersResponse(self, message):
#        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
#                                                          data = {"parameters" : self.camera_control.getParameters()}))

#    def broadcastParameters(self):
#        self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "current parameters",
#                                                   data = self.camera_control.getCameraConfig()))

#        self.film_length = None
#        self.finished_timer = QtCore.QTimer(self)
#        self.unprocessed_frames = 0

#        self.finished_timer.setInterval(10)
#        self.finished_timer.timeout.connect(self.handleFinished)
#        self.finished_timer.setSingleShot(True)

#    def decUnprocessed(self):
#        self.unprocessed_frames -= 1

#    def handleEMCCD(self, gain):
#        """
#        'emccd' is the signal the camera emits when it changes the gain.
#        """
#        self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "camera emccd gain",
#                                                   data = {"camera" : self.module_name,
#                                                           "emccd gain" : gain}))

#    def handleFinished(self):
#        """
#        'finished' is the signal the thread emits when the run() method stops.
#        """
#        if (self.unprocessed_frames == 0):
#            self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                       m_type = "camera stopped"))
#        else:
#            self.finished_timer.start()

#    def handleNewData(self, frames):
#        return
#        for frame in frames:
#            #
#            # If possible the camera should stop when it has recorded the
#            # expected number of frames, but not all camera support this
#            # so we software back-stop this here.
#            #
#            if self.film_length is not None:
#
#                # Broadcast that we've captured the expected number of frames.
#                if (frame.frame_number == self.film_length):
#                    self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                               m_type = "camera film complete"))
#                    break
#
#                # Don't send more frames than were requested for the film.
#                if (frame.frame_number >= self.film_length):
#                    break
#
#            self.incUnprocessed()
#            self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                       m_type = "new frame",
#                                                       level = 2,
#                                                       data = {"frame" : frame},
#                                                       finalizer = lambda : self.decUnprocessed()))
    
#    def incUnprocessed(self):
#        self.unprocessed_frames += 1



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
