#!/usr/bin/python
#
## @file
#
# Heuristically programmed ALgorithmic STORM setup control.
#
# In its most basic form, this just runs a camera
# and displays (and records) the resulting data.
#
# ACamera:
#   Control, record and display the data from one (or more)
#   camera(s).
#
#  The camera control class should be a subclass of
#  camera.genericCamera, which (attempts to) encapsulate
#  all the stuff related to the controlling and displaying
#  the data from one or more cameras. Examples and related
#  classes can all be found in the camera directory.
#
#
# More advanced functionality is provided by the following
# classes which should be specialized as appropriate to
# interface with the hardware on the machine of interest.
# The Window __init__ method below demonstrates how these 
# modules are intended to be loaded and used. Basically,
# if requested, they are dynamically loaded based on the 
# machine name in the parameters file.
#
# These modules can also respond to "remote" signals
# that arrive via the tcp_control module.
#
#
# AFocusLockZ:
#   Piezo Z stage with QPD feedback and control.
#
# AIlluminationControl:
#   Control of laser powers. Control of shutters except
#   when filming.
#
# AShutterControl:
#   "Automatic" control of the shutters during filming.
#
# AStageControl:
#   Control of a motorized stage.
#
# Hazen 12/13
#

import os
import sys
import datetime
import traceback

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# Misc.
import camera.filmSettings as filmSettings
import halLib.parameters as params
import halLib.imagewriters as writers
import qtWidgets.qtAppIcon as qtAppIcon
import qtWidgets.qtParametersBox as qtParametersBox

## getFileName
#
# Returns the filename given a path.
#
# @param path The full path with the file name.
#
# @return Returns the file name.
#
def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]

## halImport
#
# Wrap __import__ to make dynamic import a little simpler.
#
# @param module_name The name of the module to import.
#
# @return Returns the module
#
def halImport(module_name):
    return __import__(module_name, globals(), locals(), [module_name], -1)

## trimString
#
# Trims string to max_len characters if string is longer than max_len.
#
# @param string The string to trim.
# @param max_len The maximum string length.
#
# @return Returns the trimmed string.
#
def trimString(string, max_len):
    if len(string) > max_len:
        return "..." + string[-(max_len-3):]
    else:
        return string

## Window
#
# The main window.
#
class Window(QtGui.QMainWindow):

    ## __init__
    #
    # Set up the main window, connect and initialize all the hardware.
    #
    # @param hardware The hardware associated with this setup.
    # @param parameters The initial (and default) parameters for the hardware.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # General (alphabetically ordered)
        self.current_directory = False
        self.directory = False
        self.filename = ""
        self.filming = False
        self.logfile_fp = open(parameters.logfile, "a")
        self.old_shutters_file = ""
        self.parameters = parameters
        self.running_shutters = False
        self.settings = QtCore.QSettings("Zhuang Lab", "hal-4000_" + parameters.setup_name.lower())
        self.ui_mode = ""
        self.will_overwrite = False
        self.writer = False

        # Logfile setup
        self.logfile_fp.write("\r\n")
        self.logfile_fp.flush()

        
        setup_name = parameters.setup_name.lower()

        #
        # Load the camera module
        #
        # The camera module defines (to some extent) what the HAL UI
        # will look like.
        #
        the_camera = halImport('camera.' + hardware.camera.module)
        self.ui_mode = the_camera.getMode()

        #
        # UI setup, this is one of:
        #
        # 1. single: single window, single camera
        # 2. detached: detached camera window, single camera
        # 3. dual: detached camera windows, dual camera
        #
        if (self.ui_mode == "single"):
            import qtdesigner.hal4000_ui as hal4000Ui
        elif (self.ui_mode == "detached"):
            import qtdesigner.hal4000_detached_ui as hal4000Ui
        elif (self.ui_mode == "dual"):
            import qtdesigner.hal4000_detached_ui as hal4000Ui
        else:
            print "unrecognized mode:", self.ui_mode
            print " mode should be one of: single, detached or dual"
            exit()

        # Load the ui
        self.ui = hal4000Ui.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle(self.parameters.setup_name)
        self.setWindowIcon(qtAppIcon.QAppIcon())

        self.parameters_box = qtParametersBox.QParametersBox(self.ui.settingsScrollArea)
        self.ui.settingsScrollArea.setWidget(self.parameters_box)
        self.ui.settingsScrollArea.setWidgetResizable(True)
        self.parameters_box.addParameters(self.parameters)

        file_types = writers.availableFileFormats(self.ui_mode)
        for type in file_types:
            self.ui.filetypeComboBox.addItem(type)

        #
        # Remote control via TCP/IP
        #
        self.tcp_requested_movie = 0
        self.tcp_control = 0
        if parameters.have_tcp_control:
            import tcpControl
            self.tcp_control = tcpControl.TCPControl(parameters.tcp_port, parent = self)
            self.tcp_control.commGotConnection.connect(self.handleCommStart)
            self.tcp_control.commLostConnection.connect(self.handleCommStop)
            self.connect(self.tcp_control, QtCore.SIGNAL("abortMovie()"), self.handleCommAbortMovie)
            self.connect(self.tcp_control, QtCore.SIGNAL("parameters(int)"), self.handleCommParameters)
            self.connect(self.tcp_control, QtCore.SIGNAL("movie(PyQt_PyObject, int)"), self.handleCommMovie)
            self.connect(self.tcp_control, QtCore.SIGNAL("setDirectory(PyQt_PyObject)"), self.handleCommSetDirectory)

        #
        # Hardware control modules
        #

        # This is the classic single-window HAL display. To work properly, the camera 
        # controls UI elements that "belong" to the main window and vice-versa.
        if (self.ui_mode == "single"):
            self.camera = the_camera.ACamera(hardware.camera.parameters,
                                             parameters,
                                             self.ui.cameraFrame,
                                             self.ui.cameraParamsFrame,
                                             parent = self)
            self.ui.recordButton = self.camera.getRecordButton()

        # Both detached and dual-modes have the proper separation of UI elements
        else:
            self.camera = the_camera.ACamera(hardware.camera.parameters,
                                             parameters,
                                             parent = self)

        # Insert additional menu items for the camera(s) as necessary
        if (self.ui_mode == "detached"):
            self.ui.actionCamera1 = QtGui.QAction(self.tr("Camera"), self)
            self.ui.menuFile.insertAction(self.ui.actionFocus_Lock, self.ui.actionCamera1)
            self.ui.actionCamera1.triggered.connect(self.camera.showCamera1)

        if (self.ui_mode == "dual"):
            self.ui.actionCamera1 = QtGui.QAction(self.tr("Camera1"), self)
            self.ui.menuFile.insertAction(self.ui.actionFocus_Lock, self.ui.actionCamera1)
            self.ui.actionCamera1.triggered.connect(self.camera.showCamera1)

            self.ui.actionCamera2 = QtGui.QAction(self.tr("Camera2"), self)
            self.ui.menuFile.insertAction(self.ui.actionFocus_Lock, self.ui.actionCamera2)
            self.ui.actionCamera2.triggered.connect(self.camera.showCamera2)
        
        # AOTF / DAQ illumination control
        self.shutter_control = False
        self.illumination_control = False
        if hasattr(hardware, "illumination"):
            illuminationControl = halImport('illumination.' + hardware.illumination.module)
            self.illumination_control = illuminationControl.AIlluminationControl(hardware.illumination.parameters,
                                                                                 parameters,
                                                                                 self.tcp_control,
                                                                                 parent = self)
            shutterControl = halImport('illumination.' + hardware.shutters.module)
            self.shutter_control = shutterControl.AShutterControl(self.illumination_control.power_control.powerToVoltage)
        else:
            self.ui.actionIllumination.setEnabled(False)

        # XY motorized stage control
        self.stage_control = False
        if hasattr(hardware, "stage"):
            stagecontrol = halImport('stagecontrol.' + hardware.stage.module)
            self.stage_control = stagecontrol.AStageControl(hardware.stage.parameters,
                                                            parameters, 
                                                            self.tcp_control, 
                                                            parent = self)
        else:
            self.ui.actionStage.setEnabled(False)

        # Piezo Z stage with feedback control
        self.focus_lock = False
        if hasattr(hardware, "focuslock"):
            focusLock = halImport('focuslock.' + hardware.focuslock.module)
            self.focus_lock = focusLock.AFocusLockZ(hardware.focuslock.parameters,
                                                    parameters,
                                                    self.tcp_control,
                                                    parent = self)
        else:
            self.ui.actionFocus_Lock.setEnabled(False)

        # Spot counter
        single_camera = True
        if (self.ui_mode == "dual"):
            single_camera = False
        self.spot_counter = False
        if parameters.have_spot_counter:
            import spotCounter
            self.spot_counter = spotCounter.SpotCounter(parameters,
                                                        single_camera,
                                                        parent = self)
        else:
            self.ui.actionSpot_Counter.setEnabled(False)

        # Misc control
        #  This needs the camera display area for the purpose of capturing mouse events
        self.misc_control = False
        if hasattr(hardware, "misc_control"):
            misccontrol = halImport('miscControl.' + hardware.misc_control.module)
            self.misc_control = misccontrol.AMiscControl(hardware.misc_control.parameters,
                                                         parameters,
                                                         self.tcp_control,
                                                         self.camera.getCameraDisplayArea(),
                                                         parent = self)
        else:
            self.ui.actionMisc_Controls.setEnabled(False)

        # Temperature logger
        self.temperature_logger = False
        if hasattr(hardware, "temperature_logger"):
            temp_logger = halImport(hardware.temperature_logger.module)
            self.temperature_logger = temp_logger.ATemperatureLogger(hardware.temperature_logger.parameters)

        # Progression control
        self.progression_control = False
        if parameters.have_progressions and self.illumination_control:
            import progressionControl
            self.progression_control = progressionControl.ProgressionControl(parameters,
                                                                             self.tcp_control,
                                                                             channels = self.illumination_control.getNumberChannels(),
                                                                             parent = self)
            self.connect(self.progression_control, QtCore.SIGNAL("progSetPower(int, float)"), self.handleProgSetPower)
            self.connect(self.progression_control, QtCore.SIGNAL("progIncPower(int, float)"), self.handleProgIncPower)
        else:
            self.ui.actionProgression.setEnabled(False)

        # Joystick
        self.joystick_control = False
        if hasattr(hardware, "joystick"):
            joystick = halImport('joystick.' + hardware.joystick.module)
            self.joystick_control = joystick.AJoystick(hardware.joystick.parameters,
                                                       parameters,
                                                       parent = self)
            self.joystick_control.lock_jump.connect(self.jstickLockJump)
            self.joystick_control.motion.connect(self.jstickMotion)
            self.joystick_control.step.connect(self.jstickStep)
            self.joystick_control.toggle_film.connect(self.jstickToggleFilm)

        #
        # More ui stuff
        #

        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # ui signals
        self.ui.actionDirectory.triggered.connect(self.newDirectory)
        self.ui.actionDisconnect.triggered.connect(self.handleCommDisconnect)
        self.ui.actionFocus_Lock.triggered.connect(self.handleFocusLock)
        self.ui.actionIllumination.triggered.connect(self.handleIllumination)
        self.ui.actionMisc_Controls.triggered.connect(self.handleMiscControls)
        self.ui.actionProgression.triggered.connect(self.handleProgressions)
        self.ui.actionSettings.triggered.connect(self.newSettingsFile)
        self.ui.actionShutter.triggered.connect(self.newShuttersFile)
        self.ui.actionSpot_Counter.triggered.connect(self.handleSpotCounter)
        self.ui.actionStage.triggered.connect(self.handleStage)
        self.ui.actionQuit.triggered.connect(self.quit)
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

        # other signals
        self.parameters_box.settingsToggled.connect(self.toggleSettings)

        # camera signals
        self.camera.reachedMaxFrames.connect(self.stopFilm)
        self.camera.newFrames.connect(self.newFrames)

        # load GUI settings
        self.move(self.settings.value("main_pos", QtCore.QPoint(100, 100)).toPoint())

        self.gui_settings = [[self.illumination_control, "illumination"],
                             [self.stage_control, "stage"],
                             [self.focus_lock, "focus_lock"],
                             [self.spot_counter, "spot_counter"],
                             [self.misc_control, "misc"],
                             [self.progression_control, "progression"]]

        if (self.ui_mode == "single"):
            self.resize(self.settings.value("main_size", self.size()).toSize())

        elif (self.ui_mode == "detached"):
            self.camera.resize(self.settings.value("camera_size", self.camera.size()).toSize())
            self.gui_settings.append([self.camera, "camera1"])

        elif (self.ui_mode == "dual"):
            self.camera.camera1.resize(self.settings.value("camera1_size", self.camera.camera1.size()).toSize())
            self.camera.camera2.resize(self.settings.value("camera2_size", self.camera.camera2.size()).toSize())
            self.gui_settings.append([self.camera.camera1, "camera1"])
            self.gui_settings.append([self.camera.camera2, "camera2"])

        for [object, name] in self.gui_settings:
            if object:
                object.move(self.settings.value(name + "_pos", QtCore.QPoint(200, 200)).toPoint())
                if self.settings.value(name + "_visible", False).toBool():
                    object.show()

        #
        # start the camera
        #
        self.camera.cameraInit()

    ########################################################
    #
    # Methods that handle external/remote commands that come by TCP/IP.
    #
    # In keeping with the new tradition these should all
    # be renamed tcpXYZ
    #

    ## handleCommAbortMovie
    #
    # This is called when the external program wants to stop a movie.
    #
    @hdebug.debug
    def handleCommAbortMovie(self):
        if self.filming:
            self.stopFilm()

    ## handleCommDisconnect
    #
    # This is useful for those occasions where things get
    # messed up by having two programs connected at once.
    # Hopefully this is no longer possible so this method
    # is not needed.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleCommDisconnect(self, bool):
        if self.tcp_control:
            self.tcp_control.disconnect()

    ## handleCommMovie
    #
    # This called when the external program wants to take a movie.
    #
    # Notes:
    # 1. This will overwrite existing movies of the same
    #    name without asking or warning.
    # 2. The movie name is specified by the external program
    #    but the file type is still specified by HAL.
    #
    # @param name The name of the movie.
    # @param length The length of the movie in frames.
    #
    @hdebug.debug
    def handleCommMovie(self, name, length):

        # set to new comm specific values
        self.ui.filenameLabel.setText(name + self.parameters.filetype)

        # start the film
        self.tcp_requested_movie = True
        self.startFilm(filmSettings.FilmSettings("fixed_length", length))

    ## handleCommParameters
    #
    # This is called when the external program want to change
    # the current parameters. It can only select a parameters
    # file that has already been loaded.
    #
    # @param index The index of the desired parameter file.
    #
    @hdebug.debug
    def handleCommParameters(self, index):
        self.parameters_box.setCurrentParameters(index)

    ## handleCommSetDirectory
    #
    # This is called when the external program wants to change
    # the current working directory.
    #
    # @param directory
    #
    @hdebug.debug
    def handleCommSetDirectory(self, directory):
        if (not self.current_directory):
            self.current_directory = self.directory[:-1]
        self.newDirectory(directory)

    ## handleCommStart
    #
    # This is called when a external program connects.
    #
    @hdebug.debug
    def handleCommStart(self):
        print "commStart"
        self.ui.recordButton.setEnabled(False)
        if self.stage_control:
            self.stage_control.startLockout()

    ## handleCommStop
    #
    # This is called when a external program disconnects.
    #
    @hdebug.debug
    def handleCommStop(self):
        print "commStop"
        self.ui.recordButton.setEnabled(True)
        if self.current_directory:
            self.newDirectory(self.current_directory)
            self.current_directory = False
        if self.stage_control:
            self.stage_control.stopLockout()


    ########################################################
    #
    # Methods for joystick control.
    #

    ## jstickLockJump
    #
    # Jump the focus lock up or down by step_size.
    #
    # @param step_size Distance to jump the focus lock.
    #
    @hdebug.debug
    def jstickLockJump(self, step_size):
        if self.focus_lock and (not self.filming):
            self.focus_lock.jump(step_size)

    ## jstickMotion
    #
    # Move the XY stage at the given speed (um/s?)
    #
    # @param x_speed Speed at which to move the stage in x.
    # @param y_speed Speed at which to move the stage in y.
    #
    def jstickMotion(self, x_speed, y_speed):
        if self.stage_control and (not self.filming):
            self.stage_control.jog(x_speed, y_speed)

    ## jstickStep
    #
    # Step the XY stage a fixed amount (um?)
    #
    # @param x_step Distance to step the stage in x.
    # @param y_step Distance to step the stage in y.
    #
    def jstickStep(self, x_step, y_step):
        if self.stage_control and (not self.filming):
            self.stage_control.step(x_step, y_step)
    
    ## jstickToggleFilm
    #
    # Start/stop filming.
    #
    @hdebug.debug
    def jstickToggleFilm(self):
        self.toggleFilm()

    ########################################################
    #
    # All other methods alphabetically ordered, for lack of a better system.
    #

    ## cleanUp
    #
    # This is called upon closing the program. It stops all of the various
    # threads and disconnects from the hardware. This also saves the current 
    # GUI layout, i.e. the locations of the various windows and whether or 
    # not they are open.
    #
    @hdebug.debug
    def cleanUp(self):
        print " Dave? What are you doing Dave?"
        print "  ..."

        # Save GUI settings.
        self.settings.setValue("main_pos", self.pos())
        if (self.ui_mode == "single"):
            self.settings.setValue("main_size", self.size())

        elif (self.ui_mode == "detached"):
            self.settings.setValue("camera_size", self.camera.size())

        elif (self.ui_mode == "dual"):
            self.settings.setValue("camera1_size", self.camera.camera1.size())
            self.settings.setValue("camera2_size", self.camera.camera2.size())

        for [object, name] in self.gui_settings:
            if object:
                self.settings.setValue(name + "_pos", object.pos())
                self.settings.setValue(name + "_visible", object.isVisible())

        # Close the film notes log file.
        self.logfile_fp.close()

        # stop the camera
        self.camera.quit()

        # stop the spot counter
        if self.spot_counter:
            try:
                self.spot_counter.shutDown()
            except:
                print traceback.format_exc()
                print "problem stopping the spot counter."

        if self.illumination_control:
            # stop talking to the AOTF
            self.illumination_control.quit()

            # shutdown the national instruments stuff
            self.shutter_control.cleanup()
            self.shutter_control.shutDown()

        # shutdown the stage
        if self.stage_control:
            self.stage_control.quit()

        # shutdown the focus lock
        if self.focus_lock:
            self.focus_lock.quit()

        # shutdown the misc controls
        if self.misc_control:
            self.misc_control.quit()

        # shutdown the tcp/ip control
        if self.tcp_control:
            self.tcp_control.close()

        # shutdown the progression control
        if self.progression_control:
            self.progression_control.close()

        # shutdown joystick
        if self.joystick_control:
            self.joystick_control.close()

    ## closeEvent
    #
    # This called when the user wants to close the program.
    #
    # @param event A QEvent object.
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
    # This is called when a file is dropped on the main window. It
    # first tries to interpret the file as a parameters file, then
    # as a shutters file.
    #
    # @param event A QEvent object containing the filenames.
    #
    @hdebug.debug
    def dropEvent(self, event):
        filenames = []
        for url in event.mimeData().urls():
            #filenames.append(str(url.encodedPath())[1:])
            filenames.append(str(url.toLocalFile()))
        for filename in sorted(filenames):
            try:
                params.Parameters(filename)
                self.newSettings(filename)
            except:
                print traceback.format_exc()
                hdebug.logText(" Not a settings file, trying as shutters file")
                self.newShutters(filename)

    ## handleAutoInc
    #
    # This is called when the auto-increment check box is clicked.
    #
    # @param flag True if the check box is checked, false otherwise.
    #
    @hdebug.debug
    def handleAutoInc(self, flag):
        self.parameters.auto_increment = flag

    ## handleAutoShutters
    #
    # This is called when the shutters check box is clicked.
    #
    # @param flag True if the check box is checked, false otherwise.
    #
    @hdebug.debug
    def handleAutoShutters(self, flag):
        self.parameters.auto_shutters = flag

    ## handleFocusLock
    #
    # This is called to make the focus lock GUI visible, if 
    # there is a focus lock.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleFocusLock(self, bool):
        if self.focus_lock:
            self.focus_lock.show()

    ## handleIllumination
    #
    # This is called to make the illumination GUI visible, if
    # there is illumination control.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleIllumination(self, bool):
        if self.illumination_control:
            self.illumination_control.show()

    ## handleMiscControls
    #
    # This is called to make the misc controls GUI visible, if
    # there are misc controls.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleMiscControls(self, bool):
        if self.misc_control:
            self.misc_control.show()

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
        if mode == 0:
            self.parameters.acq_mode = "run_till_abort"
        else:
            self.parameters.acq_mode = "fixed_length"
        self.showHideLength()

    ## handleProgIncPower
    #
    # This is called by the progression GUI to cause the illumination
    # control to change the power of a particular channel.
    #
    # @param channel The channel (wavelength) to change.
    # @param power_inc The amount to change the power by.
    #
    @hdebug.debug
    def handleProgIncPower(self, channel, power_inc):
        if self.illumination_control:
            self.illumination_control.remoteIncPower(channel, power_inc)

    ## handleProgressions
    #
    # This is called to show the progressions GUI.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug  
    def handleProgressions(self, bool):
        if self.progression_control:
            self.progression_control.show()

    ## handleProgSetPower
    #
    # This is called by the progression GUI to cause the illumination
    # control to set the power of a channel to a particular value.
    #
    # @param channel The channel (wavelength) to set.
    # @param power The power to set channel to.
    #
    @hdebug.debug
    def handleProgSetPower(self, channel, power):
        if self.illumination_control:
            self.illumination_control.remoteSetPower(channel, power)

    ## handleSpotCounter
    #
    # This is called to show the spot counter GUI.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleSpotCounter(self, bool):
        if self.spot_counter:
            self.spot_counter.show()

    ## handleStage
    #
    # This is called to show the stage control GUI.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleStage(self, bool):
        if self.stage_control:
            self.stage_control.show()

    ## handleSyncChange
    #
    # This is called by the camera display GUI to set sync parameter.
    # Sync specifies which frame to show if we are taking a movie
    # with a multi-frame shutter sequence.
    #
    # FIXME: Is this still used? I think it is all in the camera
    #    display class now.
    @hdebug.debug
    def handleSyncChange(self, sync):
        self.parameters.sync = sync

    ## newDirectory
    #
    # Show the new directory dialog box (if a directory is not specified.
    # Change to the new directory (if it exists).
    #
    # @param directory The new directory name (optional).
    #
    @hdebug.debug            
    def newDirectory(self, directory = False):
        self.stopCamera()
        if (not directory):
            directory = str(QtGui.QFileDialog.getExistingDirectory(self, 
                                                                   "New Directory", 
                                                                   str(self.parameters.directory),
                                                                   QtGui.QFileDialog.ShowDirsOnly))
        if directory and os.path.exists(directory):
            self.directory = directory + "/"
            self.parameters.directory = self.directory
            self.ui.directoryText.setText(trimString(self.parameters.directory, 31))
        self.updateFilenameLabel("foo")
        self.startCamera()

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
                if self.focus_lock:
                    self.focus_lock.newFrame(frame)
                if self.illumination_control:
                    self.illumination_control.newFrame(frame)
                if self.progression_control:
                    self.progression_control.newFrame(frame)
            if self.spot_counter:
                self.spot_counter.newFrame(frame)
            if self.misc_control:
                self.misc_control.newFrame(frame)
            if self.temperature_logger:
                self.temperature_logger.newFrame(frame)

    ## newParameters
    #
    # This is called after new parameters are selected. It changes the
    # film setting based on the new parameters and propogates the new
    # parameters to all of the various pieces of hardware.
    #
    @hdebug.debug
    def newParameters(self):
        # for conveniently accessing parameters
        p = self.parameters

        #
        # setup camera
        #
        self.camera.newParameters(p)

        # The working directory is set by the initial parameters. Subsequent
        # parameters files don't change the directory
        if self.directory:
            p.directory = self.directory
        else:
            self.directory = p.directory

        #
        # Setup the illumination control (and the spot counter).
        #
        # If there is illumination control then the spot counter is initialized
        # in the call to newShutters, otherwise it is initialized here.
        #
        if self.illumination_control:
            self.illumination_control.newParameters(p)
            self.newShutters(p.shutters)
        else:
            if self.spot_counter:
                self.spot_counter.newParameters(p, [])

        #
        # setup the stage
        #
        if self.stage_control:
            self.stage_control.newParameters(p)

        #
        # setup the focus lock
        #
        if self.focus_lock:
            self.focus_lock.newParameters(p)

        #
        # setup the misc controls
        #
        if self.misc_control:
            self.misc_control.newParameters(p)

        #
        # setup the progressions
        #
        if self.progression_control:
            self.progression_control.newParameters(p)

        # film settings
        extension = p.extension # Save a temporary copy as the original will get wiped out when we set the filename, etc.
        filetype = p.filetype
        self.ui.directoryText.setText(trimString(p.directory, 31))
        self.ui.filenameEdit.setText(p.filename)
        if p.auto_increment:
            self.ui.autoIncCheckBox.setChecked(True)
        else:
            self.ui.autoIncCheckBox.setChecked(False)
        self.ui.extensionComboBox.clear()
        for ext in p.extensions:
            self.ui.extensionComboBox.addItem(ext)
        self.ui.extensionComboBox.setCurrentIndex(self.ui.extensionComboBox.findText(extension))
        self.ui.filetypeComboBox.setCurrentIndex(self.ui.filetypeComboBox.findText(filetype))
        if p.acq_mode == "run_till_abort":
            self.ui.modeComboBox.setCurrentIndex(0)
        else:
            self.ui.modeComboBox.setCurrentIndex(1)
        self.ui.lengthSpinBox.setValue(p.frames)
        self.showHideLength()
        if p.auto_shutters:
            self.ui.autoShuttersCheckBox.setChecked(True)
        else:
            self.ui.autoShuttersCheckBox.setChecked(False)
        self.updateFilenameLabel("foo")

        #
        # start the camera
        #        
        self.startCamera()

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
        parameters = params.Parameters(parameters_filename, is_HAL = True)
        self.parameters_box.addParameters(parameters)

    ## newSettingsFile
    #
    # This is called when the user selects the new setting file menu option.
    # It opens a dialog where the user can select a new parameters file, then
    # tries to load the new parameter file.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def newSettingsFile(self, bool):
        self.stopCamera()
        parameters_filename = QtGui.QFileDialog.getOpenFileName(self, "New Settings", "", "*.xml")
        if parameters_filename:
            try:
                params.Parameters(str(parameters_filename), is_HAL = True)
                self.newSettings(str(parameters_filename))
            except:
                print traceback.format_exc()
                print "failed to parse settings file"
        else:
            self.startCamera()

    ## newShutters
    #
    # Parse a shutters file & if successful, update the main window UI,
    # the camera (shutter sequence length) and the spot counter (frame
    # colors and shutter sequence length).
    #
    # @param shutters_filename The name of the shutters file.
    #
    @hdebug.debug
    def newShutters(self, shutters_filename):
        if self.shutter_control:
            self.shutter_control.stopFilm()
            self.shutter_control.cleanup()
        new_shutters = 0
        shutters_filename = str(shutters_filename)
        if self.shutter_control:
            try:
                self.shutter_control.parseXML(shutters_filename)
                new_shutters = 1
            except:
                print traceback.format_exc()
                hdebug.logText("failed to parse shutter file.")
                self.shutter_control.parseXML(self.old_shutters_file)
                self.parameters.shutters = self.old_shutters_file
            if new_shutters:
                self.parameters.shutters = shutters_filename
                self.old_shutters_file = shutters_filename
                self.ui.shuttersText.setText(getFileName(self.parameters.shutters))
                self.camera.setSyncMax(self.shutter_control.getCycleLength())
                params.setDefaultShutter(shutters_filename)
        else:
            self.parameters.shutters = shutters_filename
            self.old_shutters_file = shutters_filename
            self.ui.shuttersText.setText(getFileName(self.parameters.shutters))

        #
        # Setup the spot counter.
        #
        if self.spot_counter:
            colors = []
            if self.shutter_control:
                colors = self.shutter_control.getColors()
            self.spot_counter.newParameters(self.parameters, colors)

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
        self.stopCamera()
        shutters_filename = QtGui.QFileDialog.getOpenFileName(self, "New Shutter Sequence", "", "*.xml")
        if shutters_filename and self.shutter_control:
            self.newShutters(str(shutters_filename))
        self.startCamera()

    ## quit
    #
    # Called to quit the program. This saves the current GUI layout, i.e. the
    # locations of the various windows and whether or not they are open.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def quit(self, bool):
        self.close()

    ## showHideLength
    #
    # This is called show or hide movie length text box depending on whether
    # or not the filming mode is fixed length or run till abort.
    #
    @hdebug.debug
    def showHideLength(self):
        if self.ui.modeComboBox.currentIndex() == 0:
            self.ui.lengthLabel.hide()
            self.ui.lengthSpinBox.hide()
        else:
            self.ui.lengthLabel.show()
            self.ui.lengthSpinBox.show()

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
        self.filming = True
        self.filename = self.parameters.directory + str(self.ui.filenameLabel.text())
        self.filename = self.filename[:-len(self.ui.filetypeComboBox.currentText())]

        if not film_settings:
            film_settings = filmSettings.FilmSettings(self.parameters.acq_mode,
                                                      self.parameters.frames)
            save_film = self.ui.saveMovieCheckBox.isChecked()
        else:
            save_film = True

        # film file prep
        self.ui.recordButton.setText("Stop")
        if save_film:
            if (self.ui_mode == "dual"):
                self.writer = writers.createFileWriter(self.ui.filetypeComboBox.currentText(),
                                                       self.filename,
                                                       self.parameters,
                                                       ["camera1", "camera2"])
            else:
                self.writer = writers.createFileWriter(self.ui.filetypeComboBox.currentText(),
                                                       self.filename,
                                                       self.parameters,
                                                       ["camera1"])
            self.camera.startFilm(self.writer, film_settings)
            self.ui.recordButton.setStyleSheet("QPushButton { color: red }")
        else:
            self.camera.startFilm(None, film_settings)
            self.ui.recordButton.setStyleSheet("QPushButton { color: orange }")

        # stage
        if self.stage_control and (not self.tcp_requested_movie):
            self.stage_control.startLockout()

        # temperature / humidity logging
        if self.temperature_logger and save_film:
            self.temperature_logger.startThum(self.filename)

        # focus lock
        if self.focus_lock:
            if save_film:
                self.focus_lock.startLock(self.filename)
            else:
                self.focus_lock.startLock(0)

        # shutters
        self.running_shutters = 0 # This is necessary because if the user unchecks the shutters box
                                  # during a film and we looked at parameters.auto_shutters the
                                  # shutters would not get stopped at the end of the film.
        if self.illumination_control:
            if save_film:
                self.illumination_control.openFile(self.filename)
            if self.parameters.auto_shutters:
                self.running_shutters = 1

                # aotf prep
                channels_used = self.shutter_control.getChannelsUsed()
                self.shutter_control.prepare()
                self.illumination_control.startFilm(channels_used)
                
                # ni prep
                self.shutter_control.setup(self.parameters.kinetic_value)
                self.shutter_control.startFilm()
                    
        # spot counter
        if self.spot_counter:
            if save_film:
                self.spot_counter.startCounter(self.filename)
            else:
                self.spot_counter.startCounter(0)

        # progression control
        if self.progression_control:
            self.progression_control.startFilm()

        # go...
        self.startCamera()

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

        # beep to warn the user that the film is done in the case of longer 
        # fixed length films during which they might have passed out.
        if self.parameters.want_bell and (self.parameters.acq_mode == "fixed_length"):
            if (self.parameters.frames > 1000):
                print "\7\7"

        # film file finishing up
        if self.writer:
            self.camera.stopFilm()
            stage_position = [0.0, 0.0, 0.0]
            if self.stage_control:
                stage_position = self.stage_control.getStagePosition()
            lock_target = 0.0
            if self.focus_lock:
                lock_target = self.focus_lock.getLockTarget()
            self.updateNotes() # Get any changes to the notes made during filming.
            self.logfile_fp.write(str(datetime.datetime.now()) + "," + self.filename + "," + str(self.parameters.notes) + "\r\n")
            self.logfile_fp.flush()
            self.writer.closeFile(stage_position, lock_target)
            self.writer = False
            if self.ui.autoIncCheckBox.isChecked() and (not self.tcp_requested_movie):
                self.ui.indexSpinBox.setValue(self.ui.indexSpinBox.value() + 1)
            self.updateFilenameLabel("foo")
        else:
            self.camera.stopFilm()

        # shutters
        if self.illumination_control:
            self.illumination_control.closeFile()
            if self.running_shutters:
                # ni cleanup
                self.shutter_control.stopFilm()

                # aotf cleanup
                channels_used = self.shutter_control.getChannelsUsed()
                self.illumination_control.stopFilm(channels_used)

        # focus lock
        if self.focus_lock:
            self.focus_lock.stopLock()

        # stage
        if self.stage_control and (not self.tcp_requested_movie):
            self.stage_control.stopLockout()

        # temperature / humidity logging
        if self.temperature_logger:
            self.temperature_logger.stopThum()

        # spot counter
        if self.spot_counter:
            self.spot_counter.stopCounter()

        # progression control
        if self.progression_control:
            self.progression_control.stopFilm()

        # restart the camera
        self.startCamera()
        self.ui.recordButton.setText("Record")
        self.ui.recordButton.setStyleSheet("QPushButton { color: black }")

        # notify tcp/ip client that the movie is finished
        # if the client requested the movie.
        if self.tcp_requested_movie:

            if (lock_target == "failed"):
                hdebug.logText("QPD/Camera appears to have frozen..")
                self.quit()
            if self.spot_counter:
                self.tcp_control.sendComplete(str(self.spot_counter.getCounts()))
            else:
                self.tcp_control.sendComplete()
            self.tcp_requested_movie = False

    ## toggleFilm
    #
    # Start/stop filming. If this file already exists this will warn that
    # it is about to get overwritten.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def toggleFilm(self, bool):
        if self.filming:
            self.stopFilm()
        else:
            reply = QtGui.QMessageBox.Yes
            if self.will_overwrite and self.ui.saveMovieCheckBox.isChecked():
                reply = QtGui.QMessageBox.question(self,
                                                   #QtCore.QString(u"\u5C0F\u5FC3"),
                                                   "Warning!",
                                                   "Overwrite Existing Movie?",
                                                   QtGui.QMessageBox.Yes,
                                                   QtGui.QMessageBox.No)
            if not self.ui.saveMovieCheckBox.isChecked():
                reply = QtGui.QMessageBox.question(self,
                                                   #QtCore.QString(u"\u5C0F\u5FC3"),
                                                   "Warning!",
                                                   "Do you know that the movie will not be saved?",
                                                   QtGui.QMessageBox.Yes,
                                                   QtGui.QMessageBox.No)
            if (reply == QtGui.QMessageBox.Yes):
                self.startFilm()

    ## toggleSettings
    #
    # This is called when the user changes the parameters in the parameters GUI.
    # It stops the camera & switches to the new parameters.
    #
    @hdebug.debug
    def toggleSettings(self):
        self.parameters = self.parameters_box.getCurrentParameters()
        self.stopCamera()
        self.newParameters()

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
        self.parameters.filename = name

        name += "_{0:04d}".format(self.ui.indexSpinBox.value())

        self.parameters.extension = str(self.ui.extensionComboBox.currentText())
        if len(self.parameters.extension) > 0:
            name += "_" + self.parameters.extension

        self.parameters.filetype = str(self.ui.filetypeComboBox.currentText())
        name += self.parameters.filetype

        self.ui.filenameLabel.setText(name)
        if os.path.exists(self.parameters.directory + name):
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
        self.parameters.frames = length

    ## updateNotes
    #
    # This is called when the notes box is editted. The notes are saved in
    # the .inf file associated with the film.
    #
    @hdebug.debug
    def updateNotes(self):
        self.parameters.notes = self.ui.notesEdit.toPlainText()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # Splash Screen.
    pixmap = QtGui.QPixmap("splash.png")
    splash = QtGui.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Load settings.
    if (len(sys.argv) == 4):
        setup_name = sys.argv[1]
        hardware = params.Hardware(sys.argv[2])
        parameters = params.Parameters(sys.argv[3], is_HAL = True)
    else:
        parameters = params.Parameters("settings_default.xml")
        setup_name = parameters.setup_name
        hardware = params.Hardware(setup_name + "_hardware.xml")
        parameters = params.Parameters(setup_name + "_default.xml", is_HAL = True)
    params.setSetupName(parameters, setup_name)

    # Start logger.
    hdebug.startLogging(parameters.directory + "logs/", "hal4000")

    # Load app.
    window = Window(hardware, parameters)
    window.newParameters()
    splash.hide()
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
