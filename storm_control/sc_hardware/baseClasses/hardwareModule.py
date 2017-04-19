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


def getThreadPool():
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
    This is used to communicate with less responsive hardware. 

    There may be several of these per device, self.device_mutex is used
    to coordinate.

    Requests are expected to be simple objects like strings. Processing
    will actually be done on a copy.copy() of the request.

    maybeProcess() only gaurantees that the most recently received
    request will be processed.

    mustProcess() will process all requests.
    """
    done = QtCore.pyqtSignal()
    
    def __init__(self, device_mutex = QtCore.QMutex(), **kwds):
        super().__init__(**kwds)
        self.busy = False
        self.device_mutex = device_mutex        
        self.next_request = None

        self.done.connect(self.handleDone)

    def handleDone(self):
        if self.next_request is not None:
            self.start(self.next_request, True)
            self.next_request = None

    def maybeProcess(self, request):
        """
        Call this method with requests that don't absolutely have to be
        processed. This will process them in the order received, but 
        will only process the most recently received request.
        """
        if not self.busy:
            self.start(request, True)
        else:
            self.next_request = request

    def mustProcess(self, request):
        """
        Call this method with requests that must be processed.
        """
        self.start(request, False)
            
    def processRequest(self, request):
        """
        Override this with device specific request processing. This
        should be the only method that you need to override.
        """
        pass
    
    def run(self, request, emit_done):
        self.device_mutex.lock()
        self.processRequest(request)
        self.device_mutex.unlock()
        self.busy = False
        if emit_done:
            self.done.emit()

    def start(self, request, emit_done):
        self.busy = True
        bw = BufferedWorker(request = copy.copy(request),
                            task = self.run,
                            emit_done = emit_done)
        getThreadPool().start(bw)
        

class BufferedWorker(QtCore.QRunnable):
    """
    The worker QRunnable used by BufferedFunctionality.
    """
    def __init__(self, request = None, task = None, emit_done = True, **kwds):
        super().__init__(**kwds)
        self.emit_done = emit_done
        self.request = request
        self.task = task

    def run(self):
        self.task(self.request, self.emit_done)
        

class HardwareModule(halModule.HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        # Other modules will send this to get hardware functionalities.
        halMessage.addMessage("get functionality",
                              check_exists = False,
                              validator = {"data" : {"name" : [True, str],
                                                     "extra data" : [False, str]},
                                           "resp" : {"functionality" : [True, HardwareFunctionality]}})
