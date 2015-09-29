#!/usr/bin/python
#
## @file
#
# Camera / Objective Z based focus lock control specialized for jfocal.
#
# Hazen 09/15
#

# qpd and stage.
import sc_hardware.madCityLabs.mclVoltageZController as MCLVZC
#import sc_hardware.madCityLabs.mclController as mclController
import sc_hardware.thorlabs.uc480Camera as uc480Cam

# focus lock control thread.
import focuslock.stageOffsetControl as stageOffsetControl

# ir laser control
import sc_hardware.thorlabs.LDC210 as LDC210

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for jfocal
# with UC480 camera and MCL piezo z stage.
#
class AFocusLockZ(focusLockZ.FocusLockZCam):
    def __init__(self, hardware, parameters, parent = None):
        cam = uc480Cam.CameraQPD(camera_id = 1, x_width = 340, y_width = 40, sigma = 4.0)
        stage = MCLVZC.MCLVZControl("PCI-6229", 0, scale = 10.0/100.0)
        #stage = mclController.MCLStage("c:/Program Files/Mad City Labs/NanoDrive/")
        lock_fn = lambda (x): 0.4 * x
        control_thread = stageOffsetControl.StageCamThread(cam,
                                                           stage,
                                                           lock_fn,
                                                           parameters.get("focuslock.qpd_sum_min", 50.0), 
                                                           parameters.get("focuslock.qpd_zcenter"),
                                                           parameters.get("focuslock.is_locked_buffer_length", 10),
                                                           parameters.get("focuslock.is_locked_offset_thresh", 0.01))
        ir_laser = LDC210.LDC210PWMNI("PCI-6229", 0)
        focusLockZ.FocusLockZCam.__init__(self,
                                          parameters,
                                          control_thread,
                                          ir_laser,
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
