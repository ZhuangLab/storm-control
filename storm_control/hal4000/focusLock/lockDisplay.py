#!/usr/bin/env python
"""
This class handles the lock display group box and it's widgets.

Hazen 04/17
"""

from PyQt5 import QtWidgets

# UI.
import storm_control.hal4000.qtdesigner.lockdisplay_ui as lockdisplayUi


class LockDisplay(QtWidgets.QGroupBox):
    """
    The lock display UI group box.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.display_widgets = []
        self.ir_laser_functionality = None
        self.ir_on = False
        self.ir_power = configuration.get("ir_power", 0)

        # UI setup
        self.ui = lockdisplayUi.Ui_Form()
        self.ui.setupUi(self)
        
        self.ui.irButton.hide()
        self.ui.irSlider.hide()

    def handleIrButton(self, boolean):
        """
        Handles the IR laser button. Turns the laser on/off and
        updates the button accordingly.
        """
        if self.ir_on:
            self.ir_laser_functionality.onOff(0.0, False)
            self.ir_on = False
            self.ui.irButton.setText("IR ON")
            self.ui.irButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.ir_laser_functionality.onOff(self.ir_power, True)
            self.ir_on = True
            self.ui.irButton.setText("IR OFF")
            self.ui.irButton.setStyleSheet("QPushButton { color: red }")

    def handleIrSlider(self, value):
        """
        Handles the IR laser power slider.
        """
        self.ir_power = value
        self.ir_laser_functionality.output(self.ir_power)

    def haveAllFunctionalities(self):
        if self.ir_laser_functionality is None:
            return False
        for widget in self.display_widgets:
            if not widget.haveFunctionality():
                return False
        return True
        
    def setFunctionality(self, name, functionality):
        if (name == "ir_laser"):
            self.ir_laser_functionality = functionality
            
            self.ui.irButton.show()
            self.ui.irButton.clicked.connect(self.handleIrButton)
            if self.ir_laser_functionality.hasPowerAdjustment():
                self.ui.irSlider.show()
                self.ui.irSlider.setMaximum(self.ir_laser_functionality.getMaximum())
                self.ui.irSlider.setValue(self.ir_power)
                self.ui.irSlider.valueChanged.connect(self.handleIrSlider)
        else:
            for widget in self.display_widgets:
                widget.setFunctionality(name, functionality)
                

#    def handleAdjustStage(self, direction):
#        self.jump(float(direction)*self.parameters.get("lockt_step"))


            


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
