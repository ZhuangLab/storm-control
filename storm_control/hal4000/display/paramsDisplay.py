#!/usr/bin/python
#
## @file
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
# Hazen 09/15
#

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

## ParamsDisplay
#
# This class handles displaying (some of) the current camera parameters
# in the UI. It also handles the EMCCD gain slider.
#
class ParamsDisplay(QtGui.QGroupBox):
    gainChange = QtCore.pyqtSignal(str, int)

    ## __init__
    #
    # Create a camera parameters object.
    #
    # @param camera_params_ui The UI object like what would be created from a .ui file.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, camera_params_ui, which_camera, parent = None):
        QtGui.QGroupBox.__init__(self, parent)
        self.parameters = None
        self.temperature = False
        self.which_camera = which_camera

        # UI setup
        self.ui = camera_params_ui
        self.ui.setupUi(self)

        # connect signals
        self.ui.EMCCDSlider.valueChanged.connect(self.handleGainChange)

    ## handleGainChange
    #
    # Handles camera gain changes. Updates the display and emits a gainChange signal
    # that is received by the camera control object.
    #
    # @param new_gain The new EMCCD gain value.
    #
    @hdebug.debug
    def handleGainChange(self, new_gain):
        self.ui.EMCCDLabel.setText("EMCCD Gain: %d" % new_gain)
        self.gainChange.emit(self.which_camera, new_gain)

    ## newParameters
    #
    # Update the displayed camera parameters based on the new parameters object.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug        
    def newParameters(self, parameters):
        self.parameters = parameters.get(self.which_camera)
        p = self.parameters
        if p.has("temperature"):
            self.temperature = p.get("temperature")

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

    ## showEMCCD
    #
    # Show or hide the UI fields associated with EM gain.
    #
    # @param visible True/False.
    #
    @hdebug.debug
    def showEMCCD(self, visible):
        if visible:
            self.ui.EMCCDLabel.show()
            self.ui.EMCCDSlider.show()
        else:
            self.ui.EMCCDLabel.hide()
            self.ui.EMCCDSlider.hide()

    ## showPreamp
    #
    # Show or hide the UI fields associated with pre-amplifier gain.
    #
    # @param visible True/False.
    #
    @hdebug.debug
    def showPreamp(self, visible):
        if visible:
            self.ui.preampGainLabel.show()
            self.ui.preampGainText.show()
        else:
            self.ui.preampGainLabel.hide()
            self.ui.preampGainText.hide()

    ## showTemperature
    #
    # Show or hide the UI fields associated with camera sensor temperature.
    #
    @hdebug.debug
    def showTemperature(self, visible):
        if visible:
            self.ui.temperatureLabel.show()
            self.ui.temperatureText.show()
        else:
            self.ui.temperatureLabel.hide()
            self.ui.temperatureText.hide()

    ## startFilm
    #
    @hdebug.debug
    def startFilm(self):
        self.ui.EMCCDSlider.setEnabled(False)
        
    ## stopFilm
    #
    @hdebug.debug
    def stopFilm(self):
        self.ui.EMCCDSlider.setEnabled(True)

    ## updateCameraProperties
    #
    # @param camera_properties A dictionary containing property sets for each camera.
    #
    @hdebug.debug
    def updateCameraProperties(self, camera_properties):
        properties = camera_properties[self.which_camera]
        self.showEMCCD("have_emccd" in properties)
        self.showPreamp("have_preamp" in properties)
        self.showTemperature("have_temperature" in properties)

    ## updatedParams
    #
    # The temperature and the emgain might have changed.
    #
    @hdebug.debug
    def updatedParams(self):
        if self.parameters.has("temperature_control"):
            if (self.parameters.get("temperature_control") == "stable"):
                self.ui.temperatureText.setStyleSheet("QLabel { color: green }")
            else:
                self.ui.temperatureText.setStyleSheet("QLabel { color: red }")
            actual_temp = self.parameters.get("actual_temperature")
            self.ui.temperatureText.setText(str(actual_temp) + " (" + str(self.temperature) + ")")        
    
#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
