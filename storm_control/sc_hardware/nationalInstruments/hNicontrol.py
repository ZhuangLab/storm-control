#!/usr/bin/env python
"""
This file contains hardware classes that interface National 
Instruments cards with HAL illumination control software.

Hazen 04/17
"""

import hashlib
import time

# Debugging
import storm_control.sc_library.hdebug as hdebug

import storm_control.sc_hardware.baseClasses.illuminationHardware as illuminationHardware
import storm_control.sc_hardware.nationalInstruments.nicontrol as nicontrol


class Nidaq(illuminationHardware.DaqModulation):
    """
    National Instruments DAQ card (modulation).
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ao_task = False
        self.ct_task = False
        self.do_task = False

        if (hasattr(parameters, "counter_board")):
            self.counter_board = parameters.counter_board
            self.counter_id = parameters.counter_id
            self.counter_trigger = parameters.counter_trigger
        else:
            self.counter_board = False
            self.counter_id = False
            self.counter_trigger = False

        # FIXME:
        #   Need a waveform_clock_board parameter and we need to fix
        #   nicontrol to respect this, otherwise we can only use one
        #   board for waveform output.
        if (hasattr(parameters, "waveform_clock")):
            self.waveform_clock = parameters.waveform_clock
        else:
            self.waveform_clock = False
    
    def analogOff(self, channel_id):
        """
        Sets the analog voltage to the minimum.
        """
        if not self.filming:
            nicontrol.setAnalogLine(self.analog_settings[channel_id].board,
                                    self.analog_settings[channel_id].channel,
                                    self.analog_settings[channel_id].min_voltage)

    def analogOn(self, channel_id):
        """
        Sets the analog voltage to the maximum.
        """
        if not self.filming:
            nicontrol.setAnalogLine(self.analog_settings[channel_id].board,
                                    self.analog_settings[channel_id].channel,
                                    self.analog_settings[channel_id].max_voltage)

    def digitalOff(self, channel_id):
        """
        Sets the digital line to 0.
        """
        if not self.filming:
            nicontrol.setDigitalLine(self.digital_settings[channel_id].board,
                                     self.digital_settings[channel_id].channel,
                                     False)

    def digitalOn(self, channel_id):
        """
        Sets the digital line to 1.
        """
        if not self.filming:
            nicontrol.setDigitalLine(self.digital_settings[channel_id].board,
                                     self.digital_settings[channel_id].channel,
                                     True)

    def shutterOff(self, channel_id):
        """
        Sets the shutter digital line to 0.
        """
        nicontrol.setDigitalLine(self.shutter_settings[channel_id].board,
                                 self.shutter_settings[channel_id].channel,
                                 False)

    def shutterOn(self, channel_id):
        """
        Sets the shutter digital line to 1.
        """
        nicontrol.setDigitalLine(self.shutter_settings[channel_id].board,
                                 self.shutter_settings[channel_id].channel,
                                 True)

    def startFilm(self, frames_per_second, oversampling):
        """
        Called at the start of filming (when shutters are active).
        """
        super().startFilm(frames_per_second, oversampling)

        # Calculate frequency. This is set slightly higher than the camere
        # frequency so that we are ready at the start of the next frame.
        frequency = (1.01 * seconds_per_frame) * float(oversampling)

        # If oversampling is 1 then just trigger the ao_task 
        # and do_task directly off the camera fire pin.
        wv_clock = self.waveform_clock
        if (oversampling == 1):
            wv_clock = "PFI" + str(self.counter_trigger)

        # Setup the counter.
        if self.counter_board and (oversampling > 1):
            def startCtTask():
                try:
                    self.ct_task = nicontrol.CounterOutput(self.counter_board, 
                                                           self.counter_id,
                                                           frequency, 
                                                           0.5)
                    self.ct_task.setCounter(oversampling)
                    self.ct_task.setTrigger(self.counter_trigger)
                    self.ct_task.startTask()
                except nicontrol.NIException:
                    return True

                return False

            iters = 0
            while (iters < 5) and startCtTask():
                hdebug.logText("startCtTask failed " + str(iters))
                self.ct_task.clearTask()
                time.sleep(0.5)
                iters += 1

            if iters == 5:
                hdebug.logText("startCtTask critical failure")
                raise nicontrol.NIException("NIException: startCtTask critical failure")

        else:
            self.ct_task = False

        # Setup analog waveforms.
        if (len(self.analog_data) > 0):

            # Sort by board, channel.
            analog_data = sorted(self.analog_data, key = lambda x: (x[0], x[1]))

            # Set waveforms.
            waveform = []
            for i in range(len(analog_data)):
                waveform += analog_data[i][2]

            def startAoTask():
                
                try:
                    # Create channels.
                    self.ao_task = nicontrol.AnalogWaveformOutput(analog_data[0][0], analog_data[0][1])
                    for i in range(len(analog_data) - 1):
                        self.ao_task.addChannel(analog_data[i+1][0], analog_data[i+1][1])

                    # Add waveform
                    self.ao_task.setWaveform(waveform, frequency, clock = wv_clock)

                    # Start task.
                    self.ao_task.startTask()
                except nicontrol.NIException:
                    return True
                    
                return False

            iters = 0
            while (iters < 5) and startAoTask():
                hdebug.logText("startAoTask failed " + str(iters))
                self.ao_task.clearTask()
                time.sleep(0.1)
                iters += 1

            if iters == 5:
                hdebug.logText("startAoTask critical failure")
                raise nicontrol.NIException("NIException: startAoTask critical failure")

        else:
            self.ao_task = False

        # Setup digital waveforms.
        if (len(self.digital_data) > 0):

            # Sort by board, channel.
            digital_data = sorted(self.digital_data, key = lambda x: (x[0], x[1]))

            # Set waveforms.
            waveform = []
            for i in range(len(digital_data)):
                waveform += digital_data[i][2]

            def startDoTask():

                try:
                    # Create channels.
                    self.do_task = nicontrol.DigitalWaveformOutput(digital_data[0][0], digital_data[0][1])
                    for i in range(len(digital_data) - 1):
                        self.do_task.addChannel(digital_data[i+1][0], digital_data[i+1][1])

                    # Add waveform
                    self.do_task.setWaveform(waveform, frequency, clock = wv_clock)

                    # Start task.
                    self.do_task.startTask()
                except nicontrol.NIException:
                    return True

                return False

            iters = 0
            while (iters < 5) and startDoTask():
                hdebug.logText("startDoTask failed " + str(iters))
                self.do_task.clearTask()
                time.sleep(0.1)
                iters += 1

            if iters == 5:
                hdebug.logText("startDoTask critical failure")
                raise nicontrol.NIException("NIException: startDoTask critical failure")

        else:
            self.do_task = False

    def stopFilm(self):
        """
        Called at the end of filming (when shutters are active).
        """
        illuminationHardware.DaqModulation.stopFilm(self)
        for task in [self.ct_task, self.ao_task, self.do_task]:
            if task:
                try:
                    task.stopTask()
                    task.clearTask()
                except nicontrol.NIException as e:
                    hdebug.logText("stop / clear failed for task " + str(task) + " with " + str(e))


class NidaqAmp(illuminationHardware.AmplitudeModulation):
    """
    National Instruments DAQ card analog amplitude modulation.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def amplitudeOff(self, channel_id):
        """
        Called when the module should turn off a channel.
        """
        nicontrol.setAnalogLine(self.channel_parameters[channel_id].board,
                                self.channel_parameters[channel_id].channel,
                                self.channel_parameters[channel_id].min_voltage)

    def amplitudeOn(self, channel_id, amplitude):
        """
        Called when the module should turn on a channel.
        """
        nicontrol.setAnalogLine(self.channel_parameters[channel_id].board,
                                self.channel_parameters[channel_id].channel,
                                0.001 * amplitude)

    def getMaxAmplitude(self, channel_id):
        return self.channel_parameters[channel_id].maximum

    def getMinAmplitude(self, channel_id):
        params = self.channel_parameters[channel_id]
        if (hasattr(params, "minimum")):
            return params.minimum
        else:
            return 0

    def initialize(self, interface, channel_id, parameters):
        """
        This is called by each of the channels that wants to use this module.
        """
        self.channel_parameters[channel_id] = parameters
        self.channel_parameters[channel_id].maximum = int(1000.0 * parameters.max_voltage)
        self.channel_parameters[channel_id].minimum = int(1000.0 * parameters.min_voltage)

    def setAmplitude(self, channel_id, amplitude):
        self.amplitudeOn(channel_id, amplitude)



##
## I'm pretty sure that:
##
## (1) This doesn't work.
## (2) It was a bad idea.
##
## NidaqTR
#
# National Instruments DAQ card (modulation) with task recycling.
# Waveforms are considered different if they have different md5
# hashs. Hopefully hash collisions will be very rare..
#
class NidaqTR(Nidaq):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        Nidaq.__init__(self, parameters, parent)

        self.ao_tasks = {}
        self.ct_tasks = {}
        self.do_tasks = {}

    ## startFilm
    #
    # Called at the start of filming (when shutters are active).
    #
    # @param seconds_per_frame How many seconds it takes to acquire each frame.
    # @param oversampling The number of values in the shutter waveform per frame.
    #
    def startFilm(self, seconds_per_frame, oversampling):
        illuminationHardware.DaqModulation.startFilm(self, seconds_per_frame, oversampling)

        # Calculate frequency. This is set slightly higher than the camere
        # frequency so that we are ready at the start of the next frame.
        frequency = (1.01 / seconds_per_frame) * float(oversampling)

        # Setup analog waveforms.
        print "analog"
        if (len(self.analog_data) > 0):

            # Sort by board, channel.
            analog_data = sorted(self.analog_data, key = lambda x: (x[0], x[1]))

            # Set waveforms.
            waveform = []
            for i in range(len(analog_data)):
                waveform += analog_data[i][2]

            # Check if we already have a task for this waveform.
            waveform_hash = hashlib.md5("".join(str(elt) for elt in waveform)).hexdigest()
            if waveform_hash in self.ao_tasks:
                self.ao_task = self.ao_tasks[waveform_hash]
                self.ao_task.reserveTask()
                print "using recycled ao_task", waveform_hash

            else:
                def initAoTask():

                    # Create channels.
                    self.ao_task = nicontrol.AnalogWaveformOutput(analog_data[0][0], analog_data[0][1])
                    for i in range(len(analog_data) - 1):
                        self.ao_task.addChannel(analog_data[i+1][0], analog_data[i+1][1])

                    # Add waveform
                    return self.ao_task.setWaveform(waveform, frequency, clock = self.waveform_clock)

                iters = 0
                valid = initAoTask()
                while (iters < 5) and (not valid):
                    hdebug.logText("initAoTask failed " + str(iters))
                    self.ao_task.clearTask()
                    time.sleep(0.1)
                    valid = initAoTask()                    
                    iters += 1

                if valid:
                    self.ao_tasks[waveform_hash] = self.ao_task

        else:
            self.ao_task = False

        # Setup digital waveforms
        print "digital"
        if (len(self.digital_data) > 0):

            # Sort by board, channel.
            digital_data = sorted(self.digital_data, key = lambda x: (x[0], x[1]))

            # Set waveforms.
            waveform = []
            for i in range(len(digital_data)):
                waveform += digital_data[i][2]

            # Check if we already have a task for this waveform.
            waveform_hash = hashlib.md5("".join(str(elt) for elt in waveform)).hexdigest()
            if waveform_hash in self.do_tasks:
                self.do_task = self.do_tasks[waveform_hash]
                self.do_task.reserveTask()
                print "using recycled do_task", waveform_hash

            else:
                def initDoTask():

                    # Create channels.
                    self.do_task = nicontrol.DigitalWaveformOutput(digital_data[0][0], digital_data[0][1])
                    for i in range(len(digital_data) - 1):
                        self.do_task.addChannel(digital_data[i+1][0], digital_data[i+1][1])

                    # Add waveform
                    return self.do_task.setWaveform(waveform, frequency, clock = self.waveform_clock)

                iters = 0
                valid = initDoTask()
                while (iters < 5) and (not valid):
                    hdebug.logText("initDoTask failed " + str(iters))
                    self.do_task.clearTask()
                    time.sleep(0.1)
                    valid = initDoTask()
                    iters += 1

                if valid:
                    self.do_tasks[waveform_hash] = self.do_task

        else:
            self.do_task = False

        # Setup the counter.
        print "counter"
        if self.counter_board:

            ct_hash = str(frequency) + str(oversampling)
            if ct_hash in self.ct_tasks:
                self.ct_task = self.ct_tasks[ct_hash]
                self.ct_task.reserveTask()
                print "using recycled ct_task", ct_hash

            else:
                def initCtTask():
                    self.ct_task = nicontrol.CounterOutput(self.counter_board, 
                                                           self.counter_id,
                                                           frequency, 
                                                           0.5)
                    self.ct_task.setCounter(oversampling)
                    self.ct_task.setTrigger(self.counter_trigger)
                    print self.ct_task.verifyTask()
                    return self.ct_task

                iters = 0
                valid = initCtTask()
                while (iters < 5) and (not valid):
                    hdebug.logText("initCtTask failed " + str(iters))
                    self.ct_task.clearTask()
                    time.sleep(0.1)
                    valid = initCtTask()
                    iters += 1

                if valid:
                    self.ct_tasks[ct_hash] = self.ct_task

        else:
            self.ct_task = False

        # Start tasks
        for task in [self.ct_task, self.ao_task, self.do_task]:
            if task:
                task.startTask()

    ## stopFilm
    #
    # Called at the end of filming (when shutters are active).
    #
    def stopFilm(self):
        illuminationHardware.DaqModulation.stopFilm(self)
        for task in [self.ct_task, self.ao_task, self.do_task]:
            if task:
                task.stopTask()
                task.unreserveTask()


#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
