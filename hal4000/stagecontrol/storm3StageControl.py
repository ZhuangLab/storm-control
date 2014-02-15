#!/usr/bin/python
#
## @file
#
# Stage and filter wheel control for STORM3
#
# Hazen 4/12
#

from PyQt4 import QtCore

# stage.
import prior.prior as prior

# stage control thread
import stagecontrol.stageThread as stageThread

# stage control dialog.
import stagecontrol.stageControl as stageControl

#
# STORM3 also uses the Prior stage for filter wheel control.
#

#prior_stage = prior.Prior(port = "COM2")
prior_stage = prior.Prior(port = "COM9", baudrate = 115200, wait_time = 1.0e-4)
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
# Use QStageThread for communication with the Prior stage.
#
class QPriorThread(stageThread.QStageThread):
    def __init__(self, stage, parent = None):
        stageThread.QStageThread.__init__(self, stage, parent)
        global prior_mutex
        self.mutex = prior_mutex

#
# Stage control dialog specialized for STORM3
# with Prior motorized stage.
#
class AStageControl(stageControl.StageControl):
    def __init__(self, hardware, parameters, parent = None):
        self.stage = QPriorThread(prior_stage)
        self.stage.start(QtCore.QThread.NormalPriority)
        stageControl.StageControl.__init__(self,
                                           parameters,
                                           parent)

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
