#!/usr/bin/python
#
# Generic stage control thread for buffering communication
# with those stages that do not respond very quickly.
#
# Hazen 04/12
#

from PyQt4 import QtCore

#
# QThread for communication with a slow stage.
#
# This is necessary for position updates as otherwise
# the periodic communication with the (slow) stage
# will cause the whole UI to behave a bit jerkily.
#
class QStageThread(QtCore.QThread):
    def __init__(self, stage, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.jbuffer = []
        self.stage = stage
        self.stage_position = [0.0, 0.0, 0.0]
        self.running = self.stage.getStatus()
        self.mutex = QtCore.QMutex()

    def getStatus(self):
        return self.running

    def goAbsolute(self, x, y):
        self.mutex.lock()
        self.stage.goAbsolute(x, y)
        #self.stage_position = self.stage.position()
        self.mutex.unlock()

    def goRelative(self, dx, dy):
        self.mutex.lock()
        self.stage.goRelative(dx, dy)
        #self.stage_position = self.stage.position()
        self.mutex.unlock()

    def jog(self, x_speed, y_speed):
        self.mutex.lock()
        self.jbuffer = [x_speed, y_speed]
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
        counter = 0
        while self.running:
            self.mutex.lock()
            counter += 1
            if (len(self.jbuffer) > 0):
                self.stage.jog(self.jbuffer[0], self.jbuffer[1])
                self.jbuffer = []
            if (counter == 100):
                self.stage_position = self.stage.position()
                counter = 0
            self.mutex.unlock()
            self.msleep(5)

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
