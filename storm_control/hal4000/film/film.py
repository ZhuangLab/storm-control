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

import storm_control.sc_library.hgit as hgit
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
        self.parameters.add(params.ParameterSetString("Acquisition mode",
                                                      "acq_mode",
                                                      "fixed_length",
                                                      ["run_till_abort", "fixed_length"]))
        
        self.parameters.add(params.ParameterSetBoolean("Automatically increment movie counter between movies",
                                                       "auto_increment",
                                                       True))
        
        self.parameters.add(params.ParameterSetBoolean("Run shutters during the movie",
                                                       "auto_shutters",
                                                       True))
        
        self.parameters.add(params.ParameterString("Current movie file name",
                                                   "filename",
                                                   "movie"))
        
        self.parameters.add(params.ParameterSetString("Movie file type",
                                                      "filetype",
                                                      ".dax",
                                                      [".dax", ".tif"]))
        
        self.parameters.add(params.ParameterRangeInt("Movie length in frames",
                                                     "frames",
                                                     10,
                                                     1,
                                                     1000000000))
        
        self.parameters.add(params.ParameterSetBoolean("Sound bell at the end of long movies",
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
                             "basename" :os.path.join(self.parameters.get("directory"), self.getBasename()),
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
                       self.ui.modeComboBox,
                       self.ui.saveMovieCheckBox]:
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

    def incIndex(self):
        if self.parameters.get("auto_increment"):
            self.ui.indexSpinBox.stepUp()
        
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
        
    def updateFrames(self, new_number):
        self.ui.framesText.setText(str(new_number))

    def updateSize(self, new_size):
        if (new_size < 1000.0):
            self.ui.sizeText.setText("{0:.1f} MB".format(new_size))
        else:
            self.ui.sizeText.setText("{0:.1f} GB".format(new_size * 0.00097656))

        
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
        # The method sequence for a film is:
        #   1. startFilmLevel1() - Initiates the start of filming.
        #      film_state = "start"
        #
        #   2. startFilmLevel2() - Fires when all the cameras have stopped.
        #      film_state = "run"
        #
        #   3. stopFilmLevel1() - Initiates the end of filming.
        #      film_state = "stop"
        #
        #   4. stopFilmLevel2() - Fire when all the cameras have stopped.
        #      film_state = "idle"
        #
        # The problem that we are trying to solve is that we need to
        # wait until all the cameras have actually stopped before
        # creating / destroying the image writers as any camera that
        # is still running could be throwing off 'new frame' messages
        # which we might want (or not want) to save.
        #
        self.active_camera_count = 0
        self.feed_list = None
        self.film_settings = None
        self.film_size = 0.0
        self.film_state = "idle"
        self.pixel_size = 1.0
        self.tcp_requested = False
        self.writers = None

        self.logfile_fp = open(module_params.get("directory") + "image_log.txt", "a")

        p = module_params.getp("parameters")
        p.add(params.ParameterStringDirectory("Current working directory",
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

    def handleResponses(self, message):
        """
        Modules are expected to add their current parameters as responses
        to the 'stop film' message. We save them as an xml file here.
        """
        if (message.getType() == "stop film"):
            film_settings = message.getData()["film_settings"]
            if film_settings["save_film"]:
                to_save = params.StormXMLObject()
                acq_p = to_save.addSubSection("acquisition")
                acq_p.add(params.ParameterString("", "version", hgit.getVersion()))
                acq_p.add(params.ParameterInt("", "number_frames", film_settings["number_frames"]))
                for response in message.getResponses():
                    data = response.getData()

                    # Add general parameters 'en-bloc'.
                    to_save.addSubSection(response.source, data["parameters"])

                    # Add any acquisition parameters, these will be a list.
                    if "acquisition" in data:
                        for p in data["acquisition"]:
                            acq_p.addParameter(p.getName(), p)
                            
                to_save.saveToFile(film_settings["basename"] + ".xml")
        
    def processMessage(self, message):

        if (message.level == 1):
            
            if (message.m_type == "camera stopped"):
                self.active_camera_count -= 1
                if (self.active_camera_count == 0):
                    if (self.film_state == "start"):
                        self.startFilmingLevel2()
                    elif (self.film_state == "stop"):
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
            #        For now this message should only come from camera1 when it
            #        has recorded the required number of frames.
            #
            elif (message.m_type == "film complete"):
                if (self.film_state == "run"):
                    self.stopFilmingLevel1()

            elif (message.m_type == "new directory"):
                self.view.setDirectory(message.getData()["directory"])

            #
            # We need to keep track of the current value so that
            # we can save this in the tif images / stacks.
            #
            elif (message.m_type == "pixel size"):
                self.pixel_size = message.getData()["pixel_size"]
                
            elif (message.m_type == "record clicked"):
                self.tcp_requested = False

                # Start filming if we are idle.
                if (self.film_state == "idle"):
                    film_settings = self.view.getFilmParams()
                    if film_settings is not None:
                        film_settings["pixel_size"] = self.pixel_size
                        self.startFilmingLevel1(film_settings)

                # Otherwise stop filming if we are running.
                elif (self.film_state == "run"):
                    self.stopFilmingLevel1()

            elif (message.m_type == "start"):
                if self.view.amInLiveMode():
                    self.startCameras()

            elif (message.getType() == "stop film"):
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"parameters" : self.view.getParameters()}))

        elif (message.level == 2) and (self.film_state == "run"):
            if (message.getType() == "new frame"):
                
                frame = message.getData()["frame"]
                
                # Update frame counter if the frame is from camera1.
                if (frame.which_camera == "camera1"):
                    self.film_settings["number_frames"] = frame.frame_number + 1
                    self.view.updateFrames(frame.frame_number + 1)

                # Save frame (if needed).
                if frame.which_camera in self.writers:

                    #
                    # Potential for round off error here in tracking the total amount of
                    # data that has been saved.. Probably does not really matter..
                    #
                    self.film_size += self.writers[frame.which_camera].saveFrame(frame)
                    self.view.updateSize(self.film_size)

        super().processMessage(message)

    def startCameras(self):
        
        # Start slave cameras first.
        for feed in self.feed_list:
            if feed["is_camera"] and not feed["is_master"]:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : feed["feed_name"]}))

        # Force sync.
        #
        # We need to make sure that the slave cameras have started before
        # starting the master cameras or we'll have a race condition.
        #
        self.newMessage.emit(halMessage.SyncMessage(self))

        # Start master cameras last.
        for feed in self.feed_list:
            if feed["is_camera"] and feed["is_master"]:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : feed["feed_name"]}))

    def startFilmingLevel1(self, film_settings):
        """
        First, tell the cameras to stop.
     
        This is hopefully a NOP if the cameras are not currently
        running, i.e. we are not in live mode.
        """
        self.film_settings = film_settings
        self.film_size = 0.0
        self.film_state = "start"
        self.view.enableUI(False)

        self.stopCameras()

    def startFilmingLevel2(self):
        """
        Then once all the cameras are stopped configure the imagewriters 
        for all of the feeds, and send the 'start film' message, followed 
        by the 'start camera' message.
        """
        self.film_state = "run"
        
        # Create writers as needed for each feed.
        self.writers = {}
        if self.film_settings["save_film"]:
            for feed in self.feed_list:
                if feed["is_saved"]:
                    self.writers[feed["feed_name"]] = imagewriters.createFileWriter(feed, self.film_settings)
        if (len(self.writers) == 0):
            self.view.updateSize(self.film_size)

        # Start filming.
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   sync = True,
                                                   m_type = "start film",
                                                   data = {"film_settings" : self.film_settings}))
        # Start cameras.
        self.startCameras()
        
    def stopCameras(self):
        self.active_camera_count = 0

        # Stop master cameras first.
        for feed in self.feed_list:
            if feed["is_camera"] and feed["is_master"]:
                self.active_camera_count += 1
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "stop camera",
                                                           data = {"camera" : feed["feed_name"]}))

        # Force sync.
        self.newMessage.emit(halMessage.SyncMessage(self))

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
        self.film_state = "stop"
        self.view.enableUI(True)
        self.stopCameras()

    def stopFilmingLevel2(self):
        """
        Once all the cameras have stopped close the imagewriters
        and restart the cameras (if we are in live mode).
        """
        for name in self.writers:
            self.writers[name].closeFile()

        # Stop filming.
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "stop film",
                                                   data = {"film_settings" : self.film_settings}))

        # Restart cameras, if needed.
        if self.view.amInLiveMode():
            self.startCameras()

        # Increment film counter.
        if not self.tcp_requested:
            self.view.incIndex()

        self.film_state = "idle"
            
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
