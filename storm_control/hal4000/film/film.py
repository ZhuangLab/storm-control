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

import copy
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


def truncateFilename(filename):
    max_len = 25
    if (len(filename) > max_len):
        return ".." + filename[-(max_len-2):]
    else:
        return filename
    
    
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
            #
            # 1. Always fixed length.
            # 2. Are always saved.
            # 3. Always have a base name.
            #

            # Figure out what directory to use.
            if film_request.getDirectory() is None:
                directory = self.parameters.get("directory")
            else:
                directory = film_request.getDirectory()

            return filmSettings.FilmSettings(basename = os.path.join(directory, film_request.getBasename()),
                                             filetype = self.parameters.get("filetype"),
                                             film_length = film_request.getFrames(),
                                             overwrite = film_request.overwriteOk(),
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
        self.ui.directoryText.setText("  " + truncateFilename(new_directory))
        self.updateFilenameLabel()

    def setShutters(self, shutters_filename):
        self.ui.shuttersText.setText("  " + truncateFilename(shutters_filename))

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
        #   1. startFilmingLevel1() - Initiates the start of filming.
        #      film_state = "start"
        #
        #   2. startFilmingLevel2() - Fires when all the cameras have stopped.
        #      film_state = "run"
        #
        #   3. stopFilmingLevel1() - Initiates the end of filming.
        #      film_state = "stop"
        #
        #   4. stopFilmingLevel2() - Fire when all the cameras have stopped.
        #      film_state = "idle"
        #
        # The problem that we are trying to solve is that we need to wait until
        # all the cameras have actually stopped before creating / destroying the
        # image writers as any camera that is still running could be generating
        # frames that we might want (or not want) to save.
        #
        self.active_cameras = 0
        self.camera_functionalities = []
        self.feed_names = None
        self.film_settings = None
        self.film_state = "idle"
        self.locked_out = False
        self.number_frames = 0
        self.number_fn_requested = 0
        self.parameter_change = False
        self.pixel_size = 1.0
        self.timing_functionality = None
        self.wait_for = []
        self.waiting_on = []
        self.writers = None
        self.writers_stopped_timer = QtCore.QTimer(self)

        try:
            self.logfile_fp = open(module_params.get("directory") + "image_log.txt", "a")
        except FileNotFoundError:
            print(">> image_log.txt file not found")
            self.logfile_fp = None

        self.writers_stopped_timer.setSingleShot(True)
        self.writers_stopped_timer.setInterval(10)
        self.writers_stopped_timer.timeout.connect(self.stopFilmingLevel2)

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

        # Sent when filming is not possible/possible. While this is true we'll
        # throw an error if another modules attempts to start/stop a film
        # or a camera. This is also the marker for the beginning / end of the
        # the film cycle.
        halMessage.addMessage("film lockout",
                              validator = {"data" : {"locked out" : [True, bool],
                                                     "acquisition parameters" : [False, params.StormXMLObject]},
                                           "resp" : None})
        
        # In live mode the camera also runs between films.
        halMessage.addMessage("live mode",
                              validator = {"data" : {"live mode" : [True, bool]},
                                           "resp" : None})

        # This comes from other modules that added a "wait for" request
        # to the 'start film' message.
        halMessage.addMessage("ready to film",
                              validator = {"data" : None, "resp" : None})
        
        # Start a camera.
        halMessage.addMessage("start camera",
                              validator = {"data" : {"camera" : [True, str]},
                                           "resp" : None})

        # Start filming.
        #
        # Filming won't start until all the modules that have
        # requested a wait send a "ready to film" message.
        #
        halMessage.addMessage("start film",
                              validator = {"data" : {"film settings" : [True, filmSettings.FilmSettings]}})

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
                                           "resp" : {"parameters" : [False, params.StormXMLObject],
                                                     "acquisition" : [False, list]}})

        # Request to stop filming.
        halMessage.addMessage("stop film request",
                              validator = {"data" : None,
                                           "resp" : None})

    def cleanUp(self, qt_settings):
        if self.logfile_fp is not None:
            self.logfile_fp.close()

    def handleLiveModeChange(self, state):
        if state:
            self.startCameras()
        else:
            self.stopCameras()
        self.sendMessage(halMessage.HalMessage(m_type = "live mode",
                                               data = {"live mode" : state}))

    def handleNewFrame(self, frame_number):
        self.number_frames = frame_number + 1

        # Update display of the number of frames.
        self.view.updateFrames(self.number_frames)

        # Update display of the (total) storage used.
        total_size = 0.0
        for writer in self.writers:
            total_size += writer.getSize()
        self.view.updateSize(total_size)
        
    def handleResponses(self, message):

        if message.isType("get functionality"):
            assert (len(message.getResponses()) == 1)
            for response in message.getResponses():
                self.camera_functionalities.append(response.getData()["functionality"])
                self.number_fn_requested -= 1

            # And we are done with the parameter change.
            if self.parameter_change and (self.number_fn_requested == 0):
                self.parameter_change = False
                self.sendMessage(halMessage.HalMessage(m_type = "parameters changed"))

        # Modules that need additional time to get ready to film should
        # specify at start up that they need to be waited for.
        elif message.isType("start film"):

            # No modules requested waits, so start now.
            if (len(self.wait_for) == 0):
                self.startCameras()
        
        # Modules are expected to add their current parameters as responses
        # to the 'stop film' message. We save them in an xml file here.
        elif message.isType("stop film"):
            self.film_state = "idle"
            acq_p = None
            notes = ""
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
                    if "parameters" in data:
                        to_save.addSubSection(response.source,
                                              svalue = data["parameters"])

                    # Add any acquisition parameters, these will be a list.
                    if "acquisition" in data:
                        for p in data["acquisition"]:
                            acq_p.addParameter(p.getName(), p)
                            if (p.getName() == "notes"):
                                notes = p.getv()

                to_save.saveToFile(film_settings.getBasename() + ".xml")

                if self.logfile_fp is not None:
                    msg = ",".join([str(datetime.datetime.now()),
                                    film_settings.getBasename(),
                                    notes])
                    msg += "\r\n"
                    self.logfile_fp.write(msg)
                    self.logfile_fp.flush()

            # Now that everything is complete end the filming lock out.
            self.setLockout(False, acquisition_parameters = acq_p)

    def handleStopCamera(self):
        self.active_cameras -= 1
        if (self.active_cameras == 0):
            if (self.film_state == "start"):
                self.startFilmingLevel2()
            elif (self.film_state == "stop"):
                self.stopFilmingLevel2()

    def processMessage(self, message):

        if message.isType("change directory"):
            self.view.setDirectory(message.getData()["directory"])
                    
        elif message.isType("configuration"):
            if message.sourceIs("feeds"):
                self.camera_functionalities = []
                for name in message.getData()["properties"]["feed names"]:
                    self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                           data = {"name" : name}))
                    self.number_fn_requested += 1

            elif message.sourceIs("illumination"):
                properties = message.getData()["properties"]
                if "shutters filename" in properties:
                    self.view.setShutters(properties["shutters filename"])

            elif message.sourceIs("mosaic"):
                # We need to keep track of the current value so that
                # we can save this in the tif images / stacks.
                self.pixel_size = message.getData()["properties"]["pixel_size"]
                    
            elif message.sourceIs("timing"):
                # We'll get this message from timing.timing, the part we are interested in is
                # the timing functionality which we will use both to update the frame counter
                # and to know when a fixed length film is complete.
                self.timing_functionality = message.getData()["properties"]["functionality"]
                self.timing_functionality.newFrame.connect(self.handleNewFrame)
                self.timing_functionality.stopped.connect(self.stopFilmingLevel1)

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to ui",
                                                   data = self.configure_dict))
                
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))

            # Let the settings.settings module know that it needs
            # to wait for us during a parameter change.
            self.sendMessage(halMessage.HalMessage(m_type = "wait for",
                                                   data = {"module names" : ["settings"]}))

        elif message.isType("current parameters"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters().copy()}))

        elif message.isType("new parameters"):
            if self.locked_out:
                raise halExceptions.HalException("'new parameters' received while locked out.")
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            # Update parameters.
            self.view.newParameters(message.getData()["parameters"].get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))


        elif message.isType("new shutters file"):
            self.view.setShutters(message.getData()["filename"])

        elif message.isType("ready to film"):
            self.waiting_on.remove(message.getSourceName())

            # All modules are ready, so start the cameras.
            if (len(self.waiting_on) == 0):
                self.startCameras()

        elif message.isType("start"):
            if self.view.amInLiveMode():
                self.startCameras()

        elif message.isType("start camera"):
            if self.locked_out and (message.getSource() != self):
                raise halExceptions.HalException("'start camera' received while locked out.")

        elif message.isType("start film request"):
            if self.locked_out:
                raise halExceptions.HalException("'start film request' received while locked out.")
            self.setLockout(True)
            film_settings = self.view.getFilmSettings(message.getData()["request"])
            if film_settings is not None:
                film_settings.setPixelSize(self.pixel_size)
                self.startFilmingLevel1(film_settings)
            else:
                self.setLockout(False)

        elif message.isType("stop camera"):
            if self.locked_out and (message.getSource() != self):
                raise halException.HalException("'stop camera' received while locked out.")

        elif message.isType("stop film"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters()}))

        elif message.isType("stop film request"):
            if (self.film_state != "run"):
                raise halExceptions.HalException("Stop film request received while not filming.")
            self.stopFilmingLevel1()

        elif message.isType("updated parameters"):
            self.parameter_change = True

        elif message.isType("wait for"):
            if self.module_name in message.getData()["module names"]:
                self.wait_for.append(message.getSourceName())

    def setLockout(self, state, acquisition_parameters = None):
        self.locked_out = state
        if acquisition_parameters is not None:
            self.sendMessage(halMessage.HalMessage(m_type = "film lockout",
                                                   data = {"locked out" : self.locked_out,
                                                           "acquisition parameters" : acquisition_parameters}))
        else:
            self.sendMessage(halMessage.HalMessage(m_type = "film lockout",
                                                   data = {"locked out" : self.locked_out}))
            
    def startCameras(self):
        
        # Start slave cameras first.
        for camera in self.camera_functionalities:
            if camera.isCamera() and not camera.isMaster():
                self.sendMessage(halMessage.HalMessage(m_type = "start camera",
                                                       data = {"camera" : camera.getCameraName()}))

        # Force sync.
        #
        # We need to make sure that the slave cameras have started before
        # starting the master cameras or we'll have a race condition.
        #
        self.sendMessage(halMessage.SyncMessage(self))

        # Start master cameras last.
        for camera in self.camera_functionalities:
            if camera.isCamera() and camera.isMaster():
                self.sendMessage(halMessage.HalMessage(m_type = "start camera",
                                                       data = {"camera" : camera.getCameraName()}))

    def startFilmingLevel1(self, film_settings):
        """
        First, tell the cameras to stop.
     
        This is hopefully a NOP if the cameras are not currently
        running, i.e. we are not in live mode.
        """
        self.film_settings = film_settings
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

        #
        # Check if we are going to overwrite existing files by checking
        # if we are going to overwrite the movies .xml file.
        #
        filename = self.film_settings.getBasename() + ".xml"
        if not self.film_settings.overwriteOk() and os.path.exists(filename):
            raise halExceptions.HALException("Movie files exist and overwrite Ok is false " + filename)

        # Create writers as needed for each feed.
        self.writers = []
        if self.film_settings.isSaved():
            for camera in self.camera_functionalities:
                if camera.getParameter("saved"):
                    self.writers.append(imagewriters.createFileWriter(camera, self.film_settings))
        if (len(self.writers) == 0):
            self.view.updateSize(0.0)
        
        # Start filming.
        self.waiting_on = copy.copy(self.wait_for)
        self.sendMessage(halMessage.HalMessage(sync = True,
                                               m_type = "start film",
                                               data = {"film settings" : self.film_settings}))

    def stopCameras(self):
        
        self.active_cameras = 0
        
        # Stop master cameras first.
        for camera in self.camera_functionalities:
            if camera.isCamera() and camera.isMaster():
                self.active_cameras += 1
                self.sendMessage(halMessage.HalMessage(m_type = "stop camera",
                                                       data = {"camera" : camera.getCameraName()},
                                                       finalizer = self.handleStopCamera))

        # Force sync.
        self.sendMessage(halMessage.SyncMessage(self))

        # Stop slave cameras last.
        for camera in self.camera_functionalities:
            if camera.isCamera() and not camera.isMaster():
                self.active_cameras += 1
                self.sendMessage(halMessage.HalMessage(m_type = "stop camera",
                                                       data = {"camera" : camera.getCameraName()},
                                                       finalizer = self.handleStopCamera))

    def stopFilmingLevel1(self):
        """
        Tell the cameras to stop, then wait until we get the
        'camera stopped' message from all the cameras.
        """
        # Disconnect the timing functionality as it is stopped now.
        self.timing_functionality.newFrame.disconnect(self.handleNewFrame)
        self.timing_functionality.stopped.disconnect(self.stopFilmingLevel1)
        self.timing_functionality = None

        self.film_state = "stop"
        self.stopCameras()

    def stopFilmingLevel2(self):
        """
        Once all the cameras/feeds have stopped close the imagewriters
        and restart the cameras (if we are in live mode).
        """

        # Check that the writers have stopped. The problem (I think) is a race condition
        # where the 'stopped' signal from the Camera has not reached the functionalities
        # of the writers before the handleStopCamera() finalizer for the 'stop camera'
        # message calls this function. If any of the writers have not stopped we wait
        # ~10ms and try again.
        for writer in self.writers:
            if not writer.isStopped():
                self.writers_stopped_timer.start()
                return

        # Close writers.
        for writer in self.writers:
            writer.closeWriter()

        # Enable the UI.
        self.view.enableUI(True)
        
        # Stop filming.
        #
        # The message includes the current number of frames so that even if this gets
        # reset before we handle the responses we'll still have the right numbers.
        #
        self.sendMessage(halMessage.HalMessage(m_type = "stop film",
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
