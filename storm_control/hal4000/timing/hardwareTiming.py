#!/usr/bin/env python
"""
Handles hardware timing for a setup. This is a setup that doesn't
use a camera for the time base, but instead uses another source 
such as a counter on a DAQ card.

Note: In this case it is enforced that there are no master cameras.

Hazen 10/19
"""

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class HardwareTiming(halModule.HalModule):
    """
    Hardware timing for a film.

    The actual timing is provided by a functionality that behaves like
    a nidaqModule.CTTaskFunctionality().
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.checked_no_master = False
        self.counter_functionality = None

        self.configuration = module_params.get("configuration")

        self.parameters = params.StormXMLObject()

        #
        # FIXME: The range would be better set by what the cameras allow
        #        based on their current configuration.
        #
        self.parameters.add(params.ParameterRangeFloat(description = "Frames per second",
                                                       name = "FPS",
                                                       value = self.configuration.get("FPS", 0.1),
                                                       min_value = self.configuration.get("FPS_min", 0.001),
                                                       max_value = self.configuration.get("FPS_max", 10000.0)))

        #
        # This message will come from film.film telling us to start or
        # stop the hardware timing source. We use messages instead of
        # passing the counter to film.film as a functionality so that
        # the counter will only get started once everything else is ready.
        #
        halMessage.addMessage("hardware timing",
                              validator = {"data" : {"start" : [True, bool]},
                                           "resp" : None})
    
    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            
            if (message.getData()["extra data"] == "counter"):
                self.counter_functionality = response.getData()["functionality"]

                self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                       data = {"properties" : {}}))

            # Every other response should be a camera or a feed.
            elif (message.getData()["extra data"] == "feed"):
                cam_fn = response.getData()["functionality"]
                if cam_fn.isCamera() and cam_fn.isMaster():
                    raise halExceptions.HalException("master camera detected in hardware timed setup.")

    def processMessage(self, message):

        if message.isType("configuration"):

            # Check for master cameras, only do this once.
            if message.sourceIs("feeds") and not self.checked_no_master:
                for name in message.getData()["properties"]["feed names"]:
                    self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                           data = {"name" : name, "extra data" : "feed"}))
                self.checked_no_master = True

        elif message.isType("configure1"):

            # Broadcast initial parameters.
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.parameters}))

            # Get DAQ counter like functionality.
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("counter_fn_name"),
                                                           "extra data" : "counter"}))

        elif message.isType("hardware timing"):
            if message.getData()["start"]:
                self.counter_functionality.setFrequency(self.parameters.get("FPS"))
                self.counter_functionality.startCounter()
            else:
                self.counter_functionality.stopCounter()

        elif message.isType("new parameters"):
            #
            # FIXME: We have a similar problem here as with timing.timing. We don't know
            #        the allowed FPS range for the cameras based on their new parameters
            #        at this point. By the time we do know at 'updated parameters' it is
            #        to late to change the allowed range that settings.settings will show
            #        in the parameter editor GUI.
            #
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.parameters.copy()}))
            p = message.getData()["parameters"].get(self.module_name)
            self.parameters.setv("FPS", p.get("FPS"))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.parameters}))

        elif message.isType("start"):
            if self.counter_functionality is None:
                raise halExceptions.HalException("no counter functionality available for camera timing.")

