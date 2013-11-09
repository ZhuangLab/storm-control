#!/usr/bin/python
#
## @file
#
# Generic stage control thread for buffering communication
# with those stages that do not respond very quickly.
#
# Hazen 04/12
#

from PyQt4 import QtCore

## QStageThread
#
# QThread for communication with a slow stage.
#
# This is necessary for position updates as otherwise
# the periodic communication with the (slow) stage
# will cause the whole UI to behave a bit jerkily.
#
class QStageThread(QtCore.QThread):

    ## __init__
    #
    # @param stage A stage (hardware) control object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, stage, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.jbuffer = []
        self.stage = stage
        self.stage_position = [0.0, 0.0, 0.0]
        self.running = self.stage.getStatus()
        self.mutex = QtCore.QMutex()

    ## getStatus
    #
    # @return True/False if we can actually talk to the stage hardware.
    #
    def getStatus(self):
        return self.running

    ## goAbsolute
    #
    # @param x The x position in um.
    # @param y The y position in um.
    #
    def goAbsolute(self, x, y):
        self.mutex.lock()
        self.stage.goAbsolute(x, y)
        #self.stage_position = self.stage.position()
        self.mutex.unlock()

    ## goRelative
    #
    # @param dx The x displacement in um.
    # @param dy The y displacement in um.
    #
    def goRelative(self, dx, dy):
        self.mutex.lock()
        self.stage.goRelative(dx, dy)
        #self.stage_position = self.stage.position()
        self.mutex.unlock()

    ## jog
    #
    # @param x_speed The speed to move in x.
    # @param y_speed The speed to move in y.
    #
    def jog(self, x_speed, y_speed):
        self.mutex.lock()
        self.jbuffer = [x_speed, y_speed]
        self.mutex.unlock()

    ## lockout
    #
    # @param flag True/False turn on/off the stage joystick lockout.
    #
    def lockout(self, flag):
        self.mutex.lock()
        self.stage.joystickOnOff(not flag)
        self.mutex.unlock()

    ## position
    #
    # @return The stage position.
    #
    def position(self):
        self.mutex.lock()
        stage_position = self.stage_position
        self.mutex.unlock()
        return stage_position

    ## run
    #
    # The stage control thread. Jogs the stage, if requested, and gets
    # the current stage position.
    #
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

    ## setVelocity
    #
    # @param x_vel The stage velocity in x.
    # @param y_vel The stage velocity in y.
    #
    def setVelocity(self, x_vel, y_vel):
        self.mutex.lock()
        self.stage.setVelocity(x_vel, y_vel)
        self.mutex.unlock()

    ## shutDown
    #
    # Stop the thread & close the connection to the stage.
    #
    def shutDown(self):
        self.running = 0
        self.wait()
        self.stage.shutDown()

    ## zero
    #
    # Set the current position as the new stage zero.
    #
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
