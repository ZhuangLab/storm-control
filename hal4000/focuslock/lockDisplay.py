#!/usr/bin/python
#
## @file
#
# This class handles the talking to the lock hardware
# for a single focus lock via a control thread and
# providing a visual display of the current stage of
# the focus lock.
#
# Hazen 12/12
#

import numpy
from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.lockdisplay_ui as lockdisplayUi

# Widgets
import focuslock.lockDisplayWidgets as lockDisplayWidgets
import focuslock.lockModes as lockModes

## LockDisplay
#
# The lock display UI and lock control base class.
#
class LockDisplay(QtGui.QWidget):
    foundOptimal = QtCore.pyqtSignal(float)
    foundSum = QtCore.pyqtSignal(float)
    lockDisplay = QtCore.pyqtSignal(object)
    lockStatus = QtCore.pyqtSignal(float, float)
    recenteredPiezo = QtCore.pyqtSignal()

    ## __init__
    #
    # Create the LockDisplay class and setup the UI.
    #
    # ir_laser is a class with the following methods:
    #
    # on(power)
    #   Turn on the IR laser. Power is a value from 1 to 100.
    #
    # off()
    #   Turn off the IR laser
    #
    # @param parameters A parameters object.
    # @param control_thread A TCP control object.
    # @param ir_laser A ir laser control object as described above.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, control_thread, ir_laser, parent):
        QtGui.QWidget.__init__(self, parent)

        # general
        self.ir_laser = ir_laser
        self.ir_power = 0
        self.offset = 0
        self.optimizing_sum = False
        self.parameters = parameters
        self.power = 0
        self.stage_z = 0

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
        
        self.current_mode = self.lock_modes[parameters.get("qpd_mode")]

        # UI setup
        self.ui = lockdisplayUi.Ui_Form()
        self.ui.setupUi(self)
        if self.ir_laser:
            if (not ir_laser.havePowerControl()):
                self.ui.irSlider.hide()
            # connect signals
            self.ui.irButton.clicked.connect(self.handleIrButton)
            self.ui.irSlider.valueChanged.connect(self.handleIrSlider)

        else:
            self.ui.irButton.hide()
            self.ui.irSlider.hide()

        # start the qpd monitoring thread & stage control thread
        self.control_thread = control_thread
        self.control_thread.start(QtCore.QThread.NormalPriority)
        self.control_thread.controlUpdate.connect(self.controlUpdate)
        self.control_thread.foundSum.connect(self.handleFoundSum)
        self.control_thread.recenteredPiezo.connect(self.handleRecenteredPiezo)

        # connect to the ir laser & turn it off.
        if self.ir_laser:
            self.ir_state = True
            self.handleIrButton(None)
            if self.ir_laser.havePowerControl():
                self.ui.irSlider.setValue(parameters.get("ir_power"))

        self.newParameters(parameters)

    ## amLocked
    #
    # @return Is focus currently locked.
    #
    @hdebug.debug
    def amLocked(self):
        return self.current_mode.amLocked()

    ## changeLockMode
    #
    # Changes the current lock mode to the new mode (if this is
    # different from the old mode.
    #
    # @param which_mode A integer that is used as a index into the array of lock modes.
    #
    # @return True if the new mode is different from the old mode, otherwise False.
    #
    @hdebug.debug
    def changeLockMode(self, which_mode):
        if (self.current_mode == self.lock_modes[which_mode]):
            return False
        else:
            self.current_mode.stopLock()
            self.current_mode.reset()
            self.current_mode = self.lock_modes[which_mode]
            return True

    ## controlUpdate
    #
    # Handles the controlUpdate signal from the focus lock control thread.
    #
    # @param x_offset The current x offset of the focus lock.
    # @param y_offset The current y offset of the focus lock.
    # @param power The current focus lock sum signal.
    # @param stage_z The current z position of the stage.
    #
    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        offset = 0
        if (power > 10):
            offset = x_offset / power

        # These are saved so that they can be recorded when we are filming
        self.offset = offset
        self.power = power
        self.stage_z = stage_z

    ## getLockModes
    #
    # @return A python array containing all the available lock modes.
    #
    def getLockModes(self):
        return self.lock_modes

    ## getLockTarget
    #
    # @return The current lock target.
    #
    @hdebug.debug
    def getLockTarget(self):
        target = self.control_thread.getLockTarget()
        if (target == None):
            return "NA"
        elif (target == "failed"):
            return "failed"
        else:
            return target * self.scale

    ## getOffsetPowerStage
    #
    # @return [offset, power, stage]
    #
    def getOffsetPowerStage(self):
        return [self.offset, self.power, self.stage_z]

    ## handleAdjustStage
    #
    # This handles when you click on the stage indicator element
    # of the UI. It lets you move the stage up and down using
    # the wheel button of the mouse.
    #
    @hdebug.debug
    def handleAdjustStage(self, direction):
        self.jump(float(direction)*self.parameters.get("lockt_step"))

    ## handleFoundSum
    #
    # Handles the foundSum signal from the focus lock control thread.
    #
    @hdebug.debug
    def handleFoundSum(self, sum):
        self.foundSum.emit(sum)

    ## handleIrButton
    #
    # Handles the IR laser button. Turns the laser on/off and
    # updates the button accordingly.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleIrButton(self, boolean):
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

    ## handleIrSlider
    #
    # Handles the IR laser power slider.
    #
    # @param value The current position of the IR slider.
    #
    @hdebug.debug
    def handleIrSlider(self, value):
        self.ir_power = value
        if self.ir_state:
            self.ir_laser.off()
            self.ir_laser.on(self.ir_power)

    ## handleRecenteredPiezo
    #
    # Handles the recentered piezo signal from the focus lock control thread.
    #
    @hdebug.debug
    def handleRecenteredPiezo(self):
        self.recenteredPiezo.emit()

    ## jump
    #
    # Handles requests to jump the piezo stage.
    #
    # @param step_size The amount to move the piezo by.
    #
    @hdebug.debug
    def jump(self, step_size):
        self.current_mode.handleJump(step_size)

    ## lockButtonToggle
    #
    # Handles toggling the lock button
    #
    @hdebug.debug
    def lockButtonToggle(self):
        self.current_mode.lockButtonToggle()

    ## newFrame
    #
    # Handles new frame data from the camera.
    #
    # @param frame A frame data object.
    #
    def newFrame(self, frame):
        self.current_mode.newFrame(frame, self.offset, self.power, self.stage_z)

    ## newParameters
    #
    # Handles a change in parameters.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        p = parameters
        for lock_mode in self.lock_modes:
            lock_mode.newParameters(parameters)
        self.control_thread.newZCenter(p.get("qpd_zcenter"))
        if not self.current_mode.amLocked():
            self.control_thread.recenter()
        self.scale = p.get("qpd_scale")

    ## quit
    #
    # Stops the focus lock control thread and cleans things up prior to shutting down.
    #
    @hdebug.debug
    def quit(self):
        self.control_thread.stopThread()
        self.control_thread.wait()
        self.control_thread.cleanUp()
        if self.ir_laser:
            self.ir_laser.off()

    ## shouldDisplayLockButton
    #
    # @return True/False depending on whether the lock button should be shown for the current lock mode.
    #
    @hdebug.debug
    def shouldDisplayLockButton(self):
        return self.current_mode.shouldDisplayLockButton()

    ## shouldDisplayLockLabel
    #
    # @return True/False depending on whether the lock label should be shown for the current lock mode.
    #
    @hdebug.debug
    def shouldDisplayLockLabel(self):
        return self.current_mode.shouldDisplayLockLabel()

    ## startLock
    #
    # Start the focus lock. The filename parameter is ignored.
    #
    # @param filename This is not used.
    #
    @hdebug.debug
    def startLock(self, filename):
        self.current_mode.startLock()

    ## stopLock
    #
    # Stop the focus lock.
    #
    @hdebug.debug
    def stopLock(self):
        self.current_mode.stopLock()

    ## tcpHandleFindSum
    #
    # Tell the control thread to execute the find sum signal procedure.
    #
    def tcpHandleFindSum(self, min_sum):
        self.control_thread.findSumSignal(min_sum)

    ## tcpHandleOptimizeSum
    #
    # Adjust the laser power until the sum signal is in the range 0.5 - 0.9.
    #
    def tcpHandleOptimizeSum(self):
        if self.ir_laser and self.ir_laser.havePowerControl():
            self.optimizing_sum = True
        else:
            self.foundOptimal.emit(self.power)

    ## tcpHandleRecenterPiezo
    #
    # Tell the control thread to recenter the piezo.
    #
    @hdebug.debug
    def tcpHandleRecenterPiezo(self):
        self.control_thread.recenterPiezo()

    ## tcpHandleSetLockTarget
    #
    # Tell the control thread to set its lock target to target.
    #
    # @param target The desired lock target.
    #
    @hdebug.debug
    def tcpHandleSetLockTarget(self, target):
        self.current_mode.setLockTarget(target/self.scale)


## LockDisplayQPD
#
# LockDisplay specialized for QPD style offset data.
#
class LockDisplayQPD(LockDisplay):

    ## __init__
    #
    # Set up the lock display UI widgets to display QPD style offset data.
    #
    # @param parameters A parameters object.
    # @param control_thread A TCP control object.
    # @param ir_laser A ir laser control object as described above.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, control_thread, ir_laser, parent):
        LockDisplay.__init__(self, parameters, control_thread, ir_laser, parent)

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
                                                         parameters.get("qpd_sum_max"),
                                                         self.sum_min,
                                                         False,
                                                         parent = self.ui.sumFrame)
        self.sumDisplay.setGeometry(2, 2, status_x, status_y)

        # stage display widget setup
        stage_max = int(2.0 * parameters.get("qpd_zcenter"))
        status_x = self.ui.zFrame.width() - 4
        status_y = self.ui.zFrame.height() - 4
        self.zDisplay = lockDisplayWidgets.QStageDisplay(status_x,
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

    ## controlUpdate
    #
    # This updates the various UI elements based on data received
    # from the focus lock control thread.
    #
    # @param x_offset The current x offset of the focus lock.
    # @param y_offset The current y offset of the focus lock.
    # @param power The current sum signal of the focus lock.
    # @param stage_z The current z position of the piezo stage.
    #
    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        LockDisplay.controlUpdate(self, x_offset, y_offset, power, stage_z)

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

        # Send lock status signal.
        self.lockStatus.emit(self.offsetDisplay.getValue(),
                             self.sumDisplay.getValue())

        # Send current lock picture.
        self.lockDisplay.emit(QtGui.QPixmap.grabWidget(self.qpdDisplay))


## LockDisplayCam
#
# LockDisplay specialized for camera style offset data.
#
class LockDisplayCam(LockDisplay):

    ## __init__
    #
    # Set up the lock display UI widgets to display camera style offset data.
    #
    # @param parameters A parameters object.
    # @param control_thread A TCP control object.
    # @param ir_laser A ir laser control object as described above.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, control_thread, ir_laser, parent):
        LockDisplay.__init__(self, parameters, control_thread, ir_laser, parent)

        self.filename = ""
        self.save_image = False
        self.show_dot = False
        self.x_offset = 0
        self.y_offset = 0

        self.ui.qpdLabel.setText("Camera")
        self.ui.qpdXText.hide()
        self.ui.qpdYText.hide()

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
                                                         parameters.get("qpd_sum_max"),
                                                         self.sum_min,
                                                         255,
                                                         parent = self.ui.sumFrame)
        self.sumDisplay.setGeometry(2, 2, status_x, status_y)

        # stage display widget setup
        stage_max = int(2.0 * parameters.get("qpd_zcenter"))
        status_x = self.ui.zFrame.width() - 4
        status_y = self.ui.zFrame.height() - 4
        self.zDisplay = lockDisplayWidgets.QStageDisplay(status_x,
                                                         status_y,
                                                         0,
                                                         stage_max,
                                                         int(0.1 * stage_max),
                                                         int(0.9 * stage_max),
                                                         parent = self.ui.zFrame)
        self.zDisplay.setGeometry(2, 2, status_x, status_y)
        self.zDisplay.adjustStage.connect(self.handleAdjustStage)

        # camera display
        status_x = self.ui.qpdFrame.width() - 4
        status_y = self.ui.qpdFrame.height() - 4
        self.camDisplay = lockDisplayWidgets.QCamDisplay(parent = self.ui.qpdFrame)
        self.camDisplay.setGeometry(2, 2, status_x, status_y)
        self.camDisplay.adjustCamera.connect(self.handleAdjustAOI)
        self.camDisplay.adjustOffset.connect(self.handleAdjustOffset)
        self.camDisplay.changeFitMode.connect(self.handleChangeFitMode)

        # timer for updating the display of snapshots captured by the camera.
        self.cam_timer = QtCore.QTimer()
        self.cam_timer.setInterval(100)
        self.cam_timer.start()

        self.cam_timer.timeout.connect(self.updateCamera)

    ## controlUpdate
    #
    # This updates the various UI elements based on data received
    # from the focus lock control thread.
    #
    # @param x_offset The current x offset of the focus lock.
    # @param y_offset The current y offset of the focus lock.
    # @param power The current sum signal of the focus lock.
    # @param stage_z The current z position of the piezo stage.
    #
    def controlUpdate(self, x_offset, y_offset, power, stage_z):
        LockDisplay.controlUpdate(self, x_offset, y_offset, power, stage_z)

        # Update the various displays
        self.offsetDisplay.updateValue(self.offset * self.scale)
        self.ui.offsetText.setText("{0:.1f}".format(self.offset * self.scale))
        self.sumDisplay.updateValue(power)
        self.ui.sumText.setText("{0:.1f}".format(power))
        self.zDisplay.updateValue(stage_z)
        self.ui.zText.setText("{0:.3f}um".format(stage_z))

        # Save offset values
        if (power > 0):
            self.x_offset = x_offset/power
            self.y_offset = y_offset/power

        # Adjust laser power, if requested.
        if self.optimizing_sum:
            cur_sum = self.sumDisplay.getValue()
            if (cur_sum < 0.5):
                self.ui.irSlider.setValue(self.ui.irSlider.value() + 1)
            elif (cur_sum > 0.9):
                self.ui.irSlider.setValue(self.ui.irSlider.value() - 1)
            else:
                self.optimizing_sum = False
                self.foundOptimal.emit(power)

        # Change blinking value so that the red dot in the camera display blinks.
        self.show_dot = not self.show_dot

        # Send lock status signal.
        self.lockStatus.emit(self.offsetDisplay.getValue(),
                             self.sumDisplay.getValue())

        # Send current lock picture.
        self.lockDisplay.emit(QtGui.QPixmap.grabWidget(self.camDisplay))

    ## handleAdjustAOI
    #
    # Tells the control thread to adjust the position of the AOI on the 
    # focus lock camera.
    #
    def handleAdjustAOI(self, dx, dy):
        self.control_thread.adjustCamera(dx, dy)

    ## handleAdjustOffset
    #
    # Tells the control thread to adjust the zero point of the offset measurement. 
    # Basically it sets what distance between the two spots is considered to be zero.
    #
    def handleAdjustOffset(self, dx):
        self.control_thread.adjustOffset(dx)

    ## handleChangeFitMode
    #
    # Tells the control thread to change the fit mode.
    #
    def handleChangeFitMode(self, mode):
        self.control_thread.changeFitMode(mode)

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

    ## startLock
    #
    # Starts the focus lock. The first image from the focus lock camera
    # is saved in the filenae + "_lock_cam.png".
    #
    # @param filename The base name for the current acquisition or False if we are not filming.
    #
    @hdebug.debug
    def startLock(self, filename):
        LockDisplay.startLock(self, filename)
        if filename:
            self.filename = filename + "_lock_cam.png"
            self.save_image = True

    ## updateCamera
    #
    # This is called approximately every ten seconds to update the picture
    # that is displayed from the camera.
    #
    def updateCamera(self):
        self.camDisplay.newImage(self.control_thread.getImage(), self.show_dot)
        
        # Save the first (more or less) image from the focus lock USB camera 
        # for debugging purposes.
        if self.save_image:
            q_image = self.camDisplay.getImage()
            q_image.save(self.filename)
            self.save_image = False

    ## quit
    #
    # Calls quit LockDisplay.quit() and stops the camera picture update timer.
    #
    def quit(self):
        LockDisplay.quit(self)
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
