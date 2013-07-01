#!/usr/bin/python
#
# Utility for imaging array tomography samples.
#
# Hazen 02/13
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
import sections

# Communications
import capture

# Misc
import coord
import halLib.parameters as params


# Find the magnification and offsets for the current objective.

def findMO(objective, spin_boxes):
    magnification = 1.0
    x_offset = 0.0
    y_offset = 0.0
    for box in spin_boxes:
        if (box.objective == objective):
            if (box.box_type == "magnification"):
                magnification = box.value()
            elif (box.box_type == "xoffset"):
                x_offset = box.value()
            elif (box.box_type == "yoffset"):
                y_offset = box.value()

    return [magnification, x_offset, y_offset]

#
# Spin boxes that are used to update magnification & offset.
#
class MagOffsetSpinBox(QtGui.QDoubleSpinBox):
    
    moValueChange = QtCore.pyqtSignal(object, object, float)

    def __init__(self, objective, box_type, initial_value, parent = None):
        QtGui.QDoubleSpinBox.__init__(self, parent)

        self.box_type = box_type
        self.objective = objective
        
        if (self.box_type == "magnification"):
            self.setDecimals(2)
            self.setMaximum(200.0)
            self.setMinimum(1.0)
            self.setSingleStep(0.01)
        else:
            self.setMaximum(10000.0)
            self.setMinimum(-10000.0)

        self.setValue(initial_value)

        self.valueChanged.connect(self.handleValueChange)

#    def enableDisable(self, objective):
#        if (objective == self.objective):
#            self.setReadOnly(True)
#        else:
#            self.setReadOnly(False)

    def handleValueChange(self, value):
        self.moValueChange.emit(self.objective, self.box_type, value)


#
# Main window
#
class Window(QtGui.QMainWindow):

    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # coordinate system setup
        coord.Point.pixels_to_um = parameters.pixels_to_um

        # variables
        self.circles = []
        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_magnification = 1.0
        self.current_objective = False
        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.debug = parameters.debug
        self.parameters = parameters
        self.picture_queue = []
        self.rects = []

        # ui setup
        self.ui = steveUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # hide some things that we don't currently use & resize group-box.
        self.ui.backgroundComboBox.hide()
        self.ui.backgroundLabel.hide()
        self.ui.moveAllSectionsCheckBox.hide()
        self.ui.showFeaturesCheckBox.hide()
        self.ui.thresholdLabel.hide()
        self.ui.thresholdSlider.hide()
        self.ui.sectionViewSettingsGroupBox.setMaximumHeight(50)

        self.setWindowIcon(QtGui.QIcon("steve.ico"))

        # Initialize objectives.
        objectives = []
        for i in range(10):
            mag = "mag" + str(i)
            if hasattr(self.parameters, mag):
                data = getattr(self.parameters, mag)
                obj_name = data.split(",")[0]
                objectives.append(data)
                self.ui.magComboBox.addItem(obj_name, data)

        # Create labels and spin boxes for objective settings.
        self.spin_boxes = []
        layout = QtGui.QGridLayout(self.ui.objectivesFrame)

        for i, label_text in enumerate(["Objective", "Magnification", "X Offset", "Y Offset"]):
            text_item = QtGui.QLabel(label_text, self.ui.objectivesFrame)
            layout.addWidget(text_item, 0, i)

        # The first objective is assumed to be the 100x & is not adjustable.
        data = objectives[0].split(",")
        self.current_objective = data[0]
        for j, datum in enumerate(data):
            text_item = QtGui.QLabel(datum, self.ui.objectivesFrame)
            layout.addWidget(text_item, 1, j)

        # The other objectives are adjustable.
        for i, obj in enumerate(objectives[1:]):
            data = obj.split(",")
            text_item = QtGui.QLabel(data[0], self.ui.objectivesFrame)
            layout.addWidget(text_item, i+2, 0)

            for j, btype in enumerate(["magnification", "xoffset", "yoffset"]):
                sbox = MagOffsetSpinBox(data[0], btype, float(data[j+1]))
                layout.addWidget(sbox, i+2, j+1)
                sbox.moValueChange.connect(self.handleMOValueChange)
                self.spin_boxes.append(sbox)

        # Initialize view.
        self.view = mosaicView.MosaicView(parameters, self.ui.mosaicFrame)
        layout = QtGui.QGridLayout(self.ui.mosaicFrame)
        layout.addWidget(self.view)
        self.view.show()

        # Initialize positions list.
        self.positions = positions.Positions(self.ui.positionsFrame)
        layout = QtGui.QGridLayout(self.ui.positionsFrame)
        layout.addWidget(self.positions)
        self.positions.show()

        # Initialize sections.
        self.sections = sections.Sections(self.view,
                                          self.ui.sectionsDisplayFrame,
                                          self.ui.sectionsScrollArea,
                                          self.ui.sectionsTab)

        # Initialize communications.
        self.comm = capture.Capture(parameters)

        # signals
        self.ui.abortButton.clicked.connect(self.handleAbort)
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionConnect.triggered.connect(self.handleConnect)
        self.ui.actionDisconnect.triggered.connect(self.handleDisconnect)
        self.ui.actionClear_Mosaic.triggered.connect(self.handleClearMosaic)
        self.ui.actionLoad_Mosaic.triggered.connect(self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.ui.actionSave_Mosaic.triggered.connect(self.handleSaveMosaic)
        self.ui.actionSave_Positions.triggered.connect(self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleSnapshot)
        self.ui.actionSet_Working_Directory.triggered.connect(self.handleSetWorkingDirectory)
        self.ui.connectRadioButton.toggled.connect(self.handleConnectChange)
        self.ui.foregroundOpacitySlider.valueChanged.connect(self.handleOpacityChange)
        self.ui.magComboBox.currentIndexChanged.connect(self.handleObjectiveChange)
        self.ui.tabWidget.currentChanged.connect(self.handleTabChange)
        self.ui.xSpinBox.valueChanged.connect(self.handleGridChange)
        self.ui.ySpinBox.valueChanged.connect(self.handleGridChange)

        self.view.addPosition.connect(self.addPositions)
        self.view.addSection.connect(self.addSection)
        self.view.gotoPosition.connect(self.gotoPosition)
        self.view.mouseMove.connect(self.updateMosaicLabel)
        self.view.takePictures.connect(self.takePictures)

        self.positions.addPositionSig.connect(self.addPositions)
        self.positions.currentPositionChange.connect(self.handlePositionSelection)
        self.positions.deletePosition.connect(self.handlePositionDelete)

        self.sections.addPositions.connect(self.addPositions)
        self.sections.currentSectionChange.connect(self.handleSectionSelection)
        self.sections.deleteSection.connect(self.handleSectionDelete)
        self.sections.moveSection.connect(self.handleSectionMove)
        self.sections.takePictures.connect(self.takePictures)

        self.comm.captureComplete.connect(self.addImage)

        self.handleObjectiveChange(0)

    def addImage(self, image):
        self.view.addImage(image, self.current_objective, self.current_magnification, self.current_offset)
        if len(self.picture_queue) > 0:
            next_item = self.picture_queue[0]
            if (type(next_item) == type(coord.Point(0,0,"um"))):
                self.setCenter(next_item)
                next_x_um = self.current_center.x_um
                next_y_um = self.current_center.y_um
            else:
                [tx, ty] = next_item
                next_x_um = self.current_center.x_um + 0.95 * float(image.width) * self.parameters.pixels_to_um * tx / self.current_magnification
                next_y_um = self.current_center.y_um + 0.95 * float(image.height) * self.parameters.pixels_to_um * ty / self.current_magnification
            self.picture_queue = self.picture_queue[1:]
            self.comm.captureStart(next_x_um, next_y_um)

    def addPositions(self, points):
        for a_point in points:
            self.rects.append(self.view.addPositionRectangle(a_point))
            self.positions.addPosition(a_point)

    def addSection(self, a_point):
        self.circles.append(self.view.addSectionCircle(a_point))
        self.sections.addSection(a_point)

    @hdebug.debug
    def cleanUp(self):
        pass

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    def gotoPosition(self, point):
        self.comm.gotoPosition(point.x_um - self.current_offset.x_um, point.y_um - self.current_offset.y_um)

    def handleAbort(self):
        self.comm.abort()
        self.picture_queue = []

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
        self.sections.gridChange(self.ui.xSpinBox.value(),
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

    def handleMOValueChange(self, objective, box_type, value):
        if (box_type == "magnification"):
            value = value/100.0
            if (objective == self.current_objective):
                self.current_magnification = value
            self.view.changeMagnification(objective, value)
        elif (box_type == "xoffset"):
            if (objective == self.current_objective):
                self.current_offset = coord.Point(value, self.current_offset.y_um, "um")
            self.view.changeXOffset(objective, coord.umToPix(value))
        elif (box_type == "yoffset"):
            if (objective == self.current_objective):
                self.current_offset = coord.Point(self.current_offset.x_um, value, "um")
            self.view.changeYOffset(objective, coord.umToPix(value))
        else:
            print "unknown box type:", box_type

    def handleObjectiveChange(self, mag_index):
        data = self.ui.magComboBox.itemData(mag_index).toString()
        if data:
            data = data.split(",")
            if (mag_index == 0):
                [mag, x_offset, y_offset] = map(float, data[1:])
            else:
                [mag, x_offset, y_offset] = findMO(data[0], self.spin_boxes)
            mag = mag/100.0
            self.current_objective = data[0]
            self.current_magnification = mag
            self.current_offset = coord.Point(x_offset, y_offset, "um")

    def handleOpacityChange(self, value):
        self.sections.changeOpacity(0.01*float(value))

    def handlePositionDelete(self, index):
        self.view.removeRectangle(self.rects[index])
        del self.rects[index]

    def handlePositionSelection(self, a_point):
        self.view.moveSelectionRectangle(a_point)

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

    def handleSectionDelete(self, index):
        self.view.removeCircle(self.circles[index])
        del self.circles[index]

    def handleSectionMove(self, index, a_point):
        self.view.moveSectionEllipse(self.circles[index], a_point)
        self.view.moveSectionSelection(a_point)
        self.sections.handleSectionChanged()

    def handleSectionSelection(self, a_point):
        self.view.moveSectionSelection(a_point)
        self.sections.handleSectionChanged()

    def handleSetWorkingDirectory(self):
        directory = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.directory),
                                                               QtGui.QFileDialog.ShowDirsOnly))
        if directory:
            self.parameters.directory = directory + "/"
            self.comm.setDirectory(self.parameters.directory)
            print self.parameters.directory

    def handleSnapshot(self):
        snapshot_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.parameters.directory, 
                                                                  "*.png"))
        if snapshot_filename:
            pixmap = QtGui.QPixmap.grabWidget(self.view.viewport())
            pixmap.save(snapshot_filename)

    def handleTabChange(self, value):
        if (value == 0):
            self.ui.mosaicLabel.show()
        else:
            self.ui.mosaicLabel.hide()

    def updateMosaicLabel(self, a_point):
        self.ui.mosaicLabel.setText("{0:.2f}, {1:.2f}".format(a_point.x_um, a_point.y_um))

    def setCenter(self, a_point):
        x_um = a_point.x_um - self.current_offset.x_um
        y_um = a_point.y_um - self.current_offset.y_um
        self.current_center = coord.Point(x_um, y_um, "um")

    def takePictures(self, picture_list):
        point = picture_list[0]
        self.setCenter(point)
        self.picture_queue = picture_list[1:]
        self.comm.captureStart(self.current_center.x_um, 
                               self.current_center.y_um)

    @hdebug.debug
    def quit(self):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")

    # Start logger.
    hdebug.startLogging(parameters.directory + "logs/", "steve")

    # Load app.
    window = Window(parameters)
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
