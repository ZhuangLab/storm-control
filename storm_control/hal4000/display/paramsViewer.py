#!/usr/bin/env python
"""
Handles the display of the current parameters for a given camera.

Hazen 04/17
"""

import importlib
from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class ParamsViewerException(halExceptions.HalException):
    pass

class ParamsViewer(QtWidgets.QGroupBox):
    """
    This class handles displaying (some of) the current camera parameters
    in the UI. It also handles the EMCCD gain slider (if the camera has
    an EMCCD).
    """
    def __init__(self, viewer_name = "", viewer_ui = None, **kwds):
        super().__init__(**kwds)
        self.cam_fn = None
        self.temperature = 50
        self.viewer_name = viewer_name

        # UI setup
        self.ui = viewer_ui.Ui_GroupBox()
        self.ui.setupUi(self)

        # connect signals
        self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

    def handleEMCCDGain(self, new_gain):
        if (new_gain != self.ui.EMCCDSlider.value()):
            self.ui.EMCCDSlider.valueChanged.disconnect()
            self.ui.EMCCDSlider.setValue(new_gain)
            self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)
        self.ui.EMCCDLabel.setText("EMCCD Gain: {0:d}".format(new_gain))

    def handleGainChange(self, new_gain):
        if self.cam_fn is not None:
            self.cam_fn.setEMCCDGain(new_gain)
            
    def handleTemperature(self, t_dict):
        if (t_dict["state"] == "stable"):
            self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
        else:
            self.ui.temperatureText.setStyleSheet("QLabel { color: red }")
        self.ui.temperatureText.setText(str(t_dict["temperature"]) + " (" + str(self.temperature) + ")")

    def setCameraFunctionality(self, camera_functionality):

        # Disconnect signals from previous camera_functionality, if any.
        if self.cam_fn is not None:
            self.cam_fn.emccdGain.disconnect(self.handleEMCCDGain)
            self.cam_fn.temperature.disconnect(self.handleTemperature)

        # If this is a feed we want it's source camera functionality.
        if camera_functionality.isCamera():
            self.cam_fn = camera_functionality
        else:
            self.cam_fn = camera_functionality.getCameraFunctionality()

        # Connect new signals.
        self.cam_fn.emccdGain.connect(self.handleEMCCDGain)
        self.cam_fn.temperature.connect(self.handleTemperature)

        # Set the group box title.
        self.setTitle(self.cam_fn.getCameraName().title())

        # Show hide UI elements.
        if self.cam_fn.hasEMCCD():
            if not self.cam_fn.hasParameter("emccd_gain"):
                raise ParamsViewerException("EMCCD cameras must have the 'emccd_gain' parameter.")
            self.ui.EMCCDLabel.show()
            self.ui.EMCCDSlider.show()
        else:
            self.ui.EMCCDLabel.hide()
            self.ui.EMCCDSlider.hide()

        if self.cam_fn.hasPreamp():
            if not self.cam_fn.hasParameter("preampgain"):
                msg = "Cameras with adjustable preamp gain must have the 'preampgain' parameter."
                raise ParamsViewerException(msg)
            self.ui.preampGainLabel.show()
            self.ui.preampGainText.show()
        else:
            self.ui.preampGainLabel.hide()
            self.ui.preampGainText.hide()

        if self.cam_fn.hasTemperature():
            if not self.cam_fn.hasParameter("temperature"):
                msg = "Cameras with temperature control must have the 'temperature' parameter."
                raise ParamsViewerException(msg)
            self.ui.temperatureLabel.show()
            self.ui.temperatureText.show()
        else:
            self.ui.temperatureLabel.hide()
            self.ui.temperatureText.hide()

        # Update UI elements.
        if self.cam_fn.hasParameter("emccd_gain"):
            gainp = self.cam_fn.getParameterObject("emccd_gain")
            self.ui.EMCCDSlider.valueChanged.disconnect()
            self.ui.EMCCDSlider.setMinimum(gainp.getMinimum())
            self.ui.EMCCDSlider.setMaximum(gainp.getMaximum())
            self.ui.EMCCDSlider.setValue(gainp.getv())
            self.ui.EMCCDLabel.setText("EMCCD Gain: {0:d}".format(gainp.getv()))
            self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

#        if self.cam_fn.hasParameter("external_trigger") and self.cam_fn.getParameter("external_trigger"):
            
        if self.cam_fn.isMaster():
            self.ui.exposureTimeText.setText("{0:.4f}".format(self.cam_fn.getParameter("exposure_time")))
            self.ui.FPSText.setText("{0:.4f}".format(self.cam_fn.getParameter("fps")))
        else:
            self.ui.exposureTimeText.setText("External")
            self.ui.FPSText.setText("External")
            
        if self.cam_fn.hasParameter("preampgain"):
            self.ui.preampGainText.setText("{0:.1f}".format(self.cam_fn.getParameter("preampgain")))

        if self.cam_fn.hasParameter("temperature"):
            self.temperature = self.cam_fn.getParameter("temperature")

        self.ui.pictureSizeText.setText(str(self.cam_fn.getParameter("x_pixels")) + " x " +
                                        str(self.cam_fn.getParameter("y_pixels")) + " (" +
                                        str(self.cam_fn.getParameter("x_bin")) + "," +
                                        str(self.cam_fn.getParameter("y_bin")) + ")")

    def startFilm(self):
        self.ui.EMCCDSlider.setEnabled(False)

    def stopFilm(self):
        self.ui.EMCCDSlider.setEnabled(True)
            

#
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
