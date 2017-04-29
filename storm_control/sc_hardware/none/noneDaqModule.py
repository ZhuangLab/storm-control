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
    pass

    
class DOTaskFunctionality(daqModule.DaqFunctionality):
    pass

    
class NoneDaqModule(daqModule.DaqModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        
        # Create functionalities we will provide.
        self.daq_fns = {}
        self.daq_fns_by_source = {}
        for fn_name in configuration.getAttrs():
            task = configuration.get(fn_name)
            for task_name in task.getAttrs():
                task_params = task.get(task_name)
            
                daq_fn_name = ".".join([self.module_name, fn_name, task_name])
                if (task_name == "ao_task"):
                    ao_task = AOTaskFunctionality(source = task_params.get("source"))
                    self.daq_fns[daq_fn_name] = ao_task
                    self.daq_fns_by_source[ao_task.getSource()] = ao_task
                elif (task_name == "do_task"):
                    do_task = DOTaskFunctionality(source = task_params.get("source"))
                    self.daq_fns[daq_fn_name] = do_task
                    self.daq_fns_by_source[do_task.getSource()] = do_task
                else:
                    raise NoneDaqModuleException("Unknown task type", task_name)

    def getFunctionality(self, message):
        daq_fn_name = message.getData()["name"]
        if daq_fn_name in self.daq_fns:
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.daq_fns[daq_fn_name]}))

    def filmTiming(self, message):
        if self.run_shutters:

            # Disable functionalities & notify modules that were using them.
            for waveform in self.analog_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(True)
            for waveform in self.digital_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(True)

            # Notify film.film that we are ready.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "ready to film"))

    def stopFilm(self, message):
        if self.run_shutters:
            
            # Restore functionalities & notify modules that were using them.
            for waveform in self.analog_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(False)

            for waveform in self.digital_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(False)

        super().stopFilm(message)
