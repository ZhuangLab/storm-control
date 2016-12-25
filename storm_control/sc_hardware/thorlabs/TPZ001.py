#!/usr/bin/python
#
## @file
#
# Active X based APT piezo & strain gauge control.
#
# Ke 12/09
#

from PyQt4 import QtCore, QtGui, QAxContainer

import sys
import time

class APTPiezo(QAxContainer.QAxWidget):
    def __init__(self, parent = None):
        QAxContainer.QAxWidget.__init__(self, parent)

        self.setControl("MGPIEZO.MGPiezoCtrl.1")
        self.dynamicCall('SetHWSerialNum(int)', 81822491) # Piezo control
#        self.dynamicCall('SetHWSerialNum(int)', 84822210) # Strain gauge control
        self.dynamicCall('StartCtrl()')

        self.hw_channel = 0
        
        # Set to closed loop mode.
        self.dynamicCall('SetControlMode(int, int)', self.hw_channel, 2)

#    def getPosition(self):
#        pos = QtCore.QVariant(-1.0)
#        pos = -1.0
#        resp = self.dynamicCall('SG_GetReading(int, single)', self.hw_channel, pos)
#        resp = self.dynamicCall('GetPosOutput(int, double &)', self.hw_channel, pos)
#        print resp.toString(), pos
        
    def moveTo(self, axis, pos):
        TPZ001Output = pos*4.05295555479678 + 7.85579353535888        
        self.dynamicCall('SetPosOutput(int, float)', self.hw_channel, TPZ001Output)
   
    def shutDown(self):
        self.dynamicCall('StopCtrl()')

#
# Testing
#

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    aptPiezo = APTPiezo()
    aptPiezo.moveTo(0,10.143)
    aptPiezo.shutDown()

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

