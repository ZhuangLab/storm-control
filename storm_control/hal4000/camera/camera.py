#!/usr/bin/env python
"""
Handles a single camera.

Hazen 02/17
"""

import importlib

from PyQt5 import QtCore


import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class Camera(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        camera_params = module_params.get("camera")
        a_module = importlib.import_module("storm_control.hal4000." + camera_params.get("module_name"))
        a_class = getattr(a_module, camera_params.get("class_name"))
        self.camera_control = a_class(camera_params.get("parameters"))

        self.camera_control.newFrame.connect(self.handleNewFrame)

    def cleanUp(self, qt_settings):
        self.camera_control.cleanUp()

    def handleNewFrame(self, frame, key):
        if (key == self.key):
            self.newFrame.emit(frame)

    def processMessage(self, message):
        super().processMessage(message)


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
