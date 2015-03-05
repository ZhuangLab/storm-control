#!/usr/bin/env python
#
## @file
#
# Control of Holoeye SLM, though this could probably be used
# with any device that works in a similar fashion. It takes
# over the screen that (hopefully) corresponds to the Holoeye
# and displays full screen images in that display.
#
# Hazen 07/14
#

from PyQt4 import QtCore, QtGui

## HoloeyeSLM
#
# This uses a full screen dialog to take over a display.
#
class HoloeyeSLM(QtGui.QDialog):
    grabbedScreen = QtCore.pyqtSignal(int)
    rightSize = QtCore.pyqtSignal(bool)

    ## __init__
    #
    # @param parent The parent widget of this dialog.
    #
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.desktop = QtGui.QDesktopWidget()
        self.q_image = None
        self.screen_id = None

    ## getScreenSize
    #
    # @param screen_id (Optional) The id of the display to query, default to the current screen.
    #
    # @return [width, height] of the screen.
    #
    def getScreenSize(self, screen_id = None):
        if screen_id is not None:
            drect = self.desktop.screenGeometry(screen_id)
        else:
            drect = self.desktop.screenGeometry(self.screen_id)
        return [drect.width(), drect.height()]

    ## getNumScreens
    #
    # @return The number of screens.
    #
    def getNumScreens(self):
        print "getNumScreens", self.desktop.screenCount()
        return self.desktop.screenCount()

    ## grabScreen
    #
    # Takes over the requested screen.
    #
    # @param screen_id (Integer) The id of the screen to take over.
    #
    def grabScreen(self, screen_id):
        self.screen_id = screen_id
        self.setGeometry(self.desktop.screenGeometry(screen_id))
        self.showFullScreen()
        self.grabbedScreen.emit(screen_id)

    ## mousePressEvent
    #
    # This is useful for recovering when you accidentally grab the
    # wrong display.
    #
    # @param event A QMouseEvent.
    #
    def mousePressEvent(self, event):
        self.hide()
        self.grabbedScreen.emit(-1)

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
        if self.q_image is not None:
            painter.drawImage(0, 0, self.q_image)

    ## setImage
    #
    # @param q_image The image to display.
    #
    def setImage(self, q_image):
        if (q_image.width() == self.width()) and (q_image.height() == self.height()):
            self.rightSize.emit(True)
        else:
            self.rightSize.emit(False)
        self.q_image = q_image.scaled(self.width(), self.height())
        self.update()
