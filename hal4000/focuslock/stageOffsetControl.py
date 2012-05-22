#!/usr/bin/python
#
# Stage and offset detector thread classes
#
# Hazen 03/12
#

from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

#
# QPD monitoring and stage control thread.
#
# This is a PyQt thread for controlling the z stage position
# and getting the current position reading from the QPD.
#
# stage is a class with the following methods:
#
#   zMoveTo(z)
#      Move the stage to position z in um.
#
#   shutDown()
#      Perform whatever cleanup is necessary to stop the stage cleanly
#
#
# qpd is a class with the following methods:
#
#   qpdScan()
#      Return the current reading from the QPD in a list
#      [power, x_offset, y_offset]
#
#   shutDown()
#      Perform whatever cleanup is necessary to stop the qpd cleanly
#
#
# lock_fn is a function that takes a single number (the QPD error signal)
#   and returns the appropriate response (in um) by the stage.
#
class stageQPDThread(QtCore.QThread):
    @hdebug.debug
    def __init__(self, qpd, stage, lock_fn, min_sum, z_center, slow_stage = False, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.qpd = qpd
        self.stage = stage
        self.lock_fn = lock_fn
        self.sum_min = min_sum

        self.count = 0
        self.debug = 1
        self.find_sum = False
        self.locked = 0
        self.max_pos = 0
        self.max_sum = 0
        self.offset = 0
        self.qpd_mutex = QtCore.QMutex()
        self.running = 1
        self.slow_stage = slow_stage
        self.stage_mutex = QtCore.QMutex()
        self.stage_z = z_center - 1.0
        self.sum = 0
        self.target = None
        self.unacknowledged = 1
        self.z_center = z_center

        # center the stage
        # self.newZCenter(z_center)

    @hdebug.debug
    def cleanUp(self):
        self.qpd.shutDown()
        self.stage.shutDown()

    @hdebug.debug
    def getLockTarget(self):
        self.qpd_mutex.lock()
        target = self.target
        self.qpd_mutex.unlock()
        return target

    @hdebug.debug
    def getOffset(self):
        self.qpd_mutex.lock()
        temp = self.offset
        self.qpd_mutex.unlock()
        return temp

    @hdebug.debug
    def findSumSignal(self):
        if (self.sum < (2.0 * self.sum_min)):
            self.qpd_mutex.lock()
            self.find_sum = True
            self.max_sum = 0
            self.max_pos = 0
            self.moveStageAbs(0)
            self.qpd_mutex.unlock()
        else:
            self.emit(QtCore.SIGNAL("foundSum()"))

    def moveStageAbs(self, new_z):
        self.stage_mutex.lock()
        if new_z != self.stage_z:
            self.stage_z = new_z
            self.stage.zMoveTo(self.stage_z)
        self.stage_mutex.unlock()

    def moveStageRel(self, dz):
        new_z = self.stage_z + dz
        self.moveStageAbs(new_z)

    def newZCenter(self, z_center):
        self.z_center = z_center

    def qpdScan(self):
        return self.qpd.qpdScan()

    def recenter(self):
        self.moveStageAbs(self.z_center)

    def recenterPiezo(self):
        self.emit(QtCore.SIGNAL("recenteredPiezo()"))

    def run(self):
        while(self.running):
            [power, x_offset, y_offset] = self.qpdScan()

            self.qpd_mutex.lock()
            if (power > 0):
                self.sum = power
                self.offset = x_offset / power
            self.unacknowledged = 0

            # scan for sum signal.
            if self.find_sum:
                if (power > self.max_sum):
                    self.max_sum = power
                    self.max_pos = self.stage_z
                if (power > (2.0 * self.sum_min)) and (power < (0.5 * self.max_sum)):
                    self.moveStageAbs(self.max_pos)
                    self.find_sum = False
                    self.emit(QtCore.SIGNAL("foundSum()"))
                else:
                    if (self.stage_z >= (2 * self.z_center)):
                        if (self.max_sum > 0):
                            self.moveStageAbs(self.max_pos)
                        else:
                            self.moveStageAbs(self.z_center)
                        self.find_sum = False
                        self.emit(QtCore.SIGNAL("foundSum()"))
                    else:
                        self.moveStageRel(1.0)

            # update position, if locked.
            else:
                if self.locked and (power > self.sum_min):
                    if self.slow_stage:
                        self.count += 1
                        if (self.count > 2):
                            self.count = 0
                            self.moveStageRel(self.lock_fn(self.offset - self.target))
                    else:
                        self.moveStageRel(self.lock_fn(self.offset - self.target))

            self.emit(QtCore.SIGNAL("controlUpdate(float, float, float, float)"), x_offset, y_offset, power, self.stage_z)
            self.qpd_mutex.unlock()
            self.msleep(1)

    def setStage(self, stage):
        self.qpd_mutex.lock()
        self.stage = stage
        self.qpd_mutex.unlock()

    @hdebug.debug
    def setTarget(self, target):
        self.qpd_mutex.lock()
        self.target = target
        self.qpd_mutex.unlock()

    @hdebug.debug
    def startLock(self):
        self.qpd_mutex.lock()
        self.unacknowledged = 1
        self.locked = 1
        if self.target == None:
            self.target = self.offset
        self.qpd_mutex.unlock()
        self.waitForAcknowledgement()

    @hdebug.debug
    def stopLock(self):
        self.qpd_mutex.lock()
        self.unacknowledged = 1
        self.locked = 0
        self.target = None
        self.qpd_mutex.unlock()
        self.waitForAcknowledgement()

    @hdebug.debug
    def stopThread(self):
        self.running = 0

    @hdebug.debug
    def waitForAcknowledgement(self):
        while(self.unacknowledged):
            self.msleep(20)

#
# Motorized Z, Piezo Stage and QPD Control Thread Class.
#
# This is a PyQt thread for controlling a motorized z stage,
# a piezo stage (for focusing) and getting the current
# position reading from the QPD. It is a subclass of the
# stageQPDThread that also controls a motorized focus.
#
# motor is a class with the following methods:
#
#   zMoveRelative(z)
#      Move the stage up or down by the amount z in um.
#
class motorStageQPDThread(stageQPDThread):
    @hdebug.debug
    def __init__(self, qpd, stage, motor, lock_fn, min_sum, z_center, slow_stage = False, parent = None):
        stageQPDThread.__init__(self,
                                qpd,
                                stage,
                                lock_fn,
                                min_sum,
                                z_center,
                                slow_stage = slow_stage,
                                parent = parent)
        self.motor = motor

    def recenterPiezo(self):
        print "recenter", self.stage_z, self.z_center
        if self.motor.live:
            offset = self.z_center - self.stage_z
            self.moveStageAbs(self.z_center)
            self.motor.zMoveRelative(offset)
        stageQPDControl.QControlThread.recenterPiezo(self)

#
# USB camera monitoring and stage control thread.
#
# This is a PyQt thread for controlling the z stage position
# and getting the current position reading from a USB camera.
# It is a subclass of stageQPDThread.
#
# cam is a class that uses a (USB) camera to emulate the readout
#    that you would normally get from a QPD. It has the following 
#    methods:
#
#   getImage()
#      Returns the current image from the USB camera as a numpy.uint8
#      2D array.
#
#   qpdScan()
#      Return the current reading from the camera in the same format
#      as we would have gotten from a QPD, [power, x_offset, y_offset]
#
#   shutDown()
#      Perform whatever cleanup is necessary to stop the qpd cleanly
#
class stageCamThread(stageQPDThread):
    @hdebug.debug
    def __init__(self, cam, stage, lock_fn, min_sum, z_center, slow_stage = False, parent = None):
        stageQPDThread.__init__(self,
                                cam,
                                stage,
                                lock_fn,
                                min_sum,
                                z_center,
                                slow_stage = slow_stage,
                                parent = parent)
        self.cam = cam
        self.cam_data = False
        self.cam_mutex = QtCore.QMutex()

    @hdebug.debug
    def getImage(self):
        self.cam_mutex.lock()
        data = self.cam_data
        self.cam_mutex.unlock()
        return data

    def qpdScan(self):
        self.cam_mutex.lock()
        data = self.cam.qpdScan()
        self.cam_data = list(self.cam.getImage())
        self.cam_data[0] = self.cam_data[0].copy()
        self.cam_mutex.unlock()
        return data


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
