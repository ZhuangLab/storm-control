#!/usr/bin/python
#
# Motorized Z, Piezo Stage and QPD Control Thread Class.
#
# This is a PyQt thread for controlling a motorized z stage,
# a piezo stage (for focusing) and getting the current
# position reading from the QPD.
#
# motor is a class with the following methods:
#
#   zMoveRelative(z)
#      Move the stage up or down by the amount z in um.
#
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
#
# Hazen 12/10
#

from PyQt4 import QtCore

# Debugging
import halLib.hdebug as hdebug

import stageQPDControl

#
# QPD monitoring and stage control thread.
#
class QControlThread(stageQPDControl.QControlThread):
    @hdebug.debug
    def __init__(self, qpd, stage, motor, lock_fn, min_sum, z_center, slow_stage = False, parent = None):
        stageQPDControl.QControlThread.__init__(self,
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
