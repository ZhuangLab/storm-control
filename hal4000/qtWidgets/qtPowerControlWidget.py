#!/usr/bin/python
#
## @file
#
# Deprecated!
#
# Qt Widget for handling "manual" laser power control and display.
# This class also handles converting a power request (0.0 - 1.0)
# into a voltage to be put out by the DAQ board for "automatic"
# laser power control.
#
# Hazen 2/09
#

from PyQt4 import QtCore, QtGui
import sys
from xml.dom import minidom, Node

have_aotf = 1
try:
    import crystalTechnologies.AOTF as AOTF
except:
    print "failed to load crystalTechnologies.AOTF."
    have_aotf = 0

have_cube = 1
try:
    import coherent.cube405 as cube405
except:
    print "failed to load coherent.cube405"
    have_cube = 0

#
# Remove AOTF settings that apply to the current channel. This way
# when you move the slider and generate 100 events only the last
# one gets acted on, but pending events for other channels are not lost.
#
def removeChannelDuplicates(queue, channel):
    final_queue = []
    for item in queue:
        if item[1] == channel: continue
        final_queue.append(item)
    return final_queue

#
# Channel settings object, created based on the XML descriptor file
#
class XMLToChannelObject():
    def __init__(self, block_node):
        for node in block_node:
            if node.nodeType == Node.ELEMENT_NODE:
                slot = node.nodeName
                value = node.firstChild.nodeValue
                type = node.attributes.item(0).value
                if type == "int":
                    setattr(self, slot, int(value))
                elif type == "float":
                    setattr(self, slot, float(value))
                elif type == "boolean":
                    if value.upper() == "TRUE":
                        setattr(self, slot, 1)
                    else:
                        setattr(self, slot, 0)
                else:
                    setattr(self, slot, value)
        self.range = self.max_voltage - self.min_voltage


#
# Channel Qt display and control
#
# AOTF UI commands are buffered through the aotf_queue.
# Cube UI commands are buffered through the cube_queue.
#
class QChannel():
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x, height, dx):
        self.aotf_queue = parent.aotf_queue
        self.cube_queue = parent.cube_queue
        self.channel_settings = settings
        self.current_amplitude = int(float(settings.amplitude) * default_power)
        self.displayed_amplitude = default_power
        self.inFskMode = 0
        self.filming_on = 0

        # container frame
        self.channel_frame = QtGui.QFrame(parent)
        self.channel_frame.setGeometry(x, 0, dx, height)
        self.channel_frame.setStyleSheet("background-color: rgb(" + settings.color + ");")
        self.channel_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.channel_frame.setFrameShadow(QtGui.QFrame.Raised)

        # text label
        self.channel_frame.wavelength_label = QtGui.QLabel(self.channel_frame)
        self.channel_frame.wavelength_label.setGeometry(5, 5, 40, 10)
        self.channel_frame.wavelength_label.setText(settings.description)
        self.channel_frame.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)

        # current power label
        self.channel_frame.power_label = QtGui.QLabel(self.channel_frame)
        self.channel_frame.power_label.setGeometry(5, 19, 40, 10)
        self.channel_frame.power_label.setText("{0:.4f}".format(default_power))
        self.channel_frame.power_label.setAlignment(QtCore.Qt.AlignCenter)

        # power slider
        self.channel_frame.powerslider = QtGui.QSlider(self.channel_frame)
        self.channel_frame.powerslider.setGeometry(13, 34, 24, 141)
        self.channel_frame.powerslider.setMinimum(0)
        self.channel_frame.powerslider.setMaximum(settings.amplitude)
        self.channel_frame.powerslider.setValue(int(float(settings.amplitude) * default_power))
        self.channel_frame.powerslider.setPageStep(0.1 * settings.amplitude)
        self.channel_frame.powerslider.setSingleStep(1)
        
        # power buttons
        y = 180
        self.channel_frame.buttons = []
        self.channel_frame.buttons_fns = []

        # This generates the function that is connected to the button that
        # will set the power appropriately when the button is pressed. It
        # did not work to just use lambda in the for loop, presumably because
        # the button variable is not properly closed over.
        def button_fn(power):
            return lambda: self.channel_frame.powerslider.setValue(int(float(self.channel_settings.amplitude) * power))
        for button in buttons:
            # create the button
            temp = QtGui.QPushButton(self.channel_frame)
            temp.setStyleSheet("background-color: None;")
            temp.setGeometry(6, y, 38, 20)
            temp.setText(str(button[0]))
            self.channel_frame.buttons.append(temp)
            # connect it
            temp_fn = button_fn(button[1])
            self.channel_frame.buttons_fns.append(temp_fn)
            QtCore.QObject.connect(temp, QtCore.SIGNAL("clicked()"), temp_fn)

            y += 22

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        QtCore.QObject.connect(self.channel_frame.powerslider, QtCore.SIGNAL("valueChanged(int)"),
                               self.amplitudeChange)
        QtCore.QObject.connect(self.channel_frame.on_off_button, QtCore.SIGNAL("clicked()"),
                               self.onOffChange)

        self.channel_frame.show()
        self.uiUpdate()

    def amOn(self):
        return (self.channel_frame.on_off_button.isChecked() or self.filming_on)

    def amplitudeChange(self, amplitude):
        self.current_amplitude = amplitude
        self.displayed_amplitude = float(amplitude)/float(self.channel_settings.amplitude)
        self.channel_frame.power_label.setText("{0:.4f}".format(self.displayed_amplitude))
        self.uiUpdate()

    def close(self):
        self.channel_frame.close()

    def getCurrentAmplitude(self):
        return self.current_amplitude

    def getCurrentDefaultPower(self):
        return float(self.current_amplitude)/float(self.channel_settings.amplitude)

    def getDisplayedAmplitude(self):
        return self.displayed_amplitude

    def fskOnOff(self, on):
        off_freq = 20.0
        if self.channel_settings.use_aotf:
            if on:
                if not(self.inFskMode):
                    print "FSK on for", self.channel_settings.channel
                    self.inFskMode = 1
                    self.aotf_queue.fskOnOff(self.channel_settings.channel, on)
                    self.aotf_queue.setFrequencies(self.channel_settings.channel,
                                                   [off_freq, self.channel_settings.frequency, off_freq, off_freq])
            else:
                if self.inFskMode:
                    print "FSK off for", self.channel_settings.channel
                    self.inFskMode = 0
                    self.aotf_queue.fskOnOff(self.channel_settings.channel, on)
                    self.aotf_queue.setFrequency(self.channel_settings.channel,
                                                 self.channel_settings.frequency)

    def incDisplayedAmplitude(self, power_inc):
        new_power = self.displayed_amplitude + power_inc
        self.setDisplayedAmplitude(new_power)

    def onOffChange(self):
        self.uiUpdate()

    def setDisplayedAmplitude(self, power):
        self.channel_frame.powerslider.setValue(int(float(self.channel_settings.amplitude) * power))

    def setFilmMode(self, on):
        if on:
            self.filming_on = 1
        else:
            self.filming_on = 0

    def setFrequency(self):
        if self.channel_settings.use_aotf:
            self.aotf_queue.setFrequency(self.channel_settings.channel,
                                         self.channel_settings.frequency)

    def uiUpdate(self):
        if self.channel_settings.use_aotf:
            self.aotf_queue.addRequest(self.amOn(),
                                       self.channel_settings.channel,
                                       self.current_amplitude)
        elif self.channel_settings.use_cube405:
            self.cube_queue.addRequest(self.amOn(),
                                       self.current_amplitude)            

    def update(self, on):
        if self.channel_settings.use_aotf:
            self.aotf_queue.setAmplitude(on, self.channel_settings.channel, self.current_amplitude)
        elif self.channel_settings.use_cube405:
            self.cube_queue.setAmplitude(on, self.current_amplitude)

    
# Cube405 communication thread.
#
# This "buffers" communication with the Cube 405.
#
# All communication with the Cube 405 should go 
# through this thread to avoid two processes trying 
# to talk to the laser at the same time.
#
class QCubeThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.cube_mutex = QtCore.QMutex()
        self.running = 1

        global have_cube
        if have_cube:
            self.cube = cube405.Cube405()
            if not(self.cube.getStatus()):
                self.cube.shutDown()
                self.cube = 0
        else:
            self.cube = 0

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

    def analogModulationOff(self):
        self.cube_mutex.lock()
        if self.cube:
            self.cube.setExtControl(0)
        self.cube_mutex.unlock()

    def analogModulationOn(self):
        self.cube_mutex.lock()
        if self.cube:
            self.cube.setExtControl(1)
        self.cube_mutex.unlock()

    def setAmplitude(self, on, amplitude):
        self.cube_mutex.lock()
        if self.cube:
            if on:
                self.cube.setPower(amplitude)
            else:
                self.cube.setPower(0)
        else:
            if on:
                print "CUBE: ", amplitude
            else:
                print "CUBE: ", 0
        self.cube_mutex.unlock()

    def stopThread(self):
        self.running = 0
        if self.cube:
            self.cube.shutDown()


# AOTF communication thread.
#
# This "buffers" communication with the AOTF, which doesn't
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

        # connect to the AOTF
        global have_aotf
        if have_aotf:
            self.aotf = AOTF.AOTF()
            if not(self.aotf.getStatus()):
                self.aotf = 0
        else:
            self.aotf = 0

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

    def stopThread(self):
        if self.aotf:
            self.aotf.shutDown()
            self.aotf = 0
        self.running = 0


# Power control widget
#
# Since the channel number and the index, at least in theory,
# do not have to correspond the program checks the requested
# channel number against the channel number stored for a
# particular channel. Is this necessary? People should not
# be editing the power_control_settings.xml file anyway so
# one could probably count on it not being so confusing...
#
class QPowerControlWidget(QtGui.QWidget):
    def __init__(self, settings_file_name, parameters, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.debug = 1

        # setup the AOTF communication thread
        self.aotf_queue = QAOTFThread()
        self.aotf_queue.start(QtCore.QThread.NormalPriority)

        # setup the Cube communication thread
        self.cube_queue = QCubeThread()
        self.cube_queue.start(QtCore.QThread.NormalPriority)

        # parse the settings file
        xml = minidom.parse(settings_file_name)
        blocks = xml.getElementsByTagName("block")
        self.settings = []
        for i in range(blocks.length):
            self.settings.append(XMLToChannelObject(blocks[i].childNodes))
        self.number_channels = blocks.length

        # layout the widget
        self.setWindowTitle("Laser Power Control")
        self.last_parameters = 0
        self.channels = []
        self.newParameters(parameters)

        # set the aotf frequencies & go to manual control
        for channel in self.channels:
            channel.setFrequency()
        self.manualControl()

    def allOff(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,0)

    def autoControl(self, channels):
        self.aotf_queue.analogModulationOn()
        self.cube_queue.analogModulationOn()
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.channels[i].fskOnOff(1)
                    self.channels[i].setFilmMode(1)

    def closeEvent(self, event):
        self.shutDown()

    def manualControl(self):
        self.aotf_queue.analogModulationOff()
        self.cube_queue.analogModulationOff()
        for channel in self.channels:
            channel.fskOnOff(0)
            channel.setFilmMode(0)

    def newParameters(self, parameters):
        # delete old channels, if they exist
        if len(self.channels) > 0:
            for i, channel in enumerate(self.channels):
                n = self.settings[i].channel
                self.last_parameters.on_off_state[n] = channel.amOn()
                self.last_parameters.default_power[n] = channel.getCurrentDefaultPower()
                channel.close()
        self.channels = []
        # layout the widget
        dx = 50
        width = self.number_channels * dx
        # the height is based on how many buttons there are per channel
        max_buttons = 0
        for i in range(self.number_channels):
            n_buttons = len(parameters.power_buttons[i])
            if n_buttons > max_buttons:
                max_buttons = n_buttons
        height = 204 + max_buttons * 22
        self.resize(width,height)
        self.setMinimumSize(QtCore.QSize(width,height))
        self.setMaximumSize(QtCore.QSize(width,height))
        x = 0
        for i in range(self.number_channels):
            n = self.settings[i].channel
            self.channels.append(QChannel(self,
                                          self.settings[i],
                                          parameters.default_power[n],
                                          parameters.on_off_state[n],
                                          parameters.power_buttons[n],
                                          x,
                                          height,
                                          dx))
            x += dx
        self.last_parameters = parameters

    def onOff(self, index, on):
        if on:
            if self.debug:
                print " powering on channel", self.settings[index].channel, self.channels[index].getCurrentAmplitude()
        else:
            if self.debug:
                print " powering off channel", self.settings[index].channel, self.channels[index].getCurrentAmplitude()
        self.channels[index].update(on)

    def powerToVoltage(self, channel, power):
        assert power >= 0.0, "power out of range: " + str(power) + " " + str(channel)
        assert power <= 1.0, "power out of range: " + str(power) + " " + str(channel)
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                return self.settings[i].range * power - self.settings[i].min_voltage
        print "unknown channel: " + str(channel)
        return 0.0

    def remoteIncPower(self, channel, power_inc):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].incDisplayedAmplitude(power_inc)

    def remoteSetPower(self, channel, power):
        for i in range(self.number_channels):
            if self.settings[i].channel == channel:
                self.channels[i].setDisplayedAmplitude(power)

    def reset(self):
        for i in range(self.number_channels):
            if self.channels[i].amOn():
                self.onOff(i,1)

    def saveHeader(self, fp):
        str = "frame"
        for i in range(self.number_channels):
            str = str + " {0:d}".format(self.settings[i].channel)
        fp.write(str + "\n")

    def savePowers(self, fp, frame):
        str = "{0:d}".format(frame)
        for channel in self.channels:
            str = str + " {0:.4f}".format(channel.getDisplayedAmplitude())
        fp.write(str + "\n")

    def shutDown(self):
        self.allOff()
        self.aotf_queue.stopThread()
        self.aotf_queue.wait()
        self.cube_queue.stopThread()
        self.cube_queue.wait()

    def turnOnOff(self, channels, on):
        for channel in channels:
            for i in range(self.number_channels):
                if self.settings[i].channel == channel:
                    self.onOff(i, on)
        


#
# Testing
#

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    pc = QPowerControlWidget("power_control_settings.xml")
    pc.show()
    sys.exit(app.exec_())


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
