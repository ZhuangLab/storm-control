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
        # Jfocal specific focus lock parameters
        lock_params = parameters.addSubSection("focuslock")
##        lock_params.add("qpd_zcenter", params.ParameterRangeFloat("Piezo center position in microns",
##                                                                  "qpd_zcenter",
##                                                                  100.0, 0.0, 200.0))
        lock_params.add("qpd_zcenter", params.ParameterRangeFloat("Piezo center position in microns",
                                                          "qpd_zcenter",
                                                          50.0, 0.0, 100.0))

        lock_params.add("qpd_scale", params.ParameterRangeFloat("Offset to nm calibration value",
                                                                "qpd_scale",
                                                                -1000.0, -10000, 10000.0))
        lock_params.add("qpd_sum_min", 50.0)
        lock_params.add("qpd_sum_max", 100000.0)
        lock_params.add("is_locked_buffer_length", params.ParameterRangeInt("Length of in focus buffer",
                                                                "is_locked_buffer_length",
                                                                3, 1, 100))
        lock_params.add("is_locked_offset_thresh", params.ParameterRangeFloat("Offset distance still considered in focus",
                                                                "is_locked_offset_thresh",
                                                                1, 0.001, 1000))

        lock_params.add("focus_rate", params.ParameterRangeFloat("Proportionality constant for focus",
                                                                "focus_rate",
                                                                0.1, -1000, 1000))

        
        lock_params.add("ir_power", params.ParameterInt("", "ir_power", 6, is_mutable = False))

        # Add parameters for hardware timed z offsets
        lock_params.add("z_offsets", params.ParameterString("Comma separated list of offset positions per frame",
                                                            "z_offsets",
                                                            ""))

        # Create camera
        cam = uc480Cam.CameraQPD(camera_id = 1,
                                 x_width = 900,
                                 y_width = 50,
                                 sigma = 4.0,
                                 offset_file = "cam_offsets_jfocal_1.txt",
                                 background = 50000)
##        stage = MCLVZC.MCLVZControl("PCIe-6351", 0, scale = 10.0/200.0, trigger_source = "PFI0")
        stage = MCLVZC.MCLVZControl("PCIe-6351", 0, scale = 10.0/100.0, trigger_source = "PFI0")

        lock_fn = lambda (x): lock_params.get("focus_rate") * x
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
