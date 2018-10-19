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
import storm_control.steve.mosaic as mosaic
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

        self.comm = comm.Comm()
        self.item_store = steveItems.SteveItemsStore()
        self.parameters = parameters
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

        # Handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent
        self.ui.centralwidget.setAcceptDrops(True)
        
        # Signals
        self.ui.actionDelete_Images.triggered.connect(self.handleDeleteImages)
        self.ui.actionLoad_Movie.triggered.connect(self.handleLoadMovie)
        self.ui.actionLoad_Mosaic.triggered.connect(self.handleLoadMosaic)
        self.ui.actionLoad_Positions.triggered.connect(self.handleLoadPositions)
        self.ui.actionQuit.triggered.connect(self.handleQuit)
        self.ui.actionSave_Mosaic.triggered.connect(self.handleSaveMosaic)
        self.ui.actionSave_Positions.triggered.connect(self.handleSavePositions)
        self.ui.actionSave_Snapshot.triggered.connect(self.handleSnapshot)
        self.ui.actionSet_Working_Directory.triggered.connect(self.handleSetWorkingDirectory)

        # Add Modules
        self.mosaic = mosaic.Mosaic(comm = self.comm,
                                    item_store = self.item_store,
                                    parameters = self.parameters)
        layout = QtWidgets.QVBoxLayout(self.ui.mosaicTab)
        layout.addWidget(self.mosaic)
        layout.setContentsMargins(0,0,0,0)
        self.ui.mosaicTab.setLayout(layout)

        self.sections = sections.Sections(comm = self.comm,
                                          item_store = self.item_store,
                                          parameters = self.parameters)
        layout = QtWidgets.QVBoxLayout(self.ui.sectionsTab)
        layout.addWidget(self.sections)
        layout.setContentsMargins(0,0,0,0)
        self.ui.sectionsTab.setLayout(layout)        
        
    @hdebug.debug
    def cleanUp(self):
        self.settings.setValue("position", self.pos())
        self.settings.setValue("size", self.size())

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    @hdebug.debug
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

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

    @hdebug.debug
    def handleDeleteImages(self, boolean):
        reply = QtWidgets.QMessageBox.question(self,
                                               "Warning!",
                                               "Delete Images?",
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if (reply == QtWidgets.QMessageBox.Yes):
            pass

    @hdebug.debug
    def handleLoadMosaic(self, boolean):
        mosaic_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                "Load Mosaic",
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]

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

    @hdebug.debug
    def handleLoadPositions(self, boolean):
        positions_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                   "Load Positions",
                                                                   self.parameters.get("directory"),
                                                                   "*.txt")[0]
        if positions_filename:
            self.positions.loadPositions(positions_filename)

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
            pass

    @hdebug.debug
    def handleSaveMosaic(self, boolean):
        mosaic_filename = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save Mosaic", 
                                                                self.parameters.get("directory"),
                                                                "*.msc")[0]
        if mosaic_filename:
            pass

    @hdebug.debug
    def handleSetWorkingDirectory(self, boolean):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                               "New Directory",
                                                               str(self.parameters.get("directory")),
                                                               QtWidgets.QFileDialog.ShowDirsOnly)
        if directory:
            self.parameters.set("directory", directory + os.path.sep)
            self.snapshot_directory = directory + os.path.sep

    @hdebug.debug
    def handleSnapshot(self, boolean):
        snapshot_filename = QtWidgets.QFileDialog.getSaveFileName(self, 
                                                                  "Save Snapshot", 
                                                                  self.snapshot_directory, 
                                                                  "*.png")[0]
        if snapshot_filename:
            pass



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
