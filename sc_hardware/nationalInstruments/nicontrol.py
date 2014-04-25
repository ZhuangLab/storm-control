#!/usr/bin/python
#
## @file
#
# Communicates with the National Instrument card(s).
#
# Hazen 3/12
#

from ctypes import *
import time
import traceback

# Load the NIDAQmx driver library.
nidaqmx = windll.nicaiu

# Constants
DAQmx_Val_ChanForAllLines = 1
DAQmx_Val_ChanPerLine = 0
DAQmx_Val_ContSamps = 10123
DAQmx_Val_Falling = 10171
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_High = 10192
DAQmx_Val_Hz = 10373
DAQmx_Val_Low = 10214
DAQmx_Val_Rising = 10280
DAQmx_Val_Volts = 10348
DAQmx_Val_RSE = 10083
DAQmx_Val_NRSE = 10078
DAQmx_Val_Diff = 10106
DAQmx_Val_PseudoDiff = 12529

TaskHandle = c_ulong


#
# Utility functions
#

## checkStatus
#
# If status is an error code this prints the error code and
# the corresponding text as well as the current call stack.
#
# @param status The return value from a NI library function call.
#
def checkStatus(status):
    if status < 0:
        buf_size = 1000
        buf = create_string_buffer(buf_size)
        nidaqmx.DAQmxGetErrorString(c_long(status), buf, buf_size)
        print "nidaq error:", status, buf.value
        traceback.print_stack()
        print " --"
        #raise RuntimeError('nidaq call failed with error %d: %s'%(status, buf.value))


#
# NIDAQ functions
#

## getDAQBoardInfo
#
# @return A array listing the NI devices that are currently attached to the computer.
#
def getDAQBoardInfo():
    daq_boards = []
    devices_len = 100
    devices = create_string_buffer(devices_len)
    checkStatus(nidaqmx.DAQmxGetSysDevNames(devices, devices_len))
    devices_string = devices.value
    for dev in devices_string.split(", "):
        dev_data_len = 100
        dev_data = create_string_buffer(dev_data_len)
        c_dev = c_char_p(dev)
        checkStatus(nidaqmx.DAQmxGetDevProductType(c_dev, dev_data, dev_data_len))
        daq_boards.append([dev_data.value, dev[-1:]])
    return daq_boards

## getBoardDevNumber
#
# Return the device number that corresponds to a given board
# This assumes that you do not have two identically named boards.
#
# @param board The board name as a string.
#
# @return The device number.
#
def getBoardDevNumber(board):
    available_boards = getDAQBoardInfo()
    index = 1
    device_number = 0
    for available_board in available_boards:
        if board == available_board[0]:
            device_number = available_board[1]
        index += 1
        
    assert device_number != 0, str(board) + " is not available."

    return device_number

#
# DAQ communication classes
#

## NIDAQTask
#
# NIDAQmx task base class
#
class NIDAQTask():

    ## __init__
    #
    # @param board The board name as a string.
    #
    def __init__(self, board):
        self.board_number = getBoardDevNumber(board)
        self.taskHandle = TaskHandle(0)
        checkStatus(nidaqmx.DAQmxCreateTask("", byref(self.taskHandle)))

    ## clearTask
    #
    # Clears the task from the board.
    #
    def clearTask(self):
        checkStatus(nidaqmx.DAQmxClearTask(self.taskHandle))

    ## startTask
    #
    # Starts the task.
    #
    def startTask(self):
        checkStatus(nidaqmx.DAQmxStartTask(self.taskHandle))

    ## stopTask
    #
    # Stops the task.
    #
    def stopTask(self):
        checkStatus(nidaqmx.DAQmxStopTask(self.taskHandle))

    ## taskIsDoneP
    #
    # FIXME: This doesn't look like it would work. Do we even use it?
    #
    # @return 1/0 The task is done.
    #
    def taskIsDoneP(self):
        #done = c_long(0)
        checkStatus(nidaqmx.DAQmxIsTaskDone(self.taskHandle, None))
        return done.value


## AnalogOutput
#                    
# Simple analog output class
#
class AnalogOutput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The channel to use for output.
    # @param min_val (Optional) Defaults to -10.0V.
    # @param max_val (Optional) Defaults to 10.0V.
    #
    def __init__(self, board, channel, min_val = -10.0, max_val = 10.0):
        NIDAQTask.__init__(self, board)
        self.channel = channel
        self.dev_and_channel = "Dev" + str(self.board_number) + "/ao" + str(self.channel)
        checkStatus(nidaqmx.DAQmxCreateAOVoltageChan(self.taskHandle, 
                                                     c_char_p(self.dev_and_channel),
                                                     "", 
                                                     c_double(min_val), 
                                                     c_double(max_val), 
                                                     c_int(DAQmx_Val_Volts), 
                                                     ""))

    ## output
    #
    # Output a single voltage more or less as soon as it is called, 
    # assuming that no other task is running.
    #
    # @param voltage The voltage to output.
    #
    def output(self, voltage):
        c_samples_written = c_long(0)
        c_voltage = c_double(voltage)
        checkStatus(nidaqmx.DAQmxWriteAnalogF64(self.taskHandle, 
                                                c_long(1),
                                                c_long(1),
                                                c_double(10.0),
                                                c_long(DAQmx_Val_GroupByChannel),
                                                byref(c_voltage),
                                                byref(c_samples_written), 
                                                None))
        assert c_samples_written.value == 1, "outputVoltage failed: " + str(c_samples_written.value) + " 1"


## AnalogWaveformInput
#
# Analog input class
#
# Geared towards acquiring a fixed number of samples at a predefined rate,
# asynchronously timed off the internal clock.
#
class AnalogWaveformInput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The channel to use for input.
    # @param min_val (Optional) Defaults to -10.0V.
    # @param max_val (Optional) Defaults to 10.0V.
    #
    def __init__(self, board, channel, min_val = -10.0, max_val = 10.0):
        NIDAQTask.__init__(self, board)
        self.c_waveform = 0
        self.dev_and_channel = "Dev" + str(self.board_number) + "/ai" + str(channel)
        self.min_val = min_val
        self.max_val = max_val
        self.channels = 1
        checkStatus(nidaqmx.DAQmxCreateAIVoltageChan(self.taskHandle, 
                                                     c_char_p(self.dev_and_channel),
                                                     "",
                                                     c_int(DAQmx_Val_RSE),
                                                     c_double(self.min_val), 
                                                     c_double(self.max_val), 
                                                     c_int(DAQmx_Val_Volts),
                                                     None))

    ## addChannel
    #
    # Add a channel to the task. I'm pretty sure they have to be added sequentially
    # with increasing channel number.
    #
    # @param channel The channel to add.
    #
    def addChannel(self, channel):
        self.channels += 1
        self.dev_and_channel = "Dev" + str(self.board_number) + "/ai" + str(channel)        
        checkStatus(nidaqmx.DAQmxCreateAIVoltageChan(self.taskHandle, 
                                                     c_char_p(self.dev_and_channel),
                                                     "",
                                                     c_int(DAQmx_Val_RSE),
                                                     c_double(self.min_val), 
                                                     c_double(self.max_val), 
                                                     c_int(DAQmx_Val_Volts),
                                                     None))

    ## configureAcquisition
    #
    # Set the sample timing and buffer length.
    #
    # @param samples The number of samples to acquire.
    # @param sample_rate_Hz The sampling rate (in Hz).
    #
    def configureAcquisition(self, samples, sample_rate_Hz):
        self.samples = samples
        checkStatus(nidaqmx.DAQmxCfgSampClkTiming(self.taskHandle,
                                                  "",
                                                  c_double(sample_rate_Hz),
                                                  c_long(DAQmx_Val_Rising),
                                                  c_long(DAQmx_Val_FiniteSamps),
                                                  c_ulonglong(self.samples)))

    ## getData
    #
    # Get the acquired data from the DAQ card.
    #
    # @return The data as a flat c-types array of size samples * channels.
    #
    def getData(self):
        # allocate space to store the data.
        c_data_type = c_double * (self.samples * self.channels)
        data = c_data_type()
        # acquire the data.
        c_samples_read = c_long(0)
        checkStatus(nidaqmx.DAQmxReadAnalogF64(self.taskHandle,
                                               c_long(self.samples),
                                               c_double(10.0),
                                               c_long(DAQmx_Val_GroupByChannel),
                                               byref(data),
                                               c_ulong(self.channels*self.samples),
                                               byref(c_samples_read),
                                               None))
        assert c_samples_read.value == self.samples, "Failed to read the right number of samples " + str(c_samples_read.value) + " " + str(self.samples)
        return data


## AnalogWaveformOutput
#
# Analog waveform output class
#
class AnalogWaveformOutput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The channel to use for output.
    # @param min_val (Optional) Defaults to -10.0V.
    # @param max_val (Optional) Defaults to 10.0V.
    #
    def __init__(self, board, channel, min_val = -10.0, max_val = 10.0):
        NIDAQTask.__init__(self, board)
        self.c_waveform = 0
        self.dev_and_channel = "Dev" + str(self.board_number) + "/ao" + str(channel)
        self.min_val = min_val
        self.max_val = max_val
        self.channels = 1
        checkStatus(nidaqmx.DAQmxCreateAOVoltageChan(self.taskHandle, 
                                                     c_char_p(self.dev_and_channel),
                                                     "", 
                                                     c_double(self.min_val), 
                                                     c_double(self.max_val), 
                                                     c_int(DAQmx_Val_Volts), 
                                                     ""))

    ## addChannel
    #
    # Add additional channels to the waveform task. Note that these have
    # to be added sequentially with increasing channel number (I'm pretty sure).
    #
    # @param board The board name.
    # @param channel The channel to use for output.
    #
    def addChannel(self, board, channel):
        self.channels += 1
        board_number = self.board_number
        if board:
            board_number = getBoardDevNumber(board)
        self.dev_and_channel = "Dev" + str(board_number) + "/ao" + str(channel)
        checkStatus(nidaqmx.DAQmxCreateAOVoltageChan(self.taskHandle, 
                                                     c_char_p(self.dev_and_channel),
                                                     "", 
                                                     c_double(self.min_val), 
                                                     c_double(self.max_val), 
                                                     c_int(DAQmx_Val_Volts), 
                                                     ""))

    ## setWaveform
    #
    # The output waveforms for all the analog channels are stored in one 
    # big array, so the per channel waveform length is the total length 
    # divided by the number of channels.
    #
    # You need to add all your channels first before calling this.
    #
    # @param waveform A python array containing the wave form data.
    # @param sample_rate The update frequency at which the wave form will be output.
    # @param finite (Optional) Output the wave form repeatedly or just once, defaults to repeatedly.
    # @param clock (Optional) The clock signal to use as a time base for the wave form, defaults to ctr0out.
    # @param rising (Optional) Update on the rising or falling edge, defaults to rising.
    #
    def setWaveform(self, waveform, sample_rate, finite = 0, clock = "ctr0out", rising = True):
        waveform_len = len(waveform)/self.channels

        clock_source = ""
        if len(clock) > 0:
            clock_source = "/Dev" + str(self.board_number) + "/" + str(clock)

        # set the timing for the waveform.
        sample_mode = DAQmx_Val_ContSamps
        if finite:
            sample_mode = DAQmx_Val_FiniteSamps
        c_rising = c_long(DAQmx_Val_Rising)
        if (not rising):
            c_rising = c_long(DAQmx_Val_Falling)
        checkStatus(nidaqmx.DAQmxCfgSampClkTiming(self.taskHandle,
                                                  c_char_p(clock_source),
                                                  c_double(sample_rate),
                                                  c_rising,
                                                  c_long(sample_mode),
                                                  c_ulonglong(waveform_len)))

        # transfer the waveform data to the DAQ board buffer.
        data_len = len(waveform)
        c_samples_written = c_long(data_len)
        c_wave_form_type = c_double * data_len
        self.c_waveform = c_wave_form_type()
        for i in range(data_len):
            self.c_waveform[i] = c_double(waveform[i])
        checkStatus(nidaqmx.DAQmxWriteAnalogF64(self.taskHandle, 
                                                c_long(waveform_len),
                                                c_long(0),
                                                c_double(10.0),
                                                c_long(DAQmx_Val_GroupByChannel),
                                                byref(self.c_waveform), 
                                                byref(c_samples_written), 
                                                None))
        assert c_samples_written.value == waveform_len, "Failed to write the right number of samples " + str(c_samples_written.value) + " " + str(waveform_len)


## CounterOutput
#
# Counter output class.
#
class CounterOutput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The counter to use.
    # @param frequency The frequency of the output square wave.
    # @param duty_cycle The duty cycle of the square wave.
    # @param initial_delay (Optional) The delay between the trigger signal and starting output, defaults to 0.0.
    #
    def __init__(self, board, channel, frequency, duty_cycle, initial_delay = 0.0):
        NIDAQTask.__init__(self, board)
        self.channel = channel
        self.dev_and_channel = "Dev" + str(self.board_number) + "/ctr" + str(self.channel)
	checkStatus(nidaqmx.DAQmxCreateCOPulseChanFreq(self.taskHandle,
                                                       c_char_p(self.dev_and_channel),
                                                       "",
                                                       c_long(DAQmx_Val_Hz),
                                                       c_long(DAQmx_Val_Low),
                                                       c_double(initial_delay),
                                                       c_double(frequency),
                                                       c_double(duty_cycle)))

    ## setCounter
    #
    # @param number_samples Number of waveform cycles to output, zero is continuous.
    #
    def setCounter(self, number_samples):
        if (number_samples > 0):
            checkStatus(nidaqmx.DAQmxCfgImplicitTiming(self.taskHandle,
                                                       c_long(DAQmx_Val_FiniteSamps),
                                                       c_ulonglong(number_samples)))
        else:
            checkStatus(nidaqmx.DAQmxCfgImplicitTiming(self.taskHandle,
                                                       c_long(DAQmx_Val_ContSamps),
                                                       c_ulonglong(1000)))

    ## setTrigger
    #
    # @param trigger_source The pin to use as the trigger source.
    # @param retriggerable (Optional) The task can be repeatedly triggered (or not), defaults to repeatedly.
    # @param board (Optional) The board the trigger pin is located on, defaults to the board specified as object creation.
    #
    def setTrigger(self, trigger_source, retriggerable = 1, board = None):
        if retriggerable:
            checkStatus(nidaqmx.DAQmxSetStartTrigRetriggerable(self.taskHandle, 
                                                               c_long(1)))
        else:
            checkStatus(nidaqmx.DAQmxSetStartTrigRetriggerable(self.taskHandle, 
                                                               c_long(0)))
        board_number = self.board_number
        if board:
            board_number = getBoardDevNumber(board)
        trigger = "/Dev" + str(board_number) + "/PFI" + str(trigger_source)
	checkStatus(nidaqmx.DAQmxCfgDigEdgeStartTrig(self.taskHandle,
                                                     c_char_p(trigger),
                                                     c_long(DAQmx_Val_Rising)))


## DigitalOutput
#
# Digital output task (for simple non-triggered digital output).
#
class DigitalOutput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The digital channel to use.
    #
    def __init__(self, board, channel):
        NIDAQTask.__init__(self, board)
        self.channel = channel
        self.dev_and_channel = "Dev" + str(self.board_number) + "/port0/line" + str(self.channel)
        checkStatus(nidaqmx.DAQmxCreateDOChan(self.taskHandle,
                                              c_char_p(self.dev_and_channel),
                                              "",
                                              c_long(DAQmx_Val_ChanPerLine)))

    ## output
    #
    # @param high True/False Output a high/low voltage.
    #
    def output(self, high):
        if high:
            c_data = c_byte(1)
        else:
            c_data = c_byte(0)
        c_written = c_long(0)
        checkStatus(nidaqmx.DAQmxWriteDigitalLines(self.taskHandle,
                                                   c_long(1),
                                                   c_long(1),
                                                   c_double(10.0),
                                                   c_long(DAQmx_Val_GroupByChannel),
                                                   byref(c_data),
                                                   byref(c_written),
                                                   None))
        assert c_written.value == 1, "Digital output failed"


## DigitalInput
#
# Digital input task (for simple non-triggered digital input).
#
class DigitalInput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param channel The digital channel to use for input.
    #
    def __init__(self, board, channel):
        NIDAQTask.__init__(self, board)
        self.channel = channel
        self.dev_and_channel = "Dev" + str(self.board_number) + "/port0/line" + str(self.channel)
        checkStatus(nidaqmx.DAQmxCreateDIChan(self.taskHandle,
                                              c_char_p(self.dev_and_channel),
                                              "",
                                              c_long(DAQmx_Val_ChanPerLine)))

    ## input
    #
    # @return True/False the input line is high/low.
    #
    def input(self):
        c_read = c_byte(0)
        c_samps_read = c_long(0)
        c_bytes_per_samp = c_long(0)
        checkStatus(nidaqmx.DAQmxReadDigitalLines(self.taskHandle,
                                                  c_long(-1),
                                                  c_double(10.0),
                                                  c_long(DAQmx_Val_GroupByChannel),
                                                  byref(c_read),
                                                  c_long(1),
                                                  byref(c_samps_read),
                                                  byref(c_bytes_per_samp),
                                                  None))
        assert c_samps_read.value == 1, "Digital input failed"
        if c_read.value == 1:
            return 1
        else:
            return 0


## DigitalWaveformOutput
#
# Digital waveform output class.
#
class DigitalWaveformOutput(NIDAQTask):

    ## __init__
    #
    # @param board The board name.
    # @param line The digital line to use for wave form output.
    #
    def __init__(self, board, line):
        NIDAQTask.__init__(self, board)
        self.dev_line = "Dev" + str(self.board_number) + "/port0/line" + str(line)
        self.channels = 1
        checkStatus(nidaqmx.DAQmxCreateDOChan(self.taskHandle,
                                              c_char_p(self.dev_line),
                                              "",
                                              c_int(DAQmx_Val_ChanPerLine)))

    ## addChannel
    #
    # Add a channel to the task. I'm pretty sure that the channels have to be added
    # sequentially in order of increasing line number (at least on the same board).
    #
    # @param board The board name.
    # @param line The digital line.
    #
    def addChannel(self, board, line):
        self.channels += 1
        self.dev_line = "Dev" + str(self.board_number) + "/port0/line" + str(line)
        checkStatus(nidaqmx.DAQmxCreateDOChan(self.taskHandle,
                                              c_char_p(self.dev_line),
                                              "",
                                              c_int(DAQmx_Val_ChanPerLine)))

    ## setWaveform
    #
    # The output waveforms for all the digital channels are stored in one 
    # big array, so the per channel waveform length is the total length 
    # divided by the number of channels.
    #
    # You need to add all your channels first before calling this.
    #
    # @param waveform A python array containing the wave form data.
    # @param sample_rate The update rate for wave form output.
    # @param finite (Optional) Output the wave form once or repeatedly, defaults to repeatedly.
    # @param clock (Optional) The clock signal that will drive the wave form output, defaults to "ctr0out".
    # @param rising (Optional) True/False update on the rising edge, defaults to True.
    #
    def setWaveform(self, waveform, sample_rate, finite = 0, clock = "ctr0out", rising = True):
        waveform_len = len(waveform)/self.channels

        clock_source = ""
        if len(clock) > 0:
            clock_source = "/Dev" + str(self.board_number) + "/" + str(clock)

        # set the timing for the waveform.
        sample_mode = DAQmx_Val_ContSamps
        if finite:
            sample_mode = DAQmx_Val_FiniteSamps
        c_rising = c_long(DAQmx_Val_Rising)
        if (not rising):
            c_rising = c_long(DAQmx_Val_Falling)
        checkStatus(nidaqmx.DAQmxCfgSampClkTiming(self.taskHandle,
                                                  c_char_p(clock_source),
                                                  c_double(sample_rate),
                                                  c_rising,
                                                  c_long(sample_mode),
                                                  c_ulonglong(waveform_len)))

        # transfer the waveform data to the DAQ board buffer.
        data_len = len(waveform)
        c_samples_written = c_int(data_len)
        c_wave_form_type = c_uint8 * data_len
        self.c_waveform = c_wave_form_type()
        for i in range(data_len):
            if (waveform[i] > 0):
                self.c_waveform[i] = c_uint8(1)
            else:
                self.c_waveform[i] = c_uint8(0)
        checkStatus(nidaqmx.DAQmxWriteDigitalLines(self.taskHandle,
                                                   c_int(waveform_len),
                                                   c_int(0),
                                                   c_double(10.0),
                                                   c_int(DAQmx_Val_GroupByChannel),
                                                   byref(self.c_waveform), 
                                                   byref(c_samples_written), 
                                                   None))
        assert c_samples_written.value == waveform_len, "Failed to write the right number of samples " + str(c_samples_written.value) + " " + str(waveform_len)

#
# Convenience functions.
#

## setAnalogLine
#
# @param board The board name.
# @param line The analog output line.
# @param voltage The desired voltage.
#
def setAnalogLine(board, line, voltage):
    task = AnalogOutput(board, line)
    task.output(voltage)
    task.stopTask()
    task.clearTask()

## setDigitalLine
#
# @param board The board name.
# @param line The digital output line.
# @param value True/False high/low.
#
def setDigitalLine(board, line, value):
    task = DigitalOutput(board, line)
    task.output(value)
    task.stopTask()
    task.clearTask()

#
# Testing.
#

if __name__ == "__main__":
    print getDAQBoardInfo()
    print getBoardDevNumber("PCI-6733")
    
    if 0:
        waveform1 = [1, 0, 1, 0, 1, 0]
        waveform2 = [0, 1, 0, 1, 0, 1]
        waveform3 = [0, 0, 0, 0, 0, 0]
        waveform = waveform1 + waveform2 + waveform3
        frequency = 1.0
        wv_task = DigitalWaveformOutput("PCI-6733", 0)
        wv_task.addChannel("PCI-6733", 1)
        wv_task.addChannel("PCI-6733", 2)
        wv_task.setWaveform(waveform, 10.0 * frequency)
        wv_task.startTask()
        
        ct_task = CounterOutput("PCI-6733", 0, frequency, 0.5)
        ct_task.setCounter(2*len(waveform))
#        ct_task.setTrigger(0)
        ct_task.startTask()
        foo = raw_input("Key Return")
        ct_task.stopTask()
        ct_task.clearTask()
        
        wv_task.stopTask()
        wv_task.clearTask()

    if 0:
        waveform = [5.0, 4.0, 3.0, 2.0, 1.0, 0.5]
        frequency = 31.3 * len(waveform) * 0.5
        wv_task = WaveformOutput("PCI-MIO-16E-4", 0)
        wv_task.setWaveform(waveform, frequency)
        wv_task.startTask()
        
        ct_task = CounterOutput("PCI-MIO-16E-4", 0, frequency, 0.5)
        ct_task.setCounter(len(waveform))
        ct_task.setTrigger(0)
        ct_task.startTask()
        foo = raw_input("Key Return")
        ct_task.stopTask()
        ct_task.clearTask()
        
        wv_task.stopTask()
        wv_task.clearTask()

    if 0:
        d_task = DigitalOutput("PCI-6722", 0)
        d_task.output(1)
        time.sleep(2)
        d_task.output(0)

    if 0:
        samples = 10
        a_task = AnalogInput("PCIe-6321", 0)
        a_task.addChannel(1)
        a_task.configureAcquisition(samples, 1000)
        a_task.startTask()
        data = a_task.getData()
        for i in range(2 * samples):
            print data[i]
        a_task.stopTask()
        a_task.clearTask()

    if 0:
        ct_task = CounterOutput("PCI-6733", 1, 50000, 0.10)
        ct_task.setCounter(-1)
        ct_task.startTask()
        time.sleep(60)
        ct_task.stopTask()
        ct_task.clearTask()

    if 1:
        waveform = [0, 1.0]
        print "1"
        #wv_task1 = WaveformOutput("PCI-6733", 6)
        #wv_task1.setWaveform(waveform, 100000.0, clock="")
        print "2"
        wv_task2 = WaveformOutput("PCI-6733", 0)
        wv_task2.setWaveform(waveform, 100000.0)

        #wv_task1.startTask()
        wv_task2.startTask()

        print "3"
        ct_task = CounterOutput("PCI-6733", 0, 1000, 0.5)
        ct_task.setCounter(100)
        ct_task.setTrigger(0)
        ct_task.startTask()
        foo = raw_input("Key Return")
        ct_task.stopTask()
        ct_task.clearTask()
        
        #wv_task1.stopTask()
        #wv_task1.clearTask()
        wv_task2.stopTask()
        wv_task2.clearTask()

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
