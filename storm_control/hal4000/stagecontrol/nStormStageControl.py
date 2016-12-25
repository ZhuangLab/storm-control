#!/usr/bin/python
#
## @file
#
# Stage control for Nikon TiU
#
# Hazen 04/15
#

from PyQt4 import QtCore

# stage.
import sc_hardware.nikon.tiUStage as tiUStage

# stage control thread
import stagecontrol.stageThread as stageThread

# stage control dialog.
import stagecontrol.stageControl as stageControl

#
# Stage control dialog specialized for Prism2
# with marzhauser motorized stage.
#
class AStageControl(stageControl.StageControl):
    def __init__(self, hardware, parameters, parent = None):
        self.stage = stageThread.QStageThread(tiUStage.TiUStage())
        self.stage.start(QtCore.QThread.NormalPriority)
        stageControl.StageControl.__init__(self, 
                                           parameters,
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
