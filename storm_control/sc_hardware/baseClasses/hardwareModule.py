#!/usr/bin/env python
"""
The core functionality for a HAL hardware module. Most HAL
modules that interact with hardware are sub-classes of
this module.

Hazen 04/17
"""

import copy

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


def getThreadPool(self):
    """
    Return the applications threadpool instance. This is stored in halModule.
    """
    return halModule.threadpool

    
class HardwareFunctionality(halFunctionality.HalFunctionality):
    """
    These are requested using the 'get functionality' message. The
    expected form of the "name" field of this message is the string
    "module_name.functionality_name".
    """
    pass


class BufferedFunctionality(HardwareFunctionality):
    """
    This is used to communicate with less responsive hardware. There
    may be several of these per device, self.device_mutex is used
    to coordinate.
    """
    done = QtCore.pyqtSignal()
    
    def __init__(self, device_mutex = QtCore.QMutex(), **kwds):
        super().__init__(**kwds)
        self.current_request = None
        self.device_mutex = device_mutex

        self.done.connect(self.handleDone)

    def handleDone(self):
        if self.current_request is not None:
            request = copy.copy(self.current_request)
            self.current_request = None
            getThreadPool().start(self.run(request))

    def handleRequest(self, request):
        if self.current_request is None:
            getThreadPool().start(self.run(copy.copy(request)))
        self.current_request = request

    def processRequest(self, request):
        pass
    
    def run(self, request):
        self.device_mutex.lock()
        self.processRequest(request)
        self.device_mutex.unlock()
        self.done.emit()

        

class HardwareModule(halModule.HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        # Other modules will send this to get hardware functionalities.
        halMessage.addMessage("get functionality",
                              check_exists = False,
                              validator = {"data" : {"name" : [True, str],
                                                     "extra data" : [False, str]},
                                           "resp" : {"functionality" : [True, HardwareFunctionality]}})
