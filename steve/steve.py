#!/usr/bin/python
#
## @file
#
# A utility for creating image mosaics and imaging array tomography type samples.
#
# Hazen 07/13
#

import os
import sys
import re
from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.steve_ui as steveUi
from qtdesigner.loaddax_dialog_ui import Ui_Dialog as loaddax_dialog

# Graphics
import mosaicView
import positions
import sections

# Communications
import capture

# Misc
import coord
import sc_library.parameters as params

class LoadDaxDialog(QtGui.QDialog, loaddax_dialog):
    ## __init__
    #
    # @param title_text The text of the title of the dialog box
    # @param default_directory The default directory for loading dax
    # @param default_filter The default filter for loading dax
    # @param parent (Optional) The PyQt parent of this object, default is None.
    #
    @hdebug.debug
    def __init__(self, parent = None,
                 title_text = "Load Dax by Pattern",
                 default_directory = "",
                 default_filter = "\S+.dax",
                 ):
        QtGui.QDialog.__init__(self,parent)
        self.setupUi(self)

        # Update window title
        self.setWindowTitle(title_text)

        # Add provided defaults to line edit widgets
        self.directory_line_edit.setText(default_directory)
        self.file_filter_line_edit.setText(default_filter)

        # Connect buttons
        self.new_directory_button.clicked.connect(self.handleNewDirectory)

    ## getValues
    #
    # Return the values of the directory and file filter text boxes
    #
    # @return The directory value
    # @return The file filter value
    @hdebug.debug
    def getValues(self):
        return str(self.directory_line_edit.text()), str(self.file_filter_line_edit.text())

    ## handleNewDirectory
    #
    # Handle request for a new directory
    #
    @hdebug.debug
    def handleNewDirectory(self, boolean):
        directory = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.directory_line_edit.text()),
                                                               QtGui.QFileDialog.ShowDirsOnly))
        if directory:
            self.directory_line_edit.setText(directory)
    

## findMO
#
# Find the magnification and offsets for the current objective.
#
# @param objective The microscope objective (a string).
# @param spin_boxes A list of spin boxes.
#
# @return [magnification, offset in x, offset in y].
#
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

## MagOffsetSpinBox
#
# Spin boxes that are used to update magnification & offset.
#
class MagOffsetSpinBox(QtGui.QDoubleSpinBox):
    
    moValueChange = QtCore.pyqtSignal(object, object, float)

    ## __init__
    #
    # @param objective The objective the spin boxes are associated with.
    # @param box_type What kind of spin box this is, one of "magnification", "xoffset" or "yoffset".
    # @param initial_value The initial value for the spin box.
    # @param parent (Optional) The PyQt parent of the spin box, default is None.
    #
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

    ## handleValueChange
    #
    # Emits the moValueChange signal.
    #
    def handleValueChange(self, value):
        self.moValueChange.emit(self.objective, self.box_type, value)


## Window
#
# The main window of the Steve program.
#
class Window(QtGui.QMainWindow):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object, default is None.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # coordinate system setup
        coord.Point.pixels_to_um = parameters.pixels_to_um

        # variables
        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_magnification = 1.0
        self.current_objective = False
        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.debug = parameters.debug
        self.file_filter = "\S+.dax"
        self.parameters = parameters
        self.picture_queue = []
        self.requested_stage_pos = False
        self.stage_tracking_timer = QtCore.QTimer(self)
        self.taking_pictures = False
        self.snapshot_directory = self.parameters.directory
        self.stage_tracking_timer.setInterval(500)

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

        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent
        self.ui.centralwidget.setAcceptDrops(True)
        
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

        # Create a validator for scaleLineEdit.
        self.sce_validator = QtGui.QDoubleValidator(1.0e-6, 1.0e+6, 6, self.ui.scaleLineEdit)
        self.ui.scaleLineEdit.setValidator(self.sce_validator)

        # Initialize view.
        self.view = mosaicView.MosaicView(parameters, self.ui.mosaicFrame)
        layout = QtGui.QGridLayout(self.ui.mosaicFrame)
        layout.addWidget(self.view)
        self.ui.mosaicFrame.setLayout(layout)
        self.view.show()

        # Initialize positions list.
        self.positions = positions.Positions(parameters,
                                             self.view.getScene(),
                                             self.ui.positionsFrame)
        layout = QtGui.QGridLayout(self.ui.positionsFrame)
        layout.addWidget(self.positions)
        self.ui.positionsFrame.setLayout(layout)
        self.positions.show()

        # Initialize sections.
        self.sections = sections.Sections(parameters,
                                          self.view.getScene(),
                                          self.ui.sectionsDisplayFrame,
                                          self.ui.sectionsScrollArea,
                                          self.ui.sectionsTab)

        # Initialize communications.
        self.comm = capture.Capture(parameters)

        # signals
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionDelete_Images.triggered.connect(self.handleDeleteImages)
        self.ui.actionLoad_Dax.triggered.connect(self.handleLoadDax)
        self.ui.actionLoad_Dax_By_Pattern.triggered.connect(self.handleLoadDaxByPattern)
        self.ui.actionLoad_Mosaic.triggered.connect(self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.ui.actionSave_Mosaic.triggered.connect(self.handleSaveMosaic)
        self.ui.actionSave_Positions.triggered.connect(self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleSnapshot)
        self.ui.actionSet_Working_Directory.triggered.connect(self.handleSetWorkingDirectory)
        self.ui.foregroundOpacitySlider.valueChanged.connect(self.handleOpacityChange)
        self.ui.getStagePosButton.clicked.connect(self.handleGetStagePosButton)
        self.ui.imageGridButton.clicked.connect(self.handleImageGrid)
        self.ui.magComboBox.currentIndexChanged.connect(self.handleObjectiveChange)
        self.ui.scaleLineEdit.textEdited.connect(self.handleScaleChange)
        self.ui.tabWidget.currentChanged.connect(self.handleTabChange)
        self.ui.trackStageCheckBox.stateChanged.connect(self.handleTrackStage)
        self.ui.xSpinBox.valueChanged.connect(self.handleGridChange)
        self.ui.ySpinBox.valueChanged.connect(self.handleGridChange)

        self.stage_tracking_timer.timeout.connect(self.handleStageTrackingTimer)

        self.view.addPosition.connect(self.addPositions)
        self.view.addSection.connect(self.addSection)
        self.view.gotoPosition.connect(self.gotoPosition)
        self.view.mouseMove.connect(self.updateMosaicLabel)
        self.view.scaleChange.connect(self.updateScaleLineEdit)
        self.view.takePictures.connect(self.takePictures)

        self.sections.addPositions.connect(self.addPositions)
        self.sections.takePictures.connect(self.takePictures)

        self.comm.captureComplete.connect(self.addImage)
        self.comm.disconnected.connect(self.handleDisconnected)
        self.comm.getPositionComplete.connect(self.handleGetPositionComplete)
        self.comm.gotoComplete.connect(self.handleGotoComplete)

        self.handleObjectiveChange(0)

    ## addImage
    #
    # Adds a capture.Image object to the graphics scene. Checks self.picture_queue to see if there
    # are more images to take. If there are then this starts taking the next image.
    #
    # @param image The capture.Image object.
    #
    @hdebug.debug
    def addImage(self, image):

        # If image is not an object then we are done.
        if not image:
            self.toggleTakingPicturesStatus(False)
            self.comm.commDisconnect()
            return

        self.view.addImage(image, self.current_objective, self.current_magnification, self.current_offset)
        self.view.setCrosshairPosition(image.x_pix, image.y_pix)
        if (len(self.picture_queue) > 0):
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
        else:
            if self.taking_pictures:
                self.toggleTakingPicturesStatus(False)
                self.comm.commDisconnect()

    ## addPositions
    #
    # @param points An array of coord.Point that specify the positions to add to the list of positions.
    #
    @hdebug.debug
    def addPositions(self, points):
        for a_point in points:
            self.positions.addPosition(a_point)

    ## addSection
    #
    # @param a_point A coord.Point object that specifies the location of the section to add.
    #
    @hdebug.debug
    def addSection(self, a_point):
        self.sections.addSection(a_point)

    ## cleanUp
    #
    # Called at closing, currently does nothing.
    #
    @hdebug.debug
    def cleanUp(self):
        pass

    ## closeEvent
    #
    # Called when the user clicks on the close box in the window.
    #
    # @param event A PyQt close event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    ## dragEnterEvent
    #
    # This is called when a file is dragged into the main window.
    #
    # @param event A QEvent object.
    #
    @hdebug.debug
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    ## dropEvent
    #
    # This is called when a file is dropped on the main window. 
    #
    # @param event A QEvent object containing the filenames.
    #
    @hdebug.debug
    def dropEvent(self, event):
        # Initialize filenames variable
        filenames = []

        # Tranfer urls to filenames
        for url in event.mimeData().urls():
            filenames.append(str(url.toLocalFile()))

        # Sort file names
        filenames = sorted(filenames)

        # Identify first type
        name, firstType = os.path.splitext(filenames[0])

        # Check to see if all types are the same
        sameType = []
        for filename in filenames:
            name, fileType = os.path.splitext(filename)
            sameType.append(fileType == firstType)

        # If not, raise an error and abort load
        if not all(sameType):
            hdebug.logText(" Loaded mixed file types")
            QtGui.QMessageBox.information(self,
                                          "Too many file types",
                                          "")
            return
        
        # Load files
        if (firstType == '.dax'): # Load dax files
            filenameList = QtCore.QStringList() # Convert strings to QStringList
            for filename in filenames:
                filenameList.append(filename)
            self.loadDax(filenameList)
        elif (firstType == '.msc'): # Load mosaics
            for filename in sorted(filenames):
                self.loadMosaic(filename)
        else:
            hdebug.logText(" " + firstType + " is not recognized")
            QtGui.QMessageBox.information(self,
                                          "File type not recognized",
                                          "")                    

    ## gotoPosition
    #
    # Tell HAL to move to the specified position (if self.taking_pictures is False).
    #
    # @param point A coord.Point object specifying where to move to.
    #
    @hdebug.debug
    def gotoPosition(self, point):
        if not self.taking_pictures:
            self.comm.commConnect()
            self.comm.gotoPosition(point.x_um - self.current_offset.x_um, point.y_um - self.current_offset.y_um)

    ## handleDeleteImages
    #
    # Handles the delete images action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleDeleteImages(self, boolean):
        reply = QtGui.QMessageBox.question(self,
                                           "Warning!",
                                           "Delete Images?",
                                           QtGui.QMessageBox.Yes,
                                           QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.view.clearMosaic()

    ## handleDisconnected
    #
    # Handles the disconnected signal from the capture.Capture object.
    #
    @hdebug.debug
    def handleDisconnected(self):
        self.toggleTakingPicturesStatus(False)

    ## handleGetStagePosButton
    #
    # @param dummy Dummy parameter.
    #
    @hdebug.debug
    def handleGetStagePosButton(self, dummy):
        self.requested_stage_pos = True
        self.comm.commConnect()
        self.comm.getPosition()
        
    ## handleGetPositionComplete
    #
    # @param a_point A coord.Point object specifying the current stage location.
    #
    @hdebug.debug
    def handleGetPositionComplete(self, a_point):
        if not self.requested_stage_pos:
            # Update cross hair
            offset_point = coord.Point(a_point.x_um + self.current_offset.x_um,
                                       a_point.y_um + self.current_offset.y_um,
                                       "um")
            self.view.setCrosshairPosition(offset_point.x_pix, offset_point.y_pix)
        else:
            self.requested_stage_pos = False
            self.ui.xStartPosSpinBox.setValue(a_point.x_um)
            self.ui.yStartPosSpinBox.setValue(a_point.y_um)
            self.comm.commDisconnect()

    ## handleGotoComplete
    #
    @hdebug.debug
    def handleGotoComplete(self):
        self.comm.commDisconnect()

    ## handleGridChange
    #
    # Handles a change in the size of the grid of images to take when asked to take a grid of images.
    #
    # @param num Dummy parameter.
    #
    @hdebug.debug
    def handleGridChange(self, num):
        self.view.gridChange(self.ui.xSpinBox.value(),
                             self.ui.ySpinBox.value())
        self.sections.gridChange(self.ui.xSpinBox.value(),
                                 self.ui.ySpinBox.value())

    ## handleImageGrid
    #
    # Handles the press of the Image Grid button.
    #
    # @param num Dummy parameter.
    #
    @hdebug.debug
    def handleImageGrid(self, dummy):
        if not self.taking_pictures:
            # Build position list
            pos_list = mosaicView.createGrid(self.ui.xSpinBox.value(), self.ui.ySpinBox.value())

            # Define first position
            first_pos = coord.Point(self.ui.xStartPosSpinBox.value(),
                                    self.ui.yStartPosSpinBox.value(),
                                    "um")
            pos_list.insert(0,first_pos)

            # Take pictures
            self.takePictures(pos_list)
        else: # Abort button
            self.picture_queue = []
            # addImage will handle reseting the ui and disconnecting comm

    ## handleLoadDax
    #
    # Handles user request to load dax files.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadDax(self, boolean):
        # Open dialog to select files
        dax_filenames = QtGui.QFileDialog.getOpenFileNames(self,
                                                           "Load Dax Files",
                                                           self.parameters.directory,
                                                           "*.dax")
        # Convert to a list of strings
        filenames = [str(f) for f in dax_filenames]

        # Load dax.
        self.loadDax(filenames)

    ## handleLoadDaxByPattern
    #
    # Handles loading dax files via a specified regular expression pattern.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadDaxByPattern(self, boolean):
        # Prepare and display dialog
        dialog = LoadDaxDialog(self,
                               default_directory = self.parameters.directory,
                               default_filter = self.file_filter)
    
        
        if dialog.exec_():
            directory, file_filter = dialog.getValues() # Get values
        else:
            return

        # Update internal record of file filter
        self.file_filter = file_filter
        
        # Check to see if file filter is a valid regular expression
        try:
            re.compile(str(file_filter))
        except re.error:
            QtGui.QMessageBox.warning(self,
                                      "Error",
                                      str(file_filter) + " is not a valid regular expression.")
            return
        
        # Find files matching filter in default directory
        filenames = [directory + f for f in os.listdir(directory) if re.match(str(file_filter), f)]
        
        # Exit if empty
        if not filenames:
            error_string = "No files in " + directory
            error_string += " matched the provided filter: " + str(file_filter)
           
            QtGui.QMessageBox.warning(self,
                                      "Error",
                                      error_string)

            return
        
        else:
            print "Found " + str(len(filenames)) + " files matching " + file_filter + " in " + self.parameters.directory

        # Load dax
        self.loadDax(filenames)
                                         
    ## handleLoadMosaic
    #
    # Handles a user request to load a mosaic.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadMosaic(self, boolean):
        mosaic_filename = str(QtGui.QFileDialog.getOpenFileName(self,
                                                                "Load Mosaic",
                                                                self.parameters.directory,
                                                                "*.msc"))    
        self.loadMosaic(mosaic_filename)
    
    ## handleLoadPositions
    #
    # Handles the load positions action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadPositions(self, boolean):
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.parameters.directory,
                                                                   "*.txt"))
        if positions_filename:
            self.positions.loadPositions(positions_filename)

    ## handleMOValueChange
    #
    # Handles the moValueChange signal from the magnification and offset spin boxes.
    #
    # @param objective The objective associated with the spin box that was changed.
    # @param box_type The box type of the spin box that was changed.
    # @param value The new value of the spin box that was changed.
    #
    @hdebug.debug
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

    ## handleObjectiveChange
    #
    # Handles the currentIndexChanged signal from the combo box that lists the objectives.
    #
    # @param mag_index The index of the newly selected objective.
    #
    @hdebug.debug
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

    ## handleOpacityChange
    #
    # Handles the valueChanged signal from the foreground opacity slider.
    #
    # @param value The current value of the slider.
    #
    @hdebug.debug
    def handleOpacityChange(self, value):
        self.sections.changeOpacity(0.01*float(value))

    ## handleSavePositions
    #
    # Handles the save positions action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSavePositions(self, boolean):
        positions_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.parameters.directory, 
                                                                   "*.txt"))
        if positions_filename:
            self.positions.savePositions(positions_filename)

    ## handleSaveMosaic
    #
    # Handles the save mosaic action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSaveMosaic(self, boolean):
        mosaic_filename = str(QtGui.QFileDialog.getSaveFileName(self,
                                                                "Save Mosaic", 
                                                                self.parameters.directory,
                                                                "*.msc"))
        if mosaic_filename:
            mosaic_fileptr = open(mosaic_filename, "w")
            self.view.saveToMosaicFile(mosaic_fileptr, mosaic_filename)
            self.positions.saveToMosaicFile(mosaic_fileptr, mosaic_filename)
            self.sections.saveToMosaicFile(mosaic_fileptr, mosaic_filename)

    ## handleScaleChange.
    #
    # Handles user editting the display scale.
    #
    # @param new_text The new (text) representation of the desired scale.
    #
    @hdebug.debug
    def handleScaleChange(self, new_text):
        try:
            new_scale = float(new_text)
            if (new_scale <= 0.0):
                new_scale = 1.0e-6
            self.view.setScale(new_scale)
        except:
            pass

    ## handleSetWorkingDirectory
    #
    # Handles changing the current working directory.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSetWorkingDirectory(self, boolean):
        directory = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.directory),
                                                               QtGui.QFileDialog.ShowDirsOnly))
        if directory:
            self.parameters.directory = directory + os.path.sep
            self.snapshot_directory = directory + os.path.sep
            print self.parameters.directory

    ## handleSnapshot
    #
    # Handles the save snap shot action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSnapshot(self, boolean):
        snapshot_filename = str(QtGui.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.snapshot_directory, 
                                                                  "*.png"))
        if snapshot_filename:
            pixmap = QtGui.QPixmap.grabWidget(self.view.viewport())
            pixmap.save(snapshot_filename)

            self.snapshot_directory = os.path.dirname(snapshot_filename)
            

    ## handleStageTrackingTimer
    #
    # Get the current stage position from HAL and update the mosaic.
    #
    @hdebug.debug
    def handleStageTrackingTimer(self):
        if not self.taking_pictures:
            self.comm.commConnect()
            self.comm.getPosition()

    ## handleTabChange
    #
    # When the Mosiac tab is selected this shows the UI element where the current
    # mouse position in microns is displayed. It also makes the section circles visible.
    #
    # When the Sections tab is selected the current mouse position display is hidden
    # along with the section circles.
    #
    # @param value The index of currenty selected tab.
    #
    @hdebug.debug
    def handleTabChange(self, value):
        if (value == 0):
            self.ui.mosaicLabel.show()
            self.sections.setSceneItemsVisible(True)
        else:
            self.ui.mosaicLabel.hide()
            self.sections.setSceneItemsVisible(False)

    ## handleTrackStage
    #
    # Turn on/off (HAL) stage tracking when checked.
    #
    # @param state Current state of the check box.
    #
    @hdebug.debug
    def handleTrackStage(self, state):
        if (state == QtCore.Qt.Checked):
            self.view.showCrosshair(True)
            self.stage_tracking_timer.start()
            self.comm.commConnect()
        else:
            self.view.showCrosshair(False)
            self.stage_tracking_timer.stop()
            self.comm.commDisconnect()

    ## loadDax
    #
    # Handles loading dax files, which can be useful for retrospective analysis.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def loadDax(self, filenames):

        # Create progress bar
        progress_bar = QtGui.QProgressDialog("Loading " + str(len(filenames)) +  " Files ...",
                                             "Abort Load",
                                             0,
                                             len(filenames),
                                             self)
        progress_bar.setWindowTitle("Dax Load Progress")
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)
        file_number = 1
        
        # Load dax files
        for filename in filenames:
            if progress_bar.wasCanceled(): break
            self.comm.loadImage(filename)
            progress_bar.setValue(file_number)
            file_number += 1

        # Close progress bar
        progress_bar.close()
        
    ## loadMosaic
    #
    # Handles the load mosaic action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def loadMosaic(self, mosaic_filename):
        if mosaic_filename:
            legacy_format = True
            dirname = os.path.dirname(mosaic_filename)

            mosaic_fp = open(mosaic_filename, "r")

            # First, figure out file size
            mosaic_fp.readline()
            number_lines = 0
            while 1:
                line = mosaic_fp.readline()
                if not line: break
                number_lines += 1
            mosaic_fp.seek(0)

            # Create progress bar
            progress_bar = QtGui.QProgressDialog("Load Files...",
                                                 "Abort Load",
                                                 0,
                                                 number_lines,
                                                 self)
            progress_bar.setWindowModality(QtCore.Qt.WindowModal)

            mosaic_dirname = os.path.dirname(mosaic_filename)
            file_number = 1
            while 1:
                if progress_bar.wasCanceled(): break
                line = mosaic_fp.readline().rstrip()
                if not line: break
                data = line.split(",")
                if (self.view.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                elif (self.positions.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                elif (self.sections.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                else:
                    print "Unrecognized scene element:", data[0]
                
                progress_bar.setValue(file_number)
                file_number += 1

            progress_bar.close()
            mosaic_fp.close()

            if legacy_format:
                # load older data formats here..
                pass


    ## setCenter
    #
    # Sets the current center (for image acquisition). If an item in the picture_queue is not
    # a coord.Point object then the picture for this item is taken relative to this center
    # position.
    #
    # @param a_point A coord.Point object.
    #
    @hdebug.debug
    def setCenter(self, a_point):
        x_um = a_point.x_um - self.current_offset.x_um
        y_um = a_point.y_um - self.current_offset.y_um
        self.current_center = coord.Point(x_um, y_um, "um")

    ## takePictures
    #
    # Takes pictures at the specified absolute or relative positions.
    #
    # @param picture_list An array of positions to take the pictures at.
    #
    @hdebug.debug
    def takePictures(self, picture_list):
        if self.taking_pictures:
            self.picture_queue = []
        else:
            # Set center point
            point = picture_list[0]
            self.setCenter(point)
            
            # Update tile settings
            pointInUm = point.getUm()
            self.ui.xStartPosSpinBox.setValue(pointInUm[0])
            self.ui.yStartPosSpinBox.setValue(pointInUm[1])
            
            # Set picture queue and start imaging
            self.picture_queue = picture_list[1:]
            self.toggleTakingPicturesStatus(True)
            
            self.comm.commConnect()
            if self.comm.setDirectory(self.parameters.directory):
                self.comm.captureStart(self.current_center.x_um, self.current_center.y_um)
            else:
                self.toggleTakingPicturesStatus(False)
                self.picture_queue = []

    ## toggleTakingPicturesStatus
    #
    # Takes pictures at the specified absolute or relative positions.
    #
    # @param status A boolean determining the imaging status.
    #
    @hdebug.debug
    def toggleTakingPicturesStatus(self, status):
        self.taking_pictures = status
        self.ui.xSpinBox.setEnabled(not status)
        self.ui.ySpinBox.setEnabled(not status)
        self.ui.xStartPosSpinBox.setEnabled(not status)
        self.ui.yStartPosSpinBox.setEnabled(not status)
        self.ui.getStagePosButton.setEnabled(not status)
        if status:
            self.ui.imageGridButton.setText("Abort")
        else:
            self.ui.imageGridButton.setText("Acquire")

    ## updateMosaicLabel
    #
    # Updates the UI element that displays the current mouse position in microns.
    #
    # @param a_point A coord.Point object with current mouse position in microns.
    #
    def updateMosaicLabel(self, a_point):
        offset_point = coord.Point(a_point.x_um - self.current_offset.x_um,
                                   a_point.y_um - self.current_offset.y_um,
                                   "um")
        self.ui.mosaicLabel.setText("{0:.2f}, {1:.2f}".format(offset_point.x_um, offset_point.y_um))

    ## updateScaleLineEdit
    #
    # @param new_value The new value of the scale.
    #
    def updateScaleLineEdit(self, new_value):
        self.ui.scaleLineEdit.setText("{0:.6f}".format(new_value))

    ## quit
    #
    # Handles the quit action, closes the window.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def quit(self, boolean):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # Load settings.
    if (len(sys.argv)==2):
        parameters = params.Parameters(sys.argv[1])
    else:
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
