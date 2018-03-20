#!/usr/bin/env python
"""
These are for testing HAL's handling of errors.

Hazen 03/18
"""

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP


class TestSimpleError(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
    def processMessage(self, message):
        if message.isType("start"):
            raise halMessage.HalMessageException("Failed!")

class TestWorkerError(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
    def processMessage(self, message):
        if message.isType("start"):
            halModule.runWorkerTask(self, message, self.throwError)

    def throwError(self):
        raise halMessage.HalMessageException("Failed!")
