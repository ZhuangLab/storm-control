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

import datetime
import os

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.hgit as hgit
import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.film.filmRequest as filmRequest
import storm_control.hal4000.film.filmSettings as filmSettings
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
        self.parameters.add(params.ParameterSetString(description = "Acquisition mode",
                                                      name = "acq_mode",
                                                      value = "fixed_length",
                                                      allowed = ["run_till_abort", "fixed_length"]))
        
        self.parameters.add(params.ParameterSetBoolean(description = "Automatically increment movie counter between movies",
                                                       name = "auto_increment",
                                                       value = True))
        
        self.parameters.add(params.ParameterSetBoolean(description = "Run shutters during the movie",
                                                       name = "auto_shutters",
                                                       value = True))
        
        self.parameters.add(params.ParameterString(description = "Current movie file name",
                                                   name = "filename",
                                                   value = "movie"))

        formats = imagewriters.availableFileFormats()        
        self.parameters.add(params.ParameterSetString(description = "Movie file type",
                                                      name = "filetype",
                                                      value = formats[0],
                                                      allowed = formats))
        
        self.parameters.add(params.ParameterRangeInt(description = "Movie length in frames",
                                                     name = "frames",
                                                     value = 10,
                                                     min_value = 1,
                                                     max_value = 1000000000))
        
        self.parameters.add(params.ParameterSetBoolean(description = "Sound bell at the end of long movies",
                                                       name = "want_bell",
                                                       value = True))

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

    def getFilmSettings(self, film_request):

        if film_request.isTCPRequest():
            #
            # TCP requested films are
            # 1. Always fixed length.
            # 2. Will always overwrite.
            # 3. Are always saved.
            #
            return filmSettings.FilmSettings(basename = os.path.join(self.parameters.get("directory"), film_request.getBasename()),
                                             filetype = self.parameters.get("filetype"),
                                             film_length = film_request.getFrames(),
                                             run_shutters = self.ui.autoShuttersCheckBox.isChecked(),
                                             tcp_request = True)

        else:
            reply = QtWidgets.QMessageBox.Yes

            # Overwrite check.
            if self.will_overwrite and self.ui.saveMovieCheckBox.isChecked():
                reply = halMessageBox.halMessageBoxResponse(self,
                                                            "Warning!",
                                                            "Overwrite Existing Movie?")
                if (reply == QtWidgets.QMessageBox.No):
                    return

            # Not saved check.
            if not self.ui.saveMovieCheckBox.isChecked():
                reply = halMessageBox.halMessageBoxResponse(self,
                                                            "Warning!",
                                                            "Do you know that the movie will not be saved?")
                if (reply == QtWidgets.QMessageBox.No):
                    return

            return filmSettings.FilmSettings(acq_mode = self.parameters.get("acq_mode"),
                                             basename  = os.path.join(self.parameters.get("directory"), self.getBasename()),
                                             filetype = self.parameters.get("filetype"),
                                             film_length = self.parameters.get("frames"),
                                             run_shutters = self.ui.autoShuttersCheckBox.isChecked(),
                                             save_film = self.ui.saveMovieCheckBox.isChecked())

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

    def soundBell(self):
        if not self.parameters.get("want_bell"):
            return False
        if not (self.parameters.get("acq_mode") == "fixed_length"):
            return False
        if not (self.parameters.get("frames") > 1000):
            return False
        return True

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


class Film(halModule.HalModule):
    """
    Filming controller.
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
        self.camera_functionalities = None
        self.feed_names = None
        self.film_settings = None
        self.film_size = 0.0
        self.film_state = "idle"
        self.number_frames = 0
        self.pixel_size = 1.0
        self.writers = None

        self.logfile_fp = open(module_params.get("directory") + "image_log.txt", "a")
        self.logfile_fp.write("\r\n")
        self.logfile_fp.flush()

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

        # In live mode the camera also runs between films.
        halMessage.addMessage("live mode",
                              validator = {"data" : {"live mode" : [True, bool]},
                                           "resp" : None})

        # Start a camera.
        halMessage.addMessage("start camera",
                              validator = {"data" : {"camera" : [True, str]},
                                           "resp" : None})

        # Start filming.
        halMessage.addMessage("start film",
                              validator = {"data" : {"film settings" : [True, filmSettings.FilmSettings]},
                                           "resp" : None})

        # Request to start filming, either from a record button or via TCP.
        halMessage.addMessage("start film request",
                              validator = {"data" : {"request" : [True, filmRequest.FilmRequest]},
                                           "resp" : None})

        # Stop a camera.
        halMessage.addMessage("stop camera",
                              validator = {"data" : {"camera" : [True, str]},
                                           "resp" : None})

        # Stop filming.
        halMessage.addMessage("stop film",
                              validator = {"data" : {"film settings" : [True, filmSettings.FilmSettings],
                                                     "number frames" : [True, int]},
                                           "resp" : {"parameters" : [False, params.StormXMLObject]}})

        # Request to stop filming.
        halMessage.addMessage("stop film request",
                              validator = {"data" : None,
                                           "resp" : None})

    def cleanUp(self, qt_settings):
        self.logfile_fp.close()

    def handleLiveModeChange(self, state):
        if state:
            self.startCameras()
        else:
            self.stopCameras()
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "live mode",
                                                   data = {"live mode" : state}))

    def handleResponses(self, message):
        """
        Modules are expected to add their current parameters as responses
        to the 'stop film' message. We save them in an xml file here.
        """
        if message.isType("get camera functionality"):
            assert (len(message.getResponses()) == 1)
            for response in message.getResponses():
                self.camera_functionalities.append(response.getData()["functionality"])
            
        elif message.isType("stop film"):
            self.film_state = "idle"
            film_settings = message.getData()["film settings"]
            number_frames = message.getData()["number frames"]
            if film_settings.isSaved():
                to_save = params.StormXMLObject()
                acq_p = to_save.addSubSection("acquisition")
                acq_p.add(params.ParameterString(name = "version",
                                                 value = hgit.getVersion()))
                acq_p.add(params.ParameterInt(name = "number_frames",
                                              value = number_frames))
                for response in message.getResponses():
                    data = response.getData()

                    # Add general parameters 'en-bloc'.
                    to_save.addSubSection(response.source,
                                          svalue = data["parameters"])

                    # Add any acquisition parameters, these will be a list.
                    if "acquisition" in data:
                        for p in data["acquisition"]:
                            acq_p.addParameter(p.getName(), p)

                # FIXME: Also include notes.
                msg = str(datetime.datetime.now()) + ","
                msg += film_settings.getBasename()
                msg += "\r\n"
                self.logfile_fp.write(msg)
                to_save.saveToFile(film_settings.getBasename() + ".xml")
        
    def processMessage(self, message):
            
        if message.isType("feeds stopped"):
            if (self.film_state == "start"):
                self.startFilmingLevel2()
            elif (self.film_state == "stop"):
                self.stopFilmingLevel2()

        elif message.isType("configure1"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to ui",
                                                       data = self.configure_dict))
                
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "initial parameters",
                                                       data = {"parameters" : self.view.getParameters()}))

        elif message.isType("feed names"):
            self.camera_functionalities = []
            for name in message.getData()["feed names"]:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "get camera functionality",
                                                           data = {"camera" : name}))


        #
        # FIXME: This will stop everything when the first camera reaches the
        #        expected number of frames. It should not fire until all the
        #        cameras that should be done are done.
        #
        #        For now this message should only come from camera1 when it
        #        has recorded the required number of frames.
        #
        elif message.isType("camera film complete"):
            if (self.film_state == "run"):
                self.stopFilmingLevel1()
                
        elif message.isType("new directory"):
            self.view.setDirectory(message.getData()["directory"])

        elif message.isType("new parameters"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))

            # Update parameters.
            self.view.newParameters(message.getData()["parameters"].get(self.module_name))

            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))
            
        #
        # We need to keep track of the current value so that
        # we can save this in the tif images / stacks.
        #
        elif message.isType("pixel size"):
            self.pixel_size = message.getData()["pixel size"]

        elif message.isType("start"):
            if self.view.amInLiveMode():
                self.startCameras()

        elif message.isType("start film request"):
            if (self.film_state != "idle"):
                raise halException.HalException("Start film request received while filming.")

            film_settings = self.view.getFilmSettings(message.getData()["request"])
            if film_settings is not None:
                film_settings.setPixelSize(self.pixel_size)
                self.startFilmingLevel1(film_settings)

        elif message.isType("stop film"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters()}))

        elif message.isType("stop film request"):
            if (self.film_state != "run"):
                raise halException.HalException("Stop film request received while not filming.")
            self.stopFilmingLevel1()

#    def processL2Message(self, message):            
#        if (self.film_state == "run") or (self.film_state == "stop"):
#
#            frame = message.getData()["frame"]
#
#            # Update frame counter if the frame is from camera1.
#            if (frame.which_camera == "camera1"):
#                self.number_frames = frame.frame_number + 1
#                self.view.updateFrames(self.number_frames)
#
#            # Save frame (if needed).
#            if frame.which_camera in self.writers:
#
#                #
#                # Potential for round off error here in tracking the total amount of
#                # data that has been saved.. Probably does not really matter..
#                #
#                self.film_size += self.writers[frame.which_camera].saveFrame(frame)
#                self.view.updateSize(self.film_size)

    def startCameras(self):
        
        # Start slave cameras first.
        for camera in self.camera_functionalities:
            if camera.isCamera() and not camera.isMaster():
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : camera.getCameraName()}))

        # Force sync.
        #
        # We need to make sure that the slave cameras have started before
        # starting the master cameras or we'll have a race condition.
        #
        self.newMessage.emit(halMessage.SyncMessage(self))

        # Start master cameras last.
        for camera in self.camera_functionalities:
            if camera.isCamera() and camera.isMaster():
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "start camera",
                                                           data = {"camera" : camera.getCameraName()}))

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
        if self.film_settings.isSaved():
            for feed_name, feed in self.feeds_info.items():
                if feed.getParameter("saved"):
                    self.writers[feed.getFeedName()] = imagewriters.createFileWriter(feed, self.film_settings)
        if (len(self.writers) == 0):
            self.view.updateSize(self.film_size)

        # Start filming.
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   sync = True,
                                                   m_type = "start film",
                                                   data = {"film settings" : self.film_settings}))
        # Start cameras.
        self.startCameras()
        
    def stopCameras(self):

        # Stop master cameras first.
        for camera in self.camera_functionalities:
            if camera.isCamera() and camera.isMaster():
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "stop camera",
                                                           data = {"camera" : camera.getCameraName()}))

        # Force sync.
        self.newMessage.emit(halMessage.SyncMessage(self))

        # Stop slave cameras last.
        for camera in self.camera_functionalities:
            if camera.isCamera() and not camera.isMaster():
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "stop camera",
                                                           data = {"camera" : camera.getCameraName()}))

    def stopFilmingLevel1(self):
        """
        Tell the cameras to stop, then wait until we get the
        'camera stopped' message from all the cameras.
        """
        self.film_state = "stop"
        self.stopCameras()

    def stopFilmingLevel2(self):
        """
        Once all the cameras have stopped close the imagewriters
        and restart the cameras (if we are in live mode).
        """
        self.view.enableUI(True)

        # Close writers.
        for name in self.writers:
            self.writers[name].closeFile()

        # Stop filming.
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "stop film",
                                                   data = {"film settings" : self.film_settings,
                                                           "number frames" : self.number_frames}))

        # Restart cameras, if needed.
        if self.view.amInLiveMode():
            self.startCameras()

        # Increment film counter.
        if not self.film_settings.isTCPRequest():
            self.view.incIndex()
            if self.view.soundBell():
                print("\7\7")

        #raise halExceptions.HalException("done now!")

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
