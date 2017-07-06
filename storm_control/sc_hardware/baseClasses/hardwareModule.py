#!/usr/bin/env python
"""
The core functionality for a HAL hardware module. Most HAL
modules that interact with hardware are sub-classes of
this module.

Hazen 04/17
"""
#import copy

import time
from PyQt5 import QtCore

import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


def getThreadPool():
    """
    Return the applications threadpool instance. This is stored in halModule.
    """
    return halModule.threadpool

def runHardwareTask(module, message, task):
    """
    This just wraps halModule.runWorkerTask so that hardware modules do not
    need to also import halLib.halModule.

    Use this if your hardware module gets a message from HAL to do something 
    which it cannot process immediately. This includes error handling and as
    well as holding onto the message so that HAL knows that is has not been
    fully processed.
    """
    halModule.runWorkerTask(module, message, task)


class HardwareFunctionality(halFunctionality.HalFunctionality):
    """
    These are requested using the 'get functionality' message. The
    expected form of the "name" field of this message is the string
    "module_name.functionality_name".
    """
    pass


class HardwareWorker(QtCore.QRunnable):
    """
    Primarily this is used by BufferedFunctionality, but it may also 
    be useful by itself for one off communication with hardware.

    Note: These are all run with setAutoDelete(False) as it appears
          problematic to have Qt do the memory management.
    """
    def __init__(self, task = None, args = [], **kwds):
        super().__init__(**kwds)
        self.args = args
        self.task = task
        self.task_complete = False

    def isFinished(self):
        return self.task_complete
        
    def run(self):
        self.task(*self.args)
        self.task_complete = True


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
        self.running = True
        self.workers = []
        
        # This signal is used to let us know
        # when a worker has finished.
        self.done.connect(self.handleDone)

    def cleanUpWorkers(self):
        """
        Remove any workers that have finished.
        """
        still_working = []
        for worker in self.workers:
            if not worker.isFinished():
                still_working.append(worker)
        self.workers = still_working

    def handleDone(self):

        # Start the next 'maybe' request, if there was one.
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
            self.busy = True
            self.start(task, args, ret_signal)
        else:
            self.next_request = [task, args, ret_signal]

    def mustRun(self, task = None, args = [], ret_signal = None):
        """
        Call this method with requests that must be processed.

        FIXME: There is some danger here of being able to build up a
               large backlog of QRunnables that are waiting to run.
        """
        self.start(task, args, ret_signal)

    def run(self, task, args, ret_signal):
        """
        run the task with arguments args, and use the ret_signal
        pyqtSignal to return the results.
        """
        self.busy = True
        self.device_mutex.lock()
        retv = task(*args)
        self.device_mutex.unlock()
        self.busy = False
        self.done.emit()
        if ret_signal is not None:
            ret_signal.emit(retv)

    def start(self, task, args, ret_signal):
        hw = HardwareWorker(task = self.run,
                            args = [task, args, ret_signal])
        self.startWorker(hw)

    def startWorker(self, worker):
        if not self.running:
            return

        # Remove any old workers that have finished.
        self.cleanUpWorkers()

        # We need to manage the workers ourselves because otherwise we'll
        # experience strange/sporadic errors like the GUI freezing.
        worker.setAutoDelete(False)
        self.workers.append(worker)
        
        getThreadPool().start(worker)
        
    def wait(self):
        """
        Block job submission and wait for the last job to finish.
        """
        self.running = False
        while(self.busy):
            print("BufferedFunctionality wait")
            time.sleep(0.1)

        self.cleanUpWorkers()


class HardwareModule(halModule.HalModule):

    def __init__(self, **kwds):
        super().__init__(**kwds)

