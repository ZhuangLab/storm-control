#!/usr/bin/python
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
#
# Hazen 12/12
#

import os
import sys
import datetime
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# Misc.
import halLib.parameters as params
import halLib.imagewriters as writers
import qtWidgets.qtParametersBox as qtParametersBox

# helper functions
def trimString(string, max_len):
    if len(string) > max_len:
        return "..." + string[-(max_len-3):]
    else:
        return string

def getFileName(path):
    return os.path.splitext(os.path.basename(path))[0]

#
# Main window
#
class Window(QtGui.QMainWindow):
    reachedMaxFrames = QtCore.pyqtSignal()

    @hdebug.debug
    def __init__(self, parameters, parent = None):
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
        self.settings = QtCore.QSettings("Zhuang Lab", "hal-4000")
        self.software_max_frames = False
        self.ui_mode = ""
        self.will_overwrite = False
        self.writer = False

        # Logfile setup
        self.logfile_fp.write("\r\n")
        self.logfile_fp.flush()

        #
        # Load the camera module
        #
        # The camera module defines (to some extent) what the HAL UI
        # will look like.
        #
        setup_name = parameters.setup_name.lower()
        the_camera = __import__('camera.' + setup_name + 'Camera', globals(), locals(), [setup_name], -1)
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

        self.parameters_box = qtParametersBox.QParametersBox(self.ui.settingsScrollArea)
        self.ui.settingsScrollArea.setWidget(self.parameters_box)
        self.ui.settingsScrollArea.setWidgetResizable(True)
        self.parameters_box.addParameters(self.parameters)

        file_types = writers.availableFileFormats()
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
            self.connect(self.tcp_control, QtCore.SIGNAL("abortMovie()"), self.handleCommAbortMovie)
            self.connect(self.tcp_control, QtCore.SIGNAL("commGotConnection()"), self.handleCommStart)
            self.connect(self.tcp_control, QtCore.SIGNAL("commLostConnection()"), self.handleCommStop)
            self.connect(self.tcp_control, QtCore.SIGNAL("parameters(int)"), self.handleCommParameters)
            self.connect(self.tcp_control, QtCore.SIGNAL("movie(PyQt_PyObject, int)"), self.handleCommMovie)
            self.connect(self.tcp_control, QtCore.SIGNAL("setDirectory(PyQt_PyObject)"), self.handleCommSetDirectory)

        #
        # Hardware control modules
        #

        # This is the classic single-window HAL display. To work properly, the camera 
        # controls UI elements that "belong" to the main window and vice-versa.
        if (self.ui_mode == "single"):
            self.camera = the_camera.ACamera(parameters,
                                             self.ui.cameraFrame,
                                             self.ui.cameraParamsFrame,
                                             parent = self)
            layout = QtGui.QGridLayout(self.ui.cameraFrame)
            layout.setMargin(0)
            layout.addWidget(self.camera.getCameraDisplay())
            self.ui.recordButton = self.camera.getRecordButton()
        # Both detached and dual-modes have the proper separation of UI elements
        else:
            self.camera = the_camera.ACamera(parameters,
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
        if parameters.have_illumination:
            illuminationControl = __import__('illumination.' + setup_name + 'IlluminationControl', globals(), locals(), [setup_name], -1)
            self.illumination_control = illuminationControl.AIlluminationControl(parameters,
                                                                                 self.tcp_control,
                                                                                 parent = self)
            shutterControl = __import__('illumination.' + setup_name + 'ShutterControl', globals(), locals(), [setup_name], -1)
            self.shutter_control = shutterControl.AShutterControl(self.illumination_control.power_control.powerToVoltage)

        # Motorized stage control
        self.stage_control = False
        if parameters.have_stage:
            stagecontrol = __import__('stagecontrol.' + setup_name + 'StageControl', globals(), locals(), [setup_name], -1)
            self.stage_control = stagecontrol.AStageControl(parameters, self.tcp_control, parent = self)

        # Piezo Z stage with feedback control
        self.focus_lock = False
        if parameters.have_focus_lock:
            focusLock = __import__('focuslock.' + setup_name + 'FocusLockZ', globals(), locals(), [setup_name], -1)
            self.focus_lock = focusLock.AFocusLockZ(parameters,
                                                    self.tcp_control,
                                                    parent = self)

        # Spot counter
        self.spot_counter = False
        if parameters.have_spot_counter:
            import spotCounter
            self.spot_counter = spotCounter.SpotCounter(parameters,
                                                        parent = self)

        # Misc control
        #  This needs the camera display area for the purpose of capturing mouse events
        self.misc_control = False
        if parameters.have_misc_control:
            misccontrol = __import__('miscControl.' + setup_name + 'MiscControl', globals(), locals(), [setup_name], -1)
            self.misc_control = misccontrol.AMiscControl(parameters,
                                                         self.tcp_control,
                                                         self.camera.getCameraDisplayArea(),
                                                         parent = self)

        # Temperature logger
        self.temperature_logger = False
        if parameters.have_temperature_logger:
            import THUM.thum as thum
            self.temperature_logger = thum.Thum()

        # Progression control
        self.progression_control = False
        if parameters.have_progressions and parameters.have_illumination:
            import progressionControl
            self.progression_control = progressionControl.ProgressionControl(parameters,
                                                                             self.tcp_control,
                                                                             channels = self.illumination_control.getNumberChannels(),
                                                                             parent = self)
            self.connect(self.progression_control, QtCore.SIGNAL("progSetPower(int, float)"), self.handleProgSetPower)
            self.connect(self.progression_control, QtCore.SIGNAL("progIncPower(int, float)"), self.handleProgIncPower)

        # Joystick
        self.joystick_control = False
        if parameters.have_joystick:
            joystick = __import__('joystick.' + setup_name + 'JoystickControl', globals(), locals(), [setup_name], -1)
            self.joystick_control = joystick.AJoystick(parameters, parent = self)
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
        self.reachedMaxFrames.connect(self.handleMaxFrames)

        # camera signals
        self.camera.idleCamera.connect(self.idleCamera)
        self.camera.newFrames.connect(self.newFrames)

        # load GUI settings
        self.move(self.settings.value("main_pos", QtCore.QPoint(100, 100)).toPoint())

        self.gui_settings = [[self.illumination_control, "illumination"],
                             [self.stage_control, "stage"],
                             [self.focus_lock, "focus_lock"],
                             [self.spot_counter, "spot_counter"],
                             [self.misc_control, "misc"],
                             [self.progression_control, "progression"]]

        if (self.ui_mode == "detached"):
            self.gui_settings.append([self.camera, "camera1"])

        if (self.ui_mode == "dual"):
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
    ##
    ## Methods that handle external/remote commands.
    ##
    ## In keeping with the new tradition these should all
    ## be renamed tcpXYZ
    ##

    @hdebug.debug
    def handleCommAbortMovie(self):
        if self.filming:
            self.stopFilm()

    #
    # This is useful for those occasions where things get
    # messed up by having two programs connected at once.
    # Though this should not be possible?
    #
    @hdebug.debug
    def handleCommDisconnect(self):
        if self.tcp_control:
            self.tcp_control.disconnect()

    @hdebug.debug
    def handleCommMovie(self, name, length):

        # record old settings
        checked = self.ui.saveMovieCheckBox.isChecked()
        p = self.parameters
        old_settings = [p.acq_mode, p.frames]

        # set to new comm specific values
        self.ui.saveMovieCheckBox.setChecked(True)
        self.ui.filenameLabel.setText(name + p.filetype)
        p.acq_mode = "fixed_length"
        p.frames = length

        # start the film
        self.tcp_requested_movie = 1
        self.startFilm()

        # restore old settings
        if not checked:
            self.ui.saveMovieCheckBox.setChecked(False)
        [p.acq_mode, p.frames] = old_settings

    @hdebug.debug
    def handleCommParameters(self, index):
        self.parameters_box.setCurrentParameters(index)

    @hdebug.debug
    def handleCommSetDirectory(self, directory):
        if (not self.current_directory):
            self.current_directory = self.directory[:-1]
        self.newDirectory(directory)

    @hdebug.debug
    def handleCommStart(self):
        print "commStart"
        self.ui.recordButton.hide()
        if self.stage_control:
            self.stage_control.startLockout()

    @hdebug.debug
    def handleCommStop(self):
        print "commStop"
        self.ui.recordButton.show()
        if self.current_directory:
            self.newDirectory(self.current_directory)
            self.current_directory = False
        if self.stage_control:
            self.stage_control.stopLockout()


    ########################################################
    ##
    ## Methods for joystick control.
    ##

    @hdebug.debug
    def jstickLockJump(self, step_size):
        if self.focus_lock and (not self.filming):
            self.focus_lock.jump(step_size)

    @hdebug.debug
    def jstickMotion(self, x_speed, y_speed):
        if self.stage_control and (not self.filming):
            self.stage_control.jog(x_speed, y_speed)

    @hdebug.debug
    def jstickStep(self, x_step, y_step):
        if self.stage_control and (not self.filming):
            self.stage_control.step(x_step, y_step)
    
    @hdebug.debug
    def jstickToggleFilm(self):
        self.toggleFilm()

    ########################################################
    ##
    ## All other methods alphabetically ordered, for lack of a better system.
    ##

    @hdebug.debug
    def cleanUp(self):
        print " Dave? What are you doing Dave?"
        print "  ..."

        self.logfile_fp.close()

        # stop the camera
        self.camera.quit()

        # stop the spot counter
        if self.spot_counter:
            try:
                self.spot_counter.shutDown()
            except:
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

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    @hdebug.debug
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # FIXME: Does not handle paths with spaces in the name?
    @hdebug.debug
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filename = str(url.encodedPath())[1:]
            try:
                params.Parameters(filename)
                self.newSettings(filename)
            except Exception, e:
                print e
                print " Not a settings file, trying as shutters file"
                self.newShutters(filename)

    @hdebug.debug
    def handleAutoInc(self, flag):
        self.parameters.auto_increment = flag

    @hdebug.debug
    def handleAutoShutters(self, flag):
        self.parameters.auto_shutters = flag

    @hdebug.debug
    def handleFocusLock(self):
        if self.focus_lock:
            self.focus_lock.show()

    @hdebug.debug
    def handleIllumination(self):
        if self.illumination_control:
            self.illumination_control.show()

    @hdebug.debug
    def handleMaxFrames(self):
        if self.filming:
            self.stopFilm()

    @hdebug.debug
    def handleMiscControls(self):
        if self.misc_control:
            self.misc_control.show()

    @hdebug.debug
    def handleModeComboBox(self, mode):
        if mode == 0:
            self.parameters.acq_mode = "run_till_abort"
        else:
            self.parameters.acq_mode = "fixed_length"
        self.showHideLength()
        #self.changeCameraParameters()

    @hdebug.debug
    def handleProgIncPower(self, channel, power_inc):
        if self.illumination_control:
            self.illumination_control.remoteIncPower(channel, power_inc)

    @hdebug.debug  
    def handleProgressions(self):
        if self.progression_control:
            self.progression_control.show()

    @hdebug.debug
    def handleProgSetPower(self, channel, power):
        if self.illumination_control:
            self.illumination_control.remoteSetPower(channel, power)

    @hdebug.debug
    def handleSpotCounter(self):
        if self.spot_counter:
            self.spot_counter.show()

    @hdebug.debug
    def handleStage(self):
        if self.stage_control:
            self.stage_control.show()

    @hdebug.debug
    def handleSyncChange(self, sync):
        self.parameters.sync = sync

    @hdebug.debug
    def idleCamera(self):
        #
        # We should only get here in the event that we reach the end
        # of a fixed length film, so we stop the film.
        #
        # But we get here anyway due to some dead time between when
        # we start the camera thread and starting the camera acquiring?
        #
        # FIXME: Is this still true??
        if self.filming:
            self.stopFilm()

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
        # setup the illumination control (and the spot counter)
        #
        # note that the spot counter is also initialized by calling newShutters.
        #
        if self.illumination_control:
            self.illumination_control.newParameters(p)
            self.newShutters(p.shutters)

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

    @hdebug.debug
    def newSettings(self, parameters_filename):
        # parse parameters file
        parameters = params.Parameters(parameters_filename, is_HAL = True)
        self.parameters_box.addParameters(parameters)

    @hdebug.debug
    def newSettingsFile(self):
        self.stopCamera()
        parameters_filename = QtGui.QFileDialog.getOpenFileName(self, "New Settings", "", "*.xml")
        if parameters_filename:
            try:
                params.Parameters(str(parameters_filename), is_HAL = True)
                self.newSettings(str(parameters_filename))
            except:
                print "failed to parse settings file"
        else:
            self.startCamera()

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
                print "failed to parse shutter file."
                self.shutter_control.parseXML(self.old_shutters_file)
                self.parameters.shutters = self.old_shutters_file
            if new_shutters:
                self.parameters.shutters = shutters_filename
                self.old_shutters_file = shutters_filename
                self.ui.shuttersText.setText(getFileName(self.parameters.shutters))
                self.camera.setSyncMax(self.shutter_control.getCycleLength())
                params.setDefaultShutter(shutters_filename)
            if self.spot_counter:
                colors = self.shutter_control.getColors()
                self.spot_counter.newParameters(self.parameters, colors)
        else:
            self.parameters.shutters = shutters_filename
            self.old_shutters_file = shutters_filename
            self.ui.shuttersText.setText(getFileName(self.parameters.shutters))

    @hdebug.debug
    def newShuttersFile(self):
        self.stopCamera()
        shutters_filename = QtGui.QFileDialog.getOpenFileName(self, "New Shutter Sequence", "", "*.xml")
        if shutters_filename and self.shutter_control:
            self.newShutters(str(shutters_filename))
        self.startCamera()

    @hdebug.debug
    def quit(self):
        # Save GUI settings
        self.settings.setValue("main_pos", self.pos())
        for [object, name] in self.gui_settings:
            if object:
                self.settings.setValue(name + "_pos", object.pos())
                self.settings.setValue(name + "_visible", object.isVisible())

        self.close()

    @hdebug.debug
    def showHideLength(self):
        if self.ui.modeComboBox.currentIndex() == 0:
            self.ui.lengthLabel.hide()
            self.ui.lengthSpinBox.hide()
        else:
            self.ui.lengthLabel.show()
            self.ui.lengthSpinBox.show()

    @hdebug.debug
    def startCamera(self):
        self.camera.startCamera()

    @hdebug.debug
    def startFilm(self):
        self.filming = 1
        self.frame_count = 0
        save_film = self.ui.saveMovieCheckBox.isChecked()
        self.filename = self.parameters.directory + str(self.ui.filenameLabel.text())
        self.filename = self.filename[:-len(self.ui.filetypeComboBox.currentText())]

        # If the user wants a really long fixed length film we go to a software
        # stop mode to avoid problems with the Andor software trying to allocate
        # enough memory to store the entire film.
        if (self.parameters.acq_mode == "fixed_length") and (self.parameters.frames > 1000):
            self.software_max_frames = self.parameters.frames
            self.parameters.acq_mode = "run_till_abort"

        # film file prep
        self.ui.recordButton.setText("Stop")
        if save_film:
            self.writer = writers.createFileWriter(self.ui.filetypeComboBox.currentText(),
                                                   self.filename,
                                                   self.parameters)
            self.camera.startFilm(self.writer)
            self.ui.recordButton.setStyleSheet("QPushButton { color: red }")
        else:
            self.camera.startFilm(None)
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

    @hdebug.debug
    def stopCamera(self):
        self.camera.stopCamera()

    @hdebug.debug
    def stopFilm(self):
        self.filming = 0

        # we should only land here in the case of long fixed length films
        if self.software_max_frames != 0:
            self.software_max_frames = 0
            self.parameters.acq_mode = "fixed_length"

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
            self.tcp_control.sendComplete()
            self.tcp_requested_movie = 0

    def toggleFilm(self):
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
            if reply == QtGui.QMessageBox.Yes:
                self.startFilm()

    @hdebug.debug
    def toggleSettings(self):
        self.parameters = self.parameters_box.getCurrentParameters()
        self.stopCamera()
        self.newParameters()

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

    def updateFramesForFilm(self, frame):
        if frame.master:
            if self.software_max_frames and (frame.number >= self.software_max_frames):
                self.reachedMaxFrames.emit()
            # The first frame is numbered zero so we need to adjust for that.
            self.ui.framesText.setText("%d" % (frame.number+1))
            if self.writer: # The flag for whether or not we are actually saving anything.
                size = frame.number * self.parameters.bytesPerFrame * 0.000000953674
                if size < 1000.0:
                    self.ui.sizeText.setText("%.1f MB" % size)
                else:
                    self.ui.sizeText.setText("%.1f GB" % (size * 0.00097656))

    @hdebug.debug
    def updateLength(self, length):
        self.parameters.frames = length

    @hdebug.debug
    def updateNotes(self):
        self.parameters.notes = self.ui.notesEdit.toPlainText()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    # Splash Screen
    pixmap = QtGui.QPixmap("splash.png")
    splash = QtGui.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Load settings
    if len(sys.argv) > 1:
        parameters = params.Parameters(sys.argv[1])
    else:
        parameters = params.Parameters("settings_default.xml")
    setup_name = parameters.setup_name
    parameters = params.Parameters(setup_name + "_default.xml", is_HAL = True)
    parameters.setup_name = setup_name
    
    # Load app
    window = Window(parameters)
    window.newParameters()
    splash.hide()
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
