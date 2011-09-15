#!/usr/bin/python
#
# Widgets for illumination control and display.
#
# Hazen 12/09
#

from PyQt4 import QtCore, QtGui
from xml.dom import Node

#
# Channel settings object, created based on the XML descriptor file.
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
        if hasattr(self, "max_voltage"):
            self.range = self.max_voltage - self.min_voltage
        else:
            self.range = 1.0
            self.min_voltage = 0.0
        if not hasattr(self, "amplitude"):
            self.amplitude = 1.0


#
# Master widget for illumination channel display and control.
#
class QChannel(QtGui.QWidget):
    def __init__(self, parent, settings, default_power, x_pos, width, height):
        QtGui.QWidget.__init__(self, parent)

        self.cmd_queue = None
        self.channel_settings = settings
        self.current_amplitude = int(float(settings.amplitude) * default_power)
        self.displayed_amplitude = default_power
        self.inFskMode = 0
        self.filming_on = 0
        self.shutter_queue = None

        self.setGeometry(x_pos, 0, width, height)

        # container frame
        self.channel_frame = QtGui.QFrame(self)
        self.channel_frame.setGeometry(0, 0, width, height)
        self.channel_frame.setStyleSheet("background-color: rgb(" + settings.color + ");")
        self.channel_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.channel_frame.setFrameShadow(QtGui.QFrame.Raised)

        # text label
        self.channel_frame.wavelength_label = QtGui.QLabel(self.channel_frame)
        self.channel_frame.wavelength_label.setGeometry(5, 5, 40, 10)
        self.channel_frame.wavelength_label.setText(settings.description)
        self.channel_frame.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)

    def amOn(self):
        return (self.channel_frame.on_off_button.isChecked() or self.filming_on)

    def amplitudeChange(self, amplitude):
        pass

    def getCurrentAmplitude(self):
        return self.current_amplitude

    def getCurrentDefaultPower(self):
        return float(self.current_amplitude)/float(self.channel_settings.amplitude)

    def getDisplayedAmplitude(self):
        return self.displayed_amplitude

    def fskOnOff(self, on):
        pass

    def incDisplayedAmplitude(self, power_inc):
        pass

    def onOffChange(self):
        self.uiUpdate()

    def setCmdQueue(self, queue):
        self.cmd_queue = queue

    def setDisplayedAmplitude(self, power):
        pass

    def setFilmMode(self, on):
        if on:
            self.filming_on = 1
        else:
            self.filming_on = 0

    def setFrequency(self):
        pass

    def setShutterQueue(self, queue):
        self.shutter_queue = queue

    def shutter(self, on):
        if self.shutter_queue:
            if on and (self.displayed_amplitude > 0.0):
                self.shutter_queue.setShutter(True,
                                              self.channel_settings.ni_board,
                                              self.channel_settings.dig_line)
            else:
                self.shutter_queue.setShutter(False,
                                              self.channel_settings.ni_board,
                                              self.channel_settings.dig_line)

    def uiUpdate(self):
        pass

    def update(self, on):
        pass


#
# QChannel specialized for those channels with 
# electronically adjustable illumination control.
#
class QAdjustableChannel(QChannel):
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QChannel.__init__(self, parent, settings, default_power, x_pos, width, height)

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
        self.connect(self.channel_frame.powerslider, QtCore.SIGNAL("valueChanged(int)"),
                     self.amplitudeChange)
        self.connect(self.channel_frame.on_off_button, QtCore.SIGNAL("clicked()"),
                     self.onOffChange)

        self.show()

    def amplitudeChange(self, amplitude):
        self.current_amplitude = amplitude
        self.displayed_amplitude = float(amplitude)/float(self.channel_settings.amplitude)
        self.channel_frame.power_label.setText("{0:.4f}".format(self.displayed_amplitude))
        self.uiUpdate()

    def incDisplayedAmplitude(self, power_inc):
        new_power = self.displayed_amplitude + power_inc
        self.setDisplayedAmplitude(new_power)

    def setDisplayedAmplitude(self, power):
        self.channel_frame.powerslider.setValue(int(round((float(self.channel_settings.amplitude) * power), 0)))


#
# QChannel specialized for AOTF control.
#
class QAOTFChannel(QAdjustableChannel):
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAdjustableChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    def fskOnOff(self, on):
        off_freq = 20.0
        if on:
            if not(self.inFskMode):
                self.inFskMode = 1
                self.cmd_queue.fskOnOff(self.channel_settings.aotf_channel, on)
                self.cmd_queue.setFrequencies(self.channel_settings.channel,
                                              [off_freq, self.channel_settings.frequency, off_freq, off_freq])
        else:
            if self.inFskMode:
                self.inFskMode = 0
                self.cmd_queue.fskOnOff(self.channel_settings.aotf_channel, on)
                self.cmd_queue.setFrequency(self.channel_settings.channel,
                                            self.channel_settings.frequency)
                

    def setFrequency(self):
        self.cmd_queue.setFrequency(self.channel_settings.aotf_channel,
                                    self.channel_settings.frequency)

    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(),
                                  self.channel_settings.aotf_channel,
                                  self.current_amplitude)

    def update(self, on):
        self.cmd_queue.setAmplitude(on, self.channel_settings.aotf_channel, self.current_amplitude)


#
# QChannel specialized for AOTF control & electronic shutter.
#
class QAOTFChannelWShutter(QAOTFChannel):
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAOTFChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    def uiUpdate(self):
        self.shutter(self.amOn())
        QAOTFChannel.uiUpdate(self)

    def update(self, on):
        self.shutter(on)
        QAOTFChannel.update(self, on)

#
# QChannel specialized for Coherent cube control.
#
class QCubeChannel(QAdjustableChannel):
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAdjustableChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(), self.current_amplitude * 0.01)

    def update(self, on):
        self.cmd_queue.setAmplitude(on, self.current_amplitude * 0.01)

#
# QChannel specialized for Coherent cube control & electronic shutter.
#
class QCubeChannelWShutter(QCubeChannel):
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QCubeChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    def uiUpdate(self):
        self.shutter(self.amOn())
        QCubeChannel.uiUpdate(self)

    def update(self, on):
        self.shutter(on)
        QCubeChannel.update(self, on)

#
# QChannel specialized for National Instruments control.
#
class QNIChannel(QChannel):
    def __init__(self, parent, settings, on_off_state, x_pos, width, height):
        QChannel.__init__(self, parent, settings, 1.0, x_pos, width, height)

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        self.connect(self.channel_frame.on_off_button, QtCore.SIGNAL("clicked()"),
                     self.onOffChange)

        self.show()

    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(),
                                  self.channel_settings.ni_board,
                                  self.channel_settings.ao_channel)

    def update(self, on):
        self.cmd_queue.addRequest(on,
                                  self.channel_settings.ni_board,
                                  self.channel_settings.ao_channel)

#
# QChannel specialized for basic unsynchronized digital port control
#
class QBasicChannel(QChannel):
    def __init__(self, parent, settings, on_off_state, x_pos, width, height):
        QChannel.__init__(self, parent, settings, 1.0, x_pos, width, height)

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        self.connect(self.channel_frame.on_off_button, QtCore.SIGNAL("clicked()"),
                     self.onOffChange)

        self.show()

    def uiUpdate(self):
        self.shutter(self.amOn())
        QChannel.uiUpdate(self)

    def update(self, on):
        self.shutter(on)
        QChannel.update(self, on)

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
