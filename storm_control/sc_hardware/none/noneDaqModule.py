#!/usr/bin/env python
"""
Emulated DAQ functionality.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.daqModule as daqModule

import storm_control.sc_library.halExceptions as halExceptions


class NoneDaqModuleException(halExceptions.HardwareException):
    pass


class AOTaskFunctionality(daqModule.DaqFunctionality):

    def output(self, voltage):
        pass

    
class DOTaskFunctionality(daqModule.DaqFunctionality):

    def output(self, state):
        pass

    
class NoneDaqModule(daqModule.DaqModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        
        # Create functionalities we will provide.
        self.daq_fns = {}
        for fn_name in configuration.getAttrs():
            task = configuration.get(fn_name)
            for task_name in task.getAttrs():
                task_params = task.get(task_name)
            
                daq_fn_name = ".".join([self.module_name, fn_name, task_name])
                if (task_name == "ao_task"):
                    self.daq_fns[daq_fn_name] = AOTaskFunctionality(source = task_params.get("source"),
                                                                    used_during_filming = task_params.get("used_during_filming"))
                elif (task_name == "do_task"):
                    self.daq_fns[daq_fn_name] = DOTaskFunctionality(source = task_params.get("source"),
                                                                    used_during_filming = task_params.get("used_during_filming"))
                else:
                    raise NoneDaqModuleException("Unknown task type", task_name)

    def getFunctionality(self, message):
        daq_fn_name = message.getData()["name"]
        if daq_fn_name in self.daq_fns:
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.daq_fns[daq_fn_name]}))
