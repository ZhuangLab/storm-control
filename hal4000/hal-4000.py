#!/usr/bin/python
#
# Heuristically programmed ALgorithmic STORM setup control.
#
# In its most basic form, this just runs a camera
# and displays (and records) the resulting data.
#
# cameraControl:
#   Control of a camera.
#
#  Methods called:
#    __init__(parameters, parent)
#      Class initializer.
#
#    cameraInit()
#      Called once the main program setup is finished.
#
#    getAcquisitionTimings()
#      Get the current acquisition timings.
#
#    getFrames()
#      Get frame data from the camera.
#
#    getTemperature()
#      Get the current camera temperature.
#
#    newFilmSettings(parameters, filming = 0)
#      Called when the film settings are changed.
#
#    newParameters(parameters)
#      Called when the parameters have been changed.
#
#    setEMCCGain(gain)
#      Set the EMCCD gain.
#
#    startAcq()
#      Start the camera.
#
#    startFilming(writer)
#      Setup the camera for filming, but do not actually
#      start the camera. Writer is a class used for storing
#      the data recorded by the camera.
#
#    stopAcq()
#      Stop the camera.
#
#    stopFilming()
#      Clean up from filming and stop the camera.
#
#    toggleShutter()
#      Open/close the shutter.
#
#    quit()
#      Called when the main program ends.
#
#  Signals emitted:
#    idleCamera()
#      The camera has reached the end of a fixed length
#      film and awaits further instruction.
#
#    newData()
#      New data is available from the camera.
#
#
# cameraDisplay:
#   Display the data from the camera & handle auto-scale, etc.
#
#  Methods called:
#    __init__(parameters, parent)
#       Class initializer.
#
#    displayFrame(frame)
#       Draw the data in frame on the screen.
#
#    newParameters(parameters)
#       Called when the parameters have been changed.
#
#    setSyncMax(int)
#
#  Signals emitted:
#    syncChange(int)
#       User changed the sync combo box.
#
#
# cameraParams:
#   Display the current camera parameters.
# 
#  Methods called:
#    __init__(parent)
#      Class initializer.
#
#    newParameters(parameters)
#      Called with new parameters.
#
#    newTemperature(temperature_data)
#      Called when the temperature has been updated.
#
#  Signals emitted:
#    gainChange(int)
#      The camera gain slider has been changed.
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
#  Methods called:
#    __init__(parameters, tcp_control, parent = ..)
#      Class initializer.
#
#    getLockTarget()
#      Returns the current lock target (in nm).
#
#    newFrame()
#      Called when filming and a new image is available
#      from the camera.
#
#    newParameters(parameters)
#      Called when the parameters file has been changed.
#
#    show()
#      Show the focus lock UI dialog box (if any).
#
#    startLock(filename)
#      Called when the filming (recording) starts. "filename"
#      can also be 0 meaning that we are taking a "test" film,
#      ie we are not actually saving the data.
#
#    stopLock()
#      Called when filming has ended.
#
#    quit()
#      Clean up and shutdown prior to the program ending.
#
#
# AIlluminationControl:
#   Control of laser powers. Control of shutters except
#   when filming.
#
#  Methods_called:
#    __init__(parameters, tcp_control, parent = ..)
#      Class initializer.
#
#    getNumberChannels()
#      Returns the number of channels that are controlled.
#
#    newFrame()
#      Called when a new frame of data is available. This
#      causes illuminationControl to write the current
#      power settings into the power log file.
#
#    newParameters(parameters)
#      Update sliders, buttons, etc. on the dialog box with
#      new settings.
#
#    openFile(filename)
#      Called before filming starts with the filename for
#      logging the power setting during filming. This function
#      appends ".power" to the filename & opens the file.
#
#    powerToVoltage(channel, power)
#      Returns what voltage corresponds to what power
#      (0.0 - 1.0).
#
#    quit()
#      Cleanup and shutdown prior to the program ending.
#
#    remoteIncPower(channel, power_inc)
#      Increment power of channel about amount power_inc
#
#    remoteSetPower(channel, power)
#      Set power of channel about to power
#
#    show()
#      Display the illumination control dialog box.
#
#    startFilm(channels_used)
#      Setup for filming. Prepare the specified channels
#      for automatic control via the shutterControl class.
#
#    stopFilm(channels_used)
#      Cleanup from filming. Close the power log file. Revert
#      the specified channels to manual control mode.
#
#
# AShutterControl:
#   "Automatic" control of the shutters during filming.
#
#  Methods called:
#    __init__(powerToVoltage)
#      Class initializer. powerToVoltage is function that takes
#      a channel and a power (0.0-1.0) and returns the appropriate
#      voltage (or equivalent) to use for this power in the
#      waveform.
#
#    cleanup()
#      Clean up and shutdown prior to the program ending.
#
#    getChannelsUsed()
#      Returns an array containing which channels are actually
#      used in the shutter sequence (as opposed to being always
#      off).
# 
#    getColors()
#      Returns the colors that the user specified in the shutter
#      file for the rendering of that particular frame by the
#      real time spot counter.
#
#    getCycleLength()
#      Returns the length of the shutter sequence in frames.
#
#    parseXML(illumination_file)
#      Parses the XML illumination file and generates the
#      corresponding Pyhon arrays to be loaded to a National
#      Instruments card (or equivalent).
#
#    setup(kinetic_cycle_time)
#      kinetic_cycle_time is the length of a frame in seconds.
#      This function is called to load the waveforms into
#      whatever hardware is going output them.
#    
#    startFilm()
#      Called at the start of filming to tell get the hardware
#      prepared.
#
#    stopFilm()
#      Called at the end of filming to tell the hardware to stop.
#
#
# AStageControl:
#   Control of a motorized stage.
#
#  Methods called:
#    __init__(parameters, self.tcp_control, parent = ..)
#      Class initializer.
#
#    newParameters(parameters)
#      Update stage settings with the new parameters.
#
#    quit()
#      Cleanup and shutdown prior to the program ending.
#
#    show()
#      Display the stage control dialog box.
#
#    startFilm()
#      Called when filming starts. At this point the stage
#      could be set to lockout the joystick control, if any.
#
#    stopFilm()
#      Called when filming finishes. If the joystick is 
#      locked out then maybe renable it.
#
#
# Hazen 10/09
#

import os
import sys
import datetime
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.hal4000_ui as halUi

# Experiment Control Modules

# Camera
import camera.cameraDisplay as cameraDisplay
import camera.cameraParams as cameraParams

# Misc.
import halLib.parameters as params
import halLib.imagewriters as writers

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
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # general (alphabetically ordered)
        self.current_directory = False
        self.cycle_length = 1
        self.debug = parameters.debug
        self.directory = 0
        self.display_timer = QtCore.QTimer(self)
        self.filename = ""
        self.filming = 0
        self.frame = 0
        self.frame_count = 0
        self.key = 0
        self.logfile_fp = open(parameters.logfile, "a")
        self.max_saved = 6
        self.old_shutters_file = ""
        self.parameters = parameters
        self.running_shutters = 0
        self.saved_parameters = []
        self.saved_parameters.append(parameters)
        self.settings = QtCore.QSettings("Zhuang Lab", "hal-4000")
        self.software_max_frames = 0
        self.will_overwrite = False
        self.writer = 0

        # logfile setup
        self.logfile_fp.write("\r\n")
        self.logfile_fp.flush()

        # ui setup
        self.ui = halUi.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setWindowTitle(self.parameters.setup_name)

        self.ui.settingsButton1.setText(getFileName(parameters.parameters_file))
        self.ui.settingsButton1.setChecked(True)
        self.ui.settingsButton2.hide()
        self.ui.settingsButton3.hide()
        self.ui.settingsButton4.hide()
        self.ui.settingsButton5.hide()
        self.ui.settingsButton6.hide()

        file_types = writers.availableFileFormats()
        for type in file_types:
            self.ui.filetypeComboBox.addItem(type)
        file_type_index = self.ui.filetypeComboBox.findText(parameters.filetype)
        if (file_type_index > -1):
            self.ui.filetypeComboBox.setCurrentIndex(self.ui.filetypeComboBox.findText(parameters.filetype))

        #
        # remote control via TCP/IP
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
        # experiment control modules
        #
        setup_name = parameters.setup_name.lower()
        camera_type = parameters.camera_type.lower()

        # Camera
        cameraControl = __import__('camera.' + camera_type + 'CameraControl', globals(), locals(), [camera_type], -1)
        self.camera_control = cameraControl.ACameraControl(parameters, parent = self)
        self.camera_display = cameraDisplay.CameraDisplay(parameters,
                                                          have_record_button = True,
                                                          have_shutter_button = True,
                                                          parent = self.ui.cameraFrame)
        self.ui.recordButton = self.camera_display.getRecordButton()
        self.ui.cameraShutterButton = self.camera_display.getShutterButton()
        layout = QtGui.QGridLayout(self.ui.cameraFrame)
        layout.setMargin(0)
        layout.addWidget(self.camera_display)
        self.camera_params = cameraParams.CameraParams(parent = self.ui.cameraParamsFrame)

        # AOTF / DAQ illumination control
        self.shutter_control = 0
        self.illumination_control = 0
        if parameters.have_illumination:
            illuminationControl = __import__('illumination.' + setup_name + 'IlluminationControl', globals(), locals(), [setup_name], -1)
            self.illumination_control = illuminationControl.AIlluminationControl(parameters, self.tcp_control, parent = self)
            shutterControl = __import__('illumination.' + setup_name + 'ShutterControl', globals(), locals(), [setup_name], -1)
            self.shutter_control = shutterControl.AShutterControl(self.illumination_control.power_control.powerToVoltage)

        # Motorized stage control
        self.stage_control = 0
        if parameters.have_stage:
            stagecontrol = __import__('stagecontrol.' + setup_name + 'StageControl', globals(), locals(), [setup_name], -1)
            self.stage_control = stagecontrol.AStageControl(parameters, self.tcp_control, parent = self)

        # Piezo Z stage with QPD feedback and control
        self.focus_lock = 0
        if parameters.have_focus_lock:
            focusLock = __import__('focuslock.' + setup_name + 'FocusLockZ', globals(), locals(), [setup_name], -1)
            self.focus_lock = focusLock.AFocusLockZ(parameters, self.tcp_control, parent = self)

        # spot counter
        self.spot_counter = 0
        if parameters.have_spot_counter:
            import spotCounter
            self.spot_counter = spotCounter.SpotCounter(parameters, parent = self)

        # misc control
        self.misc_control = 0
        if parameters.have_misc_control:
            misccontrol = __import__('miscControl.' + setup_name + 'MiscControl', globals(), locals(), [setup_name], -1)
            self.misc_control = misccontrol.AMiscControl(parameters, self.tcp_control, parent = self)

        # temperature logger
        self.temperature_logger = 0
        if parameters.have_temperature_logger:
            import THUM.thum as thum
            self.temperature_logger = thum.Thum()

        # Progression control
        self.progression_control = 0
        if parameters.have_progressions and parameters.have_illumination:
            import progressionControl
            self.progression_control = progressionControl.ProgressionControl(parameters,
                                                                             self.tcp_control,
                                                                             channels = self.illumination_control.getNumberChannels(),
                                                                             parent = self)
            self.connect(self.progression_control, QtCore.SIGNAL("progSetPower(int, float)"), self.handleProgSetPower)
            self.connect(self.progression_control, QtCore.SIGNAL("progIncPower(int, float)"), self.handleProgIncPower)

        #
        # More ui stuff
        #
        self.display_timer.setInterval(100)

        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # ui signals
        self.connect(self.ui.actionSettings, QtCore.SIGNAL("triggered()"), self.newSettingsFile)
        self.connect(self.ui.actionShutter, QtCore.SIGNAL("triggered()"), self.newShuttersFile)
        self.connect(self.ui.actionDirectory, QtCore.SIGNAL("triggered()"), self.newDirectory)
        self.connect(self.ui.actionDisconnect, QtCore.SIGNAL("triggered()"), self.handleCommDisconnect)
        self.connect(self.ui.actionFocus_Lock, QtCore.SIGNAL("triggered()"), self.handleFocusLock)
        self.connect(self.ui.actionIllumination, QtCore.SIGNAL("triggered()"), self.handleIllumination)
        self.connect(self.ui.actionMisc_Controls, QtCore.SIGNAL("triggered()"), self.handleMiscControls)
        self.connect(self.ui.actionProgression, QtCore.SIGNAL("triggered()"), self.handleProgressions)
        self.connect(self.ui.actionSpot_Counter, QtCore.SIGNAL("triggered()"), self.handleSpotCounter)
        self.connect(self.ui.actionStage, QtCore.SIGNAL("triggered()"), self.handleStage)
        self.connect(self.ui.actionQuit, QtCore.SIGNAL("triggered()"), self.quit)
        self.connect(self.ui.modeComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.handleModeComboBox)
        #self.connect(self.ui.cameraShutterButton, QtCore.SIGNAL("clicked()"), self.toggleShutter)
        self.connect(self.ui.autoShuttersCheckBox, QtCore.SIGNAL("stateChanged(int)"), self.handleAutoShutters)
        self.connect(self.ui.recordButton, QtCore.SIGNAL("clicked()"), self.toggleFilm)
        self.connect(self.ui.filenameEdit, QtCore.SIGNAL("textChanged(const QString&)"), self.updateFilenameLabel)
        self.connect(self.ui.lengthSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.updateLength)
        self.connect(self.ui.notesEdit, QtCore.SIGNAL("textChanged()"), self.updateNotes)
        self.connect(self.ui.extensionComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateFilenameLabel)
        self.connect(self.ui.indexSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.updateFilenameLabel)
        self.connect(self.ui.autoIncCheckBox, QtCore.SIGNAL("stateChanged(int)"), self.handleAutoInc)
        self.ui.filetypeComboBox.currentIndexChanged.connect(self.updateFilenameLabel)
        for i in range(self.max_saved):
            button = getattr(self.ui, "settingsButton" + str(i+1))
            self.connect(button, QtCore.SIGNAL("clicked()"), self.toggleSettings)
        self.connect(self, QtCore.SIGNAL("reachedMaxFrames()"), self.handleMaxFrames)

        # camera signals
        self.connect(self.camera_control, QtCore.SIGNAL("idleCamera()"), self.idleCamera)
        self.connect(self.camera_control, QtCore.SIGNAL("newData(int)"), self.newData)
        self.connect(self.camera_display, QtCore.SIGNAL("syncChange(int)"), self.handleSyncChange)
        self.connect(self.camera_params, QtCore.SIGNAL("gainChange(int)"), self.handleGainChange)
        self.connect(self.display_timer, QtCore.SIGNAL("timeout()"), self.displayFrame)

        # load GUI settings
        self.move(self.settings.value("main_pos", QtCore.QPoint(100, 100)).toPoint())

        for [object, name] in [[self.illumination_control, "illumination"],
                               [self.stage_control, "stage"],
                               [self.focus_lock, "focus_lock"],
                               [self.spot_counter, "spot_counter"],
                               [self.misc_control, "misc"],
                               [self.progression_control, "progression"]]:
            if object:
                object.move(self.settings.value(name + "_pos", QtCore.QPoint(200, 200)).toPoint())
                if self.settings.value(name + "_visible", False).toBool():
                    object.show()
         
        #
        # start the camera
        #
        self.camera_control.cameraInit()


    #
    # Methods that handle external/remote commands.
    #
    # In keeping with the new tradition these should all
    # be renamed tcpXYZ
    #

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
        self.ui.filenameLabel.setText(name)
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
        if index < self.saved_parameters:
            button = getattr(self.ui, "settingsButton" + str(index+1))
            button.click()

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


    #
    # All other methods alphabetically ordered, for lack of a better system
    #

    @hdebug.debug
    def changeCameraParameters(self):
        self.camera_control.newParameters(self.parameters)
        self.startCamera()

    @hdebug.debug
    def cleanUp(self):
        print " Dave? What are you doing Dave?"
        print "  ..."

        self.logfile_fp.close()

        # stop the camera
        self.camera_control.quit()

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

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    def displayFrame(self):
        self.camera_display.displayFrame(self.frame)

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
            except:
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
    def handleGainChange(self, gain):
        self.stopCamera()
        self.parameters.emccd_gain = gain
        self.camera_control.setEMCCDGain(self.parameters.emccd_gain)
        self.startCamera()

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
    def handleModeComboBox(self, mode):
        if mode == 0:
            self.parameters.acq_mode = "run_till_abort"
        else:
            self.parameters.acq_mode = "fixed_length"
        self.showHideLength()
        self.changeCameraParameters()

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
        if self.filming:
            self.stopFilm()

    def newData(self, key):
        #
        # The key check is to catch the camera thread returning images
        # from a previous acquisition "cycle", messing up the timing
        # in the current "cycle".
        #
        # Note that frame can be zero instead of being an image so
        # downstream code needs to catch that.
        #
        if key == self.key:
            frames = self.camera_control.getFrames()
            for frame in frames:
                if self.filming:
                    if self.parameters.sync:
                        if (self.frame_count % self.cycle_length) == (self.parameters.sync - 1):
                            self.frame = frame
                    else:
                        self.frame = frame
                    self.updateFramesForFilm()
                    if self.focus_lock:
                        self.focus_lock.newFrame(frame)
                    if self.illumination_control:
                        self.illumination_control.newFrame()
                    if self.progression_control:
                        self.progression_control.newFrame(self.frame_count)
                else:
                    self.frame = frame
                if self.spot_counter:
                    self.spot_counter.newImageToCount(frame)
                if self.misc_control:
                    self.misc_control.newFrame(frame)
                if self.temperature_logger:
                    self.temperature_logger.newData()

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

    @hdebug.debug
    def newParameters(self):
        # for conveniently accessing parameters
        p = self.parameters

        #
        # setup camera control
        #
        self.camera_control.newParameters(p)
        [p.exposure_value, p.accumulate_value, p.kinetic_value] = self.camera_control.getAcquisitionTimings()

        #
        # setup camera display
        #
        self.camera_display.newParameters(p)

        #
        # setup camera parameters
        #
        self.camera_params.newParameters(p)

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
        parameters = params.Parameters(parameters_filename)

        # add to the list of saved parameters, ejecting the oldest
        # added if the list is already too long.
        self.saved_parameters = [parameters] + self.saved_parameters
        if len(self.saved_parameters) > self.max_saved:
            self.saved_parameters.pop()

        # update the radio buttons to reflect the new parameters.
        for i, p in enumerate(self.saved_parameters):
            filename = getFileName(p.parameters_file)
            button = getattr(self.ui, "settingsButton" + str(i+1))
            button.setText(filename)
            button.show()

        # the new settings are the first settings, generate a 
        # click event on the first button.
        self.ui.settingsButton1.click()

    @hdebug.debug
    def newSettingsFile(self):
        self.stopCamera()
        parameters_filename = QtGui.QFileDialog.getOpenFileName(self, "New Settings", "", "*.xml")
        if parameters_filename:
            try:
                params.Parameters(str(parameters_filename))
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
                #self.ui.shuttersText.setText(trimString(self.parameters.shutters, 21))
                self.ui.shuttersText.setText(getFileName(self.parameters.shutters))
                self.cycle_length = self.shutter_control.getCycleLength()
                self.camera_display.setSyncMax(self.cycle_length)
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
        for [object, name] in [[self.illumination_control, "illumination"],
                               [self.stage_control, "stage"],
                               [self.focus_lock, "focus_lock"],
                               [self.spot_counter, "spot_counter"],
                               [self.misc_control, "misc"],
                               [self.progression_control, "progression"]]:
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
        self.updateTemperature()
        self.camera_control.startAcq(self.key)
        self.display_timer.start()

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
            print self.filename
            self.writer = writers.createFileWriter(self.ui.filetypeComboBox.currentText(),
                                                   self.filename,
                                                   self.parameters)
            self.camera_control.startFilming(self.writer)
            self.ui.recordButton.setStyleSheet("QPushButton { color: red }")
        else:
            self.camera_control.startFilming(None)
#            self.stopCamera()
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

        # display frame synchronization spin box
        self.camera_display.startFilm()

        # go...
        self.startCamera()

    @hdebug.debug
    def stopCamera(self):
        self.key += 1
        self.frame = 0
        self.display_timer.stop()
        # Since checking the temperature will stop the camera, it
        # is only necessary to check the temperature.
        self.updateTemperature()

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
            self.camera_control.stopFilming()
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
            self.writer = 0
            if self.ui.autoIncCheckBox.isChecked() and (not self.tcp_requested_movie):
                self.ui.indexSpinBox.setValue(self.ui.indexSpinBox.value() + 1)
            self.updateFilenameLabel("foo")
        else:
            self.camera_control.stopFilming()
#            self.stopCamera()

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

        # hide frame synchronization spin box
        self.camera_display.stopFilm()
            
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
        for i, p in enumerate(self.saved_parameters):
            button = getattr(self.ui, "settingsButton" + str(i+1))
            if button.isChecked():
                self.parameters = p
                self.stopCamera()
                self.newParameters()

    @hdebug.debug
    def toggleShutter(self):
        open = self.camera_control.toggleShutter()
        if open:
            self.ui.cameraShutterButton.setText("Close Shutter")
            self.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.ui.cameraShutterButton.setText("Open Shutter")
            self.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")
        self.startCamera()

    @hdebug.debug
    def updateFilenameLabel(self, dummy):
        name = str(self.ui.filenameEdit.displayText())
        self.parameters.filename = name
        name += "_{0:04d}".format(self.ui.indexSpinBox.value())
        self.parameters.extension = str(self.ui.extensionComboBox.currentText())
        if len(self.parameters.extension) > 0:
            name += "_" + self.parameters.extension
        name += self.ui.filetypeComboBox.currentText()
        self.ui.filenameLabel.setText(name)
        if os.path.exists(self.parameters.directory + name):
            self.will_overwrite = True
            self.ui.filenameLabel.setStyleSheet("QLabel { color: red}")
        else:
            self.will_overwrite = False
            self.ui.filenameLabel.setStyleSheet("QLabel { color: black}")

    def updateFramesForFilm(self):
        self.frame_count += 1
        if self.software_max_frames:
            if self.frame_count > self.software_max_frames and self.filming:
                self.emit(QtCore.SIGNAL("reachedMaxFrames()"))
        self.ui.framesText.setText("%d" % self.frame_count)
        if self.writer: # The flag for whether or not we are actually saving anything.
            size = self.frame_count * self.parameters.bytesPerFrame * 0.000000953674
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

    def updateTemperature(self):
        cur_temp = self.camera_control.getTemperature()
        self.parameters.actual_temperature = cur_temp[0]
        self.camera_params.newTemperature(cur_temp)



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
    parameters = params.Parameters(setup_name + "_default.xml")    
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
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
