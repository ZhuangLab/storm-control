#!/usr/bin/python
#
## @file
#
# A wheel widget for controling things like the microscope focus motor.
#
# Hazen 11/13
#

from PyQt4 import QtCore, QtGui
import sys

## QAbstractWheel
#
# Wheel super class.
#
class QAbstractWheel(QtGui.QWidget):
    valueChanged = QtCore.pyqtSignal(float)

    ## __init__
    #
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.current_pos = 0.0
        self.display_pos = 0
        self.maximum = 100.0
        self.minimum = 0.0
        self.multiple_step = 10.0
        self.single_step = 1.0
        self.spacing = 20

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    ## changed
    #
    # Called when the current position is changed. Checks that the current
    # position is not outside the wheel range. Emits the valueChanged
    # signal & tells the wheel to redraw itself.
    #
    def changed(self):
        if (self.current_pos < self.minimum):
            self.current_pos = self.minimum
        elif (self.current_pos > self.maximum):
            self.current_pos = self.maximum

        self.display_pos = int(self.current_pos/self.single_step) % self.spacing

        if 0:
            print self.current_pos, self.display_pos

        self.valueChanged.emit(self.current_pos)
        self.update()

    ## keyPressEvent
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        key = event.key()

        # move wheel based on arrow keys
        moving_max = False
        if key == QtCore.Qt.Key_Up:
            self.current_pos += self.single_step
        elif key == QtCore.Qt.Key_Down:
            self.current_pos -= self.single_step
        elif key == QtCore.Qt.Key_PageUp:
            self.current_pos += self.multiple_step
        elif key == QtCore.Qt.Key_PageDown:
            self.current_pos -= self.multiple_step

        self.changed()

    ## setPosition
    #
    # @param current_pos The new current position for the wheel.
    #
    def setPosition(self, current_pos):
        if (current_pos != self.current_pos):
            self.current_pos = current_pos
            self.display_pos = int(self.current_pos/self.single_step) % self.spacing

            self.changed()

    ## setRange
    #
    # @param wheel_range A python array of [maximum, minimum, multi-step, single-step].
    #
    def setRange(self, wheel_range):
        self.maximum = wheel_range[1]
        self.minimum = wheel_range[0]
        self.multiple_step = wheel_range[3]
        self.single_step = wheel_range[2]

    ## wheelEvent
    #
    # Handles mouse wheel events.
    #
    # @param event A PyQt wheel event object.
    #
    def wheelEvent(self, event):
        if (event.delta() > 0):
            self.current_pos += self.single_step
        else:
            self.current_pos -= self.single_step

        self.changed()


## QVWheel
#
# A vertically oriented wheel.
#
class QVWheel(QAbstractWheel):

    ## __init__
    #
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, parent = None):
        QAbstractWheel.__init__(self, parent)

        self.wheel_pixmap = None

        self.resizeEvent(None)

    ## paintEvent
    #
    # Draw the vertical wheel.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        w = self.width()
        h = self.height()

        # draw wheel
        painter.drawPixmap(0, -self.display_pos, self.wheel_pixmap)

        # draw bounding rectangle
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

    ## resizeEvent
    #
    # Redraw the wheel pixmap.
    #
    # @param event A PyQt resize event.
    #
    def resizeEvent(self, event):
        self.wheel_pixmap = QtGui.QPixmap(self.width(), self.height() + 2*self.spacing)
        self.wheel_pixmap.fill(QtCore.Qt.black)
        painter = QtGui.QPainter(self.wheel_pixmap)
        painter.setPen(QtCore.Qt.lightGray)
        painter.setBrush(QtCore.Qt.lightGray)
        start = 0
        end = start + self.spacing
        while (end < self.wheel_pixmap.height()):
            painter.drawRect(2, start, self.wheel_pixmap.width()-4, self.spacing - 3)
            start = end
            end += self.spacing


#
# Testing
#
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    vwheel = QVWheel()
    vwheel.setRange([0.0, 6000.0, 0.01, 0.1])
    vwheel.setPosition(0.0)
    vwheel.show()
    sys.exit(app.exec_())

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

