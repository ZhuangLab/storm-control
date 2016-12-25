#!/usr/bin/python
#
## @file
#
# Focus lock control specialized for Storm4 dual objective.
#
# Hazen 12/12
#

from PyQt4 import QtCore

# camera and stage.
import sc_hardware.madCityLabs.mclController as mclController
import sc_hardware.thorlabs.uc480Camera as uc480Cam

# focus lock control thread.
import focuslock.stageOffsetControl as stageOffsetControl

# ir laser control
import sc_hardware.thorlabs.LDC210 as LDC210

# focus lock dialog.
import focuslock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for the dual objective Storm4 
# scope with two USB cameras and two MCL objective Z positioners.
#
class AFocusLockZ(focusLockZ.FocusLockZDualCam):
    def __init__(self, hardware, parameters, parent = None):
        lock_fn = lambda(x): 0.05*x

        # The numpy fitting routine is apparently not thread safe.
        fit_mutex = QtCore.QMutex()

        # Lower objective camera and piezo.
        cam1 = uc480Cam.CameraQPD300(camera_id = 2,
                                     fit_mutex = fit_mutex)
        stage1 = mclController.MCLStage("c:/Program Files/Mad City Labs/NanoDrive/",
                                        serial_number = 2636)
        control_thread1 = stageOffsetControl.StageCamThread(cam1,
                                                            stage1,
                                                            lock_fn,
                                                            50.0,
                                                            parameters.get("qpd_zcenter"))

        # Upper objective camera and piezo.
        cam2 = uc480Cam.CameraQPD300(camera_id = 3,
                                     fit_mutex = fit_mutex)
        stage2 = mclController.MCLStage("c:/Program Files/Mad City Labs/NanoDrive/",
                                        serial_number = 2637)
        control_thread2 = stageOffsetControl.StageCamThread(cam2,
                                                            stage2,
                                                            lock_fn,
                                                            50.0,
                                                            parameters.get("qpd_zcenter"))

        ir_laser = LDC210.LDC210PWMLJ()

        focusLockZ.FocusLockZDualCam.__init__(self,
                                              parameters,
                                              [control_thread1, control_thread2],
                                              [ir_laser, False],
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
