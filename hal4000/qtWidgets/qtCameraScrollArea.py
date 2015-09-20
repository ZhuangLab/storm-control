#!/usr/bin/python
#
## @file
#
# Specialized QScollArea
#

from PyQt4 import QtCore, QtGui


## QCameraScollArea
#
# A slightly specialized QScrollArea. This scroll area lets the user 
# zoom in and pan around the images from the camera.
#
class QCameraScrollArea(QtGui.QScrollArea):

    ## __init__
    #
    # Create a camera scroll area object.
    #
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, parent = None):
        QtGui.QScrollArea.__init__(self, parent)

        self.camera_widget = None
        self.magnification = 1

        self.h_scroll_bar = QCameraScrollBar(self.horizontalScrollBar())
        self.v_scroll_bar = QCameraScrollBar(self.verticalScrollBar())

    ## setWidget
    #
    # Sets the widget that will be displayed in the scroll area.
    #
    # @param camera_widget A xCameraWidget object.
    #
    def setWidget(self, camera_widget):
        QtGui.QScrollArea.setWidget(self, camera_widget)
        self.camera_widget = camera_widget

    ## wheelEvent
    #
    # Handles mouse wheel events.
    #
    # @param event A PyQt wheel event object.
    #
    def wheelEvent(self, event):
        if (event.delta() > 0):
            self.magnification += 1
        else:
            self.magnification -= 1

        if (self.magnification < 1):
            self.magnification = 1
        if (self.magnification > 8):
            self.magnification = 8
    
        [ev_x, ev_y] = self.camera_widget.getEventLocation(event)
        self.h_scroll_bar.setCurRatio(ev_x)
        self.v_scroll_bar.setCurRatio(ev_y)
        self.camera_widget.setMagnification(self.magnification)

        
## QCameraScrollBar
#
# Wrap a scroll bar so that the camera display remains more 
# or less centered on the wheel events as we zoom in and out.
#
class QCameraScrollBar():

    ## __init__
    #
    # Create a camera scroll bar object.
    #
    # @param scroll_bar A PyQt scroll bar object.
    #
    def __init__(self, scroll_bar):

        self.cur_ratio = 0.5
        self.scroll_bar = scroll_bar

        self.scroll_bar.rangeChanged.connect(self.rangeChanged)

    ## rangeChanged
    #
    # Handle scroll bar range changes.
    #
    # @param new_min The new minimum value for the scroll bar.
    # @param new_max The new maximum value for the scroll bar.
    #
    def rangeChanged(self, new_min, new_max):
        if (new_max > 0):
            self.scroll_bar.setValue(int(self.cur_ratio * float(new_max)))

    ## setCurRatio
    #
    # @param new_ratio The new ratio (or center position) for the scroll bar.
    #
    def setCurRatio(self, new_ratio):
        self.cur_ratio = new_ratio


#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
