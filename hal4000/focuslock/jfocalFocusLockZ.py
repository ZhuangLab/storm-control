#!/usr/bin/python
#
## @file
#
# Camera / Objective Z based focus lock control specialized for jfocal.
#
# Hazen 09/15
#

import sc_library.parameters as params

# qpd and stage.
import sc_hardware.madCityLabs.mclVoltageZController as MCLVZC
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
        # STORM3 specific focus lock parameters
        lock_params = parameters.addSubSection("focuslock")
        lock_params.add("qpd_zcenter", params.ParameterRangeFloat("Piezo center position in microns",
                                                                  "qpd_zcenter",
                                                                  100.0, 0.0, 200.0))
        lock_params.add("qpd_scale", params.ParameterRangeFloat("Offset to nm calibration value",
                                                                "qpd_scale",
                                                                -700.0, 0.1, 1000.0))
        lock_params.add("qpd_sum_min", 50.0)
        lock_params.add("qpd_sum_max", 100000.0)
        lock_params.add("is_locked_buffer_length", 3)
        lock_params.add("is_locked_offset_thresh", 0.1)
        lock_params.add("ir_power", params.ParameterInt("", "ir_power", 6, is_mutable = False))

        # Create camera
        cam = uc480Cam.CameraQPD(camera_id = 1,
                                 x_width = 1000,
                                 y_width = 70,
                                 sigma = 4.0,
                                 offset_file = "cam_offsets_jfocal_1.txt",
                                 background = 125000)
        stage = MCLVZC.MCLVZControl("PCIe-6351", 0, scale = 10.0/200.0)
        lock_fn = lambda (x): 0.1 * x
        control_thread = stageOffsetControl.StageCamThread(cam,
                                                           stage,
                                                           lock_fn,
                                                           parameters.get("focuslock.qpd_sum_min", 50.0), 
                                                           parameters.get("focuslock.qpd_zcenter"),
                                                           parameters.get("focuslock.is_locked_buffer_length", 3),
                                                           parameters.get("focuslock.is_locked_offset_thresh", 0.1))
        ir_laser = LDC210.LDC210PWMNI("PCIe-6351", 0)
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
