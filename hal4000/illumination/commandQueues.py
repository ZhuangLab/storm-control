#!/usr/bin/python
#
# Queues for buffering commands to various pieces
# of hardware. These queues are based on PyQt threads.
# They are currently implemented for:
#
# 1. Coherent Cube405 laser connected via serial port.
# 2. Crystal Technologies AOTF connected via USB.
# 3. National Instruments card installed in the computer.
# 4. Thorlabs filter wheel.
#
# Hazen 5/12
#

from PyQt4 import QtCore

#
# Remove settings that apply to the current channel. This way
# when you move the slider and generate 100 events only the last
# one gets acted on, but pending events for other channels are not lost.
#
def removeChannelDuplicates(queue, channel):
    final_queue = []
    for item in queue:
        if item[1] == channel:
            continue
        final_queue.append(item)
    return final_queue

#
# Generic AOTF communication thread
#
# This "buffers" communication with an AOTF, that doesn't
# respond very quickly to requests. It sends the most recent request
# and discards any backlog of older requests. It is necessary to
# keep the slider moving "smoothly" when the user tries to drag it
# up and down w/ the AOTF on.
#
# All communication with AOTF should go through this thread to avoid
# two processes trying to talk to the AOTF at the same time.
#
class QAOTFThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.aotf_mutex = QtCore.QMutex()
        self.running = 1
        self.aotf = False

    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, channel, amplitude] = self.buffer.pop()
                self.buffer = removeChannelDuplicates(self.buffer, channel)
                self.buffer_mutex.unlock()
                self.setAmplitude(on, channel, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, channel, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, channel, amplitude])
        self.buffer_mutex.unlock()

    def analogModulationOff(self):
        pass

    def analogModulationOn(self):
        pass

    def fskOnOff(self, channel, on):
        pass

    def setAmplitude(self, on, channel, amplitude):
        pass

    def setFrequencies(self, channel, frequencies):
        pass

    def setFrequency(self, channel, frequency):
        pass

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.aotf:
            self.aotf.shutDown()
            self.aotf = 0


#
# AA Opto-Electronics AOTF communication thread.
#
class QAAAOTFThread(QAOTFThread):
    def __init__(self, parent = None):
        QAOTFThread.__init__(self, parent)

        import aaopto.AOTF as AOTF
        self.aotf = AOTF.AOTF()
        if not(self.aotf.getStatus()):
            self.aotf = 0

        # The AOTF is set up (on STORM2) to use a wacky analog/
        # digital counter control scheme when in analog or
        # "use shutters mode". We try and hide those differences
        # from the user here.
        import nationalInstruments.nicontrol as nicontrol

        # set up re-triggerable single shot counters to drive the AOTF.
        ctr_info = [["PCIe-6259", 0, "PCIe-6259", 12],  # 568
                    ["PCIe-6259", 1, "PCIe-6259", 13],  # 488
                    ["PCI-6713",  0, "PCIe-6259", 14]]  # 457
        self.ctr_tasks = []
        for info in ctr_info:
            ctr_task = nicontrol.CounterOutput(info[0], info[1], 60.0, 0.999)
            ctr_task.setTrigger(info[3], board = info[2])
            self.ctr_tasks.append(ctr_task)

        # setup analog modulation
        ana_info = [["PCI-6713", 0],  # 568
                    ["PCI-6713", 1],  # 488
                    ["PCI-6713", 2]]  # 457
        self.ana_tasks = []
        for info in ana_info:
            ana_task = nicontrol.VoltageOutput(info[0], info[1], min_val = -0.01, max_val = 5.01)
            self.ana_tasks.append(ana_task)

    def analogModulationOff(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOff()
        for ctr in self.ctr_tasks:
            ctr.stopTask()
        self.aotf_mutex.unlock()

    def analogModulationOn(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOn()
        for ctr in self.ctr_tasks:
            ctr.startTask()
        self.aotf_mutex.unlock()

    def setAmplitude(self, on, channel, amplitude):
        self.aotf_mutex.lock()
        if self.aotf:
            
            # digital modulation
            if on:
                if (amplitude > 0):
                    self.aotf.channelOnOff(channel, True)
                else:
                    self.aotf.channelOnOff(channel, False)
                if (amplitude > 13):
                    power = (float(amplitude)-15.0)/10.0 - 7.0
                    self.aotf.setAmplitude(channel, power)
                    self.aotf.offsetFrequency(channel, 0.0)
                else:
                    freq_offset = 0.65 - float(amplitude)/20.0
                    self.aotf.setAmplitude(channel, -7.4)
                    self.aotf.offsetFrequency(channel, freq_offset)
            else:
                self.aotf.channelOnOff(channel, False)

            # analog modulation
            # FIXME: using hard-coded lowest amplitude value as we
            #        don't know what max to actually use here.
            if (channel>2):
                if (amplitude > 278.0):
                    amplitude = 278.0
                voltage = 5.0 * float(amplitude)/278.0
                print voltage
                self.ana_tasks[(channel-2)].outputVoltage(voltage)
                
        self.aotf_mutex.unlock()
                               
    def setFrequency(self, channel, frequency):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequency(channel, frequency)
        self.aotf_mutex.unlock()

    def stopThread(self):
        for ctr in self.ctr_tasks:
            ctr.stopTask()
            ctr.clearTask()
        for ana in self.ana_tasks:
            ana.stopTask()
            ana.clearTask()
        QAOTFThread.stopThread(self)
                               

#
# Crystal Technologies AOTF communication thread.
#
class QCTAOTFThread(QAOTFThread):
    def __init__(self, parent = None):
        QAOTFThread.__init__(self, parent)

        import crystalTechnologies.AOTF as AOTF
        self.aotf = AOTF.AOTF()
        if not(self.aotf.getStatus()):
            self.aotf = 0

    def analogModulationOff(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOff()
        self.aotf_mutex.unlock()

    def analogModulationOn(self):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.analogModulationOn()
        self.aotf_mutex.unlock()

    def fskOnOff(self, channel, on):
        self.aotf_mutex.lock()
        if self.aotf:
            if on:
                self.aotf.fskOn(channel)
            else:
                self.aotf.fskOff(channel)
        self.aotf_mutex.unlock()

    def setAmplitude(self, on, channel, amplitude):
        self.aotf_mutex.lock()
        if self.aotf:
            if on:
                self.aotf.setAmplitude(channel, amplitude)
            else:
                self.aotf.setAmplitude(channel, 0)
        else:
            print "AOTF:"
            if on:
                print "\t", channel, amplitude
            else:
                print "\t", channel, 0
        self.aotf_mutex.unlock()

    def setFrequencies(self, channel, frequencies):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequencies(channel, frequencies)
        self.aotf_mutex.unlock()

    def setFrequency(self, channel, frequency):
        self.aotf_mutex.lock()
        if self.aotf:
            self.aotf.setFrequency(channel, frequency)
        self.aotf_mutex.unlock()

#
# Crystal Technologies AOTF communication thread.
# Communication with the AOTF by IPC for 64 bit machines.
#
class QCT64BitAOTFThread(QCTAOTFThread):
    def __init__(self, parent = None):
        QAOTFThread.__init__(self, parent)

        import crystalTechnologies.AOTF as AOTF
        self.aotf = AOTF.AOTF64Bit()
        if not(self.aotf.getStatus()):
            self.aotf = 0

#
# National Instruments digital communication. This is also
# so fast that we don't bother to buffer.
#
class QNiDigitalComm():
    def __init__(self):
        self.used_channel = []
        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol

    def setShutter(self, on, board, channel):
        #if not (channel in self.used_channels):
        if 1:
            task = self.nicontrol.DigitalOutput(board, channel)
            if on:
                task.output(True)
            else:
                task.output(False)
            task.clearTask()

    def setFilming(self, channels):
        self.used_channels = channels

#
# National Instruments analog communication. This is so
# fast that we don't even bother to buffer.
#
class QNiAnalogComm():
    def __init__(self, on_voltage):
        self.filming = 0
        self.on_voltage = on_voltage
        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol

    def addRequest(self, on, board, channel):
        if not self.filming:
            task = self.nicontrol.VoltageOutput(board, channel)
            if on:
                task.outputVoltage(self.on_voltage)
            else:
                task.outputVoltage(0.0)
            task.clearTask()

    def setFilming(self, flag):
        self.filming = flag

#
# Generic serial device communication.
#
# This "buffers" communication with a serial device.
#
class QSerialComm(QtCore.QThread):
    def __init__(self, sdevice, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.sdevice_mutex = QtCore.QMutex()
        self.running = 1

        self.sdevice = sdevice
        if not (self.sdevice.getStatus()):
            self.sdevice.shutDown()
            self.sdevice = False

    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if len(self.buffer) > 0:
                [on, amplitude] = self.buffer.pop()
                self.buffer = []
                self.buffer_mutex.unlock()
                self.setAmplitude(on, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    def addRequest(self, on, amplitude):
        self.buffer_mutex.lock()
        self.buffer.append([on, amplitude])
        self.buffer_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        pass

    def stopThread(self):
        self.running = 0
        while (self.isRunning()):
            self.msleep(50)
        if self.sdevice:
            self.sdevice.shutDown()

#
# Serial port controlled filter-wheel.
#
# This "buffers" communication with a serial filter wheel.
#
# All communication with the device should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#
class QSerialFilterWheelComm(QSerialComm):
    def __init__(self, sdevice, parent = None):
        QSerialComm.__init__(self, sdevice, parent)

    def setAmplitude(self, on, amplitude):
        self.sdevice_mutex.lock()
        if self.sdevice:
            self.sdevice.setPosition(amplitude+1)
        else:
            print "Filter Wheel: ", amplitude
        self.sdevice_mutex.unlock()

#
# Serial port controlled laser.
#
# This "buffers" communication with a laser.
#
# All communication with the device should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#
class QSerialLaserComm(QSerialComm):
    def __init__(self, sdevice, parent = None):
        QSerialComm.__init__(self, sdevice, parent)

    def analogModulationOff(self):
        self.sdevice_mutex.lock()
        if self.sdevice:
            self.sdevice.setExtControl(0)
        self.sdevice_mutex.unlock()

    def analogModulationOn(self):
        self.sdevice_mutex.lock()
        if self.sdevice:
            self.sdevice.setExtControl(1)
        self.sdevice_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        self.sdevice_mutex.lock()
        if self.sdevice:
            if on:
                self.sdevice.setPower(amplitude)
            else:
                self.sdevice.setPower(0)
        else:
            if on:
                print "LASER: ", amplitude
            else:
                print "LASER: ", 0
        self.sdevice_mutex.unlock()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
