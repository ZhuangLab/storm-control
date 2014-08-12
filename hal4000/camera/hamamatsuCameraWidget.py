#!/usr/bin/python
#
## @file
#
# A qtCameraWidget specialized for displaying the data from a Hamamatsu camera.
#
# Hazen 10/13
#

import numpy
from PyQt4 import QtCore, QtGui

import qtWidgets.qtCameraWidget as qtCameraWidget

import sc_hardware.hamamatsu.scmos_image_manipulation_c as scmos_im

## ACameraWidget
#
# Hamamatsu camera widget. This is used to display the frames
# from a Hamamatsu camera.
#
class ACameraWidget(qtCameraWidget.QCameraWidget):

    ## __init__
    #
    # Create a Hamamatsu camera widget.
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, parameters, parent = None):
        qtCameraWidget.QCameraWidget.__init__(self, parameters, parent)

    ## updateImageWithFrame
    #
    # This updates the displayed image with a frame from the camera. This
    # version uses a C helper library to try and make things faster and
    # less memory intensive so that we can more easily keep up with the
    # high data rate of a sCMOS camera.
    #
    # FIXME: Ignores image orientation settings.
    #
    # @param frame A frame object.
    #
    def updateImageWithFrame(self, frame):
        if frame:
            w = frame.image_x
            h = frame.image_y
            image_data = frame.getData()
            image_data = image_data.reshape((h,w))

            # Use C library to scale image & also determine image min & max.
            [temp, self.image_min, self.image_max] = scmos_im.rescaleImage(image_data,
                                                                           self.display_range)

            # Create QImage & draw at final magnification.
            temp_image = QtGui.QImage(temp.data, w, h, QtGui.QImage.Format_Indexed8)
            self.image = temp_image.scaled(self.x_final, self.y_final)
            self.image.ndarray = temp

            # Set the images color table.
            self.setColorTable()
            self.update()

            if self.show_info:
                x_loc = self.x_click
                y_loc = self.y_click
                value = 0
                if ((x_loc >= 0) and (x_loc < w) and (y_loc >= 0) and (y_loc < h)):
                    value = image_data[y_loc, x_loc]
                    self.intensityInfo.emit(x_loc, y_loc, value)

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
