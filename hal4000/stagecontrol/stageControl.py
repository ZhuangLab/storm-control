#!/usr/bin/python
#
# This is the UI for stage control based on some sort 
# of motorized stage.
#
#  Methods called by HAL:
#
#    getStagePosition()
#      Return the current stage position.
#
#    jog(x_speed, y_speed)
#      Move stage at the velocity given by x_speed and
#      y_speed (microns / second).
#
#    newParameters(parameters)
#      Update stage settings with the new parameters.
#
#    quit()
#      Cleanup and shutdown prior to the program ending.
#
#    show()
#      Display the stage control dialog box.
#
#    startLockout()
#      Lockout the joystick.
#
#    step(x_step, y_step)
#      Move the stage by x_step in x, y_step in y (in microns).
#
#    stopLockout()
#      Turn off joystick lockout
#
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
# shutDown()
#   Cleanup prior to the program quitting.
#
# zero()
#   Define the current position as zero.
#
# Hazen 9/12
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.stage_ui as stageUi

#
# Stage Control Dialog Box
#
class StageControl(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, tcp_control, parent):
        QtGui.QMainWindow.__init__(self, parent)
        self.debug = 1
        self.locked_out = False
        self.parameters = parameters
        self.position_update_timer = QtCore.QTimer(self)
        self.position_update_timer.setInterval(500)
        self.tcp_control = tcp_control

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = stageUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Stage Control")

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

        # tcp signals
        if self.tcp_control:
            self.connect(self.tcp_control, QtCore.SIGNAL("moveTo(float, float)"), self.tcpHandleMoveTo)

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
            self.stage = 0
        self.updatePosition()
        self.position_update_timer.start()

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def downS(self):
        self.moveRelative(1, self.small_step_size)

    @hdebug.debug
    def downL(self):
        self.moveRelative(1, self.large_step_size)

    @hdebug.debug
    def getStagePosition(self):
        if self.stage:
            self.updatePosition()
        return [self.x, self.y, self.z]

    @hdebug.debug
    def handleAdd(self):
        self.ui.saveComboBox.addItem("{0:.1f}, {1:.1f}".format(self.x, self.y),
                                     [self.x, self.y])
        self.ui.saveComboBox.setCurrentIndex(self.ui.saveComboBox.count()-1)

    @hdebug.debug
    def handleClear(self):
        self.ui.saveComboBox.clear()

    @hdebug.debug
    def handleGo(self):
        x_target = self.ui.xmoveDoubleSpinBox.value()
        y_target = self.ui.ymoveDoubleSpinBox.value()
        self.moveAbsolute(x_target, y_target)

    @hdebug.debug
    def handleHome(self):
        self.moveAbsolute(0, 0)

    @hdebug.debug
    def handleLoad(self):
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

    @hdebug.debug
    def handleLockout(self):
        if self.locked_out:
            self.stopLockout()
            self.locked_out = False
            self.ui.joystickLockoutButton.setStyleSheet("QPushButton { color: red }")
        else:
            self.startLockout()
            self.locked_out = True
            self.ui.joystickLockoutButton.setStyleSheet("QPushButton { color: green }")        

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    @hdebug.debug
    def handleSave(self):
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

    @hdebug.debug
    def handleSaveIndexChange(self, index):
        data = self.ui.saveComboBox.itemData(index).toList()
        if data:
            [xvar, yvar] = data
            self.ui.xmoveDoubleSpinBox.setValue(xvar.toDouble()[0])
            self.ui.ymoveDoubleSpinBox.setValue(yvar.toDouble()[0])

    @hdebug.debug
    def jog(self, x_speed, y_speed):
        self.stage.jog(x_speed, y_speed)

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

    @hdebug.debug
    def leftS(self):
        self.moveRelative(0, self.small_step_size)

    @hdebug.debug
    def leftL(self):
        self.moveRelative(0, self.large_step_size)

    @hdebug.debug        
    def moveRelative(self, axis, distance):
        if self.stage:
            if axis == self.x_axis:
                self.stage.goRelative(distance * self.x_sign, 0)
            else:
                self.stage.goRelative(0, distance * self.y_sign)
#            [self.x, self.y, self.z] = self.stage.position()
            self.updatePosition()

    @hdebug.debug
    def moveAbsolute(self, x, y):
        if self.stage:
            self.stage.goAbsolute(x, y)
#            [self.x, self.y, self.z] = self.stage.position()
            self.updatePosition()

    @hdebug.debug    
    def newParameters(self, parameters):
        self.debug = parameters.debug
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

    @hdebug.debug
    def quit(self):
        if self.stage:
            self.stage.shutDown()

    @hdebug.debug
    def rightS(self):
        self.moveRelative(0, -1 * self.small_step_size)

    @hdebug.debug
    def rightL(self):
        self.moveRelative(0, -1 * self.large_step_size)

    @hdebug.debug
    def startLockout(self):
        if self.stage:
            self.stage.lockout(True)

    @hdebug.debug
    def step(self, x, y):
        self.stage.goRelative(x, y)

    @hdebug.debug
    def stopLockout(self):
        if self.stage:
            self.stage.lockout(False)

    @hdebug.debug
    def tcpHandleMoveTo(self, x, y):
        self.moveAbsolute(x, y)

    def updatePosition(self):
        if self.stage:
            [self.x, self.y, self.z] = self.stage.position()
        self.ui.xposText.setText("%.3f" % self.x)
        self.ui.yposText.setText("%.3f" % self.y)

    @hdebug.debug
    def upS(self):
        self.moveRelative(1, -1 * self.small_step_size)

    @hdebug.debug
    def upL(self):
        self.moveRelative(1, -1 * self.large_step_size)

    def zero(self):
        self.stage.zero()
        self.x = 0
        self.y = 0
        self.z = 0
        self.updatePosition()

#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
