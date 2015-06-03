#!/usr/bin/python
#
## @file
#
# Miscellaneous controls, such as the EPI/TIRF motor and
# the filter wheel for NSTORM.
#
# Hazen 04/15
#

from PyQt4 import QtCore, QtGui

import miscControl

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.nstorm_misc_ui as miscControlsUi

# Nikon TiU hardware control.
import sc_hardware.nikon.tiUMisc as tiUMisc


#
# Misc Control Dialog Box
#
class AMiscControl(miscControl.MiscControl):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        miscControl.MiscControl.__init__(self, parameters, parent)

        self.move_timer = QtCore.QTimer(self)
        self.move_timer.setInterval(50)
        self.tiu_misc = tiUMisc.TiUMisc()

        # UI setup
        self.ui = miscControlsUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Misc Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        # setup epi/tir stage control
        self.ui.EPIButton.clicked.connect(self.goToEPI)
        self.ui.leftSmallButton.clicked.connect(self.smallLeft)
        self.ui.rightSmallButton.clicked.connect(self.smallRight)
        self.ui.leftLargeButton.clicked.connect(self.largeLeft)
        self.ui.rightLargeButton.clicked.connect(self.largeRight)
        self.ui.TIRFButton.clicked.connect(self.goToTIRF)
        self.ui.tirGoButton.clicked.connect(self.goToX)
        self.move_timer.timeout.connect(self.updatePosition)

        self.position = self.tiu_misc.getTirfPosition()
        self.setPositionText()

        # setup filter wheel
        self.filters = [self.ui.filter1Button,
                        self.ui.filter2Button,
                        self.ui.filter3Button,
                        self.ui.filter4Button,
                        self.ui.filter5Button,
                        self.ui.filter6Button]
        for filter in self.filters:
            filter.clicked.connect(self.handleFilter)
        self.filters[self.tiu_misc.getFilterWheel()].click()

        # setup bright field shutter
        self.bf_shutter = self.tiu_misc.getBrightFieldShutter()
        self.handleBFTextUpdate()
        self.ui.bfButton.clicked.connect(self.handleBFButton)

        self.newParameters(self.parameters)

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        pass

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        pass

    @hdebug.debug
    def goToEPI(self, bool):
        self.position = self.epi_position
        self.moveStage()

    @hdebug.debug
    def goToTIRF(self, bool):
        self.position = self.tirf_position
        self.moveStage()

    @hdebug.debug
    def goToX(self, bool):
        self.position = self.ui.tirSpinBox.value()
        self.moveStage()

    @hdebug.debug
    def handleBFButton(self, bool):
        self.bf_shutter = not self.bf_shutter
        self.parameters.set("bf_shutter", self.bf_shutter)
        self.tiu_misc.setBrightFieldShutter(self.bf_shutter)
        self.handleBFTextUpdate()

    @hdebug.debug
    def handleBFTextUpdate(self):
        if self.bf_shutter:
            self.ui.bfButton.setText("Close")
            self.ui.bfButton.setStyleSheet("QPushButton { color: red}")
        else:
            self.ui.bfButton.setText("Open")
            self.ui.bfButton.setStyleSheet("QPushButton { color: black}")

    @hdebug.debug
    def handleFilter(self, bool):
        for i, filter in enumerate(self.filters):
            if filter.isChecked():
                filter.setStyleSheet("QPushButton { color: red}")
                self.tiu_misc.setFilterWheel(i)
                self.parameters.set("filter_position", i)
            else:
                filter.setStyleSheet("QPushButton { color: black}")

    @hdebug.debug
    def largeLeft(self, bool):
        if self.position > 14.0:
            self.position -= 10.0 * self.jog_size
            self.moveStage()

    @hdebug.debug
    def largeRight(self, bool):
        if self.position < 23.0:
            self.position += 10.0 * self.jog_size
            self.moveStage()

    def moveStage(self):
        self.tiu_misc.setTirfPosition(self.position)
        self.move_timer.start()

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        self.jog_size = parameters.get("jog_size")
        self.epi_position = parameters.get("epi_position")
        self.tirf_position = parameters.get("tirf_position")

        names = parameters.filter_names
        if (len(names) == 6):
            for i in range(6):
                self.filters[i].setText(names[i])
        self.filters[self.parameters.get("filter_position")].click()

        if not (self.bf_shutter == parameters.get("bf_shutter")):
            self.ui.bfButton.click()

    def setPositionText(self):
        self.ui.positionText.setText("{0:.3f}".format(self.position))

    @hdebug.debug
    def smallLeft(self, bool):
        if self.position > 14.0:
            self.position -= self.jog_size
            self.moveStage()

    @hdebug.debug
    def smallRight(self, bool):
        if self.position < 23.0:
            self.position += self.jog_size
            self.moveStage()

    def updatePosition(self):
        if not self.tiu_misc.isTirfBusy():
            self.move_timer.stop()
        self.position = self.tiu_misc.getTirfPosition()
        self.setPositionText()


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
