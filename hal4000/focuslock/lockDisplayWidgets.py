#!/usr/bin/python
#
# These widgets are used by the focusLockZ 
# class to provide user feedback.
#
# Hazen 03/12
#

from PyQt4 import QtCore, QtGui

#
# Status display widgets
#
class QStatusDisplay(QtGui.QWidget):
    def __init__(self, x_size, y_size, scale_min, scale_max, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.x_size = x_size
        self.y_size = y_size
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.range = scale_max - scale_min
        self.value = 0
        self.warning = 0

    def convert(self, value):
        scaled = int((value - self.scale_min)/self.range * float(self.y_size))
        if scaled > self.y_size:
            scaled = self.y_size
        if scaled < 0:
            scaled = 0
        return scaled

    def paintBackground(self, painter):
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

    def updateValue(self, value):
        self.value = self.convert(value)
        self.update()

class QSumDisplay(QStatusDisplay):
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, scale_min, scale_max, parent = parent)
        self.warning_low = self.convert(float(warning_low))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)

        # warning bar
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, self.y_size - self.warning_low, self.x_size, self.y_size)

        # foreground
        color = QtGui.QColor(0, 255, 0, 200)
        if self.value < self.warning_low:
            color = QtGui.QColor(255, 0, 0, 200)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.y_size - self.value, self.x_size - 5, self.value)

class QOffsetDisplay(QStatusDisplay):
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, warning_high, has_center_bar = 0, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, scale_min, scale_max, parent = parent)
        self.center_bar = 0
        if has_center_bar:
            self.center_bar = int(0.5 * self.y_size)
        self.warning_low = self.convert(float(warning_low))
        self.warning_high = self.convert(float(warning_high))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)

        # warning bars
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, self.y_size - self.warning_low, self.x_size, self.y_size)
        painter.drawRect(0, 0, self.x_size, self.y_size - self.warning_high)

        if self.center_bar:
            color = QtGui.QColor(50, 50, 50)
            painter.setPen(color)
            painter.drawLine(0, self.center_bar, self.x_size, self.center_bar)

        # foreground
        color = QtGui.QColor(0, 0, 0, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.y_size - self.value - 2, self.x_size - 5, 3)

class QQPDDisplay(QStatusDisplay):
    def __init__(self, x_size, y_size, scale, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, (-1 * scale), scale, parent = parent)
        self.center = self.convert(0.0) - 4
        self.x_value = 0
        self.y_value = 0

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)
        
        # cross hairs
        color = QtGui.QColor(50, 50, 50)
        painter.setPen(color)
        painter.drawLine(0, self.center, self.x_size, self.center)
        painter.drawLine(self.center, 0, self.center, self.y_size)

        # spot
        color = QtGui.QColor(0, 0, 0, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(self.x_value - 7, self.y_value - 7, 6, 6)

    def updateValue(self, x, y):
        self.x_value = self.convert(x)
        self.y_value = self.convert(y)
        self.update()

class QCamDisplay(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.background = QtGui.QColor(0,0,0)
        self.image = None

    def newImage(self, np_data):
        w, h = np_data.shape
        self.image = QtGui.QImage(np_data.data, w, h, QtGui.QImage.Format_Indexed8)
        self.image.ndarray = np_data
        for i in range(256):
            self.image.setColor(i, QtGui.QColor(i,i,i).rgb())
        self.update()

    def paintEvent(self, Event):
        painter = QtGui.QPainter(self)
        if self.image:
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

            destination_rect = QtCore.QRect(0, 0, self.width(), self.height())
            painter.drawImage(destination_rect, self.image)
        else:
            painter.setPen(self.background)
            painter.setBrush(self.background)
            painter.drawRect(0, 0, self.width(), self.height())

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
