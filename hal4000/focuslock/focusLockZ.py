#!/usr/bin/python
#
# Z focus lock dialog box.
#
# FocusLockZ is the base class.
#
# FocusLockZQPD is specialized for displaying QPD style
#    offset data.
#
# FocusLockZCam is specialized for displaying USB camera
#    offset data.
#
# FocusLockZDualCam is specializef for displaying USB
#    camera data from the dual objective setup.
#
# Hazen 12/12
#

import numpy
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# Widgets
import focuslock.lockDisplay as lockDisplay
import focuslock.lockModes as lockModes

#
# The base class.
#
class FocusLockZ(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, parent):
        QtGui.QDialog.__init__(self, parent)
        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # general
        self.offset_file = 0
        self.parameters = parameters
        self.jumpsize = 0.0
        self.tcp_control = tcp_control

    @hdebug.debug    
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def closeOffsetFile(self):
        if self.offset_file:
            self.offset_file.close()
            self.offset_file = 0

    @hdebug.debug
    def configureUI(self):
        parameters = self.parameters

        # UI setup
        self.setWindowTitle(parameters.setup_name + " Focus Lock")
        self.ui.lockLabel.setStyleSheet("QLabel { color: green }")
        self.toggleLockButtonDisplay(self.lock_display1.shouldDisplayLockButton())
        self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())

        # The mode radio buttons, these should be in the
        # same order as the lock modes in the lockDisplay class.
        self.buttons = [self.ui.offRadioButton,
                        self.ui.autoRadioButton,
                        self.ui.onRadioButton,
                        self.ui.optimalRadioButton,
                        self.ui.calRadioButton,
                        self.ui.zScanRadioButton]

        self.buttons[parameters.qpd_mode].setChecked(True)

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.autoRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.calRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.offRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.onRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.optimalRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.zScanRadioButton.clicked.connect(self.handleRadioButtons)
        self.ui.lockButton.clicked.connect(self.handleLockButton)
        self.ui.jumpSpinBox.valueChanged.connect(self.handleJumpSpinBox)
        self.ui.jumpButton.clicked.connect(self.handleJumpButton)

        # tcp signals
        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("findSum()"), self.tcpHandleFindSum)
            self.connect(self.tcp_control, QtCore.SIGNAL("recenterPiezo()"), self.tcpHandleRecenterPiezo)
            self.connect(self.tcp_control, QtCore.SIGNAL("setLockTarget(float)"), self.tcpHandleSetLockTarget)

        # set modeless
        self.setModal(False)

    @hdebug.debug
    def getLockTarget(self):
        return self.lock_display1.getLockTarget()

    @hdebug.debug
    def handleFoundSum(self):
        self.tcp_control.sendComplete()

    @hdebug.debug
    def handleJumpButton(self):
        self.lock_display1.jump(self.jumpsize)

    @hdebug.debug                    
    def handleJumpSpinBox(self, jumpsize):
        self.jumpsize = jumpsize

    @hdebug.debug
    def handleLockButton(self):
        self.lock_display1.lockButtonToggle()
        self.toggleLockButtonText(self.lock_display1.amLocked())
        self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleRadioButtons(self):
        for i in range(len(self.buttons)):
            if self.buttons[i].isChecked():
                if self.lock_display1.changeLockMode(i):
                    self.toggleLockButtonDisplay(self.lock_display1.shouldDisplayLockButton())
                    self.toggleLockButtonText(self.lock_display1.amLocked())
                    self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())

    @hdebug.debug
    def handleRecenteredPiezo(self):
        self.tcp_control.sendComplete()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    @hdebug.debug
    def jump(self, step_size):
        self.lock_display1.jump(step_size)

    @hdebug.debug
    def openOffsetFile(self, filename):
        self.offset_file = open(filename + ".off", "w")
        self.offset_file.write("frame offset power stage-z\n")

    def newFrame(self, frame):
        if frame.master:
            if self.offset_file:
                [offset, power, stage_z] = self.lock_display1.getOffsetPowerStage()
                self.offset_file.write("{0:d} {1:.6f} {2:.6f} {3:.6f}\n".format(frame.number, offset, power, stage_z))
            self.lock_display1.newFrame(frame)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        self.lock_display1.newParameters(self.parameters)

    @hdebug.debug
    def quit(self):
        self.lock_display1.quit()
        self.closeOffsetFile()
        
    @hdebug.debug
    def startLock(self, filename):
        self.counter = 0
        self.error = 0.0
        self.error_counts = 0
        if filename:
            self.openOffsetFile(filename)
        self.lock_display1.startLock()
        self.toggleLockButtonText(self.lock_display1.amLocked())
        self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())

    @hdebug.debug
    def stopLock(self):
        self.lock_display1.stopLock()
        self.toggleLockButtonText(self.lock_display1.amLocked())
        self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())
        self.closeOffsetFile()

    @hdebug.debug
    def tcpHandleFindSum(self):
        self.lock_display1.tcpHandleFindSum()

    @hdebug.debug
    def tcpHandleRecenterPiezo(self):
        self.lock_display1.tcpHandleRecenterPiezo()

    @hdebug.debug
    def tcpHandleSetLockTarget(self, target):
        self.lock_display1.tcpHandleSetLockTarget(target)

    def toggleLockButtonDisplay(self, show):
        if show:
            self.ui.lockButton.show()
        else:
            self.ui.lockButton.hide()

    def toggleLockLabelDisplay(self, show):
        if show:
            self.ui.lockLabel.show()
        else:
            self.ui.lockLabel.hide()

    def toggleLockButtonText(self, locked):
        if locked:
            self.ui.lockButton.setText("Unlock")
            self.ui.lockButton.setStyleSheet("QPushButton { color: green}")
        else:
            self.ui.lockButton.setText("Lock")
            self.ui.lockButton.setStyleSheet("QPushButton { color: black}")

#
# FocusLockZ specialized for QPD style offset data.
#
class FocusLockZQPD(FocusLockZ):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, control_thread, ir_laser, parent):
        FocusLockZ.__init__(self, parameters, tcp_control, parent)

        # Setup UI.
        import qtdesigner.focuslock_ui as focuslockUi

        self.ui = focuslockUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Add QPD lock display.
        self.lock_display1 = lockDisplay.LockDisplayQPD(parameters,
                                                        control_thread, 
                                                        ir_laser, 
                                                        self.ui.lockDisplayWidget)
        self.lock_display1.foundSum.connect(self.handleFoundSum)
        self.lock_display1.recenteredPiezo.connect(self.handleRecenteredPiezo)

        FocusLockZ.configureUI(self)

#
# FocusLockZ specialized for camera style offset data.
#
class FocusLockZCam(FocusLockZ):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, control_thread, ir_laser, parent):
        FocusLockZ.__init__(self, parameters, tcp_control, parent)

        # Setup UI.
        import qtdesigner.focuslock_ui as focuslockUi

        self.ui = focuslockUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Add Camera lock display.
        self.lock_display1 = lockDisplay.LockDisplayCam(parameters,
                                                        control_thread, 
                                                        ir_laser, 
                                                        self.ui.lockDisplayWidget)
        self.lock_display1.foundSum.connect(self.handleFoundSum)
        self.lock_display1.recenteredPiezo.connect(self.handleRecenteredPiezo)

        FocusLockZ.configureUI(self)

#
# FocusLockZ specialized for dual camera offset data.
#
class FocusLockZDualCam(FocusLockZ):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, control_threads, ir_lasers, parent):
        FocusLockZ.__init__(self, parameters, tcp_control, parent)

        # Setup UI.
        import qtdesigner.dualfocuslock_ui as dualfocuslockUi

        self.ui = dualfocuslockUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Add Camera1 lock display.
        self.lock_display1 = lockDisplay.LockDisplayCam(parameters,
                                                        control_threads[0], 
                                                        ir_lasers[0], 
                                                        self.ui.lockDisplay1Widget)
        self.lock_display1.ui.statusBox.setTitle("Lock1 Status")
        self.lock_display1.foundSum.connect(self.handleFoundSum)
        self.lock_display1.recenteredPiezo.connect(self.handleRecenteredPiezo)

        # Add Camera2 lock display.
        self.lock_display2 = lockDisplay.LockDisplayCam(parameters,
                                                        control_threads[1],
                                                        ir_lasers[1],
                                                        self.ui.lockDisplay2Widget)
        self.lock_display2.ui.statusBox.setTitle("Lock2 Status")

        FocusLockZ.configureUI(self)

    @hdebug.debug
    def handleJumpButton(self):
        FocusLockZ.handleJumpButton(self)
        self.lock_display2.jump(-self.jumpsize)

    @hdebug.debug
    def handleLockButton(self):
        FocusLockZ.handleLockButton(self)
        self.lock_display2.lockButtonToggle()

    @hdebug.debug
    def handleRadioButtons(self):
        for i in range(len(self.buttons)):
            if self.buttons[i].isChecked():
                if self.lock_display1.changeLockMode(i):
                    self.lock_display2.changeLockMode(i)
                    self.toggleLockButtonDisplay(self.lock_display1.shouldDisplayLockButton())
                    self.toggleLockButtonText(self.lock_display1.amLocked())
                    self.toggleLockLabelDisplay(self.lock_display1.shouldDisplayLockLabel())

    @hdebug.debug
    def jump(self, step_size):
        self.lock_display1.jump(step_size)
        self.lock_display2.jump(-step_size)

    def newFrame(self, frame):
        if frame.master:
            if self.offset_file:
                [offset1, power1, stage_z1] = self.lock_display1.getOffsetPowerStage()
                [offset2, power2, stage_z2] = self.lock_display2.getOffsetPowerStage()
                self.offset_file.write("{0:d} {1:.6f} {2:.6f} {3:.6f} {4:.6f} {5:.6f} {6:.6f}\n".format(frame.number, offset1, power1, stage_z1, offset2, power2, stage_z2))
            self.lock_display1.newFrame(frame)
            self.lock_display2.newFrame(frame)

    @hdebug.debug
    def openOffsetFile(self, filename):
        self.offset_file = open(filename + ".off", "w")
        self.offset_file.write("frame offset1 power1 stage-z1 offset2 power2 stage-z2\n")

    @hdebug.debug
    def quit(self):
        self.lock_display1.quit()
        self.lock_display2.quit()
        self.closeOffsetFile()

    @hdebug.debug
    def startLock(self, filename):
        FocusLockZ.startLock(self, filename)
        self.lock_display2.startLock()

    @hdebug.debug
    def stopLock(self):
        FocusLockZ.stopLock(self)
        self.lock_display2.stopLock()

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
