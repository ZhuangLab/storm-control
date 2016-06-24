#!/usr/bin/python
#
## @file
#
# Pseudo focus lock for none setup.
#
# Hazen 11/09
#

import sc_library.parameters as params

# none widgets
import focuslock.noneWidgets as noneWidgets

# focus lock control thread.
import focuslock.stageOffsetControl as stageOffsetControl

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for pseudo setup.
#
class AFocusLockZ(focusLockZ.FocusLockZQPD):
    def __init__(self, hardware, parameters, parent = None):

        # None specific focus lock parameters
        lock_params = parameters.addSubSection("focuslock")
        lock_params.add("qpd_zcenter", params.ParameterRangeFloat("Piezo center position in microns",
                                                                  "qpd_zcenter",
                                                                  50.0, 0.0, 100.0))
        lock_params.add("qpd_scale", params.ParameterRangeFloat("Offset to nm calibration value",
                                                                "qpd_scale",
                                                                50.0, 0.0, 10000.0))
        lock_params.add("qpd_sum_min", 50.0)
        lock_params.add("qpd_sum_max", 1500.0)
        lock_params.add("is_locked_buffer_length", 10)
        lock_params.add("is_locked_offset_thresh", 0.01)
        
        # None Initialization.
        qpd = noneWidgets.QPD()
        stage = noneWidgets.NanoP()
        lock_fn = lambda (x): 0.0 * x
        control_thread = stageOffsetControl.StageQPDThread(qpd,
                                                           stage,
                                                           lock_fn,
                                                           lock_params.get("qpd_sum_min"),
                                                           lock_params.get("qpd_zcenter"),
                                                           lock_params.get("is_locked_buffer_length"),
                                                           lock_params.get("is_locked_offset_thresh"))
        
        ir_laser = noneWidgets.IRLaser()
        focusLockZ.FocusLockZQPD.__init__(self,
                                          parameters,
                                          control_thread,
                                          ir_laser,
                                          parent)

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
