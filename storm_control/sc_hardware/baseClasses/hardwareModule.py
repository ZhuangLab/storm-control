#!/usr/bin/env python
"""
The core functionality for a HAL hardware module. Most HAL
modules that interact with hardware are sub-classes of
this module.

Hazen 04/17
"""
#import copy

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


class HardwareWorker(QtCore.QRunnable):

    def __init__(self, task = None, args = [], **kwds):
        super().__init__(**kwds)
        self.args = args
        self.task = task

    def run(self):
        self.task(*self.args)


#class BufferedHardwareWorker(HardwareWorker):
#    """
#    The HardwareWorker specialized for use by BufferedFunctionality.
#    """
#    def __init__(self, request = None, emit_done = True, **kwds):
#        kwds["args"] = [request, emit_done]
#        super().__init__(**kwds)
        

class BufferedFunctionality(HardwareFunctionality):
    """
    This is used to communicate with less responsive hardware. 

    There may be several of these per device, self.device_mutex is used
    to coordinate.

    maybeRun() only gaurantees that the most recently received
    request will be processed.

    mustRun() will process all requests.
    """
    done = QtCore.pyqtSignal()
    
    def __init__(self, device_mutex = QtCore.QMutex(), **kwds):
        super().__init__(**kwds)
        self.busy = False
        self.device_mutex = device_mutex        
        self.next_request = None

        # This signal is used to let us know when the current 'maybe'
        # request is done and we should start the next one.
        self.done.connect(self.handleDone)

    def handleDone(self):
        if self.next_request is not None:
            self.start(*self.next_request)
            self.next_request = None

    def maybeRun(self, task = None, args = [], ret_signal = None):
        """
        Call this method with requests that don't absolutely have to be
        processed. This will process them in the order received, but 
        will only process the most recently received request.
        """
        if not self.busy:
            self.start(task, args, True, ret_signal)
        else:
            self.next_request = [task, args, True, ret_signal]

    def mustRun(self, task = None, args = [], ret_signal = None):
        """
        Call this method with requests that must be processed.
        """
        self.start(task, args, False, ret_signal)
            
    def run(self, task, args, emit_done, ret_signal):
        """
        run the task with arguments args, and use the ret_signal
        pyqtSignal to return the results.
        """
        self.device_mutex.lock()
        retv = task(*args)
        self.device_mutex.unlock()
        self.busy = False
        if emit_done:
            self.done.emit()
        if ret_signal is not None:
            ret_signal.emit(retv)

    def start(self, task, args, emit_done, ret_signal):
        self.busy = True
        hw = HardwareWorker(task = self.run,
                            args = [task, args, emit_done, ret_signal])
        getThreadPool().start(hw)
        

class HardwareModule(halModule.HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        # Other modules will send this to get hardware functionalities.
        halMessage.addMessage("get functionality",
                              check_exists = False,
                              validator = {"data" : {"name" : [True, str],
                                                     "extra data" : [False, str]},
                                           "resp" : {"functionality" : [True, HardwareFunctionality]}})
