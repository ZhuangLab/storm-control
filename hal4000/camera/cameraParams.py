#!/usr/bin/python
#
# Handles the display of the current parameters for a given camera.
#
# Methods:
#
# newParameters(parameters)
#    Update the display with new parametes.
#
# newTemperature(temperature_data)
#    Update the temperature display data.
#
#
# Signals:
# 
# gainChange(int gain)
#
#
# Hazen 9/09
#

from PyQt4 import QtCore, QtGui

# UIs.
import qtdesigner.camera_params_v1 as camera_params_ui

#
# Camera Params Group Box
#
class CameraParams(QtGui.QGroupBox):
    def __init__(self, parent = None):
        QtGui.QGroupBox.__init__(self, parent)
        self.temperature = 0

        # UI setup
        self.ui = camera_params_ui.Ui_GroupBox()
        self.ui.setupUi(self)

        # connect signals
        self.connect(self.ui.EMCCDSlider, QtCore.SIGNAL("valueChanged(int)"), self.gainChange)

    def gainChange(self, new_gain):
        self.ui.EMCCDLabel.setText("EMCCD Gain: %d" % new_gain)
        self.emit(QtCore.SIGNAL("gainChange(int)"), new_gain)
        
    def newParameters(self, parameters):
        p = parameters
        self.temperature = p.temperature
        if p.emgainmode == 0:
            self.ui.EMCCDSlider.setMaximum(255)
        else:
            self.ui.EMCCDSlider.setMaximum(100)
        self.ui.EMCCDSlider.setValue(p.emccd_gain)
        self.ui.preampGainText.setText("%.1f" % p.preampgain)
        self.ui.pictureSizeText.setText(str(p.x_pixels) + " x " + str(p.y_pixels) +
                                        " (" + str(p.x_bin) + "," + str(p.y_bin) + ")")
        self.ui.exposureTimeText.setText("%.4f" % p.exposure_value)
        self.ui.FPSText.setText("%.4f" % (1.0/p.kinetic_value))
                
    def newTemperature(self, temp_data):
        if temp_data[1] == "stable":
            self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
        else:
            self.ui.temperatureText.setStyleSheet("QLabel { color: red }")
        self.ui.temperatureText.setText(str(temp_data[0]) + " (" + str(self.temperature) + ")")


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
