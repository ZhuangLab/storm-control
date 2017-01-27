#!/usr/bin/env python
"""

Heuristically programmed ALgorithmic STORM setup control.

This module handles setup, clean up and message passing
between the various sub-modules that define the 
behavior. Each of these modules must be a sub-class of
the HalModule class in halLib.halModule. Setup specific
configuration is provided by a 'XX_config.xml' file
examples of which can be found in the xml folder.

In addition this module handles drag/drops and
the film notes QTextEdit.

Jeff 03/14
Hazen 01/17

"""

from collections import deque
import importlib
import os

from PyQt5 import QtGui, QtWidgets

# Debugging
import storm_control.sc_library.hdebug as hdebug

# Misc.
import storm_control.sc_library.parameters as params
import storm_control.sc_library.hgit as hgit


class Window(QtWidgets.QMainWindow):

    @hdebug.debug
    def __init__(self, config, **kwds):
        """
        Set up the GUI, initialize and connect the various modules.
        """
        super(asdf, kwds)

        # General (alphabetically ordered)
        self.current_directory = False
        self.current_length = 0
        self.directory = False
        self.directory_test_mode = False
        self.filename = ""
        self.filming = False
        self.logfile_fp = open(parameters.get("film.logfile"), "a")
        self.modules = []
        self.old_shutters_file = ""
        self.parameters = parameters
        self.parameters_test_mode = False
        self.settings = QtCore.QSettings("Zhuang Lab", "hal-4000_" + parameters.get("setup_name").lower())
        self.tcp_message = None
        self.tcp_requested_movie = False
        self.ui_mode = ""
        self.will_overwrite = False
        self.writer = False
        self.xml_directory = ""

        # Logfile setup
        self.logfile_fp.write("\r\n")
        self.logfile_fp.flush()

        
        setup_name = parameters.get("setup_name").lower()

        #
        # UI setup, this is one of:
        #
        # 1. single: single window (the classic look).
        # 2. detached: detached camera window.
        #
        self.ui_mode = hardware.get("ui_mode")
        if (self.ui_mode == "single"):
            import storm_control.hal4000.qtdesigner.hal4000_ui as hal4000Ui
        elif (self.ui_mode == "detached"):
            import storm_control.hal4000.qtdesigner.hal4000_detached_ui as hal4000Ui
        else:
            print("unrecognized mode:", self.ui_mode)
            print(" mode should be either single or detached")
            exit()

        # Load the ui
        self.ui = hal4000Ui.Ui_MainWindow()
        self.ui.setupUi(self)
        
        title = self.parameters.get("setup_name")
        if (hgit.getBranch().lower() != "master"):
            title += " (" + hgit.getBranch() + ")"
        self.setWindowTitle(title)

        self.setWindowIcon(qtAppIcon.QAppIcon())

        self.parameters_box = qtParametersBox.QParametersBox(self.ui.settingsScrollArea)
        self.ui.settingsScrollArea.setWidget(self.parameters_box)
        self.ui.settingsScrollArea.setWidgetResizable(True)

        file_types = writers.availableFileFormats(self.ui_mode)
        self.parameters.getp("film.filetype").setAllowed(file_types)
        for ftype in file_types:
            self.ui.filetypeComboBox.addItem(ftype)

        self.ui.framesText.setText("")
        self.ui.sizeText.setText("")

        #
        # Camera control & signals.
        #
        self.camera = control.Camera(hardware.get("control"), parameters)
        self.camera.reachedMaxFrames.connect(self.stopFilm)
        self.camera.newFrames.connect(self.newFrames)

        #
        # Camera display.
        #
        if (self.ui_mode == "single"):
            n_cameras = 1
        else:
            n_cameras = self.camera.getNumberOfCameras()

        camera_displays = []
        for i in range(n_cameras):
            which_camera = "camera" + str(i+1)
            camera_displays.append(cameraDisplay.CameraDisplay(self.ui,
                                                               self.ui_mode,
                                                               which_camera,
                                                               hardware.get("display"),
                                                               parameters,
                                                               self))

        # This is the classic single-window HAL display. To work properly, the camera 
        # controls UI elements that "belong" to the main window and vice-versa.
        if (self.ui_mode == "single"):
            self.ui.recordButton = camera_displays[0].getRecordButton()

        # Insert additional menu items for the camera display(s) as necessary
        else:
            for camera_display in camera_displays:
                a_action = QtWidgets.QAction(self.tr(camera_display.getMenuName()), self)
                self.ui.menuFile.insertAction(self.ui.actionQuit, a_action)
                a_action.triggered.connect(camera_display.show)

        # Camera display modules are also standard HAL modules.
        self.modules += camera_displays

        #
        # Other hardware control modules
        #

        # Load the requested modules.
        #
        add_separator = False
        for module in hardware.get("modules").getProps():
            hdebug.logText("Loading: " + module.get("hal_type"))
            a_module = halImport("storm_control.hal4000." + module.get("module_name"))
            a_class = getattr(a_module, module.get("class_name"))
            instance = a_class(module.get("parameters", False), parameters, self)
            instance.hal_type = module.get("hal_type")
            instance.hal_gui = module.get("hal_gui")
            if module.get("hal_gui"):
                add_separator = True
                a_action = QtWidgets.QAction(self.tr(module.get("menu_item")), self)
                self.ui.menuFile.insertAction(self.ui.actionQuit, a_action)
                a_action.triggered.connect(instance.show)
            self.modules.append(instance)

        # Insert a separator into the file menu if necessary.
        if add_separator:
            self.ui.menuFile.insertSeparator(self.ui.actionQuit)

        # Connect signals between modules, HAL and the camera.
        everything = self.modules + [self] + [self.camera]
        for from_module in everything:
            signals = from_module.getSignals()

            for to_module in everything:
                to_module.connectSignals(signals)

        # Finish module initialization
        everything = self.modules + [self.camera]
        for module in everything:
            module.moduleInit()

        #
        # More ui stuff
        #

        # Configure extensions combo-box.
        self.ui.extensionComboBox.clear()
        for ext in parameters.getp("film.extension").getAllowed():
            self.ui.extensionComboBox.addItem(ext)
        
        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # ui signals
        self.ui.actionDirectory.triggered.connect(self.newDirectory)
        self.ui.actionSettings.triggered.connect(self.newSettingsFile)
        self.ui.actionShutter.triggered.connect(self.newShuttersFile)
        self.ui.actionQuit.triggered.connect(self.handleClose)
        self.ui.autoIncCheckBox.stateChanged.connect(self.handleAutoInc)
        self.ui.autoShuttersCheckBox.stateChanged.connect(self.handleAutoShutters)
        self.ui.extensionComboBox.currentIndexChanged.connect(self.updateFilenameLabel)
        self.ui.filenameEdit.textChanged.connect(self.updateFilenameLabel)
        self.ui.filetypeComboBox.currentIndexChanged.connect(self.updateFilenameLabel)
        self.ui.indexSpinBox.valueChanged.connect(self.updateFilenameLabel)
        self.ui.lengthSpinBox.valueChanged.connect(self.updateLength)
        self.ui.modeComboBox.currentIndexChanged.connect(self.handleModeComboBox)
        self.ui.notesEdit.textChanged.connect(self.updateNotes)
        self.ui.recordButton.clicked.connect(self.toggleFilm)
        self.ui.liveModeCheckBox.stateChanged.connect(self.toggleLiveView)

        # live view mode button
        self.ui.liveModeCheckBox.setChecked(True) # Turn on live mode at initialization
        self.ui.liveModeCheckBox.setEnabled(True) # Enable the check box for user control
        
        # other signals
        self.parameters_box.settingsToggled.connect(self.toggleSettings)

        #
        # Load GUI settings
        #

        # HAL GUI settings.
        self.move(self.settings.value("main_pos", self.pos()))
        self.resize(self.settings.value("main_size", self.size()))
        self.xml_directory = str(self.settings.value("xml_directory", ""))

        # Module GUI settings.
        for module in self.modules:
            module.loadGUISettings(self.settings)

        #
        # start the camera
        #

        self.camera.cameraInit()

    ## cleanUp
    #
    # This is called upon closing the program. It stops all of the various
    # threads and disconnects from the hardware. This also saves the current 
    # GUI layout, i.e. the locations of the various windows and whether or 
    # not they are open.
    #
    @hdebug.debug
    def cleanUp(self):
        if self.filming:
            self.stopFilm()

        print(" Dave? What are you doing Dave?")
        print("  ...")

        # Save HAL GUI settings.
        self.settings.setValue("main_pos", self.pos())
        self.settings.setValue("main_size", self.size())
        self.settings.setValue("xml_directory", self.xml_directory)

        # Save module GUI settings.
        for module in self.modules:
            module.saveGUISettings(self.settings)

        # Close the film notes log file.
        self.logfile_fp.close()

        # stop the camera
        self.camera.close()

        # stop the modules.
        for module in self.modules:
            module.cleanup()

    ## closeEvent
    #
    # This called when the user wants to close the program.
    #
    # @param event A QEvent object.
    #
    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "commGotConnection"):
                signal[2].connect(self.handleCommStart)
            elif (signal[1] == "commLostConnection"):
                signal[2].connect(self.handleCommStop)
            elif (signal[1] == "commMessage"):
                signal[2].connect(self.handleCommMessage)
            elif (signal[1] == "toggleFilm"):
                signal[2].connect(self.handleToggleFilm)

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
    # This is called when a file is dropped on the main window. It
    # calls parameters.fileType() to figure out the type of the file.
    #
    # @param event A QEvent object containing the filenames.
    #
    @hdebug.debug
    def dropEvent(self, event):
        if self.filming:
            return
        filenames = []
        for url in event.mimeData().urls():
            #filenames.append(str(url.encodedPath())[1:])
            filenames.append(str(url.toLocalFile()))
        for filename in sorted(filenames):
            [file_type, error_text] = params.fileType(filename)
            if (file_type == "parameters"):
                self.newSettings(filename)
            elif (file_type == "shutters"):
                self.newShutters(filename)
            else:
                if error_text:
                    hdebug.logText(" " + filename + " is not a valid XML file.")
                    QtGui.QMessageBox.information(self,
                                                  "XML file parsing error",
                                                  error_text)
                else:
                    hdebug.logText(" " + filename + " is of unknown type")
                    QtGui.QMessageBox.information(self,
                                                  "File type not recognized",
                                                  "")

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [["hal", "tcpComplete", self.tcpComplete]]

    ## handleAutoInc
    #
    # This is called when the auto-increment check box is clicked.
    #
    # @param flag True if the check box is checked, false otherwise.
    #
    @hdebug.debug
    def handleAutoInc(self, flag):
        self.parameters.set("film.auto_increment", bool(flag))

    ## handleAutoShutters
    #
    # This is called when the run shutters check box is clicked.
    #
    # @param flag True if the check box is checked, false otherwise.
    #
    @hdebug.debug
    def handleAutoShutters(self, flag):
        self.parameters.set("film.auto_shutters", bool(flag))

    ## handleClose
    #
    # Called to quit the program.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleClose(self, bool):
        self.close()

    ## handleCommMessage
    #
    # Handles all the message from tcpControl.
    #
    # @param message A tcpMessage.TCPMessage object.
    #
    @hdebug.debug
    def handleCommMessage(self, message):

        # Handle abort request.
        if (message.getType() == "Abort Movie"):
            if self.tcp_message:
                if self.tcp_message.getType() == "Take Movie":
                    self.tcp_message.addResponse("aborted", True)
            if self.filming:
                self.stopFilm()
            return

        # Reject message if Hal is filming.
        #
        # FIXME: Why? We used to allow this so that we could remotely set
        #    and adjust the power while filming.
        #
        if self.filming: 
            message.setError(True, "Hal is filming")
            self.tcpComplete.emit(message)
            return

        # Handle mosaic information request, pass mosaic XML data back:
        elif (message.getType() == "Get Mosaic Settings"):
            #message.addResponse("pixels_to_um", self.parameters.get("mosaic.pixels_to_um"))
            i = 1
            while self.parameters.has("mosaic.obj" + str(i)):
                message.addResponse("obj" + str(i), self.parameters.get("mosaic.obj" + str(i)))
                i += 1
            self.tcpComplete.emit(message)
            
        # Return the current objective.
        elif (message.getType() == "Get Objective"):
            obj_data = self.parameters.get("mosaic." + self.parameters.get("mosaic.objective"))
            message.addResponse("objective", obj_data.split(",")[0])
            self.tcpComplete.emit(message)
            
        # Handle set directory request:
        elif (message.getType() == "Set Directory"):

            if message.isTest():
                # Check that the directory exists.
                self.directory_test_mode = message.getData("directory")
                if not os.path.isdir(self.directory_test_mode):
                    message.setError(True, str(self.directory_test_mode) + " is an invalid directory")

            else:
                # Change directory if requested.
                new_directory = message.getData("directory")
                if not os.path.isdir(new_directory):
                    message.setError(True, str(new_directory) + " is an invalid directory")
                else:
                    self.newDirectory(new_directory)

            self.tcpComplete.emit(message)

        # Handle set parameters request.
        elif (message.getType() == "Set Parameters"):
            param_index = message.getData("parameters")
            if message.isTest():
                if not self.parameters_box.isValidParameters(param_index):
                    message.setError(True, str(param_index) + " is an invalid parameters option")
                    self.tcpComplete.emit(message)

                # Save parameters to keep track of parameter trajectory for accurate time and disk estimates.
                else:
                    self.parameters_test_mode = self.parameters_box.getParameters(param_index)
                    if not self.parameters_test_mode.get("initialized"):
                        self.tcp_message = message # Store message so that it can be returned.
                        self.parameters_box.setCurrentParameters(param_index)
                    else:
                        self.tcpComplete.emit(message)

            else:
                # Set parameters, double check before filming.
                if self.parameters_box.isValidParameters(param_index):
                    self.tcp_message = message
                    if self.parameters_box.setCurrentParameters(param_index):
                        self.tcp_message = None
                        self.tcpComplete.emit(message)
                else:
                    message.setError(True, str(param_index) + " is an invalid parameters option")
                    self.tcpComplete.emit(message)
        
        # Handle movie request.
        elif (message.getType() == "Take Movie"):
   
            # Check length (independent of whether the message is a test).
            if (message.getData("length") == None) or (message.getData("length") < 1):
                message.setError(True, str(message.getData("length")) + "is an invalid movie length")
                self.tcpComplete.emit(message)
                return
            
            # Check file overwrite (independence of whether the message is a test)
            if not (message.getData("overwrite") == None) and (message.getData("overwrite") == False):
                file_path = self.directory_test_mode + os.sep + message.getData("name") + self.parameters.get("film.filetype")
                if os.path.exists(file_path):
                    message.setError(True, file_path + " will be overwritten")
                    self.tcpComplete.emit(message)
                    return

            if message.isTest():
                # Set parameters
                if self.parameters_test_mode:
                    parameters = self.parameters_test_mode
                else:
                    parameters = self.parameters
                
                # Get disk usage and duration.
                num_frames = message.getData("length")
                message.addResponse("duration", num_frames * parameters.get("seconds_per_frame"))
                mega_bytes_per_frame = parameters.get("camera1.bytes_per_frame") * 1.0/2**20 # Convert to megabytes.
                message.addResponse("disk_usage", mega_bytes_per_frame * num_frames)
                self.tcpComplete.emit(message)

            else: # Take movie.

                # Set filename.
                self.ui.filenameLabel.setText(message.getData("name") + self.parameters.get("film.filetype"))
                
                # Record current length and set film length spin box to requested length.
                self.current_length = self.parameters.get("film.frames")
                self.ui.lengthSpinBox.setValue(message.getData("length"))

                # Start the film.
                self.tcp_requested_movie = True
                self.tcp_message = message
                self.startFilm(filmSettings.FilmSettings("fixed_length", message.getData("length")))

    ## handleCommStart
    #
    # This is called when a external program connects.
    #
    @hdebug.debug
    def handleCommStart(self):
        self.directory_test_mode = self.directory[:-1]
        #self.parameters_test_mode = False

    ## handleCommStop
    #
    # This is called when a external program disconnects.
    #
    @hdebug.debug
    def handleCommStop(self):
        if self.current_directory:
            self.newDirectory(self.current_directory)
            self.current_directory = False

    ## handleToggleFilm
    #
    # Start/stop filming.
    #
    @hdebug.debug
    def handleToggleFilm(self):
        self.toggleFilm(False)

    ## handleModeComboBox
    #
    # This is called when the acquistion mode combo box is
    # selected. There are only two modes, run_till_abort and
    # fixed_length.
    #
    # @param mode The index of the mode the user selected.
    #
    @hdebug.debug
    def handleModeComboBox(self, mode):
        if (mode == 0):
            self.parameters.set("film.acq_mode", "run_till_abort")
        else:
            self.parameters.set("film.acq_mode", "fixed_length")
        self.showHideLength()

    ## newDirectory
    #
    # Show the new directory dialog box (if a directory is not specified.
    # Change to the new directory (if it exists).
    #
    # @param directory The new directory name (optional).
    #
    @hdebug.debug            
    def newDirectory(self, directory = False):
        if (not directory):
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                                   "New Directory", 
                                                                   str(self.parameters.get("film.directory")),
                                                                   QtWidgets.QFileDialog.ShowDirsOnly)
        if directory and os.path.exists(directory):
            self.directory = directory
            self.parameters.set("film.directory", str(self.directory))
            self.ui.directoryText.setText(trimString(self.parameters.get("film.directory"), 31))
        self.updateFilenameLabel("foo")

    ## newFrames
    #
    # This is called when there are new frames from the camera.
    #
    # @param frames A list of frame objects.
    #
    def newFrames(self, frames):
        for frame in frames:
            if self.filming:
                self.updateFramesForFilm(frame)

            for module in self.modules:
                module.newFrame(frame, self.filming)

    ## newParameters
    #
    # This is called after new parameters are selected. It changes the
    # film setting based on the new parameters and propogates the new
    # parameters to all of the various pieces of hardware.
    #
    @hdebug.debug
    def newParameters(self):

        # For conveniently accessing parameters
        p = self.parameters

        # Camera
        #
        # Note that the camera also modifies the parameters file, adding
        # some information about the frame rate, etc.. To record that this
        # as happened we set the initialized attribute of the parameters
        # to true.
        #
        self.camera.newParameters(p)
        p.set("initialized", True)

        # The working directory is set by the initial parameters. Subsequent
        # parameters files don't change the directory.
        if self.directory:
            p.set("film.directory", self.directory)
        else:
            self.directory = p.get("film.directory")

        # Modules.
        for module in self.modules:
            module.newParameters(p)

        # If we don't already have the shutter data for these parameters, 
        # then update shutter data using the shutter file specified by 
        # the parameters file.
        if p.get("illumination", False):
            if (p.get("illumination.shutters") != p.get("illumination.last_shutters")):
                self.newShutters(p.get("illumination.shutters"))
            else:
                self.ui.shuttersText.setText(getFileName(p.get("illumination.shutters")))
        else:
            self.ui.shuttersText.setText("NA")

        # Film settings.
        extension = p.get("film.extension") # Save a temporary copy as the original will get wiped out when we set the filename, etc.
        filetype = p.get("film.filetype")
        self.ui.directoryText.setText(trimString(p.get("film.directory"), 31))
        self.ui.filenameEdit.setText(p.get("film.filename"))
        if p.get("film.auto_increment"):
            self.ui.autoIncCheckBox.setChecked(True)
        else:
            self.ui.autoIncCheckBox.setChecked(False)

        self.ui.extensionComboBox.setCurrentIndex(self.ui.extensionComboBox.findText(extension))
        
        self.ui.filetypeComboBox.setCurrentIndex(self.ui.filetypeComboBox.findText(filetype))
        if p.get("film.acq_mode") == "run_till_abort":
            self.ui.modeComboBox.setCurrentIndex(0)
        else:
            self.ui.modeComboBox.setCurrentIndex(1)
        self.ui.lengthSpinBox.setValue(p.get("film.frames"))
        self.showHideLength()
        
        if p.get("film.auto_shutters"):
            self.ui.autoShuttersCheckBox.setChecked(True)
        else:
            self.ui.autoShuttersCheckBox.setChecked(False)
        self.updateFilenameLabel("foo")

        # Mosaic settings.
        self.ui.objectiveText.setText(p.get("mosaic." + p.get("mosaic.objective")).split(",")[0])

        # Return a Set Parameters TCP message if appropriate
        if not (self.tcp_message == None):
            self.tcpComplete.emit(self.tcp_message)
            self.tcp_message = None        

    ## newSettings
    #
    # Parse a parameters file & add it to the parameters combo box. The names
    # settings and parameters are used somewhat interchangeably.
    #
    # @param parameters_filename The name & path of the parameters file.
    #
    @hdebug.debug
    def newSettings(self, parameters_filename):

        # parse parameters file
        is_valid_xml = True
        try:
            parameters = params.halParameters(parameters_filename)
        except params.ParametersException:
            is_valid_xml = False
            hdebug.logText("failed to parse parameters file " + parameters_filename)
            QtWidgets.QMessageBox.information(self,
                                              "Parameter file parsing error",
                                              traceback.format_exc())
        if is_valid_xml:
            self.parameters_box.addParameters(parameters)

    ## newSettingsFile
    #
    # This is called when the user selects the new setting file menu option.
    # It opens a dialog where the user can select a new parameters file, then
    # tries to load the new parameter file.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def newSettingsFile(self, boolean):
        if self.filming:
            return
        parameters_filename = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                                    "New Settings",
                                                                    self.xml_directory, 
                                                                    "*.xml")[0]
        if parameters_filename:
            self.xml_directory = os.path.dirname(parameters_filename)
            self.newSettings(parameters_filename)

    ## newShutters
    #
    # Parse a shutters file & if successful, update the main window UI,
    # the camera (shutter sequence length) and the spot counter (frame
    # colors and shutter sequence length). If a module handles shutter
    # file parsing & it does not like the shutters file then it should
    # throw some kind of error.
    #
    # @param shutters_filename The name of the shutters file.
    #
    @hdebug.debug
    def newShutters(self, shutters_filename):
        if self.filming:
            return
        new_shutters = False
        try:
            for module in self.modules:
                module.newShutters(shutters_filename)
            new_shutters = True
        except:
            QtWidgets.QMessageBox.information(self,
                                              "Shutter file parsing error",
                                              traceback.format_exc())
            hdebug.logText("failed to parse shutter file " + shutters_filename)
            for module in self.modules:
                module.newShutters(self.old_shutters_file)
            self.parameters.set("illumination.shutters", self.old_shutters_file)
        if new_shutters:
            self.parameters.set("illumination.shutters", shutters_filename)
            self.parameters.set("illumination.last_shutters", shutters_filename)
            self.old_shutters_file = shutters_filename
            self.ui.shuttersText.setText(getFileName(self.parameters.get("illumination.shutters")))
            params.setDefaultShutter(shutters_filename)
            
    ## newShuttersFile
    #
    # This is called when the user select new shutter sequence from the file menu.
    # It opens a GUI where the user can specify the new shutters file, then tries
    # to open the shutter file.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def newShuttersFile(self, bool):
        if self.filming:
            return
        shutters_filename = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                                  "New Shutter Sequence", 
                                                                  self.xml_directory, 
                                                                  "*.xml")[0]
        if shutters_filename:
            self.xml_directory = os.path.dirname(shutters_filename)
            self.newShutters(shutters_filename)

    ## showHideLength
    #
    # This is called show or hide movie length text box depending on whether
    # or not the filming mode is fixed length or run till abort.
    #
    @hdebug.debug
    def showHideLength(self):
        if self.ui.modeComboBox.currentIndex() == 0:
            self.ui.lengthLabel.setEnabled(False)
            self.ui.lengthSpinBox.setEnabled(False)
        else:
            self.ui.lengthLabel.setEnabled(True)
            self.ui.lengthSpinBox.setEnabled(True)

    ## startCamera
    #
    # Starts the camera.
    #
    @hdebug.debug
    def startCamera(self):
        self.camera.startCamera()

    ## startFilm
    #
    # Creates the film saving object, sets up all the hardware to take the 
    # film and then starts the camera.
    #
    # @param film_settings (Optional) A film_setting object, default is none.
    #
    @hdebug.debug
    def startFilm(self, film_settings = None):
        # Disable live mode check box
        self.ui.liveModeCheckBox.setEnabled(False)
        
        # Pause live view mode (if running)
        if self.ui.liveModeCheckBox.isChecked():
            self.stopCamera()
        self.stopLiveView()
        
        self.filming = True
        self.film_name = os.path.join(self.parameters.get("film.directory"), str(self.ui.filenameLabel.text()))
        self.film_name = self.film_name[:-len(self.ui.filetypeComboBox.currentText())]

        if film_settings is None:
            film_settings = filmSettings.FilmSettings(self.parameters.get("film.acq_mode"),
                                                      self.parameters.get("film.frames"))
            save_film = self.ui.saveMovieCheckBox.isChecked()
        else:
            save_film = True

        self.writer = None
        self.ui.recordButton.setText("Stop")
        try:
            # Film file prep
            if save_film:
                self.writer = writers.createFileWriter(self.ui.filetypeComboBox.currentText(),
                                                       self.film_name,
                                                       self.parameters,
                                                       self.camera.getFeedNamesToSave())
                self.camera.startFilm(self.writer, film_settings)
                self.ui.recordButton.setStyleSheet("QPushButton { color: red }")
            else:
                self.camera.startFilm(None, film_settings)
                self.ui.recordButton.setStyleSheet("QPushButton { color: orange }")
                self.film_name = False

            # Modules.
            for module in self.modules:
                module.startFilm(self.film_name, self.ui.autoShuttersCheckBox.isChecked())
                
        except halModule.StartFilmException as error: # Handle any start Film errors
            error_message = "startFilm() in HAL encountered an error: \n" + str(error)
            hdebug.logText(error_message)

            # Handle error returning to Dave. The subsequent call to stopFilm() will handle sending this message
            if self.tcp_requested_movie:
                message = self.tcp_message
                message.setError(True, error_message)

        # Disable parameters radio buttons.
        self.parameters_box.startFilm()

        # go...
        self.startCamera()

    ## startLiveView
    #
    # Turn on live view mode in hal and the modules
    #
    @hdebug.debug
    def startLiveView(self):
        is_live_view = self.ui.liveModeCheckBox.isChecked()

        # Start live view mode in all modules
        for module in self.modules:
            module.startLiveView(is_live_view)

    ## stopCamera
    #
    # Stop the camera.
    #
    @hdebug.debug
    def stopCamera(self):
        self.camera.stopCamera()

    ## stopFilm
    #
    # Stop the camera, finish up the file writer object, set all the hardware
    # back to the non-filming mode.
    #
    @hdebug.debug
    def stopFilm(self):
        self.filming = False

        # Beep to warn the user that the film is done in the case of longer 
        # fixed length films during which they might have passed out.
        if self.parameters.get("film.want_bell") and (self.parameters.get("film.acq_mode") == "fixed_length"):
            if (self.parameters.get("film.frames") > 1000):
                print("\7\7")

        # Stop the camera.
        self.stopCamera()
        try:
            self.camera.stopFilm()

            # Film file finishing up.
            if self.writer:

                # Stop modules.
                for module in self.modules:
                    module.stopFilm(self.writer)


                # Close film file.
                self.writer.closeFile()

                # Get any changes to the notes made during filming and update log file.
                self.updateNotes() 
                self.logfile_fp.write(str(datetime.datetime.now()) + "," + self.film_name + "," + str(self.parameters.get("film.notes")) + "\r\n")
                self.logfile_fp.flush()

                if self.ui.autoIncCheckBox.isChecked() and (not self.tcp_requested_movie):
                    self.ui.indexSpinBox.setValue(self.ui.indexSpinBox.value() + 1)
                self.updateFilenameLabel("foo")
            else:
                # Stop modules without writer.
                for module in self.modules:
                    module.stopFilm(False)

        except halModule.StopFilmException as error: # Handle any stopFilm exceptions
            error_message = "stopFilm in hal encountered an error: \n" + str(error)
            hdebug.logText(error_message)
            
            # Handle error returning to Dave. The message will be returned below.
            if self.tcp_requested_movie:
                message = self.tcp_message
                message.setError(True, error_message)
                        
        # Enable parameters radio buttons.
        self.parameters_box.stopFilm()

        # Notify tcp/ip client that the movie is finished
        # if the client requested the movie.
        if self.tcp_requested_movie:
            # Disable record button so that user can't take movies in HAL.
            # self.ui.recordButton.setEnabled(False)

            if (self.writer.getLockTarget() == "failed"):
                hdebug.logText("QPD/Camera appears to have frozen..")
                self.quit()

            # Return tcp requested message
            if self.tcp_message:
                message = self.tcp_message
                found_spots = self.writer.getSpotCounts()
                message.addResponse("found_spots", found_spots)

                length = self.writer.getFilmLength()
                message.addResponse("length", length)
                
                self.tcp_requested_movie = False
                self.tcp_message = None
                self.tcpComplete.emit(message)

                self.ui.lengthSpinBox.setValue(self.current_length)

        # Update record button status.
        self.ui.recordButton.setText("Record")
        self.ui.recordButton.setStyleSheet("QPushButton { color: black }")

        # Reenable live mode button
        self.ui.liveModeCheckBox.setEnabled(True)

        # Restart live view (if it was previously running)
        if self.ui.liveModeCheckBox.isChecked():
            self.startCamera() # Restart camera if in live mode
        self.startLiveView()        

    ## stopLiveView
    #
    # Turn off live view mode in hal and the modules
    #
    @hdebug.debug
    def stopLiveView(self):
        # Get the current state of the live mode check box
        is_live_view = self.ui.liveModeCheckBox.isChecked()
        
        # Stop live view mode in all modules
        for module in self.modules:
            module.stopLiveView(is_live_view)

    ## toggleFilm
    #
    # Start/stop filming. If this file already exists this will warn that
    # it is about to get overwritten.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def toggleFilm(self, boolean):
        if self.filming:
            self.stopFilm()
        else:
            reply = QtWidgets.QMessageBox.Yes
            if self.will_overwrite and self.ui.saveMovieCheckBox.isChecked():
                reply = QtWidgets.QMessageBox.question(self,
                                                       "Warning!",
                                                       "Overwrite Existing Movie?",
                                                       QtWidgets.QMessageBox.Yes,
                                                       QtWidgets.QMessageBox.No)
            if not self.ui.saveMovieCheckBox.isChecked():
                reply = QtWidgets.QMessageBox.question(self,
                                                       "Warning!",
                                                       "Do you know that the movie will not be saved?",
                                                       QtWidgets.QMessageBox.Yes,
                                                       QtWidgets.QMessageBox.No)
            if (reply == QtWidgets.QMessageBox.Yes):
                self.startFilm()

    ## toggleLiveView
    #
    # Turn on/off live mode. This is the only method that can change the internal attribute
    # 'live_view'
    #
    # @ param boolean Dummy parameter.
    @hdebug.debug
    def toggleLiveView(self, boolean):        
        # Get the state of the check box
        is_live_view = self.ui.liveModeCheckBox.isChecked()
        
        if is_live_view:
            # Start the camera
            self.startCamera()
            self.startLiveView() 

        else:
            # Stop the camera
            self.stopCamera()
            self.stopLiveView() 

    ## toggleSettings
    #
    # This is called when the user changes the parameters in the parameters GUI.
    # It stops the camera & switches to the new parameters.
    #
    @hdebug.debug
    def toggleSettings(self):
        self.parameters = self.parameters_box.getCurrentParameters()

        # Stop live view
        if self.ui.liveModeCheckBox.isChecked():
            self.stopCamera()
        self.stopLiveView()
        
        # Try setting the parametersc
        try:
            self.newParameters()

        # FIXME: This should not catch all errors.
        except:
            hdebug.logText("bad parameters")
            QtWidgets.QMessageBox.information(self,
                                              "Bad parameters",
                                              traceback.format_exc())
        self.parameters_box.updateParameters()

        # Restart live view
        if self.ui.liveModeCheckBox.isChecked():
            self.startCamera()
        self.startLiveView()

    ## updateFilenameLabel
    #
    # This is called when any of the various file name GUI boxes are modified
    # to update what the final file name will be. If this is the name of a
    # file that already exists the file name is displayed in red. The dummy
    # parameter is so that argument list matches that expected by the
    # PyQt signals that this handles.
    #
    # @param dummy This is not used.
    #
    @hdebug.debug
    def updateFilenameLabel(self, dummy):
        name = str(self.ui.filenameEdit.displayText())
        self.parameters.set("film.filename", name)

        name += "_{0:04d}".format(self.ui.indexSpinBox.value())

        self.parameters.set("film.extension", str(self.ui.extensionComboBox.currentText()))
        if len(self.parameters.get("film.extension")) > 0:
            name += "_" + self.parameters.get("film.extension")

        self.parameters.set("film.filetype", str(self.ui.filetypeComboBox.currentText()))
        name += self.parameters.get("film.filetype")

        self.ui.filenameLabel.setText(name)
        if os.path.exists(os.path.join(self.parameters.get("film.directory"), name)):
            self.will_overwrite = True
            self.ui.filenameLabel.setStyleSheet("QLabel { color: red}")
        else:
            self.will_overwrite = False
            self.ui.filenameLabel.setStyleSheet("QLabel { color: black}")

    ## updateFramesForFilm
    #
    # When filming, this updates the main window UI that displays how many
    # frames have been taken and how large the current film is.
    #
    # @param frame A frame object.
    #
    def updateFramesForFilm(self, frame):
        if frame.master:
            # The first frame is numbered zero so we need to adjust for that.
            self.ui.framesText.setText("%d" % (frame.number+1))
            if self.writer: # The flag for whether or not we are actually saving anything.
                size = self.camera.getFilmSize()
                if size < 1000.0:
                    self.ui.sizeText.setText("%.1f MB" % size)
                else:
                    self.ui.sizeText.setText("%.1f GB" % (size * 0.00097656))

    ## updateLength
    #
    # This is called by the film length spin box to change how long a fixed
    # length film will be.
    #
    # @param length The new film length.
    #
    @hdebug.debug
    def updateLength(self, length):
        self.parameters.set("film.frames", length)

    ## updateNotes
    #
    # This is called when the notes box is editted. The notes are saved in
    # the .inf file associated with the film.
    #
    @hdebug.debug
    def updateNotes(self):
        self.parameters.set("film.notes", str(self.ui.notesEdit.toPlainText()))


class HALCore(QtCore.QObject):
    """
    The core of it all. It sets everything else up, handles the message passing
    and tears everything down.
    """
    def __init__(self, config, **kwds):
        super().__init__(**kwds)

        self.modules = []
        self.queued_messages = deque()
        self.sent_messages = []
        self.settings = QtCore.QSettings("storm-control", "hal4000" + config.get("setup_name").lower())
        self.sync_timer = QtCore.QTimer(self)

        self.sync_timer.setInterval(50)
        self.sync_timer.timeout.connect(self.handleMessage)
        self.sync_timer.setSingleShot(True)

        # Load all the modules.
        for module in config.get("modules").getProps():
            a_module = importlib.import_module("storm_control.hal4000." + module.get("module_name"))
            a_class = getattr(a_module, module.get("class_name"))
            self.modules.append(a_class(module, self.settings, self))

        # Connect signals.
        for module in self.modules:
            module.newFrame.connect(self.handleNewFrame)
            module.newMessage.connect(self.handleNewMessage)

        # Configure
        self.handleMessage(halMessage.HalMessage(source = "core",
                                                 mtype = "configure",
                                                 sync = False))

        # Start
        self.handleMessage(halMessage.HalMessage(source = "core",
                                                 mtype = "start",
                                                 sync = True))
        
    def cleanup(self):
        for module in self.modules:
            module.cleanup(self.settings)

    def handleFrame(self, new_frame):
        """
        I was split on whether or not these should also just be messages.
        However, since there will likely be a lot of them I decided they 
        should be handled separately.
        """
        for module in self.modules:
            module.handleFrame(new_frame)
            
    def handleMessage(self, message = None):

        # Remove all the messages that have already been
        # handled from the list of sent messages.
        for sent_message in self.sent_messages:
            if (sent_message.ref_count == 0):
                self.sent_messages.remove(sent_message)
                sent_message.finalize()

        # Add this message to the queue.
        if message is not None:
            self.queued_messages.append(message)

        # Process the next message.
        if (len(self.queued_messages) > 0):
            cur_message = self.queued_message.popleft()

            #
            # If this message requested synchronization and there are
            # pending messages then push it back into the queue and wait.
            #
            if cur_message.sync and (len(self.sent_messages) > 0):
                self.queued_messages.appendleft(cur_message)
                self.sync_timer.start()

            #
            # Otherwise send the message.
            #
            else:
                for module in self.modules:
                    cur_message.ref_count += 1
                    module.handleMessage(cur_message)

                # Process any remaining messages.
                #
                # Maybe use a timer here so that there is time to
                # do something else between the messages?
                #
                if (len(self.queued_messages) > 0):
                    self.handleMessage()

    
if (__name__ == "__main__"):

    # Use both so that we can pass sys.argv to QApplication.
    import argparse
    import sys

    # Get command line arguments..
    parser = argparse.ArgumentParser(description = 'STORM microscope control software')
    parser.add_argument('config', type=str, help = "The name of the configuration file to use.")

    args = parser.parse_args()

    # FIXME: Should allow an (optional) initial setup file name.
    
    # Start..
    app = QtWidgets.QApplication(sys.argv)

    # Set default font size for linux.
    if (sys.platform == "linux2"):
        font = QtGui.QFont()
        font.setPointSize(8)
        app.setFont(font)

    # Splash Screen.
    pixmap = QtGui.QPixmap("splash.png")
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Load configuration.
    config = params.config(args.config)

    # Setup HAL and all of the modules.
    hal = Window(config)

    # Hide splash screen and start.
    splash.hide()
    hal.show()

    app.exec_()


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
