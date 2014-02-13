#!/usr/bin/python
#
## @file
#
# The stage control UI.
#
# Hazen 02/14
#

from PyQt4 import QtCore, QtGui

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.halModule as halModule

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.stage_ui as stageUi

## StageControl
#
# Stage Control Dialog Box
#
# This is the UI for stage control based on some sort 
# of motorized stage.
#
# The motorized stage class must provide the following methods:
#
# getStatus()
#   Returns True if the stage is alive and running, False otherwise.
#
# goAbsolution(x, y)
#   Go to position x, y (in um)
#
# goRelative(dx, dy)
#   Change position by dx in x, dy in y (in um).
#
# jog(sx, sy)
#   Jog at a speed given by sx, sy in um/second
#
# joystickLockout(flag)
#   Stage ignores the joystick controller if flag
#   is True.
#
# position()
#   Returns [x, y, z] stage position (in um).
#
# setVelocity(vx, vy)
#   Set maximum stage velocity in x and y (in mm/sec).
#
# shutDown()
#   Cleanup prior to the program quitting.
#
# zero()
#   Define the current position as zero.
#
class StageControl(QtGui.QDialog, halModule.HalModule):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent):
        QtGui.QMainWindow.__init__(self, parent)
        halModule.HalModule.__init__(self)

        self.joystick_lockout = False
        self.parameters = parameters
        self.position_update_timer = QtCore.QTimer(self)
        self.position_update_timer.setInterval(500)

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = stageUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Stage Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        self.ui.leftSButton.setIcon(QtGui.QIcon("./icons/1leftarrow-128.png"))
        self.ui.leftSButton.setIconSize(QtCore.QSize(56, 56))
        self.ui.leftLButton.setIcon(QtGui.QIcon("./icons/2leftarrow-128.png"))
        self.ui.leftLButton.setIconSize(QtCore.QSize(56, 56))

        self.ui.rightSButton.setIcon(QtGui.QIcon("./icons/1rightarrow-128.png"))
        self.ui.rightSButton.setIconSize(QtCore.QSize(56, 56))
        self.ui.rightLButton.setIcon(QtGui.QIcon("./icons/2rightarrow-128.png"))
        self.ui.rightLButton.setIconSize(QtCore.QSize(56, 56))

        self.ui.upSButton.setIcon(QtGui.QIcon("./icons/1uparrow-128.png"))
        self.ui.upSButton.setIconSize(QtCore.QSize(56, 56))
        self.ui.upLButton.setIcon(QtGui.QIcon("./icons/2uparrow-128.png"))
        self.ui.upLButton.setIconSize(QtCore.QSize(56, 56))

        self.ui.downSButton.setIcon(QtGui.QIcon("./icons/1downarrow1-128.png"))
        self.ui.downSButton.setIconSize(QtCore.QSize(56, 56))
        self.ui.downLButton.setIcon(QtGui.QIcon("./icons/2dowarrow-128.png"))
        self.ui.downLButton.setIconSize(QtCore.QSize(56, 56))

        self.ui.joystickLockoutButton.hide()

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)
        self.position_update_timer.timeout.connect(self.updatePosition)
        self.ui.zeroButton.clicked.connect(self.zero)
        self.ui.leftSButton.clicked.connect(self.leftS)
        self.ui.leftLButton.clicked.connect(self.leftL)
        self.ui.rightSButton.clicked.connect(self.rightS)
        self.ui.rightLButton.clicked.connect(self.rightL)
        self.ui.upSButton.clicked.connect(self.upS)
        self.ui.upLButton.clicked.connect(self.upL)
        self.ui.downSButton.clicked.connect(self.downS)
        self.ui.downLButton.clicked.connect(self.downL)
        self.ui.homeButton.clicked.connect(self.handleHome)
        self.ui.goButton.clicked.connect(self.handleGo)
        self.ui.joystickLockoutButton.clicked.connect(self.handleLockout)
        self.ui.addButton.clicked.connect(self.handleAdd)
        self.ui.clearButton.clicked.connect(self.handleClear)
        self.ui.loadButton.clicked.connect(self.handleLoad)
        self.ui.saveButton.clicked.connect(self.handleSave)
        self.ui.saveComboBox.activated.connect(self.handleSaveIndexChange)

        # set modeless
        self.setModal(False)

        # open connection to the stage
        self.small_step_size = 10.0
        self.large_step_size = 50.0
        self.x_sign = -1
        self.y_sign = 1
        if parameters:
            self.newParameters(parameters)
        self.x_axis = 1
        self.x = 0
        self.y = 0
        self.z = 0
        if not(self.stage.getStatus()):
            print "Failed to connect to the microscope stage. Perhaps it is turned off?"
            self.stage.shutDown()
            self.stage = False
        else:
            self.stage.setVelocity(parameters.stage_speed, parameters.stage_speed)
        self.updatePosition()
        self.position_update_timer.start()


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

            # Joystick signals
            elif (signal[1] == "jstickMotion"):
                signal[2].connect(self.jog)
            elif (signal[1] == "jstickStep"):
                signal[2].connect(self.step)

    ## downS
    #
    # Move down one small step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def downS(self, bool):
        self.moveRelative(1, self.small_step_size)

    ## downL
    #
    # Move down one large step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def downL(self, bool):
        self.moveRelative(1, self.large_step_size)

    ## getStagePosition
    #
    # @return [stage x, stage y, stage z]
    #
    @hdebug.debug
    def getStagePosition(self):
        if self.stage:
            self.updatePosition()
        return [self.x, self.y, self.z]

    ## handleAdd
    #
    # Add the current stage position to the saved positions combo box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleAdd(self, bool):
        self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(self.x, self.y),
                                     [self.x, self.y])
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

        m_type = message.getType()
        m_data = message.getData()

        if (m_type == "moveTo"):
            self.tcpHandleMoveTo(m_data[0], m_data[1])

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
                                                                   self.parameters.directory,
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

    ## handleLockout
    #
    # Handles locking out the (stage) joystick.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleLockout(self, bool):
        if self.joystick_lockout:
            self.stopLockout()
            self.ui.joystickLockoutButton.setStyleSheet("QPushButton { color: red }")
        else:
            self.startLockout()
            self.ui.joystickLockoutButton.setStyleSheet("QPushButton { color: green }")        

    ## handleOk
    #
    # Hide the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

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
                                                                   self.parameters.directory, 
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
            self.stage.jog(x_speed, y_speed)

    ## keyPressEvent
    #
    # @param event A PyQt key press event.
    #
    @hdebug.debug
    def keyPressEvent(self, event):
        key = event.key()
        if key == 52:
            self.leftS()
        elif key == 56:
            self.upS()
        elif key == 54:
            self.rightS()
        elif key == 50:
            self.downS()

    ## leftS
    #
    # Move left one small step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def leftS(self, bool):
        self.moveRelative(0, self.small_step_size)

    ## leftL
    #
    # Move left one large step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def leftL(self, bool):
        self.moveRelative(0, self.large_step_size)

    ## moveRelative
    #
    # Move relative to the current position.
    #
    # @param axis The axis to move.
    # @param distance The distance to move in microns.
    #
    @hdebug.debug        
    def moveRelative(self, axis, distance):
        if self.stage:
            if axis == self.x_axis:
                self.stage.goRelative(distance * self.x_sign, 0)
            else:
                self.stage.goRelative(0, distance * self.y_sign)
#            [self.x, self.y, self.z] = self.stage.position()
            self.updatePosition()

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
#            [self.x, self.y, self.z] = self.stage.position()
            self.updatePosition()

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug    
    def newParameters(self, parameters):
        self.parameters = parameters
        self.small_step_size = int(parameters.small_step_size)
        self.large_step_size = int(parameters.large_step_size)
        if parameters.x_sign > 0:
            self.x_sign = 1
        else:
            self.x_sign = -1
        if parameters.y_sign > 0:
            self.y_sign = 1
        else:
            self.y_sign = -1

    ## rightS
    #
    # Move right one small step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def rightS(self, bool):
        self.moveRelative(0, -1 * self.small_step_size)

    ## rightL
    #
    # Move right one large step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def rightL(self, bool):
        self.moveRelative(0, -1 * self.large_step_size)

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
    # Lock out the stage control joystick.
    #
    @hdebug.debug
    def startLockout(self):
        if not self.joystick_lockout:
            if self.stage:
                self.stage.lockout(True)
            self.joystick_lockout = True

    ## step
    #
    # Move a relative distance in x, y.
    #
    # @param x The x step in microns.
    # @param y The y step in microns.
    #
    @hdebug.debug
    def step(self, x, y):
        if self.stage:
            self.stage.goRelative(x, y)

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
            film_writer.setStagePosition(self.getStagePosition())

    ## stopLockout
    #
    # Turn off the lockout of the stage control joystick.
    #
    @hdebug.debug
    def stopLockout(self):
        if self.joystick_lockout:
            if self.stage:
                self.stage.lockout(False)
            self.joystick_lockout = False

    ## tcpHandleMoveTo
    #
    # Handle move requests from the tcp object.
    #
    # @param x The x position in um.
    # @param y The y position in um.
    #
    @hdebug.debug
    def tcpHandleMoveTo(self, x, y):
        self.moveAbsolute(x, y)

    ## updatePosition
    #
    # This is called every 1/2 second to update the stage position display.
    #
    def updatePosition(self):
        if self.stage:
            [self.x, self.y, self.z] = self.stage.position()
        self.ui.xposText.setText("%.3f" % self.x)
        self.ui.yposText.setText("%.3f" % self.y)

    ## upS
    #
    # Move up one small step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def upS(self, bool):
        self.moveRelative(1, -1 * self.small_step_size)

    ## upL
    #
    # Move up one large step.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def upL(self, bool):
        self.moveRelative(1, -1 * self.large_step_size)

    ## zero
    #
    # Zero the stage position.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def zero(self, bool):
        self.stage.zero()
        self.x = 0
        self.y = 0
        self.z = 0
        self.updatePosition()

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
