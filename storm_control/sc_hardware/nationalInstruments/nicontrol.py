#!/usr/bin/env python
"""
Communicates with the National Instrument card(s).

Hazen 4/17
"""

import ctypes
import numpy
import time
import traceback
import threading

import PyDAQmx

import storm_control.sc_library.halExceptions as halExceptions


timeout = 1.0

def getLock():
    return threading.RLock()


class NIException(halExceptions.HardwareException):
    """
    National instruments error.
    """
    pass


class NIDAQTask(PyDAQmx.Task):
    """
    A thin wrapper on PyDAQmx because we think that we need
    thread locks, and we also want to get NI status errors.
    """

    def __init__(self, **kwds):
        with getLock():
            super().__init__(**kwds)

    def clearTask(self):
        with getLock():
            super().ClearTask()

    def startTask(self):
        with getLock():
            super().StartTask()

    def stopTask(self):
        with getLock():
            super().StopTask()

    def taskIsDone(self):
        done = ctypes.c_long(0)
        with getLock():
            self.IsTaskDone(ctypes.byref(done))
        return done.value


class AnalogOutput(NIDAQTask):
    """
    Simple analog output class
    """
    def __init__(self, source = None, min_val = -10.0, max_val = 10.0, **kwds):
        super().__init__(**kwds)
        with getLock():
            self.CreateAOVoltageChan(source,
                                     "", 
                                     min_val, 
                                     max_val, 
                                     PyDAQmx.DAQmx_Val_Volts,
                                     None)
            
    def output(self, voltage):
        """
        Output a single voltage more or less as soon as it is called, 
        assuming that no other task is running.
        """
        with getLock():
            self.WriteAnalogScalarF64(1, timeout, voltage, None)


class AnalogWaveformInput(NIDAQTask):
    """
    Geared towards acquiring a fixed number of samples at a predefined rate,
    asynchronously timed off the internal clock.
    """
    def __init__(self, source = None, min_val = -10.0, max_val = 10.0, **kwds):
        super().__init__(**kwds)
        
        self.channels = 1
        self.max_val = max_val
        self.min_val = min_val
        
        with getLock():
            self.CreateAIVoltageChan(source,
                                     "",
                                     PyDAQmx.DAQmx_Val_RSE,
                                     self.min_val,
                                     self.max_val,
                                     PyDAQmx.DAQmx_Val_Volts,
                                     None)

    def addChannel(self, source = None):
        """
        Add additional channels to the acquisition.
        """
        self.channels += 1
        with getLock():
            self.CreateAIVoltageChan(source,
                                     "",
                                     PyDAQmx.DAQmx_Val_RSE,
                                     self.min_val, 
                                     self.max_val, 
                                     PyDAQmx.DAQmx_Val_Volts,
                                     None)

    def configureAcquisition(self, source = None, samples = None, sample_rate_Hz = None):
        """
        Set the sample timing and buffer length.
        """
        if source is None:
            source = ""
        self.samples = samples
        with getLock():
            self.CfgSampClkTiming(source,
                                  sample_rate_Hz,
                                  PyDAQmx.DAQmx_Val_Rising,
                                  PyDAQmx.DAQmx_Val_FiniteSamps,
                                  self.samples)

    def getData(self):
        """
        Acquire the data from the DAQ card.
        """
        data = numpy.zeros((self.samples * self.channels), dtype = numpy.float64)
        c_samples_read = ctypes.c_long(0)
        with getLock():
            self.ReadAnalogF64(self.samples,
                               timeout,
                               PyDAQmx.DAQmx_Val_GroupByChannel,
                               data,
                               self.samples,
                               ctypes.byref(c_samples_read),
                               None)
        if (c_samples_read.value != self.samples):
            msg = "Failed to read the right number of samples "
            msg += str(c_samples_read.value) + " " + str(self.samples)
            raise NIException(msg)
        return numpy.reshape(data, (self.samples, self.channels))


class AnalogWaveformOutput(NIDAQTask):
    """
    Analog waveform output class.
    """
    def __init__(self, source = None, min_val = -10.0, max_val = 10.0, **kwds):
        super().__init__(**kwds)
        
        self.channels = 1
        self.max_val = max_val
        self.min_val = min_val

        with getLock():
            self.CreateAOVoltageChan(source,
                                     "", 
                                     self.min_val, 
                                     self.max_val, 
                                     PyDAQmx.DAQmx_Val_Volts,
                                     "")

    def addChannel(self, source = None):
        """
        Add additional channels to the waveform task. Note that these have
        to be added sequentially with increasing channel number (I'm pretty sure).
        """
        self.channels += 1
        with getLock():
            self.CreateAOVoltageChan(source,
                                     "", 
                                     self.min_val, 
                                     self.max_val, 
                                     PyDAQmx.DAQmx_Val_Volts, 
                                     "")

    def setWaveforms(self, waveforms = None, sample_rate = None, clock = None, finite = False, rising = True):
        """
        The output waveforms for all the analog channels are expected
        to be a list of equal length numpy arrays of type numpy.float64.

        You need to add all your channels first before calling this.
        """
        assert isinstance(waveforms, list)
        assert isinstance(waveforms[0], numpy.ndarray)
        assert (waveforms[0].dtype == numpy.float64)
                            
        waveform_len = waveforms[0].size

        # Set the timing for the waveform.
        if finite:
            sample_mode = PyDAQmx.DAQmx_Val_FiniteSamps
        else:
            sample_mode = PyDAQmx.DAQmx_Val_ContSamps
        
        if rising:
            rising = PyDAQmx.DAQmx_Val_Rising
        else:
            rising = PyDAQmx.DAQmx_Val_Falling
        
        with getLock():
            self.CfgSampClkTiming(clock,
                                  sample_rate,
                                  rising,
                                  sample_mode,
                                  waveform_len)

        # Transfer the waveform data to the DAQ board buffer.
        waveform = numpy.ascontiguousarray(numpy.concatenate(waveforms), dtype = numpy.float64)        
        c_samples_written = ctypes.c_long(0)
        with getLock():
            self.WriteAnalogF64(waveform_len,
                                0,
                                timeout,
                                PyDAQmx.DAQmx_Val_GroupByChannel,
                                waveform,
                                ctypes.byref(c_samples_written),
                                None)

        if (c_samples_written.value != waveform_len):
            msg = "Failed to write the right number of samples "
            msg += str(c_samples_written.value) + " " + str(waveform_len)
            raise NIException(msg)
        

class CounterOutput(NIDAQTask):
    """
    Counter output class.
    """
    def __init__(self, source = None, frequency = None, duty_cycle = None, initial_delay = 0.0, **kwds):
        super().__init__(**kwds)
        with getLock():
            self.CreateCOPulseChanFreq(source,
                                       "",
                                       PyDAQmx.DAQmx_Val_Hz,
                                       PyDAQmx.DAQmx_Val_Low,
                                       initial_delay,
                                       frequency,
                                       duty_cycle)

    def setCounter(self, number_samples = None):
        """
        Number of waveform cycles to output, zero is continuous.
        """
        with getLock():
            if (number_samples > 0):
                self.CfgImplicitTiming(PyDAQmx.DAQmx_Val_FiniteSamps,
                                       number_samples)
            else:
                self.CfgImplicitTiming(PyDAQmx.DAQmx_Val_ContSamps,
                                       1000)

    def removeTrigger(self):
        """
        Remove the trigger for this task.
        """
        with getLock():
            self.DisableStartTrig()
                
    def setTrigger(self, trigger_source = None, retriggerable = True,
				rising_edge = True):
        if retriggerable:
            with getLock():
                self.SetStartTrigRetriggerable(1)
        else:
            with getLock():
                self.SetStartTrigRetriggerable(0)
        
        with getLock():
            if rising_edge:
                self.CfgDigEdgeStartTrig(trigger_source,
                                     PyDAQmx.DAQmx_Val_Rising)
            else:
                self.CfgDigEdgeStartTrig(trigger_source,
                                     PyDAQmx.DAQmx_Val_Falling)

    def trigger(self):
        with getLock():
            self.SendSoftwareTrigger(PyDAQmx.DAQmx_Val_AdvanceTrigger)


class DigitalOutput(NIDAQTask):
    """
    Digital output task (for simple non-triggered digital output).
    """
    def __init__(self, source = None, **kwds):
        super().__init__(**kwds)
        with getLock():
            self.CreateDOChan(source,
                              "",
                              PyDAQmx.DAQmx_Val_ChanPerLine)

    def output(self, state = None):
        if bool(state):
            data = numpy.array([1], dtype = numpy.uint8)
        else:
            data = numpy.array([0], dtype = numpy.uint8)

        c_written = ctypes.c_int32(0)
        with getLock():
            self.WriteDigitalLines(1,
                                   1,
                                   timeout,
                                   PyDAQmx.DAQmx_Val_GroupByChannel,
                                   data,
                                   ctypes.byref(c_written),
                                   None)
        if (c_written.value != 1):
            raise NIException("Digital output failed")


class DigitalInput(NIDAQTask):
    """
    Digital input task (for simple non-triggered digital input).
    """
    def __init__(self, source = None, **kwds):
        super().__init__(**kwds)
        with getLock():
            self.CreateDIChan(source,
                              "",
                              PyDAQmx.DAQmx_Val_ChanPerLine)
            
    def input(self):
        data = numpy.array([0], dtype = numpy.uint8)
        c_samps_read = ctypes.c_int32(0)
        c_bytes_per_samp = ctypes.c_int32(0)
        with getLock():
            self.ReadDigitalLines(PyDAQmx.DAQmx_Val_Auto,
                                  timeout,
                                  PyDAQmx.DAQmx_Val_GroupByChannel,
                                  data,
                                  1,
                                  ctypes.byref(c_samps_read),
                                  ctypes.byref(c_bytes_per_samp),
                                  None)
            
        if (c_samps_read.value != 1):
            raise NIException("Digital input failed")

        return bool(data[0])


class DigitalWaveformOutput(NIDAQTask):
    """
    Digital waveform output class.
    """
    def __init__(self, source = None, **kwds):
        super().__init__(**kwds)
        self.channels = 1
        with getLock():
            self.CreateDOChan(source,
                              "",
                              PyDAQmx.DAQmx_Val_ChanPerLine)
            
    def addChannel(self, source = None):
        """
        Add a channel to the task. I'm pretty sure that the channels have to be added
        sequentially in order of increasing line number (at least on the same board).
        """
        self.channels += 1
        with getLock():
            self.CreateDOChan(source,
                              "",
                              PyDAQmx.DAQmx_Val_ChanPerLine)
            
    def setWaveforms(self, waveforms = None, sample_rate = None, clock = None, finite = False, rising = True):
        """
        The output waveforms for all the analog channels are expected
        to be a list of equal length numpy arrays of type numpy.uint8.

        You need to add all your channels first before calling this.
        """
        assert isinstance(waveforms, list)
        assert isinstance(waveforms[0], numpy.ndarray)
        assert (waveforms[0].dtype == numpy.uint8)

        waveform_len = waveforms[0].size

        # Set the timing for the waveform.
        if finite:
            sample_mode = PyDAQmx.DAQmx_Val_FiniteSamps
        else:
            sample_mode = PyDAQmx.DAQmx_Val_ContSamps
        
        if rising:
            rising = PyDAQmx.DAQmx_Val_Rising
        else:
            rising = PyDAQmx.DAQmx_Val_Falling
        
        with getLock():
            self.CfgSampClkTiming(clock,
                                  sample_rate,
                                  rising,
                                  sample_mode,
                                  waveform_len)

        # Transfer the waveform data to the DAQ board buffer.
        waveform = numpy.ascontiguousarray(numpy.concatenate(waveforms), dtype = numpy.uint8)
        c_samples_written = ctypes.c_long(0)
        with getLock():
            self.WriteDigitalLines(waveform_len,
                                   0,
                                   timeout,
                                   PyDAQmx.DAQmx_Val_GroupByChannel,
                                   waveform,
                                   ctypes.byref(c_samples_written),
                                   None)

        if (c_samples_written.value != waveform_len):
            msg = "Failed to write the right number of samples "
            msg += str(c_samples_written.value) + " " + str(waveform_len)
            raise NIException(msg)


#
# Convenience functions.
#

def setAnalogLine(source, voltage):
    task = AnalogOutput(source = source)
    task.output(voltage)
    task.stopTask()

def setDigitalLine(source, value):
    task = DigitalOutput(source = source)
    task.output(value)
    task.stopTask()


if (__name__ == "__main__"):

    if True:
        di = DigitalInput(source = "Dev1/port0/line0")
        print(di.input())

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
