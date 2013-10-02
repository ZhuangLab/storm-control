#!/usr/bin/python
#
# Qt Widget for handling the display of camera data.
#
# Hazen 09/13
#

from PyQt4 import QtCore, QtGui
import sys

# Camera widget
class QCameraWidget(QtGui.QWidget):
    intensityInfo = QtCore.pyqtSignal(int, int, int)
    mousePress = QtCore.pyqtSignal(int, int)

    def __init__(self, parameters, parent = None):
        QtGui.QWidget.__init__(self, parent)
        #self.buffer = QtGui.QPixmap(512, 512)
        self.buffer = False
        self.flip_horizontal = parameters.flip_horizontal
        self.flip_vertical = parameters.flip_vertical
        self.image = False
        self.image_min = 0
        self.image_max = 1
        self.live = False

        # This is the amount of image magnification.
        # Only integer values are allowed.
        self.magnification = 1

        self.show_grid = False
        self.show_info = True
        self.show_target = False
 
        # This is the x location of the last mouse click.
        self.x_click = 0

        # This is the x size of the image buffer. Note that
        # these are updated after initialization, when the 
        # widget is properly sized by calling updateSize().
        self.x_final = 10

        # This is the x size of the current camera AOI
        # (divided by binning) in pixels.
        self.x_size = 0

        # This the (minimum) x size of the widget. The image from 
        # the camera cannot be rendered smaller than this value.
        self.x_view = 10

        # These are the same as for x.
        self.y_click = 0
        self.y_final = 10
        self.y_size = 0
        self.y_view = 10

    # Initialize the buffer.
    def blank(self):
        painter = QtGui.QPainter(self.buffer)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    #
    # "Final" is the size at which to draw the pixmap 
    # that will actually be shown in the window.
    #
    def calcFinalSize(self):

        self.x_final = self.x_view
        self.y_final = self.y_view
        if (self.x_size > self.y_size):
            self.y_final = self.x_view * self.y_size / self.x_size
        elif (self.x_size < self.y_size):
            self.x_final = self.y_view * self.x_size / self.y_size

        self.x_final = self.x_final * self.magnification
        self.y_final = self.y_final * self.magnification

        #
        # Based on the final size, determine the size for a square window. 
        # Set the widget size to this & create a buffer of this size. We'll
        # draw in the buffer first, then copy to the window.
        #
        w_size = self.x_final
        if (self.y_final > self.x_final):
            w_size = self.y_final

        self.setFixedSize(w_size, w_size)
        self.buffer = QtGui.QPixmap(w_size, w_size)

        self.blank()

    def getAutoScale(self):
        margin = int(0.1 * float(self.image_max - self.image_min))
        return [self.image_min - margin, self.image_max + margin]

    #
    # Convert the mouse click location into camera pixels. The xy 
    # coordinates of the event are correctly adjusted for the scroll 
    # bar position, we just need to scale them correctly.
    #
    def mousePressEvent(self, event):
        self.x_click = event.x() * self.x_size / self.x_final
        self.y_click = event.y() * self.y_size / self.y_final

        if (self.x_click >= self.x_size):
            self.x_click = self.x_size - 1
        if (self.y_click >= self.y_size):
            self.y_click = self.y_size - 1

        self.mousePress.emit(self.x_click, self.y_click)

    def newColorTable(self, colortable):
        self.colortable = colortable
        self.setColorTable()
        self.update()

    def newParameters(self, parameters, colortable, display_range):
        self.colortable = colortable
        self.display_range = display_range
        self.live = True
        self.flip_horizontal = parameters.flip_horizontal
        self.flip_vertical = parameters.flip_vertical
        self.x_size = parameters.x_pixels/parameters.x_bin
        self.y_size = parameters.y_pixels/parameters.y_bin

        self.image = QtGui.QImage(self.x_size, self.y_size, QtGui.QImage.Format_Indexed8)
        self.calcFinalSize()
        self.setColorTable()

    def newRange(self, range):
        self.display_range = range

    #
    # self.image is the image from the camera at 1x resolution.
    # self.buffer is where the image (appropriately scaled) is
    #    temporarily re-drawn prior to final display. In theory
    #    this reduces display flickering.
    #
    def paintEvent(self, Event):
        if self.live:
            painter = QtGui.QPainter(self.buffer)

            # Draw current image into the buffer, appropriately scaled.
            painter.drawImage(0, 0, self.image.scaled(self.x_final, self.y_final))

            # Draw the grid into the buffer.
            if self.show_grid:
                x_step = self.width()/8
                y_step = self.height()/8
                painter.setPen(QtGui.QColor(255, 255, 255))
                for i in range(7):
                    painter.drawLine((i+1)*x_step, 0, (i+1)*x_step, self.height())
                    painter.drawLine(0, (i+1)*y_step, self.width(), (i+1)*y_step)

            # Draw the target into the buffer
            if self.show_target:
                mid_x = self.width()/2 - 20
                mid_y = self.height()/2 - 20
                painter.setPen(QtGui.QColor(255, 255, 255))
                painter.drawEllipse(mid_x, mid_y, 40, 40)

            # Transfer the buffer to the screen.
            painter = QtGui.QPainter(self)
            painter.drawPixmap(0, 0, self.buffer)

    def setColorTable(self):
        if self.colortable:
            for i in range(256):
                self.image.setColor(i, QtGui.qRgb(self.colortable[i][0], 
                                                  self.colortable[i][1], 
                                                  self.colortable[i][2]))
        else:
            for i in range(256):
                self.image.setColor(i,QtGui.qRgb(i,i,i))

    def setMagnification(self, new_magnification):
        self.magnification = new_magnification
        self.calcFinalSize()

    def setShowGrid(self, bool):
        if bool:
            self.show_grid = True
        else:
            self.show_grid = False

    def setShowInfo(self, bool):
        if bool:
            self.show_info = True
        else:
            self.show_info = False

    def setShowTarget(self, bool):
        if bool:
            self.show_target = True
        else:
            self.show_target = False

    def updateImageWithFrame(self, frame):
        self.update()
        if self.show_info:
            self.intensityInfo.emit(self.x_click, self.y_click, 0)

    #
    # This is called after initialization to get the correct 
    # default size based on the size of the scroll area as 
    # specified using QtDesigner.
    #
    def updateSize(self):
        self.x_final = self.width()
        self.x_view = self.width()
        self.y_final = self.height()
        self.y_view = self.height()

#    def wheelEvent(self, event):
#        if (event.delta() > 0):
#            self.magnification += 1
#        else:
#            self.magnification -= 1
#        
#        if (self.magnification < 1):
#            self.magnification = 1
#        if (self.magnification > 8):
#            self.magnification = 8
#
#        self.calcFinalSize()


#
# Testing
#

if __name__ == "__main__":
    class Parameters:
        def __init__(self):
            self.x_pixels = 200
            self.y_pixels = 200

    parameters = Parameters()
    app = QtGui.QApplication(sys.argv)
    viewer = QCameraWidget(parameters, [200,400])
    viewer.show()

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
