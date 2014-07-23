#!/usr/bin/env python
#
## @file
#
# The HoloeyeThumbnail class.
#
# Hazen 07/14
#

from PyQt4 import QtCore, QtGui

## HoloeyeThumbnail
#
# This is used to show a reduced version of what is being shown
# on the Holoeye device.
#
class HoloeyeThumbnail(QtGui.QWidget):

    ## __init__
    #
    # @param parent The parent widget of this dialog.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.image = None

    ## paintEvent
    #
    # @param event A QPaintEvent.
    #
    def paintEvent(self, event):

        # Clear old image.
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor(0, 0, 0))
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw new image.
        if self.image is not None:
            pass

