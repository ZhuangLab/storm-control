#!/usr/bin/env python
"""
HAL interface to National Instruments cards.

Hazen 04/17
"""
import numpy

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
            if self.task is not None:
                self.task.stopTask()
                self.task.clearTask()
                self.task = None
        else:
            self.createTask()


class AITaskFunctionality(NidaqFunctionality):
    """
    Asynchronous acquisition of a series of voltages.
    """
    def __init__(self, clock = None, lines = None, n_points = None, sampling_rate = None, **kwds):
        super().__init__(**kwds)
        self.clock = clock
        self.lines = lines
        self.n_points = n_points
        self.sampling_rate = sampling_rate

    def createTask(self):
        self.task = nicontrol.AnalogWaveformInput(source = self.lines[0])
        for line in self.lines[:1]:
            self.task.addChannel(source = line)
        self.task.configureAcquisition(source = self.clock,
                                       samples = self.n_points,
                                       sample_rate_Hz = self.sampling_rate)
        self.task.startTask()

    def getData(self):
        if self.task is None:
            self.createTask()
        try:
            return self.task.getData()
        except nicontrol.NIException as exception:
            hdebug.logText("AITaskFunctionality Error", str(exception))
            self.task.stopTask()
            self.createTask()


class AOTaskFunctionality(NidaqFunctionality):
    """
    Asynchronous output of a voltage on a single line.
    """
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


class CTTaskFunctionality(NidaqFunctionality):
    """
    Counter output.
    """
    def __init__(self, frequency = None, retriggerable = True, trigger_source = None, **kwds):
        super().__init__(**kwds)
        self.frequency = frequency
        self.retriggerable = retriggerable
        self.trigger_source = trigger_source
        
    def pwmOutput(self, duty_cycle = 0.5, cycles = 0):
        if self.task is not None:
            self.task.stopTask()
            self.task.clearTask()
            self.task = None
            
        if (duty_cycle > 0.0):
            self.task = nicontrol.CounterOutput(source = self.source,
                                                frequency = self.frequency,
                                                duty_cycle = duty_cycle)
            if self.trigger_source is not None:
                self.task.setTrigger(trigger_source = self.trigger_source,
                                     retriggerable = self.retriggerable)
            self.task.setCounter(cycles)
            self.task.startTask()

    
class DOTaskFunctionality(NidaqFunctionality):
    """
    Asynchronous output of a (digital) voltage on a single line.
    """
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


class WVTaskFunctionality(daqModule.DaqFunctionality):
    """
    For generating analog waveforms. 

    Notes: (1) This is meant for standalone devices like a galvo, not 
               for generating waveforms during filming, which is handled 
               by the daq module.

           (2) Lines needs to be in an order that is acceptable to NI.
    """
    def __init__(self, clock = None, lines = None, max_val = 10.0, min_val = -10.0, **kwds):
        super().__init__(**kwds)
        self.clock = clock
        self.lines = lines
        self.max_val = max_val
        self.min_val = min_val
        self.task = None

    def analogOut(self, values = None):
        """
        Output a single analog value on each line.
        """
        self.stopAndDelete()
        for i, line in enumerate(self.lines):
            nicontrol.setAnalogLine(line, values[i])

    def startStopTask(self, start):
        """
        True/False to start/stop the task.
        """
        if start:
            self.task.startTask()
        else:
            self.task.stopTask()
        
    def stopAndDelete(self):
        """
        Stop the waveform task and delete it, if it exists.
        """
        if self.task is not None:
            self.task.stopTask()
            self.task.clearTask()
            self.task = None
        
    def waveformOutput(self,
                       waveforms = None,
                       sample_rate = None,
                       finite = False,
                       rising = True,
                       start = True):
        """
        waveforms is a list of numpy arrays of type numpy.float64 that
        are assumed to be of equal length.
        """
        self.stopAndDelete()

        # Create task.
        self.task = nicontrol.AnalogWaveformOutput(self.lines[0],
                                                   max_val = self.max_val,
                                                   min_val = self.min_val)

        # Add lines.
        for line in self.lines[1:]:
            self.task.addChannel(source = line)

        # Add waveforms.
        self.task.setWaveforms(waveforms = waveforms,
                               sample_rate = sample_rate,
                               clock = self.clock,
                               finite = finite,
                               rising = rising)

        if start:
            self.task.startTask()
        

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
                if (task_name == "ai_task"):
                    lines = list(map(lambda x: x.strip(), task_params.get("lines").split(",")))
                    task = AITaskFunctionality(clock = task_params.get("clock"),
                                               lines = lines,
                                               n_points = task_params.get("n_points"),
                                               sampling_rate = task_params.get("sampling_rate"),
                                               source = lines[0])
                elif (task_name == "ao_task"):
                    task = AOTaskFunctionality(source = task_params.get("source"))
                elif (task_name == "ct_task"):
                    trigger_source = None
                    if task_params.has("trigger_source"):
                        trigger_source = task_params.get("trigger_source")
                    task = CTTaskFunctionality(source = task_params.get("source"),
                                               frequency = task_params.get("frequency"),
                                               retriggerable = task_params.get("retriggerable", False),
                                               trigger_source = trigger_source)
                elif (task_name == "do_task"):
                    task = DOTaskFunctionality(source = task_params.get("source"))
                elif (task_name == "wv_task"):
                    lines = list(map(lambda x: x.strip(), task_params.get("lines").split(",")))
                    task = WVTaskFunctionality(clock = task_params.get("clock"),
                                               lines = lines,
                                               source = lines[0])
                else:
                    raise NidaqModuleException("Unknown task type", task_name)
                
                self.daq_fns[daq_fn_name] = task
                self.daq_fns_by_source[task.getSource()] = task

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
            self.sendMessage(halMessage.HalMessage(m_type = "ready to film"))
            
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

                    rising_edge = True
                    if self.timing.has("rising_edge"):
                        rising_edge = self.timing.get("rising_edge")

                    self.ct_task.setTrigger(
                            trigger_source = self.timing.get("camera_fire_pin"),
                            rising_edge = rising_edge)
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
                        task.clearTask()
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

        # This frees the waveform arrays & reset the oversampling attribute.
        super().stopFilm(message)
