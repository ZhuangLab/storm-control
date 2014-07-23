#!/usr/bin/env python
#
## @file
#
# Control of Holoeye SLM, though this could probably be used
# with any device that works in a similar fashion. It takes
# over the display that (hopefully) corresponds to the Holoeye
# and displays full screen gray scale images in that display.
#
# Hazen 07/14
#

from PyQt4 import QtCore, QtGui

## HoloeyeSLM
#
# This uses a full screen dialog to take over a display.
#
class HoloeyeSLM(QtGui.QDialog):

    ## __init__
    #
    # @param parent The parent widget of this dialog.
    #
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.desktop = QtGui.QDesktopWidget()

        QtCore.QTimer.singleShot(0, self.getDisplayData)
        QtCore.QTimer.singleShot(1, self.grabDisplay)

    ## getDisplaySize
    #
    # @param display_id The id of the display to query.
    #
    # @return [width, height] of the display.
    #
    def getDisplaySize(self, display_id):
        drect = self.desktop.screenGeometry(display_id)
        return [drect.width(), drect.height()]

    ## grabDisplay
    #
    # Takes over the requested display.
    #
    # @param display_id (Integer) The id of the display to take over.
    #
    def grabDisplay(self, display_id):
        self.setGeometry(self.desktop.screenGeometry(display_id))
        self.showFullScreen()

    ## mousePressEvent
    #
    # This is useful for recovering when you accidentally grab the
    # wrong display.
    #
    # @param event A QMouseEvent.
    #
    def mousePressEvent(self, event):
        self.close()


