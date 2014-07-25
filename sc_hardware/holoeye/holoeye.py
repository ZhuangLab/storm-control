#!/usr/bin/env python
#
## @file
#
# GUI for control of Holoeye SLM.
#
# Hazen 07/14
#

import numpy
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

        self.ui.periodDoubleSpinBox.hide()
        self.ui.patternComboBox.addItems(["Black",
                                          "Grey",
                                          "White",
                                          "Stripes",
                                          "Grating"])

        # Connect signals.
        if parent is not None:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.hide)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.close)
        self.ui.patternComboBox.currentIndexChanged.connect(self.handlePattern)
        self.ui.periodDoubleSpinBox.valueChanged.connect(self.handlePeriod)
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

        if (id == 0) or (id == 1) or (id == 2):
            self.ui.periodDoubleSpinBox.hide()

            # Black
            if (id == 0):
                image = monochrome(self.slm.getScreenSize(), 0)

            # Grey
            elif (id == 1):
                image = monochrome(self.slm.getScreenSize(), 128)

            # White
            else:
                image = monochrome(self.slm.getScreenSize(), 255)

        # (Vertical) stripes
        elif (id == 3) or (id == 4):
            self.ui.periodDoubleSpinBox.show()
            image = grating(self.slm.getScreenSize(),
                            self.ui.periodDoubleSpinBox.value(), 
                            (True if (id == 3) else False))

        self.setImage(image)

    ## handlePeriod
    #
    # @param period The new value for the period (of the grating).
    #
    def handlePeriod(self, period):
        image = grating(self.slm.getScreenSize(),
                        period,
                        (True if (self.ui.patternComboBox.currentIndex() == 3) else False))
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


## grating
#
# @param screen_size The size of the screen.
# @param period The grating period.
# @param binary True/False.
#
# @return A grating QImage.
#
def grating(screen_size, period, binary):
    xv = numpy.indices((screen_size[1], screen_size[0]))[1]
    sine_xv = 127.5 + 127.5*numpy.sin(xv * 2.0 *  numpy.pi * period)
    numpy_image = numpy.ascontiguousarray(sine_xv, dtype = numpy.uint8)
    
    if binary:
        mask = (numpy_image < 128)
        numpy_image[mask] = 0
        numpy_image[~mask] = 255

    image = QtGui.QImage(numpy_image.data, screen_size[0], screen_size[1], QtGui.QImage.Format_Indexed8)
    image.np_data = numpy_image

    for i in range(256):
        image.setColor(i,QtGui.qRgb(i,i,i))
    return image

## monochrome
#
# @param screen_size The size of the screen.
# @param color The image color.
#
# @return A monochrome QImage.
#
def monochrome(screen_size, color):
    image = QtGui.QImage(screen_size[0], screen_size[1], QtGui.QImage.Format_RGB32)
    painter = QtGui.QPainter(image)
    painter.setPen(QtGui.QColor(color, color, color))
    painter.setBrush(QtGui.QColor(color, color, color))
    painter.drawRect(0, 0, image.width(), image.height())
    painter.end()
    return image


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    if (len(sys.argv) == 2):
        hardware = parameters.Parameters(sys.argv[1])
    else:
        hardware = parameters.Parameters("settings.xml")

    dialog = HoloeyeDialog(hardware)
    dialog.show()
    sys.exit(app.exec_())

