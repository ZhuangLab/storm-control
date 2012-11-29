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
#
#  Methods called by HAL:
#
#    getLockTarget()
#      Returns the current lock target (in nm).
#
#    jump(offset)
#      Change the focus by offset (in um).
#
#    newFrame(frame)
#      Called when filming and a new image is available
#      from the camera.
#
#    newParameters(parameters)
#      Called when the parameters file has been changed.
#
#    show()
#      Show the focus lock UI dialog box (if any).
#
#    startLock(filename)
#      Called when the filming (recording) starts. "filename"
#      can also be 0 meaning that we are taking a "test" film,
#      ie we are not actually saving the data.
#
#    stopLock()
#      Called when filming has ended.
#
#    quit()
#      Clean up and shutdown prior to the program ending.
#
# Hazen 11/12
#

import numpy
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.focuslock_ui as focuslockUi

# Widgets
import focuslock.lockDisplayWidgets as lockDisplayWidgets
import focuslock.lockModes as lockModes

#
# Z Focus Lock Dialog Box
# QPD / piezo Z Focus Lock Control Class
#
# This is the UI for focus lock based on some sort of 
# Z positioner and a position readout of the lock target.
# The interaction with the actual hardware occurs via
# control_thread & ir_laser.
#
# The control_thread is a class with the following methods:
#
# cleanup()
#    Perform any cleanup that needs to be done prior to quitting.
#
# getLockTarget()
#    Returns the current lock target in QPD units.
#
# findSumSignal()
#    Finds sum signal, if it is too low, otherwise does nothing.
#
# moveStageAbs(pos)
#    Moves the stage to the position (in um) given by pos
#
# moveStageRel(size)
#    Moves the stage relative to it current position by size um.
#
# newZCenter(center)
#    Sets the position the stage returns when the lock stops (in um).
#
# recenter()
#    Move the stage back to its center position.
#
# recenterPiezo()
#    Center the piezo with the focus motor, if available.
#
# setStage(stage)
#    Replace current stage control class with class instance stage.
#
# setTarget()
#    Set the lock target in QPD units.
#
# start()
#    Start any threads that are needed for the focus lock.
#
# startLock()
#    Start the focus lock.
#
# stopLock()
#    Stop the focus lock.
#
# stopThread()
#    Stop any threads that are running in preparation for quitting.
#
# wait()
#    Return once all running threads have stopped.
#
#
# The control_thread class should emit the following signal when it has
# new QPD/stage position data.
#
# controlUpdate(float x_offset, float y_offset, float power, float stage_z)
#
#
# ir_laser is a class with the following methods:
#
# on(power)
#   Turn on the IR laser. Power is a value from 1 to 100.
#
# off()
#   Turn off the IR laser
#
class FocusLockZ(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, control_thread, ir_laser, parent):
        QtGui.QMainWindow.__init__(self, parent)
        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # general
        self.ir_power = 0
        self.offset = 0
        self.offset_file = 0
        self.parameters = parameters
        self.power = 0
        self.stage_z = 0
        self.tcp_control = tcp_control

        # Lock modes
        self.lock_modes = [lockModes.NoLockMode(control_thread,
                                                parameters,
                                                self),
                           lockModes.AutoLockMode(control_thread,
                                                  parameters,
                                                  self),
                           lockModes.AlwaysOnLockMode(control_thread,
                                                      parameters,
                                                      self),
                           lockModes.OptimalLockMode(control_thread,
                                                     parameters,
                                                     self),
                           lockModes.CalibrationLockMode(control_thread,
                                                         parameters,
                                                         self),
                           lockModes.ZScanLockMode(control_thread,
                                                   parameters,
                                                   self)]
        
        self.current_mode = self.lock_modes[parameters.qpd_mode]

        # UI setup
        self.ui = focuslockUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Focus Lock")
        self.ui.lockLabel.setStyleSheet("QLabel { color: green }")
        self.toggleLockButtonDisplay(self.current_mode.shouldDisplayLockButton())
        self.toggleLockLabelDisplay(self.current_mode.shouldDisplayLockLabel())
        if (not ir_laser.havePowerControl()):
            self.ui.irSlider.hide()

        # The mode radio buttons, these should be in the
        # same order as the lock modes above.
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
        self.ui.irButton.clicked.connect(self.handleIrButton)
        self.ui.irSlider.valueChanged.connect(self.handleIrSlider)

        # tcp signals
        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("findSum()"), self.tcpHandleFindSum)
            self.connect(self.tcp_control, QtCore.SIGNAL("recenterPiezo()"), self.tcpHandleRecenterPiezo)
            self.connect(self.tcp_control, QtCore.SIGNAL("setLockTarget(float)"), self.tcpHandleSetLockTarget)

        # set modeless
        self.setModal(False)

        # start the qpd monitoring thread & stage control thread
        self.control_thread = control_thread
        self.control_thread.start(QtCore.QThread.NormalPriority)
        self.control_thread.controlUpdate.connect(self.controlUpdate)
        self.control_thread.foundSum.connect(self.foundSum)
        self.control_thread.recenteredPiezo.connect(self.recenteredPiezo)

        # connect to the ir laser & turn it off.
        self.ir_laser = ir_laser
        self.ir_state = True
        self.handleIrButton()
        if self.ir_laser.havePowerControl():
            self.ui.irSlider.setValue(parameters.ir_power)

        self.newParameters(parameters)

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

    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        offset = 0
        if (power > 10):
            offset = x_offset / power
        # These are saved so that they can be recorded when we are filming
        self.offset = offset
        self.power = power
        self.stage_z = stage_z

    @hdebug.debug
    def foundSum(self):
        self.tcp_control.sendComplete()
            
    @hdebug.debug
    def getLockTarget(self):
        target = self.control_thread.getLockTarget()
        if target == None:
            return "NA"
        else:
            return target * self.scale

    @hdebug.debug
    def handleIrButton(self):
        if self.ir_state:
            self.ir_laser.off()
            self.ir_state = False
            self.ui.irButton.setText("IR ON")
            self.ui.irButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.ir_laser.on(self.ir_power)
            self.ir_state = True
            self.ui.irButton.setText("IR OFF")
            self.ui.irButton.setStyleSheet("QPushButton { color: red }")

    def handleIrSlider(self, value):
        self.ir_power = value
        if self.ir_state:
            self.ir_laser.off()
            self.ir_laser.on(self.ir_power)

    @hdebug.debug
    def handleJumpButton(self):
        self.current_mode.handleJump(self.jumpsize)

    @hdebug.debug                    
    def handleJumpSpinBox(self, jumpsize):
        self.jumpsize = jumpsize

    @hdebug.debug
    def handleLockButton(self):
        self.current_mode.lockButtonToggle()
        self.toggleLockButtonText(self.current_mode.amLocked())
        self.toggleLockLabelDisplay(self.current_mode.shouldDisplayLockLabel())

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleRadioButtons(self):
        for i in range(len(self.buttons)):
            if self.buttons[i].isChecked():
                if not (self.current_mode == self.lock_modes[i]):
                    self.current_mode.stopLock()
                    self.current_mode.reset()
                    self.current_mode = self.lock_modes[i]
                    self.toggleLockButtonDisplay(self.current_mode.shouldDisplayLockButton())
                    self.toggleLockButtonText(self.current_mode.amLocked())
                    self.toggleLockLabelDisplay(self.current_mode.shouldDisplayLockLabel())

    @hdebug.debug
    def handleQuit(self):
        self.close()

    # This is for debugging, not for general use.
#    def keyPressEvent(self, event):
#        print event.key()
#        if (event.key() == 83):
#            self.control_thread.recenterPiezo()

    @hdebug.debug
    def jump(self, step_size):
        self.current_mode.handleJump(step_size)

    @hdebug.debug
    def openOffsetFile(self, filename):
        self.offset_file = open(filename + ".off", "w")
        self.offset_file.write("frame offset power stage-z\n")

    def newFrame(self, frame):
        if self.offset_file:
            self.offset_file.write("{0:d} {1:.6f} {2:.6f} {3:.6f}\n".format(frame.number, self.offset, self.power, self.stage_z))
        self.current_mode.newFrame(frame, self.offset, self.power, self.stage_z)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        p = parameters
        for lock_mode in self.lock_modes:
            lock_mode.newParameters(parameters)
        self.control_thread.newZCenter(p.qpd_zcenter)
        if not self.current_mode.amLocked():
            self.control_thread.recenter()
        self.scale = p.qpd_scale

    @hdebug.debug
    def quit(self):
        self.control_thread.stopThread()
        self.control_thread.wait()
        self.control_thread.cleanUp()
        self.closeOffsetFile()
        self.ir_laser.off()

    @hdebug.debug
    def recenteredPiezo(self):
        self.tcp_control.sendComplete()

    @hdebug.debug
    def startLock(self, filename):
        self.counter = 0
        self.error = 0.0
        self.error_counts = 0
        if filename:
            self.openOffsetFile(filename)
        self.current_mode.startLock()
        self.toggleLockButtonText(self.current_mode.amLocked())
        self.toggleLockLabelDisplay(self.current_mode.shouldDisplayLockLabel())

    @hdebug.debug
    def stopLock(self, override = 0):
        self.current_mode.stopLock()
        self.toggleLockButtonText(self.current_mode.amLocked())
        self.toggleLockLabelDisplay(self.current_mode.shouldDisplayLockLabel())
        self.closeOffsetFile()

    @hdebug.debug
    def tcpHandleFindSum(self):
        self.control_thread.findSumSignal()

    @hdebug.debug
    def tcpHandleRecenterPiezo(self):
        self.control_thread.recenterPiezo()

    @hdebug.debug
    def tcpHandleSetLockTarget(self, target):
        self.current_mode.setLockTarget(target/self.scale)

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
        FocusLockZ.__init__(self, parameters, tcp_control, control_thread, ir_laser, parent)

        #
        # Setup lock display widgets used to display QPD style offset data.
        #

        # offset display widget setup
        # +-500nm display range hard coded (if qpd is properly calibrated).
        self.offset_min = -500
        self.offset_max = 500
        status_x = self.ui.offsetFrame.width() - 4
        status_y = self.ui.offsetFrame.height() - 4
        self.offsetDisplay = lockDisplayWidgets.QOffsetDisplay(status_x,
                                                               status_y,
                                                               self.offset_min,
                                                               self.offset_max,
                                                               self.offset_min + 100,
                                                               self.offset_max - 100,
                                                               has_center_bar = 1,
                                                               parent = self.ui.offsetFrame)
        self.offsetDisplay.setGeometry(2, 2, status_x, status_y)

        # sum display widget setup
        self.sum_min = 100
        status_x = self.ui.sumFrame.width() - 4
        status_y = self.ui.sumFrame.height() - 4
        self.sumDisplay = lockDisplayWidgets.QSumDisplay(status_x,
                                                         status_y,
                                                         0,
                                                         parameters.qpd_sum_max,
                                                         self.sum_min,
                                                         False,
                                                         parent = self.ui.sumFrame)
        self.sumDisplay.setGeometry(2, 2, status_x, status_y)

        # stage display widget setup
        stage_max = int(2.0 * parameters.qpd_zcenter)
        status_x = self.ui.zFrame.width() - 4
        status_y = self.ui.zFrame.height() - 4
        self.zDisplay = lockDisplayWidgets.QOffsetDisplay(status_x,
                                                          status_y,
                                                          0,
                                                          stage_max,
                                                          int(0.1 * stage_max),
                                                          int(0.9 * stage_max),
                                                          parent = self.ui.zFrame)
        self.zDisplay.setGeometry(2, 2, status_x, status_y)

        # qpd
        status_x = self.ui.qpdFrame.width() - 4
        status_y = self.ui.qpdFrame.height() - 4
        self.qpdDisplay = lockDisplayWidgets.QQPDDisplay(status_x,
                                                         status_y,
                                                         200,
                                                         parent = self.ui.qpdFrame)
        self.qpdDisplay.setGeometry(2, 2, status_x, status_y)

    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        FocusLockZ.controlUpdate(self, x_offset, y_offset, power, stage_z)

        # Update the various displays
        self.offsetDisplay.updateValue(self.offset * self.scale)
        self.ui.offsetText.setText("{0:.1f}".format(self.offset * self.scale))
        self.sumDisplay.updateValue(power)
        self.ui.sumText.setText("{0:.1f}".format(power))
        self.qpdDisplay.updateValue(x_offset, y_offset)
        self.ui.qpdXText.setText("x: {0:.1f}".format(x_offset))
        self.ui.qpdYText.setText("y: {0:.1f}".format(y_offset))        
        self.zDisplay.updateValue(stage_z)
        self.ui.zText.setText("{0:.3f}um".format(stage_z))

#
# FocusLockZ specialized for camera style offset data.
#
class FocusLockZCam(FocusLockZ):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, control_thread, ir_laser, parent):
        FocusLockZ.__init__(self, parameters, tcp_control, control_thread, ir_laser, parent)

        self.control_thread = control_thread
        self.filename = ""
        self.x_offset = 0
        self.y_offset = 0

        self.ui.qpdLabel.setText("Camera")
        self.ui.qpdXText.hide()
        self.ui.qpdYText.hide()

        #
        # Setup lock display widgets used to display camera style offset data.
        #

        # offset display widget setup
        # +-500nm display range hard coded (if qpd is properly calibrated).
        self.offset_min = -500
        self.offset_max = 500
        status_x = self.ui.offsetFrame.width() - 4
        status_y = self.ui.offsetFrame.height() - 4
        self.offsetDisplay = lockDisplayWidgets.QOffsetDisplay(status_x,
                                                               status_y,
                                                               self.offset_min,
                                                               self.offset_max,
                                                               self.offset_min + 100,
                                                               self.offset_max - 100,
                                                               has_center_bar = 1,
                                                               parent = self.ui.offsetFrame)
        self.offsetDisplay.setGeometry(2, 2, status_x, status_y)

        # sum display widget setup
        self.sum_min = 50
        status_x = self.ui.sumFrame.width() - 4
        status_y = self.ui.sumFrame.height() - 4
        self.sumDisplay = lockDisplayWidgets.QSumDisplay(status_x,
                                                         status_y,
                                                         0,
                                                         parameters.qpd_sum_max,
                                                         self.sum_min,
                                                         255,
                                                         parent = self.ui.sumFrame)
        self.sumDisplay.setGeometry(2, 2, status_x, status_y)

        # stage display widget setup
        stage_max = int(2.0 * parameters.qpd_zcenter)
        status_x = self.ui.zFrame.width() - 4
        status_y = self.ui.zFrame.height() - 4
        self.zDisplay = lockDisplayWidgets.QOffsetDisplay(status_x,
                                                          status_y,
                                                          0,
                                                          stage_max,
                                                          int(0.1 * stage_max),
                                                          int(0.9 * stage_max),
                                                          parent = self.ui.zFrame)
        self.zDisplay.setGeometry(2, 2, status_x, status_y)

        # camera display
        status_x = self.ui.qpdFrame.width() - 4
        status_y = self.ui.qpdFrame.height() - 4
        self.camDisplay = lockDisplayWidgets.QCamDisplay(parent = self.ui.qpdFrame)
        self.camDisplay.setGeometry(2, 2, status_x, status_y)
        self.camDisplay.adjustCamera.connect(self.handleAdjustAOI)

        # timer for updating the display of snapshots captured by the camera.
        self.cam_timer = QtCore.QTimer()
        self.cam_timer.setInterval(100)
        self.cam_timer.start()

        self.cam_timer.timeout.connect(self.updateCamera)

    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        FocusLockZ.controlUpdate(self, x_offset, y_offset, power, stage_z)

        # Update the various displays
        self.offsetDisplay.updateValue(self.offset * self.scale)
        self.ui.offsetText.setText("{0:.1f}".format(self.offset * self.scale))
        self.sumDisplay.updateValue(power)
        self.ui.sumText.setText("{0:.1f}".format(power))
        self.zDisplay.updateValue(stage_z)
        self.ui.zText.setText("{0:.3f}um".format(stage_z))

        # save offset values
        if (power > 0):
            self.x_offset = x_offset/power
            self.y_offset = y_offset/power

    def handleAdjustAOI(self, dx, dy):
        self.control_thread.adjustCamera(dx, dy)

    # for debugging..
#    def openOffsetFile(self, filename):
#        self.filename = filename
#        FocusLockZ.openOffsetFile(self, filename)
#
#    def newFrame(self, frame):
#        FocusLockZ.newFrame(self, frame)
#        if self.offset_file:
#            numpy.save(self.filename + "_" + str(self.frame_number) + ".npy",
#                       self.control_thread.getImage()[0])
        
    def updateCamera(self):
        self.camDisplay.newImage(self.control_thread.getImage())

    def quit(self):
        FocusLockZ.quit(self)
        self.cam_timer.stop()

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
