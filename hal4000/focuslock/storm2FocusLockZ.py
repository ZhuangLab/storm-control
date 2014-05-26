#!/usr/bin/python
#
## @file
#
# QPD / Objective Z based focus lock 
# control specialized for STORM2.
#
# Hazen 03/12
#

# qpd and stage.
import stagecontrol.storm2StageControl as zstage
import sc_hardware.phreshPhotonics.phreshQPD as phreshQPD

# focus lock control thread.
import focuslock.stageOffsetControl as stageOffsetControl

# ir laser control
import sc_hardware.thorlabs.LDC210 as LDC210

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for STORM3
# with Phresh QPD and MCL objective Z positioner.
#
class AFocusLockZ(focusLockZ.FocusLockZQPD):
    def __init__(self, hardware, parameters, tcp_control, parent = None):
        qpd = phreshQPD.PhreshQPDSTORM2()
        stage = zstage.QPriorZ()
#        lock_fn = lambda (x): -1.75 * x
        lock_fn = lambda (x): x
        control_thread = stageOffsetControl.StageQPDThread(qpd,
                                                           stage,
                                                           lock_fn,
                                                           50.0, 
                                                           parameters.get("qpd_zcenter"),
                                                           slow_stage = True)
        ir_laser = LDC210.LDC210("PCIe-6259", 8)
        focusLockZ.FocusLockZQPD.__init__(self,
                                          parameters,
                                          tcp_control,
                                          control_thread,
                                          ir_laser,
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
