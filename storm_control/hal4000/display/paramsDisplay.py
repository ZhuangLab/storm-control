#!/usr/bin/python
"""
Handles the display of the current parameters for a given camera.

Hazen 01/17
"""

import importlib
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class ParamsView(QtWidgets.QGroupBox):
    """
    This class handles displaying (some of) the current camera parameters
    in the UI. It also handles the EMCCD gain slider (if the camera has
    an EMCCD).
    """
    gainChange = QtCore.pyqtSignal(int)

    def __init__(self, camera_params_ui = None, **kwds):
        super().__init__(**kwds)

        # UI setup
        self.ui = camera_params_ui.Ui_GroupBox()
        self.ui.setupUi(self)

        # connect signals
        self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

    def configureUi(self, camera_config):
        self.setTitle(camera_config["camera"].title())
        
        if camera_config["have_emccd"]:
            self.ui.EMCCDLabel.show()
            self.ui.EMCCDSlider.show()
        else:
            self.ui.EMCCDLabel.hide()
            self.ui.EMCCDSlider.hide()

        if camera_config["have_preamp"]:
            self.ui.preampGainLabel.show()
            self.ui.preampGainText.show()
        else:
            self.ui.preampGainLabel.hide()
            self.ui.preampGainText.hide()

        if camera_config["have_temp"]:
            self.ui.temperatureLabel.show()
            self.ui.temperatureText.show()
        else:
            self.ui.temperatureLabel.hide()
            self.ui.temperatureText.hide()

    def enableEMCCDSlider(self, enable):
        self.ui.EMCCDSlider.setEnabled(enable)

    def handleGainChange(self, new_gain):
        self.ui.EMCCDLabel.setText("EMCCD Gain: %d" % new_gain)
        self.gainChange.emit(new_gain)

    def newParameters(self, parameters):
        p = parameters
        if p.has("emgainmode"):
            self.ui.EMCCDSlider.valueChanged.disconnect()
            self.ui.EMCCDSlider.setMinimum(p.get("em_gain_low", 1))
            self.ui.EMCCDSlider.setMaximum(p.get("em_gain_high", 10))
            self.ui.EMCCDSlider.setValue(p.get("emccd_gain"))
            self.ui.EMCCDLabel.setText("EMCCD Gain: %d" % p.get("emccd_gain"))
            self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

        if p.has("preampgain"):
            self.ui.preampGainText.setText("%.1f" % p.get("preampgain"))

        self.ui.pictureSizeText.setText(str(p.get("x_pixels")) + " x " + str(p.get("y_pixels")) +
                                        " (" + str(p.get("x_bin")) + "," + str(p.get("y_bin")) + ")")

        if p.get("external_trigger", False):
            self.ui.exposureTimeText.setText("External")
            self.ui.FPSText.setText("External")
        else:
            self.ui.exposureTimeText.setText("%.4f" % p.get("exposure_value"))
            self.ui.FPSText.setText("%.4f" % (1.0/p.get("cycle_value")))

    def updateTemperature(self, temp_data):
        if (temp_data["state"] == "stable"):
            self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
        else:
            self.ui.temperatureText.setStyleSheet("QLabel { color: red }")
            
        actual_temp = temp_data["temperature"]
        self.ui.temperatureText.setText(str(actual_temp) + " (" + str(self.temperature) + ")")        


class Params(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.current_camera = None

        if (module_params.get("ui_type") == "classic"):
            pv_ui = importlib.import_module("storm_control.hal4000.qtdesigner.camera_params_ui")
            self.view = ParamsView(camera_params_ui = pv_ui)
            self.configure_dict = {"ui_order" : 2,
                                   "ui_parent" : "hal.containerWidget",
                                   "ui_widget" : self.view}
        else:
            pv_ui = importlib.import_module("storm_control.hal4000.qtdesigner.camera_params_detached_ui")
            self.view = ParamsView(camera_params_ui = pv_ui)
            self.configure_dict = {"ui_parent" : "display.cameraParamsFrame",
                                   "ui_widget" : self.view}

        self.view.gainChange.connect(self.handleGainChange)
        
        halMessage.addMessage("set emccd gain")

    def handleGainChange(self, new_gain):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "set emccd gain",
                                                   data = {"camera" : self.current_camera,
                                                           "gain" : new_gain}))
        
    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):

            # The current camera has changed.
            if (message.getType() == "camera config"):
                data = message.getData()
                self.current_camera = data["camera"]
                self.view.configureUi(data)

            elif (message.getType() == "camera temperature"):
                data = message.getData()
                if (self.current_camera == data["camera"]):
                    self.view.updateTemperature(data)

            elif (message.getType() == "configure"):
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = self.configure_dict))

            elif (message.getType() == "new parameters"):
                p = message.getData().get(self.current_camera).copy()
                self.view.newParameters(p)


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
