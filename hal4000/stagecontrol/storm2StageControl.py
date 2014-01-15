#!/usr/bin/python
#
## @file
#
# Stage control for STORM2
#
# Hazen 7/09
#

from PyQt4 import QtCore

# stage.
import prior.prior as prior

# stage control dialog.
import stagecontrol.stageControl as stageControl

#
# STORM2 uses the same Prior stage for the focus lock
# so we create a global Prior control class here, and 
# also a global mutex so that stage XY and Z commands
# don't get crossed.
#

#prior_stage = prior.Prior(port = "COM1")
prior_stage = prior.Prior(port = "COM10", baudrate = 9600)
prior_mutex = QtCore.QMutex()

#
# Class for communication with the Prior stage for Z.
#
class QPriorZ(QtCore.QObject):
    def __init__(self, parent = None):
        QtCore.QObject.__init__(self, parent)
        global prior_stage
        global prior_mutex
        self.stage = prior_stage
        self.mutex = prior_mutex
        self.running = self.stage.getStatus()

    def zMoveTo(self, z):
        if self.running:
            self.mutex.lock()
            self.stage.zMoveTo(z)
            self.mutex.unlock()

    def shutDown(self):
        pass

#
# QThread for communication with the Prior stage for XY.
#
# This is necessary for position updates as otherwise
# the periodic communication with the Prior stage
# will cause the whole UI to behave a bit jerkily.
#
class QPriorThread(QtCore.QThread):
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        global prior_stage
        global prior_mutex
        self.stage = prior_stage
        self.stage_position = [0.0, 0.0, 0.0]
        self.running = self.stage.getStatus()
        self.mutex = prior_mutex

    def getStatus(self):
        return self.running

    def goAbsolute(self, x, y):
        self.mutex.lock()
        self.stage.goAbsolute(x, y)
        self.stage_position = self.stage.position()
        self.mutex.unlock()

    def goRelative(self, dx, dy):
        self.mutex.lock()
        self.stage.goRelative(dx, dy)
        self.stage_position = self.stage.position()
        self.mutex.unlock()
        
    def lockout(self, flag):
        self.mutex.lock()
        self.stage.joystickOnOff(not flag)
        self.mutex.unlock()

    def position(self):
        self.mutex.lock()
        stage_position = self.stage_position
        self.mutex.unlock()
        return stage_position

    def run(self):
        while self.running:
            self.mutex.lock()
            self.stage_position = self.stage.position()
            self.mutex.unlock()
            self.msleep(500)

    def setVelocity(self, vx, vy):
        self.mutex.lock()
        self.stage.setVelocity(vx, vy)
        self.mutex.unlock()

    def shutDown(self):
        self.running = 0
        self.wait()
        self.stage.shutDown()

    def zero(self):
        self.mutex.lock()
        self.stage.zero()
        self.stage_position = self.stage.position()
        self.mutex.unlock()

#
# Stage control dialog specialized for STORM2
# with Prior motorized stage.
#
class AStageControl(stageControl.StageControl):
    def __init__(self, hardware, parameters, tcp_control, parent = None):
        self.stage = QPriorThread()
        self.stage.start(QtCore.QThread.NormalPriority)
        stageControl.StageControl.__init__(self,
                                           parameters,
                                           tcp_control,
                                           parent)

#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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
