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
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, warning_high, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, scale_min, scale_max, parent = parent)
        self.warning_low = self.convert(float(warning_low))
        if warning_high:
            self.warning_high = self.convert(float(warning_high))
        else:
            self.warning_high = False

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
        if self.warning_high:
            if self.value >= self.warning_high:
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
    adjustCamera = QtCore.pyqtSignal(int, int)

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.adjust_mode = False
        self.background = QtGui.QColor(0,0,0)
        self.e_size = 8
        self.foreground = QtGui.QColor(0,255,0)
        self.image = None
        self.live_check = 0
        self.x_off1 = 0
        self.y_off1 = 0
        self.x_off2 = 0
        self.y_off2 = 0

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def keyPressEvent(self, event):
        if self.adjust_mode:
            which_key = event.key()
            # The minimun increment (at least for the
            # Thorlabs USB camera) is two pixels.
            if (which_key == QtCore.Qt.Key_Left):
                self.adjustCamera.emit(2,0)
            if (which_key == QtCore.Qt.Key_Right):
                self.adjustCamera.emit(-2,0)
            if (which_key == QtCore.Qt.Key_Up):
                self.adjustCamera.emit(0,2)
            if (which_key == QtCore.Qt.Key_Down):
                self.adjustCamera.emit(0,-2)

    def mousePressEvent(self, event):
        self.adjust_mode = not self.adjust_mode
        self.update()

    def newImage(self, data):
        # update image
        np_data = data[0]
        w, h = np_data.shape
        self.image = QtGui.QImage(np_data.data, w, h, QtGui.QImage.Format_Indexed8)
        self.image.ndarray = np_data
        for i in range(256):
            self.image.setColor(i, QtGui.QColor(i,i,i).rgb())

        # update offsets
        self.x_off1 = ((data[2]+w/2)/float(w))*float(self.width()) - 0.5*self.e_size + 1
        self.y_off1 = ((data[1]+h/2)/float(h))*float(self.height()) - 0.5*self.e_size + 1
        self.x_off2 = ((data[4]+w/2)/float(w))*float(self.width()) - 0.5*self.e_size + 1
        self.y_off2 = ((data[3]+h/2)/float(h))*float(self.height()) - 0.5*self.e_size + 1

        # Update live check
        #
        # This is for debugging an issue where the 
        # USB camera appears to freeze.
        #
        self.live_check += 255
        if(self.live_check > 255):
            self.live_check = 0

        self.update()

    def paintEvent(self, Event):
        painter = QtGui.QPainter(self)
        if self.image:
            # draw image
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            destination_rect = QtCore.QRect(0, 0, self.width(), self.height())
            painter.drawImage(destination_rect, self.image)

            # draw alignment lines
            if self.adjust_mode:
                painter.setPen(QtGui.QColor(100,100,100))
                painter.drawLine(0.0, 0.5*self.height(), self.width(), 0.5*self.height())
                for mult in [0.25, 0.5, 0.75]:
                    painter.drawLine(mult*self.width(), 0.0, mult*self.width(), self.height())


            # draw beam tracking circle
            else:
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setPen(QtGui.QColor(0,255,0))
                painter.drawEllipse(QtCore.QPointF(self.x_off1, self.y_off1), self.e_size, self.e_size)
                painter.drawEllipse(QtCore.QPointF(self.x_off2, self.y_off2), self.e_size, self.e_size)

            # display live check (for debugging)
            painter.setPen(QtGui.QColor(self.live_check,0,0))
            painter.drawRect(2,2,2,2)

        else:
            painter.setPen(self.background)
            painter.setBrush(self.background)
            painter.drawRect(0, 0, self.width(), self.height())

    def toggleCircles(self):
        self.display_circles = not self.display_circles

    def toggleLine(self):
        self.display_lines = not self.display_lines


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
