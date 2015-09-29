#!/usr/bin/python
#
## @file
#
# Pseudo focus lock for nonedual setup.
#
# Hazen 07/15
#

# none widgets
import focuslock.noneWidgets as noneWidgets

# focus lock control thread.
import focuslock.stageOffsetControl as stageOffsetControl

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for pseudo setup.
#
class AFocusLockZ(focusLockZ.FocusLockZDualCam):
    def __init__(self, hardware, parameters, parent = None):
        cam1 = noneWidgets.Camera()
        cam2 = noneWidgets.Camera()
        stage1 = noneWidgets.NanoP()
        stage2 = noneWidgets.NanoP()
        lock_fn = lambda (x): 0.0 * x
        control_thread1 = stageOffsetControl.StageCamThread(cam1,
                                                            stage1,
                                                            lock_fn,
                                                            50.0,
                                                            parameters.get("focuslock.qpd_zcenter"),
                                                            parameters.get("focuslock.is_locked_buffer_length", 10),
                                                            parameters.get("focuslock.is_locked_offset_thresh", 0.01))
        control_thread2 = stageOffsetControl.StageCamThread(cam2,
                                                            stage2,
                                                            lock_fn,
                                                            50.0,
                                                            parameters.get("focuslock.qpd_zcenter"),
                                                            parameters.get("focuslock.is_locked_buffer_length", 10),
                                                            parameters.get("focuslock.is_locked_offset_thresh", 0.01))
        

        ir_laser1 = noneWidgets.IRLaser()
        ir_laser2 = noneWidgets.IRLaser()
        focusLockZ.FocusLockZDualCam.__init__(self,
                                              parameters,
                                              [control_thread1, control_thread2],
                                              [ir_laser1, ir_laser2],
                                              parent)

#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
