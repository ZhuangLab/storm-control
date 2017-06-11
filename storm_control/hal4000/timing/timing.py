#!/usr/bin/env python
"""
Provides the time base for a film.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.sc_library.parameters as params

import storm_control.hal4000.film.filmSettings as filmSettings
import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class TimingFunctionality(halFunctionality.HalFunctionality):
    """
    This is tied to the appropriate camera/feed so that it emits a newFrame
    signal whenever the camera/feed does the same.
    """
    newFrame = QtCore.pyqtSignal(int)
    stopped = QtCore.pyqtSignal()

    def __init__(self, time_base = None, **kwds):
        super().__init__(**kwds)
        """
        time_base is a string containing the name of a feed.
        """
        self.cam_fn = None
        self.time_base = time_base

    def connectCameraFunctionality(self, camera_functionality):
        assert self.cam_fn is None
        assert (camera_functionality.getCameraName() == self.time_base)
        
        self.cam_fn = camera_functionality
        self.cam_fn.newFrame.connect(self.handleNewFrame)
        self.cam_fn.stopped.connect(self.handleStopped)

    def disconnectCameraFunctionality(self):
        self.cam_fn.newFrame.disconnect(self.handleNewFrame)
        self.cam_fn.stopped.disconnect(self.handleStopped)

    def getCameraFunctionality(self):
        """
        Return the camera functionality that drives this functionality.
        """
        return self.cam_fn

    def getFPS(self):
        return self.cam_fn.getParameter("fps")
        
    def getTimeBase(self):
        return self.time_base
    
    def handleNewFrame(self, frame):
        self.newFrame.emit(frame.frame_number)

    def handleStopped(self):
        self.stopped.emit()


class Timing(halModule.HalModule):
    """
    (Software) timing for a film.

    Modules such as illumination that need to do something on every
    frame of a film are expected to time themselves using the timing
    functionality provided by this module.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.timing_functionality = None

        self.parameters = params.StormXMLObject()

        self.parameters.add(params.ParameterSetString(description = "Feed to use as the time base when filming",
                                                      name = "time_base",
                                                      value = "",
                                                      allowed = [""]))

        default_time_base = module_params.get("parameters").get("time_base")
        self.setAllowed([default_time_base])
        self.parameters.setv("time_base", default_time_base)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.timing_functionality.connectCameraFunctionality(response.getData()["functionality"])

            # Broadcast timing information for the film.
            props = {"functionality" : self.timing_functionality}
            self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : props}))
            
            # Tell film.film that this module is ready to film.
            self.sendMessage(halMessage.HalMessage(m_type = "ready to film"))
        
    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("feeds"):
                cur_time_base = self.parameters.get("time_base")
                self.parameters.getp("time_base").setAllowed(message.getData()["properties"]["feed names"])
                self.parameters.setv("time_base", cur_time_base)

        elif message.isType("configure1"):

            # Broadcast initial parameters.
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.parameters}))

            # Let film.film know that it needs to wait for us
            # to get ready before starting the cameras.
            self.sendMessage(halMessage.HalMessage(m_type = "wait for",
                                                   data = {"module names" : ["film"]}))

        elif message.isType("new parameters"):
            #
            # FIXME: The problem is that we won't know the allowed set of feed names until
            #        feeds.feeds sends the 'configuration' message. Using the old allowed
            #        might cause a problem as the new time base might not exist in the
            #        old allowed. For now we are just setting allowed to be whatever the
            #        time_base parameter value is. Then at 'feed names' we check that
            #        that the parameter is valid. If it is not valid this will break HAL
            #        at an unexpected point, the error should have been detected in
            #        'new parameters'. Also the editor won't work because the version of the
            #        parameter that it has only allows one value. Somehow we need to know
            #        the valid feed names at the new parameter stage..
            #
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.parameters.copy()}))
            p = message.getData()["parameters"].get(self.module_name)
            self.setAllowed([p.get("time_base")])
            self.parameters.setv("time_base", p.get("time_base"))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.parameters}))

        elif message.isType("start film"):
            self.timing_functionality = TimingFunctionality(time_base = self.parameters.get("time_base"))
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.timing_functionality.getTimeBase()}))

        elif message.isType("stop film"):
            self.timing_functionality.disconnectCameraFunctionality()
            self.timing_functionality = None
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.parameters.copy()}))

    def setAllowed(self, allowed):
        self.parameters.getp("time_base").setAllowed(allowed)
