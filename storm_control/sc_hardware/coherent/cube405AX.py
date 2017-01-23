#!/usr/bin/python
#
# Active X based Coherent CUBE 405 laser control.
#
# Hazen 8/09
#

from PyQt5 import QtCore, QtGui, QAxContainer

import sys
import time


class Cube405(QAxContainer.QAxWidget):
    def __init__(self, parent = None):
        QAxContainer.QAxWidget.__init__(self, parent)

        self.setControl("{AA1AC270-AD67-40BB-A584-1AC1B9EAE533}")
        self.dynamicCall('CUBEStart(1)')

        # IE based web browser...
#        self.setControl("{8856F961-340A-11D0-A96B-00C04FD705A2}")
#        self.dynamicCall('Navigate(const QString&)', QtCore.QVariant("www.google.com"))

#        self.cubeAX = QAxContainer.QAxWidget(None)
#        print self.cubeAX

#        pass
#        try:
#            # open port
#            RS232.RS232.__init__(self, port, None, 19200, "\r", 0.05)
#
#            # see if the laser is connected
#            assert not(self.commWithResp("?HID") == None)
#
#            # finish setup
#            self.pmin = 0.0
#            self.pmax = 5.0
#            [self.pmin, self.pmax] = self.getPowerRange()
#            self.setExtControl(0)
#        except:
#            self.live = 0
#            print "Failed to connect to 405 Laser. Perhaps it is turned off"
#            print "or the Keyspan COM ports have been scrambled?"

    def respToFloat(self, resp, start):
        pass
#        return float(resp[start:-1])

    def getExtControl(self):
        pass

#        self.sendCommand("?EXT")
#        response = self.waitResponse()
#        if response.find("=1") == -1:
#            return 0
#        else:
#            return 1

    def getLaserOnOff(self):
        pass
#        self.sendCommand("?L")
#        return self.waitResponse()

    def getPowerRange(self):
        pass
#        self.sendCommand("?MINLP")
#        pmin = self.respToFloat(self.waitResponse(), 6)
#        self.sendCommand("?MAXLP")
#        pmax = self.respToFloat(self.waitResponse(), 6)
#        return [pmin, pmax]

    def getPower(self):
        pass
#        self.sendCommand("?SP")
#        power_string = self.waitResponse()
#        return float(power_string[3:-1])

    def setExtControl(self, mode):
        pass
#        if mode:
#            self.sendCommand("EXT=1")
#        else:
#            self.sendCommand("EXT=0")
#        self.waitResponse()

#    def setLaserOnOff(self, on):
#        if on and (not self.on):
#            self.sendCommand("L=1")
#            self.on = 1
#        if (not on) and self.on:
#            self.sendCommand("L=0")
#            self.on = 0
#        print self.waitResponse()

    def setPower(self, power_in_mW):
        pass
#        assert power_in_mW >= 0.0, "setPower: power to low " + str(power_in_mW)
#        assert power_in_mW <= 50.0, "setPower: power to high " + str(power_in_mW)
#        if power_in_mW < self.pmin:
#            power_in_mW = self.pmin
#        if power_in_mW > self.pmax:
#            power_in_mW = self.pmax
#        self.sendCommand("P=" + str(power_in_mW))
#        self.waitResponse()

    
#
# Testing
#

if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    cube = Cube405()
    cube.show()
    sys.exit(app.exec_())

#    if cube.getStatus():
#        print cube.getPowerRange()
#        print cube.getLaserOnOff()


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

