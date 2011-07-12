#!/usr/bin/python
#
# Stage and filter wheel control for STORM3
#
# Hazen 5/11
#

from PyQt4 import QtCore

# stage.
import prior.prior as prior

# stage control dialog.
import stagecontrol.stageControl as stageControl

#
# STORM3 also uses the Prior stage for filter wheel control.
#

#prior_stage = prior.Prior(port = "COM2")
prior_stage = prior.Prior(port = "COM9", baudrate = 115200)
prior_mutex = QtCore.QMutex()

#
# Class for communication with the Prior filter wheel.
#
class QPriorFilterWheel(QtCore.QObject):
    def __init__(self, parent = None):
        QtCore.QObject.__init__(self, parent)
        global prior_stage
        global prior_mutex
        self.stage = prior_stage
        self.mutex = prior_mutex
        self.running = self.stage.getStatus()

    def getPosition(self):
        if self.running:
            self.mutex.lock()
            filter = self.stage.getFilter()
            self.mutex.unlock()
            return filter
        else:
            return 0

    def setPosition(self, n):
        if self.running:
            self.mutex.lock()
            self.stage.changeFilter(n)
            self.mutex.unlock()

    def shutDown(self):
        pass

#
# QThread for communication with the Prior stage.
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
# Stage control dialog specialized for STORM3
# with Prior motorized stage.
#
class AStageControl(stageControl.StageControl):
    def __init__(self, parameters, tcp_control, parent = None):
        self.stage = QPriorThread()
        self.stage.start(QtCore.QThread.NormalPriority)
        stageControl.StageControl.__init__(self,
                                           parameters,
                                           tcp_control,
                                           parent)

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
