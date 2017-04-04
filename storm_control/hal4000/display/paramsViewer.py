#!/usr/bin/env python
"""
Handles the display of the current parameters for a given camera.

Hazen 04/17
"""

import importlib
from PyQt5 import QtCore, QtWidgets

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class ParamsViewer(QtWidgets.QGroupBox):
    """
    This class handles displaying (some of) the current camera parameters
    in the UI. It also handles the EMCCD gain slider (if the camera has
    an EMCCD).
    """
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, viewer_name = "", viewer_ui = None, **kwds):
        super().__init__(**kwds)
        self.temperature = 50
        self.viewer_name = viewer_name
        
        # UI setup
        self.ui = viewer_ui.Ui_GroupBox()
        self.ui.setupUi(self)

        # connect signals
        self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

    def handleGainChange(self, new_gain):
        self.ui.EMCCDLabel.setText("EMCCD Gain: {0:d}".format(new_gain))
        self.gainChange.emit(new_gain)

    def newParameters(self, parameters):
        p = parameters
        if p.has("emccd_gain"):
            gainp = p.getp("emccd_gain")
            self.ui.EMCCDSlider.valueChanged.disconnect()
            self.ui.EMCCDSlider.setMinimum(gainp.getMinimum())
            self.ui.EMCCDSlider.setMaximum(gainp.getMaximum())
            self.ui.EMCCDSlider.setValue(gainp.getv())
            self.ui.EMCCDLabel.setText("EMCCD Gain: {0:d}".format(gainp.getv()))
            self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

        if p.get("external_trigger", False):
            self.ui.exposureTimeText.setText("External")
            self.ui.FPSText.setText("External")
        else:
            self.ui.exposureTimeText.setText("{0:.4f}".format(p.get("exposure_time")))
            self.ui.FPSText.setText("{0:.4f}".format(p.get("fps")))

        if p.has("preampgain"):
            self.ui.preampGainText.setText("{0:.1f}".format(p.get("preampgain")))

        if p.has("temperature"):
            self.temperature = p.get("temperature")

        self.ui.pictureSizeText.setText(str(p.get("x_pixels")) + " x " + str(p.get("y_pixels")) +
                                        " (" + str(p.get("x_bin")) + "," + str(p.get("y_bin")) + ")")

            
    def setTemperature(self, state, temperature):
        if (state == "stable"):
            self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
        else:
            self.ui.temperatureText.setStyleSheet("QLabel { color: red }")
        self.ui.temperatureText.setText(str(temperature) + " (" + str(self.temperature) + ")")

    def setCameraConfiguration(self, camera_config):
        self.setTitle(camera_config.getCameraName().title())
        
        if camera_config.hasEMCCD():
            self.ui.EMCCDLabel.show()
            self.ui.EMCCDSlider.show()
        else:
            self.ui.EMCCDLabel.hide()
            self.ui.EMCCDSlider.hide()

        if camera_config.hasPreamp():
            self.ui.preampGainLabel.show()
            self.ui.preampGainText.show()
        else:
            self.ui.preampGainLabel.hide()
            self.ui.preampGainText.hide()

        if camera_config.hasTemperature():
            self.ui.temperatureLabel.show()
            self.ui.temperatureText.show()
        else:
            self.ui.temperatureLabel.hide()
            self.ui.temperatureText.hide()

        self.newParameters(camera_config.getParameters())

    def startFilm(self):
        self.ui.EMCCDSlider.setEnabled(False)

    def stopFilm(self):
        self.ui.EMCCDSlider.setEnabled(True)
            


# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
