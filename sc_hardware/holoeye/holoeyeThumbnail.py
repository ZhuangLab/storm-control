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
    changeScreen = QtCore.pyqtSignal(int)
    newImage = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parent The parent widget of this dialog.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.num_screens = 0
        self.q_image = None
        self.right_size = True

        self.setAcceptDrops(True)
        self.setToolTip("Drag and drop an image.\nClick and press a number to change the SLM screen.")

    ## dragEnterEvent
    #
    # @param event A QEvent object.
    #
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    ## dropEvent
    #
    # @param event A QEvent object containing the filenames.
    #
    def dropEvent(self, event):
        q_image = QtGui.QImage(event.mimeData().urls()[-1].toLocalFile())
        if q_image.isNull():
            self.newImage.emit(None)
        else:
            self.newImage.emit(q_image)

    ## keyPressEvent
    #
    # @param event A QKeyEvent.
    #
    def keyPressEvent(self, event):
        keys = []
        for i in range(self.num_screens):
            keys.append(getattr(QtCore.Qt, "Key_" + str(i)))

        for i, key in enumerate(keys):
            if (event.key() == key):
                self.changeScreen.emit(i)

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
            if not self.right_size:
                painter.setPen(QtGui.QColor(255, 0, 0))
                painter.setBrush(QtGui.QColor(255, 0, 0))
                painter.drawRect(0, 0, self.width(), self.height())
            painter.drawImage(1, 1, self.q_image)

    ## setImage
    #
    # @param q_image The image to display.
    #
    def setImage(self, q_image):
        self.q_image = q_image.scaled(self.width()-2, self.height()-2)
        self.update()

    ## setNumScreens
    #
    # @param num_screens The number of screens.
    #
    def setNumScreens(self, num_screens):
        self.num_screens = num_screens

    ## setRightSize
    #
    # @param right_size True/False if the current image matches the SLM.
    #
    def setRightSize(self, right_size):
        self.right_size = right_size

    ## setScreenSize
    #
    # Resizes the widget so that it has the right aspect ratio.
    #
    # @param s_size [width, height]
    #
    def setScreenSize(self, s_size):
        width = int(float(s_size[0])/float(s_size[1]) * (self.height()-2)) + 2
        self.setFixedWidth(width)

