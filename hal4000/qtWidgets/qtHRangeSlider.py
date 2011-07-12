#!/usr/bin/python
#
# Deprecated! Use qtRangeSlider instead!
#
# Qt Widget Range slider widget.
#
# Hazen 4/09
#

from PyQt4 import QtCore, QtGui
import sys

# Camera widget
class QHRangeSlider(QtGui.QWidget):
    def __init__(self, range = None, values = None, parent = None):
        QtGui.QWidget.__init__(self, parent)
        if (not parent):
            self.setGeometry(200, 200, 200, 20)
        self.emit_while_moving = 0
        self.scale = 0
        self.setMouseTracking(False)
        self.moving = "none"
        self.bar_width = 10
        if range:
            self.setRange(range)
        if values:
            self.setValues(values)
        else:
            self.setValues([0.3, 0.6])

    def emitRange(self):
        w = float(self.width() - 2 * self.bar_width - 1)
        if self.scale:
            fmin = (float(self.rmin - self.bar_width)/((w+1.0) * self.scale) + self.start)
            fmax = (float(self.rmax - self.bar_width)/(w * self.scale) + self.start)
        else:
            fmin = float(self.rmin - self.bar_width)/(w+1.0)
            fmax = float(self.rmax - self.bar_width)/w
        print "Range change:", fmin, fmax

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rmin = self.rmin
        rmax = self.rmax
        w = self.width()
        h = self.height()

        # background
        painter.setPen(QtCore.Qt.gray)
        painter.setBrush(QtCore.Qt.lightGray)
        painter.drawRect(2, 2, w-4, h-4)

        # range bar
        painter.setPen(QtCore.Qt.darkGray)
        painter.setBrush(QtCore.Qt.darkGray)
        painter.drawRect(rmin-1, 5, rmax-rmin+2, h-10)

        # min & max tabs
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(rmin-self.bar_width, 1, 10, h-2)

        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(rmax, 1, self.bar_width, h-2)

    def mouseMoveEvent(self, event):
        w = self.width()
        diff = self.start_x - event.x()
        if self.moving == "min":
            temp = self.start_rmin - diff
            if (temp >= self.bar_width) and (temp < w - self.bar_width):
                self.rmin = temp
                if self.rmax < self.rmin:
                    self.rmax = self.rmin
                self.update()
                if self.emit_while_moving:
                    self.emitRange()
        elif self.moving == "max":
            temp = self.start_rmax - diff
            if (temp >= self.bar_width) and (temp < w - self.bar_width):
                self.rmax = temp
                if self.rmax < self.rmin:
                    self.rmin = self.rmax
                self.update()
                if self.emit_while_moving:
                    self.emitRange()
        elif self.moving == "bar":
            temp = self.start_rmin - diff
            if (temp >= self.bar_width) and (temp < w - self.bar_width - (self.start_rmax - self.start_rmin)):
                self.rmin = temp
                self.rmax = self.start_rmax - diff
                self.update()
                if self.emit_while_moving:
                    self.emitRange()

    def mousePressEvent(self, event):
        x = event.x()
        if abs(self.rmin - 0.5 * self.bar_width - x) < (0.5 * self.bar_width):
            self.moving = "min"
        elif abs(self.rmax + 0.5 * self.bar_width - x) < (0.5 * self.bar_width):
            self.moving = "max"
        elif (x > self.rmin) and (x < self.rmax):
            self.moving = "bar"
        self.start_rmin = self.rmin
        self.start_rmax = self.rmax
        self.start_x = x
            
    def mouseReleaseEvent(self, event):
        if not (self.moving == "none"):
            self.emitRange()
        self.moving = "none"

    def setRange(self, range):
        self.start = range[0]
        self.scale = 1.0/(range[1] - range[0])

    def setValues(self, values):
        w = float(self.width() - 2 * self.bar_width - 1)
        if self.scale:
            self.rmin = int(w * (values[0] - self.start) * self.scale) + self.bar_width
            self.rmax = int(w * (values[1] - self.start) * self.scale) + self.bar_width
        else:
            self.rmin = int(w * values[0]) + self.bar_width
            self.rmax = int(w * values[1]) + self.bar_width

    def setEmitWhileMoving(self, bool):
        if bool:
            self.emit_while_moving = 1
        else:
            self.emit_while_moving = 0
        

#
# Testing
#

if __name__ == "__main__":
    class Parameters:
        def __init__(self):
            self.x_pixels = 200
            self.y_pixels = 200

    app = QtGui.QApplication(sys.argv)
#    hslider = QHRangeSlider()
    hslider = QHRangeSlider(range = [-5.0, 5.0], values = [-2.5, 2.5])
    hslider.setEmitWhileMoving(True)
    hslider.show()
    sys.exit(app.exec_())


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

