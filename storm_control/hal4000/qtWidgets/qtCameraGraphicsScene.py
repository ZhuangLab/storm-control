#!/usr/bin/env python
"""
A QGraphicsScene and a QGraphicsItem customized for displaying
data from a camera.

Hazen 3/17.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

import numpy

import storm_control.hal4000.halLib.c_image_manipulation_c as c_image


class QtCameraGraphicsItem(QtWidgets.QGraphicsItem):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.colortable = None
        self.display_range = [0, 200]
        self.display_saturated_pixels = False
        self.flip_horizontal = False
        self.flip_vertical = False
        self.image_max = 0
        self.image_min = 0
        self.intensity_info = 0
        self.max_intensity = None
        self.q_image = None
        self.transpose = False
        self.x_click = 0
        self.y_click = 0
        self.x_pixels = 256
        self.y_pixels = 256

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.x_pixels, self.y_pixels)
                             
    def newColorTable(self, colortable):
        self.colortable = colortable

    def newConfiguration(self, configuration):
        self.flip_horizontal = configuration["flip_horizontal"]
        self.flip_vertical = configuration["flip_vertical"]
        self.max_intensity = configuration["max_intensity"]
        self.transpose = configuration["transpose"]
        self.x_size = configuration["x_pixels"]
        self.y_size = configuration["y_pixels"]
        
        if "_sat.ctbl" in configuration["colortable"]:
            self.display_saturated_pixels = True
        else:
            self.display_saturated_pixels = False

    def newRange(self, d_min, d_max):
        self.display_range = [d_min, d_max]

    def paint(self, painter, option, widget):
        if self.q_image is not None:
            painter.drawImage(0, 0, self.q_image)

    def setColorTable(self):
        """
        Sets the color table of the new image. If you don't do this Qt
        will segfault without giving you a traceback or any kind of
        warning message..
        """
        if self.colortable:
            for i in range(256):
                self.q_image.setColor(i, QtGui.qRgb(self.colortable[i][0], 
                                                    self.colortable[i][1], 
                                                    self.colortable[i][2]))
        else:
            for i in range(256):
                self.q_image.setColor(i,QtGui.qRgb(i,i,i))        

    def updateImageWithFrame(self, frame):
        """
        Convert the frame to a QImage, then call update() to display it.
        """
    
        #
        # For reasons lost in the mists of time 'frame' is a 1D numpy array
        # and needs to be reshaped before rescaling and converting to a QImage.
        #
        w = frame.image_x
        h = frame.image_y
        image_data = frame.getData()
        try:
            image_data = image_data.reshape((h,w))
        except ValueError as e:
            print("Got an image with an unexpected size, ", image_data.shape, "expected [", w, ",", h, "]")
            return

        max_intensity = self.max_intensity
        if not self.display_saturated_pixels:
            max_intensity = None

        # Rescale the image & record it's minimum and maximum.        
        [temp, self.image_min, self.image_max] = c_image.rescaleImage(image_data,
                                                                      self.flip_horizontal,
                                                                      self.flip_vertical,
                                                                      self.transpose,
                                                                      self.display_range,
                                                                      max_intensity)
        
        # Create QImage
        if self.transpose:
            self.x_pixels = h
            self.y_pixels = w
            self.q_image = QtGui.QImage(temp.data, h, w, QtGui.QImage.Format_Indexed8)
        else:
            self.x_pixels = w
            self.y_pixels = h
            self.q_image = QtGui.QImage(temp.data, w, h, QtGui.QImage.Format_Indexed8)
        self.q_image.ndarray = temp

        # Set the images color table.
        self.setColorTable()

        # Record the intensity where the user last clicked on the image.
        #
        # FIXME: Need to adjust for image transformation..
        #
        x_loc = self.x_click
        y_loc = self.y_click
        if ((x_loc >= 0) and (x_loc < w) and (y_loc >= 0) and (y_loc < h)):
            self.intensity_info = image_data[y_loc, x_loc]

        self.update(self.boundingRect())


class QtCameraGraphicsScene(QtWidgets.QGraphicsScene):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        
        
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
