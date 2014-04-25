#!/usr/bin/python
#
## @file
#
# QPD / Objective Z based focus lock control specialized for STORM3 dual objective.
# Does this work? I don't remember ever figuring out Thorlabs ActiveX control.
#
# Hazen 12/09
#

# none widgets
import focuslock.noneWidgets as noneWidgets

# piezo control.
import sc_hardware.thorlabs.TPZ001 as TPZ001

# focus lock control thread.
import focuslock.stageQPDControl as stageQPDControl

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for STORM4PI
# which only has a piezo stage positioner.
#
class AFocusLockZ(focusLockZ.FocusLockZ):
    def __init__(self, parameters, parent = None):
        qpd = noneWidgets.QPD()
        stage = noneWidgets.NanoP()
        lock_fn = lambda (x): 0.0 * x
        control_thread = stageQPDControl.QControlThread(qpd,
                                                        stage,
                                                        lock_fn,
                                                        50.0,
                                                        parameters.qpd_zcenter)
        ir_laser = noneWidgets.IRLaser()
        focusLockZ.FocusLockZ.__init__(self,
                                       parameters, 
                                       control_thread,
                                       ir_laser,
                                       parent)

        # Since the stage is an ActiveX control & such controls
        # have to have a parent we have to change the stage class
        # after the focus lock dialog box has been initialized.
        stage = TPZ001.APTPiezo(parent = self)
        stage.hide()
        stage.moveTo(0, parameters.qpd_zcenter)
        control_thread.setStage(stage)
        control_thread.recenter()

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
