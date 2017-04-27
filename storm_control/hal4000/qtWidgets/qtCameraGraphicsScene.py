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
    """
    The idea is to display the image as it would appear on the 
    chip, so 0,0 is corner of the camera chip. 

    If the image is a sub-section then it should be rendered 
    with the appropriate x,y offset from 0,0.

    If the image is binned then the rendered image needs to be
    up-sampled appropriately to compensate for the binning.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.chip_size_changed = False
        self.chip_x = 0
        self.chip_y = 0
        self.click_x = 0
        self.click_y = 0
        self.colortable = None
        self.display_range = [0, 200]
        self.display_saturated_pixels = False
        self.draw_grid = False
        self.draw_target = False
        self.frame_x_offset = 0
        self.frame_y_offset = 0
        self.image_max = 0
        self.image_min = 0
        self.intensity_info = 0
        self.max_intensity = None
        self.q_image = None
        self.scale_x = 1
        self.scale_y = 1

    def boundingRect(self):
        chip_rect = QtCore.QRectF(0, 0, self.chip_x, self.chip_y)

        # Resize the scene rect if necessary.
        if self.chip_size_changed:
            self.scene().setSceneRect(chip_rect)
            self.chip_size_changed = False
        return chip_rect

    def getAutoScale(self):
        return [self.image_min, self.image_max]

    def getImage(self):
        return self.q_image
    
    def getIntensityInfo(self):
        return [self.click_x, self.click_y, self.intensity_info]
        
    def newColorTable(self, colortable):
        self.colortable = colortable
        if "_sat.ctbl" in colortable:
            self.display_saturated_pixels = True
        else:
            self.display_saturated_pixels = False

    def newConfiguration(self, camera_functionality):
        [chip_x, chip_y] = camera_functionality.getChipSize()
        [self.frame_x_offset, self.frame_y_offset] = camera_functionality.getFrameZeroZero()
        self.max_intensity = camera_functionality.getParameter("max_intensity")
        [self.scale_x, self.scale_y] = camera_functionality.getFrameScale()
        
        # Check if we need to notify the scene of a change in the chip size.
        if (chip_x != self.chip_x) or (chip_y != self.chip_y):
            self.chip_x = chip_x
            self.chip_y = chip_y
            self.chip_size_changed = True
            self.prepareGeometryChange()

    def newRange(self, d_min, d_max):
        self.display_range = [d_min, d_max]

    def paint(self, painter, option, widget):
        if self.q_image is not None:

            # Draw the image.
            painter.drawImage(self.frame_x_offset,
                              self.frame_y_offset,
                              self.q_image)
            
            # Draw the grid into the buffer.
            if self.draw_grid:
                x_step = self.chip_x/8
                y_step = self.chip_y/8
                painter.setPen(QtGui.QColor(255, 255, 255))
                for i in range(7):
                    painter.drawLine((i+1)*x_step, 0, (i+1)*x_step, self.chip_y)
                    painter.drawLine(0, (i+1)*y_step, self.chip_x, (i+1)*y_step)

            # Draw the target into the buffer
            if self.draw_target:
                mid_x = self.chip_x/2 - 20
                mid_y = self.chip_y/2 - 20
                painter.setPen(QtGui.QColor(255, 255, 255))
                painter.drawEllipse(mid_x, mid_y, 40, 40)

    def setClickPos(self, cx, cy):
        self.click_x = cx
        self.click_y = cy

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

    def setShowGrid(self, show):
        self.draw_grid = show
        
    def setShowTarget(self, show):
        self.draw_target = show
        
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
                                                                      False,
                                                                      False,
                                                                      False,
                                                                      self.display_range,
                                                                      max_intensity)
        
        # Create QImage & re-scale to compensate for binning, if any.
        temp_image = QtGui.QImage(temp.data, w, h, QtGui.QImage.Format_Indexed8)
        if (self.scale_x != 1) or (self.scale_y != 1):
            self.q_image = temp_image.scaled(w * self.scale_x, h * self.scale_y)
        else:
            self.q_image = temp_image
        self.q_image.ndarray = temp

        # Set the images color table.
        self.setColorTable()

        # Record the intensity where the user last clicked on the image.
        # self.click_x and self.click_y are in frame coordinates.
        xl = self.click_x
        yl = self.click_y
        if ((xl >= 0) and (xl < w) and (yl >= 0) and (yl < h)):
            self.intensity_info = image_data[yl, xl]
        else:
            self.intensity_info = 0

        # Force re-paint.
        self.update()


class QtCameraGraphicsScene(QtWidgets.QGraphicsScene):
    pass
        
        
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
