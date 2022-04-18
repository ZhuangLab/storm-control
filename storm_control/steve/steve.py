#!/usr/bin/env python
"""
A utility for creating image mosaics and imaging array tomography type samples.

Hazen 10/18
"""

import os
import sys
#import re
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.steve.comm as comm
import storm_control.steve.coord as coord
import storm_control.steve.imageCapture as imageCapture
import storm_control.steve.imageItem as imageItem
import storm_control.steve.mosaic as mosaic
import storm_control.steve.positions as positions
import storm_control.steve.qtRegexFileDialog as qtRegexFileDialog
import storm_control.steve.sections as sections
import storm_control.steve.steveItems as steveItems

import storm_control.steve.qtdesigner.steve_ui as steveUi


class Window(QtWidgets.QMainWindow):
    """
    The main window of the Steve program.
    """

    @hdebug.debug
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)

        self.context_actions = []
        self.context_menu = QtWidgets.QMenu(self)
        self.comm = comm.Comm()
        self.item_store = steveItems.SteveItemsStore()
        self.modules = []
        self.parameters = parameters
        self.regexp_str = ""
        self.settings = QtCore.QSettings("storm-control", "steve")
        self.snapshot_directory = self.parameters.get("directory")

        # Set Steve scale, 1 pixel is 0.1 microns.
        coord.Point.pixels_to_um = 0.1
        
        # UI setup
        self.ui = steveUi.Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(self.settings.value("position", self.pos()))
        self.resize(self.settings.value("size", self.size()))
        self.setWindowIcon(QtGui.QIcon("steve.ico"))

        # Create HAL movie/image capture object.
        self.image_capture = imageCapture.MovieCapture(comm = self.comm,
                                                       item_store = self.item_store,
                                                       parameters = parameters)
                
        #
        # Module initializations
        #

        # Mosaic
        #
        # This is the first tab.
        #
        self.mosaic = mosaic.Mosaic(comm = self.comm,
                                    image_capture = self.image_capture,
                                    item_store = self.item_store,
                                    parameters = self.parameters)
        layout = QtWidgets.QVBoxLayout(self.ui.mosaicTab)
        layout.addWidget(self.mosaic)
        layout.setContentsMargins(0,0,0,0)
        self.ui.mosaicTab.setLayout(layout)
        self.modules.append(self.mosaic)

        # Connect mosaic signals.
        self.mosaic.mosaic_view.mosaicViewContextMenuEvent.connect(self.handleMosaicViewContextMenuEvent)
        self.mosaic.mosaic_view.mosaicViewDropEvent.connect(self.handleMosaicViewDropEvent)
        self.mosaic.mosaic_view.mosaicViewKeyPressEvent.connect(self.handleMosaicViewKeyPressEvent)
        self.mosaic.mosaic_view.mosaicViewSelectionChange.connect(self.handleMosaicViewSelectionChange)
        self.mosaic.mosaicRequestPositions.connect(self.handleMosaicPositionRequest)

        # The objectives group box keeps track of the data for each objective. To
        # do this it needs HAL comm access. It also needs the item store so that
        # it can handle moving and resizing the images when the user changes values
        # in the UI.
        self.objectives = self.mosaic.ui.objectivesGroupBox
        self.objectives.postInitialization(comm_object = self.comm,
                                           item_store = self.item_store)

        # The image capture object needs the objectives object.
        self.image_capture.postInitialization(objectives = self.objectives)

        # Configure to use standard image/movie loader.
        movie_loader = imageItem.ImageItemLoaderHAL(objectives = self.objectives)
        self.image_capture.setMovieLoaderTaker(movie_loader = movie_loader,
                                               movie_taker = imageCapture.SingleMovieCapture)
        
        # Positions
        #
        # This is created separately but is contained inside the Mosaic tab.
        #
        self.positions = positions.Positions(item_store = self.item_store,
                                             parameters = self.parameters)
        pos_group_box = self.mosaic.getPositionsGroupBox()
        self.positions.setTitleBar(pos_group_box)
        layout = QtWidgets.QVBoxLayout(pos_group_box)
        layout.addWidget(self.positions)
        layout.setContentsMargins(0,0,0,0)
        pos_group_box.setLayout(layout)
        self.modules.append(self.positions)

        # Sections
        #
        # This is the second tab.
        #
        self.sections = sections.Sections(comm = self.comm,
                                          image_capture = self.image_capture,
                                          item_store = self.item_store,
                                          parameters = self.parameters)
        layout = QtWidgets.QVBoxLayout(self.ui.sectionsTab)
        layout.addWidget(self.sections)
        layout.setContentsMargins(0,0,0,0)
        self.ui.sectionsTab.setLayout(layout)
        self.modules.append(self.sections)

        #
        # UI Signals
        #
        self.ui.tabWidget.currentChanged.connect(self.handleTabChange)

        # File
        self.ui.actionDelete_Images.triggered.connect(self.handleDeleteImages)
        self.ui.actionLoad_Movies.triggered.connect(self.handleLoadMovies)
        self.ui.actionLoad_Mosaic.triggered.connect(self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.ui.actionQuit.triggered.connect(self.handleQuit)
        self.ui.actionSave_Mosaic.triggered.connect(self.handleSaveMosaic)
        self.ui.actionSave_Positions.triggered.connect(self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleSnapshot)
        self.ui.actionSet_Working_Directory.triggered.connect(self.handleSetWorkingDirectory)

        # Mosaic
        self.ui.actionAdjust_Contrast.triggered.connect(self.mosaic.handleAdjustContrast)

        #
        # Context menu initializatoin.
        #
        menu_items = [["Take Picture", self.mosaic.handleTakeMovie],
                      ["Goto Position", self.mosaic.handleGoToPosition],
                      ["Record Position", self.positions.handleRecordPosition],
                      ["Add Section", self.sections.handleAddSection],
                      ["Query Objective", self.objectives.handleGetObjective],
                      ["Remove Last Picture", self.mosaic.handleRemoveLastPicture],
                      ["Extrapolate", self.mosaic.handleExtrapolate]]

        for elt in menu_items:
            action = QtWidgets.QAction(self.tr(elt[0]), self)
            self.context_menu.addAction(action)
            action.triggered.connect(elt[1])
            self.context_actions.append(action)
        
    @hdebug.debug
    def cleanUp(self):
        self.settings.setValue("position", self.pos())
        self.settings.setValue("size", self.size())

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    @hdebug.debug
    def handleDeleteImages(self, boolean):
        reply = QtWidgets.QMessageBox.question(self,
                                               "Warning!",
                                               "Delete Images?",
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if (reply == QtWidgets.QMessageBox.Yes):
            self.item_store.removeItemType(imageItem.ImageItem)

    @hdebug.debug
    def handleLoadMosaic(self, boolean):
        mosaic_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                "Load Mosaic",
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]
        if mosaic_filename:
            self.loadMosaic(mosaic_filename)

    @hdebug.debug
    def handleLoadMovies(self, boolean):
        # Open custom dialog to select files and frame number
        [filenames, frame_num, file_filter] = qtRegexFileDialog.regexGetFileNames(directory = self.parameters.get("directory"),
                                                                                  regex = self.regexp_str,
                                                                                  extensions = ["*.dax", "*.tif", "*.spe"])
        if (filenames is not None) and (len(filenames) > 0):
            print("Found " + str(len(filenames)) + " files matching " + str(file_filter) + " in " + os.path.dirname(filenames[0]))
            print("Loading frame: " + str(frame_num))

            # Save regexp string for next time the dialog is opened
            self.regexp_str = file_filter
                
            # Load movies
            self.image_capture.loadMovies(filenames, frame_num)

    @hdebug.debug
    def handleLoadPositions(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.parameters.get("directory"),
                                                                   "*.txt")[0]
        if positions_filename:
            self.positions.loadPositions(positions_filename)

    @hdebug.debug
    def handleMosaicPositionRequest(self, position_dict):
        positions = imageCapture.createGrid(position_dict['x_grid'], position_dict['y_grid'], include_center=True)
        for pos in positions:
            x = position_dict['grid_spacing']*pos[0] + position_dict['x_center']
            y = position_dict['grid_spacing']*pos[1] + position_dict['y_center']
            self.positions.addPosition(coord.Point(float(x), float(y), "um"))

    @hdebug.debug
    def handleMosaicViewContextMenuEvent(self, event, a_coord):
        for elt in self.modules:
            elt.setMosaicEventCoord(a_coord)
        self.context_menu.exec_(event.globalPos())

    @hdebug.debug
    def handleMosaicViewDropEvent(self, filenames_list):

        file_type = os.path.splitext(filenames_list[0])[1]

        # Check for .dax files.
        if (file_type == '.dax') or (file_type == ".tif"):
            self.image_capture.loadMovies(filenames_list, 0)

        # Check for mosaic files.
        elif (file_type == '.msc'):
            for filename in sorted(filenames_list):
                self.loadMosaic(filename)

        else:
            hdebug.logText(" " + file_type + " is not recognized")
            QtGui.QMessageBox.information(self,
                                          "File type not recognized",
                                          "")

    @hdebug.debug
    def handleMosaicViewKeyPressEvent(self, event, a_coord):
        for elt in self.modules:
            elt.setMosaicEventCoord(a_coord)
            
        # Picture taking
        if (event.key() == QtCore.Qt.Key_Space):
            self.mosaic.handleTakeMovie(None)
        elif (event.key() == QtCore.Qt.Key_3):
            self.mosaic.handleTakeSpiral(3)
        elif (event.key() == QtCore.Qt.Key_5):
            self.mosaic.handleTakeSpiral(5)
        elif (event.key() == QtCore.Qt.Key_7):
            self.mosaic.handleTakeSpiral(7)
        elif (event.key() == QtCore.Qt.Key_9):
            self.mosaic.handleTakeSpiral(9)
        elif (event.key() == QtCore.Qt.Key_G):
            self.mosaic.handleTakeGrid()

        # Record position
        elif (event.key() == QtCore.Qt.Key_P):
            self.positions.handleRecordPosition(None)

        # Create section
        elif (event.key() == QtCore.Qt.Key_S):
            self.sections.handleAddSection(None)

        # Record center for new positions grid
        elif (event.key() == QtCore.Qt.Key_N):
            self.mosaic.ui.posCenterSpinX.setValue(a_coord.x_um)
            self.mosaic.ui.posCenterSpinY.setValue(a_coord.y_um)

        # Pass commands back to positions (to coordinate move/delete of selected positions)
        self.positions.keyPressEvent(event)

    @hdebug.debug
    def handleMosaicViewSelectionChange(self, selected_items):
        self.positions.toggleSelectionForSelectedGraphicsItems(selected_items)

    @hdebug.debug
    def handleQuit(self, boolean):
        self.close()

    @hdebug.debug
    def handleSavePositions(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                   "Save Positions", 
                                                                   self.parameters.get("directory"), 
                                                                   "*.txt")[0]
        if positions_filename:
            self.positions.savePositions(positions_filename)

    @hdebug.debug
    def handleSaveMosaic(self, boolean):
        mosaic_filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save Mosaic", 
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]
        if mosaic_filename:
            self.item_store.saveMosaic(mosaic_filename)

    @hdebug.debug
    def handleSetWorkingDirectory(self, boolean):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.get("directory")),
                                                               QtWidgets.QFileDialog.ShowDirsOnly)
        if directory:
            self.image_capture.setDirectory(directory)
            self.snapshot_directory = directory + os.path.sep

    @hdebug.debug
    def handleSnapshot(self, boolean):
        snapshot_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.snapshot_directory, 
                                                                  "*.png")[0]
        if snapshot_filename:
            pixmap = self.mosaic.mosaic_view.grab()
            pixmap.save(snapshot_filename)

            self.snapshot_directory = os.path.dirname(snapshot_filename)

    def handleTabChange(self, tab_index):
        for elt in self.modules:
            elt.currentTabChanged(tab_index)

    def loadMosaic(self, mosaic_filename):
        self.image_capture.mosaicLoaded()
        if self.item_store.loadMosaic(mosaic_filename):
            for elt in self.modules:
                elt.mosaicLoaded()


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
    window = Window(parameters = parameters)
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
