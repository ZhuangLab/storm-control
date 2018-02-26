#!/usr/bin/python
#
## @file
#
# A utility for creating image mosaics and imaging array tomography type samples.
#
# Hazen 07/15
#

import os
import sys
import re
from PyQt5 import QtCore, QtGui, QtWidgets

# Debugging
import storm_control.sc_library.hdebug as hdebug

# UIs.
import storm_control.steve.qtdesigner.steve_ui as steveUi
import storm_control.hal4000.qtWidgets.qtRangeSlider as qtRangeSlider
import storm_control.steve.qtRegexFileDialog as qtRegexFileDialog
 
# Graphics
import storm_control.steve.mosaicView as mosaicView
import storm_control.steve.objectives as objectives
import storm_control.steve.positions as positions
import storm_control.steve.sections as sections

# Communications
import storm_control.steve.capture as capture

# Misc
import storm_control.steve.coord as coord
import storm_control.sc_library.parameters as params

## Window
#
# The main window of the Steve program.
#
class Window(QtWidgets.QMainWindow):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object, default is None.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)

        # Coordinate system setup, the internal scale is 1 pixel is 100nm.
        coord.Point.pixels_to_um = 0.1

        # variables
        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.debug = parameters.get("debug")
        self.file_filter = "\S+.dax"
        self.parameters = parameters
        self.picture_queue = []
        self.regexp_str = ""
        self.requested_stage_pos = False
        self.settings = QtCore.QSettings("storm-control", "steve")
        self.snapshot_directory = self.parameters.get("directory")
        self.spin_boxes = []
        self.stage_tracking_timer = QtCore.QTimer(self)
        self.taking_pictures = False
        
        self.stage_tracking_timer.setInterval(500)

        # ui setup
        self.ui = steveUi.Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(self.settings.value("position", self.pos()))
        self.resize(self.settings.value("size", self.size()))

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

        # Create a validator for scaleLineEdit.
        self.scale_validator = QtGui.QDoubleValidator(1.0e-6, 1.0e+6, 6, self.ui.scaleLineEdit)
        self.ui.scaleLineEdit.setValidator(self.scale_validator)

        # Initialize view.
        self.view = mosaicView.MosaicView(parameters, self.ui.mosaicFrame)
        layout = QtWidgets.QGridLayout(self.ui.mosaicFrame)
        layout.addWidget(self.view)
        self.ui.mosaicFrame.setLayout(layout)
        self.view.show()

        # Initialize positions list.
        self.positions = positions.Positions(parameters,
                                             self.view.getScene(),
                                             self.ui.positionsFrame)
        layout = QtWidgets.QGridLayout(self.ui.positionsFrame)
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
        self.ui.actionAdjust_Contrast.triggered.connect(self.handleAdjustContrast)
        self.ui.actionDelete_Images.triggered.connect(self.handleDeleteImages)
        self.ui.actionLoad_Movie.triggered.connect(self.handleLoadMovie)
        self.ui.actionLoad_Mosaic.triggered.connect(self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.ui.actionSave_Mosaic.triggered.connect(self.handleSaveMosaic)
        self.ui.actionSave_Positions.triggered.connect(self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleSnapshot)
        self.ui.actionSet_Working_Directory.triggered.connect(self.handleSetWorkingDirectory)
        self.ui.foregroundOpacitySlider.valueChanged.connect(self.handleOpacityChange)
        self.ui.getStagePosButton.clicked.connect(self.handleGetStagePosButton)
        self.ui.imageGridButton.clicked.connect(self.handleImageGrid)
        self.ui.scaleLineEdit.textEdited.connect(self.handleScaleChange)
        self.ui.tabWidget.currentChanged.connect(self.handleTabChange)
        self.ui.trackStageCheckBox.stateChanged.connect(self.handleTrackStage)
        self.ui.xSpinBox.valueChanged.connect(self.handleGridChange)
        self.ui.ySpinBox.valueChanged.connect(self.handleGridChange)

        self.stage_tracking_timer.timeout.connect(self.handleStageTrackingTimer)

        self.view.addPosition.connect(self.addPositions)
        self.view.addSection.connect(self.addSection)
        self.view.getObjective.connect(self.handleGetObjective)
        self.view.gotoPosition.connect(self.gotoPosition)
        self.view.mouseMove.connect(self.updateMosaicLabel)
        self.view.scaleChange.connect(self.updateScaleLineEdit)
        self.view.takePictures.connect(self.takePictures)

        self.sections.addPositions.connect(self.addPositions)
        self.sections.takePictures.connect(self.takePictures)

        self.comm.captureComplete.connect(self.addImage)
        self.comm.changeObjective.connect(self.handleChangeObjective)
        self.comm.disconnected.connect(self.handleDisconnected)
        self.comm.getPositionComplete.connect(self.handleGetPositionComplete)
        self.comm.newObjectiveData.connect(self.handleNewObjectiveData)
        self.comm.otherComplete.connect(self.handleOtherComplete)

        self.ui.objectivesGroupBox.valueChanged.connect(self.handleMOValueChange)
        
        # Try and get settings from HAL.
        self.comm.commConnect()
        self.comm.getSettings()
        
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

        objective = image.parameters.get("mosaic." + image.parameters.get("mosaic.objective")).split(",")[0]
        [um_per_pixel, x_offset, y_offset] = self.ui.objectivesGroupBox.getData(objective)
        magnification = coord.Point.pixels_to_um / um_per_pixel
        self.current_offset = coord.Point(x_offset, y_offset, "um")
        self.view.addImage(image, objective, magnification, self.current_offset)
        self.view.setCrosshairPosition(image.x_pix, image.y_pix)
        if (len(self.picture_queue) > 0):
            next_item = self.picture_queue[0]
            if (type(next_item) == type(coord.Point(0,0,"um"))):
                self.setCenter(next_item)
                next_x_um = self.current_center.x_um
                next_y_um = self.current_center.y_um
            else:
                [tx, ty] = next_item
                next_x_um = self.current_center.x_um + 0.95 * float(image.width) * coord.Point.pixels_to_um * tx / magnification
                next_y_um = self.current_center.y_um + 0.95 * float(image.height) * coord.Point.pixels_to_um * ty / magnification
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
        self.settings.setValue("position", self.pos())
        self.settings.setValue("size", self.size())

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
            self.loadMovie(filenames)
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

    ## handleAdjustContrast
    #
    # Handles a request to adjust the contrast of all imageItems.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleAdjustContrast(self, boolean):
        # Determine the current contrast
        current_contrast = self.view.getContrast()
        print("Current Contrast: " + str(current_contrast))
        if current_contrast[0] is None:
            current_contrast = [0, 16000] # Default values for HAL: FIXME
 
        # Prepare and display dialog
        dialog = qtRangeSlider.QRangeSliderDialog(self,
                                                  "Adjust Contrast",
                                                  slider_range = [0, 65000,1],
                                                  values = current_contrast)

        if dialog.exec_():
            newRange = dialog.getValues() # Get values
            print("Adjusted Contrast: " + str(newRange))
            self.view.changeContrast(newRange)
        else:
            return

    ## handleChangeObjective
    #
    # Handles the objective change signal from capture.
    #
    # @param objective The name of the objective.
    #
    @hdebug.debug
    def handleChangeObjective(self, objective):
        self.ui.objectivesGroupBox.changeObjective(objective)
        [magnification, x_offset, y_offset] = self.ui.objectivesGroupBox.getData(objective)
        self.current_offset = coord.Point(x_offset, y_offset, "um")

    ## handleDeleteImages
    #
    # Handles the delete images action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleDeleteImages(self, boolean):
        reply = QtWidgets.QMessageBox.question(self,
                                               "Warning!",
                                               "Delete Images?",
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if (reply == QtWidgets.QMessageBox.Yes):
            self.view.clearMosaic()

    ## handleDisconnected
    #
    # Handles the disconnected signal from the capture.Capture object.
    #
    @hdebug.debug
    def handleDisconnected(self):
        self.toggleTakingPicturesStatus(False)

    ## handleGetObjective
    #
    @hdebug.debug
    def handleGetObjective(self):
        self.comm.commConnect()
        self.comm.getObjective()
        
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

    ## handleLoadMosaic
    #
    # Handles a user request to load a mosaic.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadMosaic(self, boolean):
        mosaic_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                "Load Mosaic",
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]
        self.loadMosaic(mosaic_filename)

    ## handleLoadMovie
    #
    # Handles user request to load movie files.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadMovie(self, boolean):
        # Open custom dialog to select files and frame number
        [filenames, frame_num, file_filter] = qtRegexFileDialog.regexGetFileNames(directory = self.parameters.get("directory"),
                                                                                  regex = self.regexp_str,
                                                                                  extensions = ["*.dax", "*.tif", "*.spe"])
        if (filenames is not None) and (len(filenames) > 0):
            print("Found " + str(len(filenames)) + " files matching " + str(file_filter) + " in " + os.path.dirname(filenames[0]))
            print("Loading frame: " + str(frame_num))

            # Save regexp string for next time the dialog is opened
            self.regexp_str = file_filter
                
            # Load dax
            self.loadMovie(filenames, frame_num)

    ## handleLoadPositions
    #
    # Handles the load positions action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleLoadPositions(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.parameters.get("directory"),
                                                                   "*.txt")[0]
        if positions_filename:
            self.positions.loadPositions(positions_filename)

    ## handleMOValueChange
    #
    # Handles the moValueChange signal from the magnification and offset spin boxes.
    #
    # @param objective The objective associated with the spin box that was changed.
    # @param pname The box type of the spin box that was changed.
    # @param value The new value of the spin box that was changed.
    #
    @hdebug.debug
    def handleMOValueChange(self, objective, pname, value):
        if (pname == "micron_per_pixel"):
            self.view.changeMagnification(coord.Point.pixels_to_um / value)
        elif (pname == "xoffset"):
            self.view.changeXOffset(objective, coord.umToPix(value))
        elif (pname == "yoffset"):
            self.view.changeYOffset(objective, coord.umToPix(value))
            
    ## handleNewObjectiveData
    #
    # Handles adding a new objective to the list of available objectives.
    #
    # @param data An array containing the description and information for the new objective.
    #
    @hdebug.debug
    def handleNewObjectiveData(self, data):
        self.ui.objectivesGroupBox.addObjective(data)
        
    ## handleOpacityChange
    #
    # Handles the valueChanged signal from the foreground opacity slider.
    #
    # @param value The current value of the slider.
    #
    @hdebug.debug
    def handleOpacityChange(self, value):
        self.sections.changeOpacity(0.01*float(value))
        
    ## handleOtherComplete
    #
    @hdebug.debug
    def handleOtherComplete(self):
        self.comm.commDisconnect()

    ## handleSavePositions
    #
    # Handles the save positions action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSavePositions(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.parameters.get("directory"), 
                                                                   "*.txt")[0]
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
        mosaic_filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save Mosaic", 
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]
        if mosaic_filename:
            with open(mosaic_filename, "w") as mosaic_fileptr:
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
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.get("directory")),
                                                               QtWidgets.QFileDialog.ShowDirsOnly)
        if directory:
            self.parameters.set("directory", directory + os.path.sep)
            self.snapshot_directory = directory + os.path.sep

    ## handleSnapshot
    #
    # Handles the save snap shot action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSnapshot(self, boolean):
        snapshot_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.snapshot_directory, 
                                                                  "*.png")[0]
        if snapshot_filename:
            pixmap = self.view.grab()
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
                if not line:
                    break

                # Deal with '\r\n'. Maybe we should not be saving files with this
                # on the end of the line? We were doing it so that they displayed
                # properly in notepad.
                #
                if (len(line) == 1):
                    continue
                number_lines += 1
            mosaic_fp.seek(0)

            # Create progress bar
            progress_bar = QtWidgets.QProgressDialog("Load Files...",
                                                     "Abort Load",
                                                     0,
                                                     number_lines,
                                                     self)
            progress_bar.setWindowModality(QtCore.Qt.WindowModal)

            mosaic_dirname = os.path.dirname(mosaic_filename)
            file_number = 1
            while 1:
                if progress_bar.wasCanceled(): break
                line = mosaic_fp.readline()
                if not line:
                    break
                if (len(line) == 1):
                    continue
                
                data = line.rstrip().split(",")
                if (self.view.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                elif (self.positions.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                elif (self.sections.loadFromMosaicFileData(data, mosaic_dirname)):
                    legacy_format = False
                else:
                    print("Unrecognized scene element:", data[0])
                
                progress_bar.setValue(file_number)
                file_number += 1

            progress_bar.close()
            mosaic_fp.close()

            if legacy_format:
                # load older data formats here..
                pass

    ## loadMovie
    #
    # Handles loading movie files, which can be useful for retrospective analysis.
    #
    # @param filenames A list of file names.
    # @param frame_num The frame number to load. Starts at 0. Default is 0.
    #
    @hdebug.debug
    def loadMovie(self, filenames, frame_num = 0):
        
        # Create progress bar.
        progress_bar = QtWidgets.QProgressDialog("Loading " + str(len(filenames)) +  " Files ...",
                                                 "Abort Load",
                                                 0,
                                                 len(filenames),
                                                 self)
        progress_bar.setWindowTitle("Dax Load Progress")
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)
        file_number = 1
        
        # Load movies.
        self.comm.fake_got_settings = False
        for filename in filenames:
            if progress_bar.wasCanceled(): break
            self.comm.loadImage(filename, frame_num)
            progress_bar.setValue(file_number)
            file_number += 1

        # Close progress bar.
        progress_bar.close()

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
            self.comm.setDirectory(self.parameters.get("directory"))
            if not self.comm.captureStart(self.current_center.x_um, self.current_center.y_um):
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
    app = QtWidgets.QApplication(sys.argv)

    # Load settings.
    if (len(sys.argv)==2):
        parameters = params.parameters(sys.argv[1])
    else:
        parameters = params.parameters("settings_default.xml")

    # Start logger.
    hdebug.startLogging(parameters.get("directory") + "logs/", "steve")

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
