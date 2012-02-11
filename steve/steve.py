#!/usr/bin/python
#
# Utility for imaging array tomography samples.
#
# Hazen 12/09
#

import sys
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.steve_ui as steveUi

# Graphics
import mosaicView
import positions

# Communications
import capture

# Misc
import halLib.parameters as params

#
# Main window
#
class Window(QtGui.QMainWindow):
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # variables
        self.debug = parameters.debug
        self.parameters = parameters
        self.picture_queue = []
        self.rects = []
        self.x_center = 0.0
        self.y_center = 0.0

        # ui setup
        self.ui = steveUi.Ui_MainWindow()
        self.ui.setupUi(self)

        for i in range(10):
            mag = "mag" + str(i)
            if hasattr(self.parameters, mag):
                data = getattr(self.parameters, mag)
                mag = int(data.split(",")[0])
                self.ui.magComboBox.addItem(str(mag)+"X", data)
                                            
#                self.ui.magComboBox.addItem("20X", 0.2)
#                self.ui.magComboBox.addItem("10X", 0.1)

        # initialize view
        self.view = mosaicView.MosaicView(parameters, self.ui.mosaicGroupBox)
        layout = QtGui.QGridLayout(self.ui.mosaicGroupBox)
        layout.addWidget(self.view)
        self.view.show()

        # initialize positions list
        self.positions = positions.Positions(self.ui.positionsFrame)
        layout = QtGui.QGridLayout(self.ui.positionsFrame)
        layout.addWidget(self.positions)
        self.positions.show()

        # initialize communications
        self.comm = capture.Capture(parameters)

        # signals
        self.connect(self.ui.actionQuit, QtCore.SIGNAL("triggered()"), self.quit)
        self.connect(self.ui.actionConnect, QtCore.SIGNAL("triggered()"), self.handleConnect)
        self.connect(self.ui.actionDisconnect, QtCore.SIGNAL("triggered()"), self.handleDisconnect)
        self.connect(self.ui.actionClear_Mosaic, QtCore.SIGNAL("triggered()"), self.handleClearMosaic)
        self.connect(self.ui.actionLoad_Mosaic, QtCore.SIGNAL("triggered()"), self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.connect(self.ui.actionSave_Mosaic, QtCore.SIGNAL("triggered()"), self.handleSaveMosaic)
        self.connect(self.ui.actionSave_Positions, QtCore.SIGNAL("triggered()"), self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleCapture)
        self.connect(self.ui.actionSet_Working_Directory, QtCore.SIGNAL("triggered()"), self.handleSetWorkingDirectory)
        self.connect(self.ui.connectRadioButton, QtCore.SIGNAL("toggled(bool)"), self.handleConnectChange)
        self.connect(self.ui.magComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.handleMagChange)
        self.connect(self.ui.xSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.handleGridChange)
        self.connect(self.ui.ySpinBox, QtCore.SIGNAL("valueChanged(int)"), self.handleGridChange)

        self.connect(self.view, QtCore.SIGNAL("mouseMove(float, float)"), self.updateMosaicLabel)
        self.connect(self.view, QtCore.SIGNAL("takePictures(float, float, PyQt_PyObject)"), self.takePictures)
        self.connect(self.view, QtCore.SIGNAL("addPosition(float, float)"), self.addPosition)
        self.connect(self.view, QtCore.SIGNAL("gotoPosition(float, float)"), self.gotoPosition)

        self.connect(self.positions, QtCore.SIGNAL("currentRowChanged(int)"), self.handleRowChange)
        self.connect(self.positions, QtCore.SIGNAL("deletePosition(int)"), self.handleRowDelete)
        self.connect(self.positions, QtCore.SIGNAL("addPosition(float, float)"), self.addPosition)

        self.connect(self.comm, QtCore.SIGNAL("captureComplete(float, float)"), self.addPixmap)


    def addPixmap(self, x, y):
        pixmap = self.comm.currentPixmap()
        self.view.addPixmap(pixmap, x, y)
        if len(self.picture_queue) > 0:
            [tx, ty] = self.picture_queue[0]
            nx = self.x_center + 0.95 * float(pixmap.width()) * tx * self.parameters.pixels_to_um / self.parameters.magnification
            ny = self.y_center + 0.95 * float(pixmap.height()) * ty * self.parameters.pixels_to_um / self.parameters.magnification
            self.picture_queue = self.picture_queue[1:]
            self.comm.captureStart(nx, ny)

    def addPosition(self, x, y):
        self.rects.append(self.view.addPositionRectangle(x, y))
        self.positions.addPosition(x, y)

    @hdebug.debug
    def cleanUp(self):
        pass

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    def gotoPosition(self, x, y):
        self.comm.gotoPosition(x, y)

    def handleCapture(self):
        snapshot_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.parameters.directory, 
                                                                  "*.png"))
        if snapshot_filename:
            pixmap = QtGui.QPixmap.grabWidget(self.view.viewport())
            pixmap.save(snapshot_filename)

    def handleClearMosaic(self):
        reply = QtGui.QMessageBox.question(self,
                                           "Warning!",
                                           "Clear Mosaic?",
                                           QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.view.clearMosaic()

    def handleConnect(self):
        if not self.ui.connectRadioButton.isChecked():
            self.ui.connectRadioButton.click()

    def handleConnectChange(self, state):
        if state:
            self.comm.commConnect()
        else:
            self.comm.commDisconnect()

    def handleDisconnect(self):
        if self.ui.connectRadioButton.isChecked():
            self.ui.connectRadioButton.click()

    def handleGridChange(self, num):
        self.view.gridChange(self.ui.xSpinBox.value(),
                             self.ui.ySpinBox.value())

    def handleLoadMosaic(self):
        mosaic_filename = str(QtGui.QFileDialog.getOpenFileName(self,
                                                                "Load Mosaic",
                                                                self.parameters.directory,
                                                                "*.msc"))
        if mosaic_filename:
            self.view.loadMosaicFile(mosaic_filename)

    def handleLoadPositions(self):
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.parameters.directory,
                                                                   "*.txt"))
        if positions_filename:
            self.positions.loadPositions(positions_filename)

    def handleMagChange(self, magIndex):
        data = self.ui.magComboBox.itemData(magIndex).toString()
        if data:
            [mag, xoffset, yoffset] = map(float, data.split(","))[1:]
            mag = mag/100.0
            self.parameters.magnification = mag
            self.view.changeMagnification(mag, xoffset, yoffset)

    def handleRowChange(self, row):
        [x, y] = self.positions.getCurrentPosition(row)
        self.view.moveSelectionRectangle(x, y)

    def handleRowDelete(self, index):
        self.view.removeRectangle(self.rects[index])
        del self.rects[index]

    def handleSavePositions(self):
        positions_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.parameters.directory, 
                                                                   "*.txt"))
        if positions_filename:
            self.positions.savePositions(positions_filename)

    def handleSaveMosaic(self):
        mosaic_filename = str(QtGui.QFileDialog.getSaveFileName(self,
                                                                "Save Mosaic", 
                                                                self.parameters.directory,
                                                                "*.msc"))
        if mosaic_filename:
            self.view.saveMosaicFile(mosaic_filename)

    def handleSetWorkingDirectory(self):
        directory = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.directory),
                                                               QtGui.QFileDialog.ShowDirsOnly))
        if directory:
            self.parameters.directory = directory + "/"
            self.comm.setDirectory(self.parameters.directory)
            print self.parameters.directory

    def updateMosaicLabel(self, x, y):
        self.ui.mosaicLabel.setText("{0:.2f}, {1:.2f}".format(x, y))

    def takePictures(self, x, y, positions):
        self.x_center = x
        self.y_center = y
        self.picture_queue = positions
        self.comm.captureStart(x, y)

    @hdebug.debug
    def quit(self):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    window = Window(parameters)
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
