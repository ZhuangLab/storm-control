#!/usr/bin/env python
"""
The core functionality for a HAL hardware module. Most HAL
modules that interact with hardware are sub-classes of
this module.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class HardwareFunctionality(halFunctionality.HalFunctionality):
    """
    These are requested using the 'get functionality' message. The
    expected form of the "name" field of this message is the string
    "module_name.functionality_name".
    """
    pass


class HardwareModule(halModule.HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        # Other modules will send this to get hardware functionalities.
        halMessage.addMessage("get functionality",
                              check_exists = False,
                              validator = {"data" : {"name" : [True, str],
                                                     "extra data" : [False, str]},
                                           "resp" : {"functionality" : [True, HardwareFunctionality]}})
        
    def configure1(self, message):
        pass

    def filmTiming(self, message):
        pass

    def getFunctionality(self, message):
        pass
    
    def processMessage(self, message):

        if message.isType("configure1"):
            self.configure1(message)

        elif message.isType("get functionality"):
            self.getFunctionality(message)
            
        elif message.isType("film timing"):
            self.filmTiming(message)
            
        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

    def startFilm(self, message):
        pass

    def stopFilm(self, message):
        pass
    
