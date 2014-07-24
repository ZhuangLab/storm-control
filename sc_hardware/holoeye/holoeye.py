#!/usr/bin/env python
#
## @file
#
# GUI for control of Holoeye SLM.
#
# Hazen 07/14
#

import sys

from PyQt4 import QtCore, QtGui

import sc_library.parameters as parameters
import sc_hardware.holoeye.holoeyeSLM as holoeyeSLM

import sc_hardware.holoeye.holoeye_ui as holoeyeUi

## HoloeyeDialog
#
# The GUI for controlling what is displayed on the Holoeye.
#
class HoloeyeDialog(QtGui.QDialog):

    ## __init__
    #
    # @param parent (Optional) default is none.
    #
    def __init__(self, hardware, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.grayscale_only = hardware.get("grayscale_only", True)
        self.screen_id = hardware.get("screen_id", -1)
        self.slm = holoeyeSLM.HoloeyeSLM(self)

        # UI setup.
        self.ui = holoeyeUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.patternComboBox.addItems(["Black",
                                          "Grey",
                                          "White",
                                          "Stripes"])

        # Connect signals.
        if parent is not None:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.hide)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.close)
        self.ui.patternComboBox.currentIndexChanged.connect(self.handlePattern)
        self.ui.thumbnailWidget.changeScreen.connect(self.handleChangeScreen)
        self.ui.thumbnailWidget.newImage.connect(self.handleNewImage)
        self.slm.grabbedScreen.connect(self.handleGrabScreen)
        self.slm.rightSize.connect(self.ui.thumbnailWidget.setRightSize)

        if (self.screen_id >= 0):
            self.slm.grabScreen(self.screen_id)

        self.ui.thumbnailWidget.setNumScreens(self.slm.getNumScreens())

    ## handleChangeScreen
    #
    # @param screen_id The id of the screen to change to.
    #
    def handleChangeScreen(self, screen_id):
        self.slm.grabScreen(screen_id)
    
    ## handleGrabScreen
    #
    # @param screen_id The id of the screen that was grabbed.
    #
    def handleGrabScreen(self, screen_id):
        if (screen_id >= 0):
            screen_size = self.slm.getScreenSize(screen_id)
            self.ui.screenLabel.setText("Displaying on screen " + str(screen_id + 1) + " (" + str(screen_size[0]) + " x " + str(screen_size[1]) + ")")
            self.ui.thumbnailWidget.setScreenSize(screen_size)
        else:
            self.ui.screenLabel.setText("Not displayed")
        
        # Reset to black.
        self.ui.patternComboBox.setCurrentIndex(0)

    ## handlePattern
    #
    # @param id The id of the pattern.
    #
    def handlePattern(self, id):

        screen_size = self.slm.getScreenSize()
        image = QtGui.QImage(screen_size[0], screen_size[1], QtGui.QImage.Format_RGB32)
        painter = QtGui.QPainter(image)

        # Black
        if (id == 0):
            painter.setPen(QtGui.QColor(0, 0, 0))
            painter.setBrush(QtGui.QColor(0, 0, 0))
            painter.drawRect(0, 0, image.width(), image.height())

        # Grey
        elif (id == 1):
            painter.setPen(QtGui.QColor(128, 128, 128))
            painter.setBrush(QtGui.QColor(128, 128, 128))
            painter.drawRect(0, 0, image.width(), image.height())

        # White
        elif (id == 2):
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setBrush(QtGui.QColor(255, 255, 255))
            painter.drawRect(0, 0, image.width(), image.height())

        # (Vertical) stripes
        elif (id == 3):
            n_stripes = 5
            inc = image.width()/n_stripes
            for i in range(n_stripes):
                if ((i%2)==0):
                    painter.setPen(QtGui.QColor(0, 0, 0))
                    painter.setBrush(QtGui.QColor(0, 0, 0))
                else:
                    painter.setPen(QtGui.QColor(255, 255, 255))
                    painter.setBrush(QtGui.QColor(255, 255, 255))
                painter.drawRect(i*inc, 0, inc, image.height())
                
        painter.end()
        self.setImage(image)

    ## handleNewImage
    #
    # @param q_image A QImage.
    #
    def handleNewImage(self, q_image):
        if q_image is None:
            QtGui.QMessageBox.information(self,
                                          "Warning!",
                                          "Image type not recognized")
        else:
            if self.grayscale_only:
                if not q_image.isGrayscale():
                    for i in range(q_image.width()):
                        for j in range(q_image.height()):
                            gray = QtGui.qGray(q_image.pixel(i,j))
                            q_image.setPixel(i,j, QtGui.qRgb(gray, gray, gray))
                        if (i > 0) and ((i%10) == 0):
                            self.setImage(q_image)
                            QtGui.QApplication.processEvents()
            self.setImage(q_image)

    ## setImage
    #
    # @param q_image A QImage to pass to the SLM and the thumbnail.
    #
    def setImage(self, q_image):
        self.slm.setImage(q_image)
        self.ui.thumbnailWidget.setImage(q_image)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    if (len(sys.argv) == 2):
        hardware = parameters.Parameters(sys.argv[1])
    else:
        hardware = parameters.Parameters("settings.xml")

    dialog = HoloeyeDialog(hardware)
    dialog.show()
    sys.exit(app.exec_())

