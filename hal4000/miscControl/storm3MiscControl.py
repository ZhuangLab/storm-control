#!/usr/bin/python
#
# Miscellaneous controls, such as the EPI/TIRF motor and
# the various lasers for STORM3.
#
# Hazen 5/11
#

import sys
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.storm3_misc_ui as miscControlsUi

# SMC100 motor (for EPI/TIRF)
import newport.SMC100 as SMC100

# Prior filter wheel
import stagecontrol.storm3StageControl as filterWheel


#
# Misc Control Dialog Box
#
class AMiscControl(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.filter_wheel = filterWheel.QPriorFilterWheel()
        self.move_timer = QtCore.QTimer(self)
        self.move_timer.setInterval(50)
        self.parameters = parameters
        self.smc100 = SMC100.SMC100()

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = miscControlsUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Misc Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleQuit)

        # setup epi/tir stage control
        self.connect(self.ui.EPIButton, QtCore.SIGNAL("clicked()"), self.goToEPI)
        self.connect(self.ui.leftSmallButton, QtCore.SIGNAL("clicked()"), self.smallLeft)
        self.connect(self.ui.rightSmallButton, QtCore.SIGNAL("clicked()"), self.smallRight)
        self.connect(self.ui.leftLargeButton, QtCore.SIGNAL("clicked()"), self.largeLeft)
        self.connect(self.ui.rightLargeButton, QtCore.SIGNAL("clicked()"), self.largeRight)
        self.connect(self.ui.TIRFButton, QtCore.SIGNAL("clicked()"), self.goToTIRF)
        self.connect(self.ui.tirGoButton, QtCore.SIGNAL("clicked()"), self.goToX)
        self.connect(self.move_timer, QtCore.SIGNAL("timeout()"), self.updatePosition)

        self.position = self.smc100.getPosition()
        self.setPositionText()

        # setup filter wheel
        self.filters = [self.ui.filter1Button,
                        self.ui.filter2Button,
                        self.ui.filter3Button,
                        self.ui.filter4Button,
                        self.ui.filter5Button,
                        self.ui.filter6Button]
        for filter in self.filters:
            self.connect(filter, QtCore.SIGNAL("clicked()"), self.handleFilter)
        self.filters[self.filter_wheel.getPosition()-1].click()

        # set modeless
#        self.setModal(False)

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def goToEPI(self):
        self.position = self.epi_position
        self.moveStage()

    @hdebug.debug
    def goToTIRF(self):
        self.position = self.tirf_position
        self.moveStage()

    @hdebug.debug
    def goToX(self):
        self.position = self.ui.tirSpinBox.value()
        self.moveStage()

    @hdebug.debug
    def handleFilter(self):
        for i, filter in enumerate(self.filters):
            if filter.isChecked():
                filter.setStyleSheet("QPushButton { color: red}")
                self.filter_wheel.setPosition(i+1)
                self.parameters.filter_position = i
            else:
                filter.setStyleSheet("QPushButton { color: black}")

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    @hdebug.debug
    def largeLeft(self):
        if self.position > 14.0:
            self.position -= 10.0 * self.jog_size
            self.moveStage()

    @hdebug.debug
    def largeRight(self):
        if self.position < 23.0:
            self.position += 10.0 * self.jog_size
            self.moveStage()

    def moveStage(self):
        self.move_timer.start()
        self.smc100.stopMove()
        self.smc100.moveTo(self.position)
        self.setPositionText()

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        self.jog_size = parameters.jog_size
        self.epi_position = parameters.epi_position
        self.tirf_position = parameters.tirf_position
        names = parameters.filter_names
        if (len(names) == 6):
            for i in range(6):
                self.filters[i].setText(names[i])
        self.filters[self.parameters.filter_position].click()

    def setPositionText(self):
        self.ui.positionText.setText("{0:.3f}".format(self.position))

    @hdebug.debug
    def smallLeft(self):
        if self.position > 14.0:
            self.position -= self.jog_size
            self.moveStage()

    @hdebug.debug
    def smallRight(self):
        if self.position < 23.0:
            self.position += self.jog_size
            self.moveStage()

    def updatePosition(self):
        if not self.smc100.amMoving():
            self.move_timer.stop()
        self.position = self.smc100.getPosition()
        self.setPositionText()

    @hdebug.debug
    def quit(self):
        self.smc100.shutDown()

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
