#!/usr/bin/env python
"""
Handles filming.

This module is responsible for everything related to filming,
including starting and stopping the cameras, saving the frames,
etc..

Much of the logic in the main part of Python2/PyQt4 HAL is 
now located in this module.

Hazen 01/17
"""

import os

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.halLib.imagewriters as imagewriters
import storm_control.hal4000.qtdesigner.film_ui as filmUi


class FilmBox(QtWidgets.QGroupBox):
    """
    The UI.
    """
    liveModeChange = QtCore.pyqtSignal(bool)
    
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.parameters = parameters
        self.will_overwrite = False

        # Add default film parameters.        
        self.parameters.add("acq_mode", params.ParameterSetString("Acquisition mode",
                                                                  "acq_mode",
                                                                  "fixed_length",
                                                                  ["run_till_abort", "fixed_length"]))
        
        self.parameters.add("auto_increment", params.ParameterSetBoolean("Automatically increment movie counter between movies",
                                                                         "auto_increment",
                                                                         True))
        
        self.parameters.add("auto_shutters", params.ParameterSetBoolean("Run shutters during the movie",
                                                                        "auto_shutters",
                                                                        True))
        
        self.parameters.add("filename", params.ParameterString("Current movie file name",
                                                               "filename",
                                                               "movie"))
        
        self.parameters.add("filetype", params.ParameterSetString("Movie file type",
                                                                  "filetype",
                                                                  ".dax",
                                                                  [".dax", ".tif"]))
        
        self.parameters.add("frames", params.ParameterRangeInt("Movie length in frames",
                                                               "frames",
                                                               10,
                                                               1,
                                                               1000000000))
        
        self.parameters.add("want_bell", params.ParameterSetBoolean("Sound bell at the end of long movies",
                                                                    "want_bell",
                                                                    True))

        # Initial UI configuration.
        self.ui = filmUi.Ui_GroupBox()
        self.ui.setupUi(self)
        
        for extname in self.parameters.getp("extension").getAllowed():
            self.ui.extensionComboBox.addItem(extname)
        
        for typename in self.parameters.getp("filetype").getAllowed():
            self.ui.filetypeComboBox.addItem(typename)

        self.ui.framesText.setText("")
        self.ui.sizeText.setText("")

        self.setDirectory(self.parameters.get("directory"))
        self.setShutters("NA")
        self.newParameters(self.parameters)
        self.updateFilenameLabel()

        # Connect signals
        self.ui.autoIncCheckBox.stateChanged.connect(self.handleAutoInc)
        self.ui.autoShuttersCheckBox.stateChanged.connect(self.handleAutoShutters)
        self.ui.extensionComboBox.currentIndexChanged.connect(self.handleExtension)
        self.ui.filenameEdit.textChanged.connect(self.handleFilename)
        self.ui.filetypeComboBox.currentIndexChanged.connect(self.handleFiletype)
        self.ui.indexSpinBox.valueChanged.connect(self.handleIndex)
        self.ui.lengthSpinBox.valueChanged.connect(self.handleLength)
        self.ui.liveModeCheckBox.stateChanged.connect(self.handleLiveMode)
        self.ui.modeComboBox.currentIndexChanged.connect(self.handleMode)

    def amInLiveMode(self):
        return self.ui.liveModeCheckBox.isChecked()

    def getBasename(self):
        name = self.parameters.get("filename")
        name += "_{0:04d}".format(self.ui.indexSpinBox.value())
        if len(self.parameters.get("extension")) > 0:
            name += "_" + self.parameters.get("extension")
        return name

    def getFilmParams(self):
        film_settings = None

        reply = QtWidgets.QMessageBox.Yes
        if self.will_overwrite and self.ui.saveMovieCheckBox.isChecked():
            reply = halMessageBox.halMessageBoxResponse(self,
                                                        "Warning!",
                                                        "Overwrite Existing Movie?")

        if not self.ui.saveMovieCheckBox.isChecked():
            reply = halMessageBox.halMessageBoxResponse(self,
                                                        "Warning!",
                                                        "Do you know that the movie will not be saved?")
            
        if (reply == QtWidgets.QMessageBox.Yes):
            film_settings = {"acq_mode" : self.parameters.get("acq_mode"),
                             "basename" : self.getBasename(),
                             "filetype" : self.parameters.get("filetype"),
                             "frames" : self.parameters.get("frames"),
                             "run_shutters" : self.ui.autoShuttersCheckBox.isChecked(),
                             "save_film" : self.ui.saveMovieCheckBox.isChecked()}

        return film_settings
        
    def getParameters(self):
        return self.parameters.copy()
    
    def enableUI(self, state):
        for ui_elt in [self.ui.autoIncCheckBox,
                       self.ui.autoShuttersCheckBox,
                       self.ui.extensionComboBox,
                       self.ui.filenameEdit,
                       self.ui.filetypeComboBox,
                       self.ui.indexSpinBox,
                       self.ui.lengthSpinBox,
                       self.ui.liveModeCheckBox,
                       self.ui.modeComboBox]:
            ui_elt.setEnabled(state)
        
    def handleAutoInc(self, state):
        self.parameters.set("auto_increment", state)

    def handleAutoShutters(self, state):
        self.parameters.set("auto_shutters", state) 

    def handleExtension(self, index):
        self.parameters.set("extension", self.ui.extensionComboBox.currentText())
        self.updateFilenameLabel()

    def handleFilename(self):
        self.parameters.set("filename", str(self.ui.filenameEdit.displayText()))
        self.updateFilenameLabel()

    def handleFiletype(self, index):
        self.parameters.set("filetype", str(self.ui.filetypeComboBox.currentText()))
        self.updateFilenameLabel()
        
    def handleIndex(self, index):
        self.updateFilenameLabel()

    def handleLength(self, index):
        self.parameters.set("frames", index)

    def handleLiveMode(self, state):
        self.liveModeChange.emit(state)
        
    def handleMode(self, index):
        print("hm", index)
        if (index == 0):
            self.parameters.set("acq_mode", "run_till_abort")
            self.ui.lengthSpinBox.hide()
        else:
            self.parameters.set("acq_mode", "fixed_length")
            self.ui.lengthSpinBox.show()
        
    def newParameters(self, parameters):
        self.ui.autoIncCheckBox.setChecked(parameters.get("auto_increment"))
        self.ui.autoShuttersCheckBox.setChecked(parameters.get("auto_shutters"))
        self.ui.extensionComboBox.setCurrentIndex(self.ui.extensionComboBox.findText(parameters.get("extension")))
        self.ui.filenameEdit.setText(parameters.get("filename"))
        self.ui.filetypeComboBox.setCurrentIndex(self.ui.filetypeComboBox.findText(parameters.get("filetype")))
        self.ui.lengthSpinBox.setValue(parameters.get("frames"))
        
        if (parameters.get("acq_mode") == "run_till_abort"):
            self.ui.modeComboBox.setCurrentIndex(0)
        else:
            self.ui.modeComboBox.setCurrentIndex(1)

    def setDirectory(self, new_directory):
        self.parameters.set("directory", new_directory)
        self.ui.directoryText.setText("  " + new_directory[-30:])
        self.updateFilenameLabel()

    def setShutters(self, new_shutters):
        self.ui.shuttersText.setText("  " + new_shutters)

    def updateFilenameLabel(self):
        name = self.getBasename() + self.parameters.get("filetype")

        self.ui.filenameLabel.setText(name)
        if os.path.exists(os.path.join(self.parameters.get("directory"), name)):
            self.will_overwrite = True
            self.ui.filenameLabel.setStyleSheet("QLabel { color: red}")
        else:
            self.will_overwrite = False
            self.ui.filenameLabel.setStyleSheet("QLabel { color: black}")
        

class Film(halModule.HalModuleBuffered):
    """
    Filming controller.

    This sends the following messages:
     'start camera'
     'start film'
     'stop camera'
     'stop film'
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        #
        # Lots of state variable here.. But the basic idea is:
        #
        # 1. self.active_camera_count keep track of how many cameras are
        #    still running.
        #
        # 2. am_filming is True from the start of filming to the end.
        #
        # 3. film_start is True if we are waiting for the cameras to stop
        #    before starting filming, otherwise it is False.
        #
        # And the method sequence for a film is:
        #   startFilmLevel1() - Initiates the start of filming.
        #   startFilmLevel2() - Fires when all the cameras have stopped.
        #   stopFilmLevel1() - Initiates the end of filming.
        #   stopFilmLevel2() - Fire when all the cameras have stopped.
        #
        self.active_camera_count = 0
        self.am_filming = False
        self.feed_list = None
        self.film_settings = None
        self.film_start = True
        self.writers = None

        self.logfile_fp = open(module_params.get("directory") + "image_log.txt", "a")

        p = module_params.getp("parameters")
        p.add("directory", params.ParameterStringDirectory("Current working directory",
                                                           "directory",
                                                           module_params.get("directory"),
                                                           is_mutable = False,
                                                           is_saved = False))
                
        self.view = FilmBox(parameters = p)
        self.view.liveModeChange.connect(self.handleLiveModeChange)

        self.configure_dict = {"ui_order" : 1,
                               "ui_parent" : "hal.containerWidget",
                               "ui_widget" : self.view}

        halMessage.addMessage("live mode")
        halMessage.addMessage("start camera")
        halMessage.addMessage("start film")
        halMessage.addMessage("stop camera")
        halMessage.addMessage("stop film")
        
    def cleanUp(self, qt_settings):
        self.logfile_fp.close()

    def handleLiveModeChange(self, state):
        if state:
            self.startCameras()
        else:
            self.stopCameras()
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "live mode",
                                                   data = {"live mode", state}))
        
    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            
            if (message.m_type == "camera stopped"):
                self.active_camera_count -= 1
                if (self.active_camera_count == 0) and self.am_filming:
                    if self.film_start:
                        self.startFilmingLevel2()
                    else:
                        self.stopFilmingLevel2()
                
            elif (message.m_type == "configure1"):
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = self.configure_dict))
                
                # Broadcast default parameters.
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "current parameters",
                                                           data = {"parameters", self.view.getParameters()}))

            elif (message.m_type == "feed list"):
                self.feed_list = message.getData()["feeds"]

            #
            # FIXME: This will stop everything when the first camera reaches the
            #        expected number of frames. It should not fire until all the
            #        cameras that should be done are done.
            #
            elif (message.m_type == "film complete"):
                self.stopFilmingLevel1()

            elif (message.m_type == "new directory"):
                self.view.setDirectory(message.getData()["directory"])

            elif (message.m_type == "record clicked"):

                # Stop filming if we are filming.
                if self.am_filming:
                    self.stopFilmingLevel1()

                # Otherwise start filming.
                else:
                    film_settings = self.view.getFilmParams()
                    if film_settings is not None:
                        self.startFilmingLevel1(film_settings)

            elif (message.m_type == "start"):
                if self.view.amInLiveMode():
                    self.startCameras()

    def startCameras(self):
        
        # Start slave cameras first.
        for feed in self.feed_list:
            if feed["is_camera"] and not feed["is_master"]:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : feed["feed_name"]}))

        # Start master cameras last.
        for feed in self.feed_list:
            if feed["is_camera"] and feed["is_master"]:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : feed["feed_name"]}))

    def startFilmingLevel1(self, film_settings):
        self.am_filming = True
        self.film_settings = film_settings
        self.film_start = True
        self.view.enableUI(False)

        # Tell the cameras to stop, then wait until we get the
        # 'camera stopped' message from all the cameras.
        #
        # This is hopefully a NOP if the cameras are not currently
        # running, i.e. we are not in live mode.
        self.stopCameras()

    def startFilmingLevel2(self):
        """
        Once all the cameras are stopped configure the imagewriters for
        all of the feeds, then send the 'start film' message, followed 
        by the 'start camera' message.
        """
        
        # Create writers as needed for each feed.
        self.writers = {}
        if self.film_settings["save_film"]:
            for feed in self.feed_list:
                if feed["is_saved"]:
                    self.writer[feed["feed_name"]] = imagewriters.createFileWriter(feed, self.film_settings)
            
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   sync = True,
                                                   m_type = "start film",
                                                   data = {"film_settings" : self.film_settings}))
        self.startCameras()
        
    def stopCameras(self):
        self.active_camera_count = 0

        # Stop master cameras first
        for feed in self.feed_list:
            if feed["is_camera"] and feed["is_master"]:
                self.active_camera_count += 1
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "stop camera",
                                                           data = {"camera" : feed["feed_name"]}))
                
        # Stop slave cameras last.
        for feed in self.feed_list:
            if feed["is_camera"] and not feed["is_master"]:
                self.active_camera_count += 1
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "stop camera",
                                                           data = {"camera" : feed["feed_name"]}))

    def stopFilmingLevel1(self):
        """
        Tell the cameras to stop, then wait until we get the
        'camera stopped' message from all the cameras.
        """
        self.film_start = False
        self.view.enableUI(True)
        self.stopCameras()

    def stopFilmingLevel2(self):
        """
        Once all the cameras have stopped close the imagewriters
        and restart the cameras (if we are in live mode).
        """
        for writer in self.writers:
            pass
        
        self.am_filming = False
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "stop film",
                                                   data = {"film_settings" : self.film_settings}))

        if self.view.amInLiveMode():
            self.startCameras()

#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
