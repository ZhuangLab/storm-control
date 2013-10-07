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
# Hazen 10/13
#

from PyQt4 import QtCore, QtGui

#
# Camera Params Group Box
#
class CameraParams(QtGui.QGroupBox):
    gainChange = QtCore.pyqtSignal(int)

    def __init__(self, camera_params_ui, parent = None):
        QtGui.QGroupBox.__init__(self, parent)
        self.temperature = False

        # UI setup
        self.ui = camera_params_ui
        self.ui.setupUi(self)

        # connect signals
        self.connect(self.ui.EMCCDSlider, QtCore.SIGNAL("valueChanged(int)"), self.cameraGainChange)

    def cameraGainChange(self, new_gain):
        self.ui.EMCCDLabel.setText("EMCCD Gain: %d" % new_gain)
        self.gainChange.emit(new_gain)
        
    def newParameters(self, parameters):
        p = parameters
        if (hasattr(p, "temperature")):
            self.temperature = p.temperature
            self.ui.temperatureLabel.show()
            self.ui.temperatureText.show()
        else:
            self.ui.temperatureLabel.hide()
            self.ui.temperatureText.hide()

        if (hasattr(p, "emgainmode")):
            self.ui.EMCCDLabel.show()
            self.ui.EMCCDSlider.show()
            if p.emgainmode == 0:
                self.ui.EMCCDSlider.setMaximum(255)
            else:
                self.ui.EMCCDSlider.setMaximum(100)
            self.ui.EMCCDSlider.setValue(p.emccd_gain)
        else:
            self.ui.EMCCDLabel.hide()
            self.ui.EMCCDSlider.hide()

        if (hasattr(p, "preampgain")):
            self.ui.preampGainLabel.show()
            self.ui.preampGainText.show()
            self.ui.preampGainText.setText("%.1f" % p.preampgain)
        else:
            self.ui.preampGainLabel.hide()
            self.ui.preampGainText.hide()

        self.ui.pictureSizeText.setText(str(p.x_pixels) + " x " + str(p.y_pixels) +
                                        " (" + str(p.x_bin) + "," + str(p.y_bin) + ")")

        if p.external_trigger:
            self.ui.exposureTimeText.setText("External")
            self.ui.FPSText.setText("External")
        else:
            self.ui.exposureTimeText.setText("%.4f" % p.exposure_value)
            self.ui.FPSText.setText("%.4f" % (1.0/p.kinetic_value))

    def newTemperature(self, temp_data):
        if (self.ui.temperatureText.isVisible()):
            if temp_data[1] == "stable":
                self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
            else:
                self.ui.temperatureText.setStyleSheet("QLabel { color: red }")


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
