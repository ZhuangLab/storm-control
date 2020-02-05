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

import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class HardwareTimingFrame(object):
    """
    This pretends to be a camera frame for the benefit of timing.timing.
    """
    def __init__(self, frame_number, **kwds):
        super().__init__(**kwds)
        
        self.frame_number = frame_number
        

class HardwareTimingFunctionality(halFunctionality.HalFunctionality):
    """
    This is tied to the source time base, such as a DAQ counter, so 
    that it emits a newFrame signal whenever the time base indicates
    the start of a new frame. 

    This pretends to be a camera functionality in order to work as
    expected with timing.timing.
    """
    newFrame = QtCore.pyqtSignal(object)
    stopped = QtCore.pyqtSignal()
    
    def __init__(self, counter_functionality = None, name = None, **kwds):
        super().__init__(**kwds)

        self.counter_fn = counter_functionality
        self.film_length = None
        self.fps = None
        self.name = name
        self.n_pulses = 0

        self.counter_fn.setDoneFn(self.handleStopped)
        self.counter_fn.setSignalFn(self.handleNewFrame)

    def getCameraName(self):
        return self.name
    
    def getParameter(self, p_name):
        assert (p_name == "fps")
        return self.fps

    def handleNewFrame(self):
        #
        # The counter outputs two pulses per cycle, so only a
        # emit a newFrame signal every other cycle.
        #
        if ((self.n_pulses%2) == 0):
            frame = HardwareTimingFrame(int(self.n_pulses/2))
            self.newFrame.emit(frame)
        self.n_pulses += 1

    def handleStopped(self):
        self.stopped.emit()

    def setFilmLength(self, film_length):
        self.film_length = film_length
        
    def setFPS(self, fps):
        self.fps = float(fps)
        
    def startCounter(self):
        self.n_pulses = 0
        self.counter_fn.setFrequency(self.fps)

        cycles = 0
        if self.film_length is not None:
            cycles = self.film_length
            
        self.counter_fn.pwmOutput(duty_cycle = 0.5, cycles = cycles)

    def stopCounter(self):
        self.counter_fn.pwmOutput(duty_cycle = 0.0)
        self.film_length = None
    

class HardwareTiming(halModule.HalModule):
    """
    Hardware timing for a film.

    The actual timing is provided by a functionality that behaves like
    a nidaqModule.CTTaskFunctionality().
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.film_settings = None
        self.hardware_timing_functionality = None

        self.configuration = module_params.get("configuration")
        self.allow_master = self.configuration.get("allow_master", False)

        self.parameters = params.StormXMLObject()

        #
        # FIXME: The range would be better set by what the cameras allow
        #        based on their current configuration.
        #
        self.parameters.add(params.ParameterRangeFloat(description = "Frames per second",
                                                       name = "fps",
                                                       value = self.configuration.get("fps", 0.1),
                                                       min_value = self.configuration.get("fps_min", 0.001),
                                                       max_value = self.configuration.get("fps_max", 10000.0)))
    
    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            
            if (message.getData()["extra data"] == "counter"):
                htf = HardwareTimingFunctionality(counter_functionality = response.getData()["functionality"],
                                                  name = self.module_name)
                self.hardware_timing_functionality = htf
                self.hardware_timing_functionality.setFPS(self.parameters.get("fps"))

                self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                       data = {"properties" : {}}))

    def processMessage(self, message):

        if message.isType("configuration"):

            # Check for master cameras. If they exist this is an error in the setup
            # configuration.
            if ("is camera" in message.getData()["properties"]):
                if not self.allow_master:
                    m_data = message.getData()["properties"]
                    if m_data["is camera"] and m_data["is master"]:
                        raise halExceptions.HalException("Master camera detected in hardware timed setup!")

            # Check if we are the time base for the film.
            #
            # If we are and this is a fixed length film then
            # set the hardware counter appropriately.
            #
            elif message.sourceIs("timing"):
                timing_fn = message.getData()["properties"]["functionality"]
                if (timing_fn.getTimeBase() == self.module_name) and self.film_settings.isFixedLength():
                    self.hardware_timing_functionality.setFilmLength(self.film_settings.getFilmLength())

        elif message.isType("configure1"):

            # Broadcast initial parameters.
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.parameters}))

            # Send 'configuration' message with information about this hardware timing
            # module. This module is always a master, but is not a camera.
            p_dict = {"module name" : self.module_name,
                      "is camera" : False,
                      "is master" : True}
            self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : p_dict}))
            
            # Get DAQ counter like functionality.
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("counter_fn_name"),
                                                           "extra data" : "counter"}))

        elif message.isType("current parameters"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.parameters.copy()}))
            
        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.hardware_timing_functionality}))

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
            self.parameters.setv("fps", p.get("fps"))
            self.hardware_timing_functionality.setFPS(p.get("fps"))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.parameters}))

        elif message.isType("start"):
            if self.hardware_timing_functionality is None:
                raise halExceptions.HalException("no counter functionality available for hardware timing.")

        elif message.isType("start camera"):
            # This message comes from film.film. This module behaves
            # like a master camera.
            if message.getData()["master"]:
                self.hardware_timing_functionality.startCounter()
                
        elif message.isType("start film"):
            # This message comes from film.film, we save the film settings
            # but don't actually do anything until we get a 'configuration'
            # message from timing.timing.
            self.film_settings = message.getData()["film settings"]

        elif message.isType("stop camera"):
            # This message comes from film.film. This module behaves
            # like a master camera.
            if message.getData()["master"]:
                self.hardware_timing_functionality.stopCounter()
                
