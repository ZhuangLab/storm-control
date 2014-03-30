#!/usr/bin/python
#
## @file
#
# The stage control UI.
#
# Hazen 03/14
#

import math

from PyQt4 import QtCore, QtGui

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.halModule as halModule

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.stage_ui as stageUi


## MotionButton
#
# Encapsulate the handling and display of the motion buttons.
#
class MotionButton(QtCore.QObject):
    buttonClicked = QtCore.pyqtSignal(float, float)
    
    ## __init__
    #
    # @param button A PyQT Button object.
    # @param icon The filename of the image to use for the button icon.
    # @param type Either "large" or "small"
    # @param xval -1, 0, 1 for motion on the x-axis of the stage.
    # @param yval -1, 0, 1 for motion on the y-axis of the stage.
    # @param parent (optional) The PyQt parent of this object.
    #
    def __init__(self, button, icon, type, xval, yval, parent = None):
        QtCore.QObject.__init__(self, parent)
        self.step_size = 1.0
        self.type = type
        self.xval = float(xval)
        self.yval = float(yval)

        self.button = button
        self.button.setIcon(QtGui.QIcon(icon))
        self.button.setIconSize(QtCore.QSize(56, 56))
        self.button.clicked.connect(self.handleClicked)

    ## handleClicked
    #
    # @param boolean Dummy parameter
    #
    def handleClicked(self, boolean):
        self.buttonClicked.emit(self.xval * self.step_size, self.yval * self.step_size)

    ## setStepSize
    #
    # @param small_step_size The small step size.
    # @param large_step_size The large step size.
    #
    def setStepSize(self, small_step_size, large_step_size):
        if (self.type == "small"):
            self.step_size = small_step_size
        else:
            self.step_size = large_step_size
        

## Translator
#
# Encapsulate going from the camera coordinate system to
# the stage coordinate system.
#
class Translator():
    
    ## __init__
    #
    # Create default translator object.
    #
    def __init__(self):
        self.camera_x_sign = 1.0
        self.camera_y_sign = 1.0
        self.camera_flip_axis = 0
        self.flip_axis = 0
        self.x_sign = 1.0
        self.y_sign = 1.0

    ## newParameters
    #
    # Update orientation adjustments based on settings.
    #
    def newParameters(self, parameters):
        self.flip_axis = parameters.flip_axis
        self.x_sign = parameters.x_sign
        self.y_sign = parameters.y_sign

        if hasattr(parameters, "camera1"):
            parameters = getattr(parameters, "camera1")

        self.camera_x_sign = 1
        if (parameters.flip_horizontal):
            self.camera_x_sign = -1

        self.camera_y_sign = 1
        if (parameters.flip_vertical):
            self.camera_y_sign = -1

        if self.flip_axis:
            [self.camera_x_sign, self.camera_y_sign] = [self.camera_y_sign, self.camera_x_sign]

        self.camera_flip_axis = 0
        if (parameters.transpose):
            self.camera_flip_axis = 1
            self.camera_x_sign = -1 * self.camera_x_sign
            self.camera_y_sign = -1 * self.camera_y_sign

    ## translate
    #
    # @param x The input x value
    # @param y The input y value
    #
    # @return [tx, ty] The translated values.
    #
    def translate(self, x, y):

        # "default" transform first.
        tx = x * self.x_sign
        ty = y * self.y_sign
        if self.flip_axis:
            [tx, ty] = [ty, tx]

        # "camera" transform next.
        tx = tx * self.camera_x_sign
        ty = ty * self.camera_y_sign
        if self.camera_flip_axis:
            [tx, ty] = [ty, tx]

        return [tx, ty]


## StageControl
#
# Stage Control Dialog Box
#
# This is the UI for stage control based on some sort 
# of motorized stage. It should be sub-classed and
# the sub-class should provide the stage to control
# as property (self.stage). Typically the self.stage
# will be a QStageThread object for buffering purposes.
#
class StageControl(QtGui.QDialog, halModule.HalModule):
    tcpComplete = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent):
        QtGui.QMainWindow.__init__(self, parent)
        halModule.HalModule.__init__(self)
        #self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.directory = ""
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.move_timer = QtCore.QTimer()
        self.stage_speed = parameters.stage_speed
        self.stage_x = 0
        self.stage_y = 0
        self.stage_z = 0
        self.tcp_message = False
        self.translator = Translator()

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup
        self.ui = stageUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Stage Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # UI motion buttons.
        icon_path = "./icons/"
        self.motion_buttons = [MotionButton(self.ui.leftSButton, icon_path + "1leftarrow-128.png", "small", 1, 0),
                               MotionButton(self.ui.leftLButton, icon_path + "2leftarrow-128.png", "large", 1, 0),
                               MotionButton(self.ui.rightSButton, icon_path + "1rightarrow-128.png", "small", -1, 0),
                               MotionButton(self.ui.rightLButton, icon_path + "2rightarrow-128.png", "large", -1, 0),
                               MotionButton(self.ui.upSButton, icon_path + "1uparrow-128.png", "small", 0, 1),
                               MotionButton(self.ui.upLButton, icon_path + "2uparrow-128.png", "large", 0, 1),
                               MotionButton(self.ui.downSButton, icon_path + "1downarrow1-128.png", "small", 0, -1),
                               MotionButton(self.ui.downLButton,  icon_path + "2dowarrow-128.png", "large", 0, -1)]

        for button in self.motion_buttons:
            button.buttonClicked.connect(self.moveRelative)

        # Configure timer.
        self.move_timer.setSingleShot(True)
        self.move_timer.timeout.connect(self.handleMoveTimer)

        # Connect signals.
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        self.ui.addButton.clicked.connect(self.handleAdd)
        self.ui.clearButton.clicked.connect(self.handleClear)
        self.ui.goButton.clicked.connect(self.handleGo)
        self.ui.homeButton.clicked.connect(self.handleHome)
        self.ui.loadButton.clicked.connect(self.handleLoad)
        self.ui.saveButton.clicked.connect(self.handleSave)
        self.ui.saveComboBox.activated.connect(self.handleSaveIndexChange)
        self.ui.zeroButton.clicked.connect(self.zero)

        # set modeless
        self.setModal(False)

        # open connection to the stage
        if not(self.stage.getStatus()):
            print "Failed to connect to the microscope stage. Perhaps it is turned off?"
            self.stage.shutDown()
            self.stage = False
        else:
            self.stage.updatePosition.connect(self.handleUpdatePosition)
            self.stage.setVelocity(parameters.stage_speed, parameters.stage_speed)

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        if self.stage:
            self.stage.shutDown()

    ## closeEvent
    #
    # If this window has parent, just hide the window, otherwise close it.
    #
    # @param event A PyQt event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            
            # Comm signals
            if (signal[1] == "commGotConnection"):
                signal[2].connect(self.startLockout)
            elif (signal[1] == "commLostConnection"):
                signal[2].connect(self.stopLockout)
            if (signal[1] == "commMessage"):
                signal[2].connect(self.handleCommMessage)

            # Joystick signals.
            elif (signal[1] == "jstickMotion"):
                signal[2].connect(self.jog)

            # Drag signals
            elif (signal[1] == "dragStart"):
                signal[2].connect(self.handleDragStart)
            elif (signal[1] == "dragMove"):
                signal[2].connect(self.handleDragMove)

            # Motion signals
            elif (signal[1] == "stepMove"):
                signal[2].connect(self.moveRelative)

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "tcpComplete", self.tcpComplete]]

    ## handleAdd
    #
    # Add the current stage position to the saved positions combo box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleAdd(self, bool):
        self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(self.stage_x, self.stage_y),
                                     [self.stage_x, self.stage_y])
        self.ui.saveComboBox.setCurrentIndex(self.ui.saveComboBox.count()-1)

    ## handleClear
    #
    # Remove all of the positions from the saved positions combo box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleClear(self, bool):
        self.ui.saveComboBox.clear()

    ## handleCommMessage
    #
    # Handles all the message from tcpControl.
    #
    # @param message A tcpControl.TCPMessage object.
    #
    @hdebug.debug
    def handleCommMessage(self, message):

        if (message.getType() == "Move Stage"):
            x_pos = message.getData("stage_x")
            y_pos = message.getData("stage_y")
            if message.isTest():
                if (x_pos == None) or (y_pos == None):
                    message.setError(True, "Invalid positions")

                message.addResponse("duration", 1) # Minimum stage move time (1s)
                self.tcpComplete.emit(message) 
            else:
                self.tcp_message = message
                self.moveAbsolute(x_pos, y_pos)

                # Based on stage speed, calculate how long the move will take.
                dx = x_pos - self.stage_x
                dy = y_pos - self.stage_y
                dd = math.sqrt(dx*dx + dy*dy)
                move_time = int(dd/self.stage_speed) + 1000

                self.move_timer.setInterval(move_time)
                self.move_timer.start()

    ## handleDragMove
    #
    # This is motion relative to a fixed point. The expected inputs are
    # displacements (in um) from the fixed point (previously recorded
    # with handleDragStart().
    #
    # @param drag_x_disp Offset distance in x in microns.
    # @param drag_y_disp Offset distance in y in microns.
    #
    def handleDragMove(self, drag_x_disp, drag_y_disp):
        if self.stage:
            [dx, dy] = self.translator.translate(drag_x_disp, drag_y_disp)
            self.stage.dragMove(self.drag_start_x + dx,
                                self.drag_start_y + dy)

    ## handleDragStart
    #
    # Record the current stage position for drag events.
    #
    @hdebug.debug
    def handleDragStart(self):
        self.drag_start_x = self.stage_x
        self.drag_start_y = self.stage_y

    ## handleGo
    #
    # Move to the position specified by the x,y position spin boxes.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleGo(self, bool):
        x_target = self.ui.xmoveDoubleSpinBox.value()
        y_target = self.ui.ymoveDoubleSpinBox.value()
        self.moveAbsolute(x_target, y_target)

    ## handleHome
    #
    # Move to the 0,0 position.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleHome(self, bool):
        self.moveAbsolute(0, 0)

    ## handleLoad
    #
    # Load a positions file into the saved position combo box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleLoad(self, bool):
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.directory,
                                                                   "*.txt"))
        if positions_filename:
            self.handleClear()
            fp = open(positions_filename, "r")
            while 1:
                line = fp.readline()
                if not line: break
                [x, y] = map(float, line.split(","))
                self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(x, y),
                                             [x, y])
            self.ui.saveComboBox.setCurrentIndex(self.ui.saveComboBox.count()-1)

    ## handleMoveTimer
    #
    # When the move timer times out we assume that the stage has
    # reached the desired position.
    #
    @hdebug.debug
    def handleMoveTimer(self):
        self.tcpComplete.emit(self.tcp_message)

    ## handleOk
    #
    # Hide the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleUpdatePosition
    #
    # @param stage_x The stage position in x in microns.
    # @param stage_y The stage position in y in microns.
    # @param stage_z The stage position in z in microns.
    #
    def handleUpdatePosition(self, stage_x, stage_y, stage_z):
        self.stage_x = stage_x
        self.stage_y = stage_y
        self.stage_z = stage_z
        self.ui.xposText.setText("%.3f" % self.stage_x)
        self.ui.yposText.setText("%.3f" % self.stage_y)

    ## handleQuit
    #
    # Close the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## handleSave
    #
    # Save the positions in the positions combo box into a file.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleSave(self, bool):
        positions_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.directory, 
                                                                   "*.txt"))
        if positions_filename and (self.ui.saveComboBox.count() > 0):
            fp = open(positions_filename, "w")
            for i in range(self.ui.saveComboBox.count()):
                [x, y] = self.ui.saveComboBox.itemData(i).toList()
                fp.write("{0:.2f}, {1:.2f}\r\n".format(x.toDouble()[0], y.toDouble()[0]))
            fp.close()

    ## handleSaveIndexChange
    #
    # When the saved positions combo box is changed this copies the current
    # values into the x,y position spin boxes.
    #
    @hdebug.debug
    def handleSaveIndexChange(self, index):
        data = self.ui.saveComboBox.itemData(index).toList()
        if data:
            [xvar, yvar] = data
            self.ui.xmoveDoubleSpinBox.setValue(xvar.toDouble()[0])
            self.ui.ymoveDoubleSpinBox.setValue(yvar.toDouble()[0])

    ## jog
    #
    # Tell the stage to move at a certain speed.
    #
    # @param x_speed The speed to move the stage in x.
    # @param y_speed The speed to move the stage in y.
    #
    def jog(self, x_speed, y_speed):
        if self.stage:
            [tx, ty] = self.translator.translate(x_speed, y_speed)
            self.stage.jog(tx, ty)

    ## moveRelative
    #
    # Move relative to the current position.
    #
    # @param dx The amount to move in x (in microns).
    # @param dy The amount to move in y (in microns).
    #
    def moveRelative(self, dx, dy):
        if self.stage:
            [tx, ty] = self.translator.translate(dx, dy)
            self.stage.goRelative(tx, ty)

    ## moveAbsolute
    #
    # Move to an absolute position.
    #
    # @param x The x position (in microns).
    # @param y The y position (in microns).
    #
    @hdebug.debug
    def moveAbsolute(self, x, y):
        if self.stage:
            self.stage.goAbsolute(x, y)

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug    
    def newParameters(self, parameters):
        self.directory = parameters.directory
        self.translator.newParameters(parameters)
        for button in self.motion_buttons:
            button.setStepSize(parameters.small_step_size, parameters.large_step_size)

    ## startFilm
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        self.startLockout()

    ## startLockout
    #
    @hdebug.debug
    def startLockout(self):
        if self.stage:
            self.stage.lockout(True)

    ## stopFilm
    #
    # Called at when filming is complete. The writer is passed to the modules
    # so that they can (optionally) add any module specific data to the film's
    # meta-data (the .inf file).
    #
    # @param film_writer The film writer object.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        self.stopLockout()
        if film_writer:
            film_writer.setStagePosition([self.stage_x, self.stage_y, self.stage_z])

    ## stopLockout
    #
    @hdebug.debug
    def stopLockout(self):
        if self.stage:
            self.stage.lockout(False)

    ## zero
    #
    # Zero the stage position.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def zero(self, bool):
        if self.stage:
            self.stage.zero()
        self.handleUpdatePosition(0, 0, 0)

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
