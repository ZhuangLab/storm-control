#!/usr/bin/env python
"""
HAL interface to National Instruments cards.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.daqModule as daqModule
import storm_control.sc_hardware.nationalInstruments.nicontrol as nicontrol

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.halExceptions as halExceptions


class NidaqModuleException(halExceptions.HardwareException):
    pass


class NidaqFunctionality(daqModule.DaqFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.am_filming = False
        self.task = None
        
    def setFilming(self, start):
        """
        start is True/False if filming is starting/stopping.
        """
        super().setFilming(start)
        if start:
            self.task.stopTask()
            self.task = None
        else:
            self.createTask()


class AOTaskFunctionality(NidaqFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def createTask(self):
        self.task = nicontrol.AnalogOutput(source = self.source)
        self.task.startTask()
        
    def output(self, voltage):
        super().output(voltage)
        if self.task is None:
            self.createTask()
        try:
            self.task.output(voltage)
        except nicontrol.NIException as exception:
            hdebug.logText("AOTaskFunctionality Error", str(exception))
            self.task.stopTask()
            self.createTask()


class DOTaskFunctionality(NidaqFunctionality):

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def createTask(self):
        self.task = nicontrol.DigitalOutput(source = self.source)
        self.task.startTask()
        
    def output(self, state):
        super().output(state)
        if self.task is None:
            self.createTask()
        try:
            self.task.output(state)
        except nicontrol.NIException as exception:
            hdebug.logText("DOTaskFunctionality Error", str(exception))
            self.task.stopTask()
            self.createTask()


class NidaqModule(daqModule.DaqModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        # These are the tasks that are used for waveform output.
        self.ao_task = None
        self.do_task = None
        self.ct_task = None
        
        configuration = module_params.get("configuration")
        self.default_timing = configuration.get("timing")
        self.timing = self.default_timing.copy()

        # Create functionalities we will provide, these are all Daq tasks.        
        self.daq_fns = {}
        self.daq_fns_by_source = {}
        for fn_name in configuration.getAttrs():
            
            # Don't provide a timing configuration, at least for now.
            if (fn_name == "timing"):
                continue

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
                    raise NidaqModuleException("Unknown task type", task_name)

    def filmTiming(self, message):
        """
        Get ready for waveform output when we get the film timing message, which
        includes the frames per second information that we need.
        """
        if self.run_shutters:

            # Get frames per second from the timing functionality. This is
            # a property of the camera that drives the timing functionality.
            fps = message.getData()["properties"]["functionality"].getFPS()
            
            # Calculate frequency. This is set slightly higher than the camere
            # frequency so that we are ready at the start of the next frame.
            frequency = 1.01 * fps * float(self.oversampling)

            # If oversampling is 1 then just trigger the ao_task 
            # and do_task directly off the camera fire pin.
            if (self.oversampling == 1):
                wv_clock = self.timing.get("camera_fire_pin")
            else:
                wv_clock = self.timing.get("counter_out")

            # Setup the counter.
            self.setupCounter(frequency)
            
            # Setup analog waveforms.
            self.setupAnalog(frequency, wv_clock)

            # Setup digital waveforms.
            self.setupDigital(frequency, wv_clock)

            # Notify film.film that we are ready.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "ready to film"))
            
    def getFunctionality(self, message):
        daq_fn_name = message.getData()["name"]
        if daq_fn_name in self.daq_fns:
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.daq_fns[daq_fn_name]}))

    def setupAnalog(self, frequency, wv_clock):
        """
        Configures for analog waveform output.
        """
        self.ao_task = None
        if (len(self.analog_waveforms) > 0):
            
            # Mark all the functionalities whose resources we'll need during
            # filming, and have them emit the 'filming' signal.
            for waveform in self.analog_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(True)

            # Sort by source.
            analog_data = sorted(self.analog_waveforms, key = lambda x: x.getSource())

            # Set waveforms.
            waveforms = []
            for data in analog_data:
                waveforms.append(data.getWaveform())

            def startAoTask():
                
                try:
                    # Create channels.
                    self.ao_task = nicontrol.AnalogWaveformOutput(source = analog_data[0].getSource())
                    for i in range(len(analog_data) - 1):
                        self.ao_task.addChannel(source = analog_data[i+1].getSource())

                    # Add waveforms
                    self.ao_task.setWaveforms(waveforms = waveforms,
                                              sample_rate = frequency,
                                              clock = wv_clock)

                    # Start task.
                    self.ao_task.startTask()
                except nicontrol.NIException as exception:
                    print(exception)
                    return True
                    
                return False

            iters = 0
            while (iters < 5) and startAoTask():
                hdebug.logText("startAoTask failed " + str(iters))
                time.sleep(0.1)
                iters += 1

            if (iters == 5):
                hdebug.logText("startAoTask critical failure")
                raise NidaqModuleException("NIException: startAoTask critical failure")
        
    def setupCounter(self, frequency):
        """
        Configures the counter for filming.
        """
        self.ct_task = None
        if (self.oversampling > 1):
            def startCtTask():
                try:
                    self.ct_task = nicontrol.CounterOutput(source = self.timing.get("counter"), 
                                                           frequency = frequency, 
                                                           duty_cycle = 0.5)
                    self.ct_task.setCounter(number_samples = self.oversampling)
                    self.ct_task.setTrigger(trigger_source = self.timing.get("camera_fire_pin"))
                    self.ct_task.startTask()
                except nicontrol.NIException as exception:
                    print(exception)
                    return True
                    
                return False

            iters = 0
            while (iters < 5) and startCtTask():
                hdebug.logText("startCtTask failed " + str(iters))
                time.sleep(0.5)
                iters += 1

            if (iters == 5):
                hdebug.logText("startCtTask critical failure")
                raise NidaqModuleException("NIException: startCtTask critical failure")

    def setupDigital(self, frequency, wv_clock):
        self.do_task = None
        if (len(self.digital_waveforms) > 0):

            # Mark all the functionalities whose resources we'll need during
            # filming, and have them emit the 'filming' signal.
            for waveform in self.digital_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(True)
                
            # Sort by board, channel.
            digital_data = sorted(self.digital_waveforms, key = lambda x: x.getSource())

            # Set waveforms.
            waveforms = []
            for data in digital_data:
                waveforms.append(data.getWaveform())

            def startDoTask():

                try:
                    # Create channels.
                    self.do_task = nicontrol.DigitalWaveformOutput(source = digital_data[0].getSource())
                    for i in range(len(digital_data) - 1):
                        self.do_task.addChannel(source = digital_data[i+1].getSource())

                    # Add waveform
                    self.do_task.setWaveforms(waveforms = waveforms,
                                              sample_rate = frequency,
                                              clock = wv_clock)

                    # Start task.
                    self.do_task.startTask()
                except nicontrol.NIException as exception:
                    print(exception)
                    return True

                return False

            iters = 0
            while (iters < 5) and startDoTask():
                hdebug.logText("startDoTask failed " + str(iters))
                time.sleep(0.1)
                iters += 1

            if iters == 5:
                hdebug.logText("startDoTask critical failure")
                raise NidaqModuleException("NIException: startDoTask critical failure")        

    def stopFilm(self, message):
        """
        Handle the 'stop film' message.
        """
        if self.run_shutters:
            for task in [self.ct_task, self.ao_task, self.do_task]:
                if task is not None:
                    try:
                        task.stopTask()
                    except nicontrol.NIException as e:
                        hdebug.logText("stop / clear failed for task " + str(task) + " with " + str(e))

            # Need to explicitly clear these so that PyDAQmx will release the resources.
            self.ao_task = None
            self.ct_task = None
            self.do_task = None

            # Restore functionalities & notify modules that were using them.
            for waveform in self.analog_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(False)

            for waveform in self.digital_waveforms:
                self.daq_fns_by_source[waveform.getSource()].setFilming(False)

        # This free the waveform arrays & reset the oversampling attribute.
        super().stopFilm(message)
