#!/usr/bin/python
#
## @file
#
# A thin layer between HAL and:
#
# 1. A CameraFrameDisplay object which actually handles displaying the frames, etc.
# 2. A ParamsDisplay object which handles displaying (some of) the camera parameters
#    like the temperature, EMGain, etc..
#

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

import display.cameraFrameDisplay as cameraFrameDisplay
import display.paramsDisplay as paramsDisplay
import halLib.halModule as halModule

class CameraDisplay(QtGui.QDialog, halModule.HalModule):
    
    @hdebug.debug
    def __init__(self, hal_ui, hal_ui_mode, which_camera, hardware, parameters, parent):
        QtGui.QDialog.__init__(self, parent)
        halModule.HalModule.__init__(self)
        
        self.camera_properties = None
        self.hal_type = "display" + which_camera[-1:]
        self.parameters = parameters
        self.which_camera = which_camera
        self.which_feed = {}
        
        # Pictures from the camera and parameters are shown in the main window.
        if (hal_ui_mode == "single"):
            self.hal_gui = False
            
            import qtdesigner.camera_params_ui as cameraParamsUi
            
            camera_frame = hal_ui.cameraFrame
            camera_params_frame = hal_ui.cameraParamsFrame
            show_record = True
            
        # Pictures from the camera and parameters are shown in their own window.
        else:
            self.hal_gui = True

            import qtdesigner.camera_detached_ui as cameraDetachedUi
            import qtdesigner.camera_params_detached_ui as cameraParamsUi

            # Configure window.
            self.ui = cameraDetachedUi.Ui_Dialog()
            self.ui.setupUi(self)
            self.setWindowTitle(parameters.get("setup_name") + " " + self.getMenuName())

            camera_frame = self.ui.cameraFrame
            camera_params_frame = self.ui.cameraParamsFrame
            show_record = False

            self.ui.okButton.clicked.connect(self.handleOk)

        # Configure camera frame display.
        self.camera_frame_display = cameraFrameDisplay.CameraFrameDisplay(hardware,
                                                                          parameters.get(which_camera),
                                                                          which_camera,
                                                                          show_record,
                                                                          parent = camera_frame)
        
        layout = QtGui.QGridLayout(camera_frame)
        layout.setMargin(0)
        layout.addWidget(self.camera_frame_display)

        self.camera_frame_display.feedChanged.connect(self.handleFeedChanged)

        # Configure camera parameters display.            
        camera_params_ui = cameraParamsUi.Ui_GroupBox()
        self.camera_params = paramsDisplay.ParamsDisplay(camera_params_ui,
                                                         which_camera,
                                                         parent = camera_params_frame)

        layout = QtGui.QGridLayout(camera_params_frame)
        layout.setMargin(0)
        layout.addWidget(self.camera_params)

    @hdebug.debug
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "cameraProperties"):
                signal[2].connect(self.handleCameraProperties)
            elif (signal[1] == "updatedParams"):
                signal[2].connect(self.handleUpdatedParams)
            elif (signal[1] == "newCycleLength"):
                signal[2].connect(self.camera_frame_display.setSyncMax)

    @hdebug.debug
    def getMenuName(self):
        return "C" + self.which_camera[1:]

    def getRecordButton(self):
        return self.camera_frame_display.getRecordButton()
    
    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "cameraShutter", self.camera_frame_display.cameraShutter],
                [self.hal_type, "dragMove", self.camera_frame_display.dragMove],
                [self.hal_type, "dragStart", self.camera_frame_display.dragStart],
                [self.hal_type, "emGainChange", self.camera_params.gainChange],
                [self.hal_type, "frameCaptured", self.camera_frame_display.frameCaptured],
                [self.hal_type, "ROISelection", self.camera_frame_display.ROISelection]]

    ## handleCameraProperties
    #
    # The camera properties are whether or not it is in an EMCCD camera,
    # if it has a preamp, a shutter and temperature control.
    #
    # @param camera_properties A dictionary containing property sets for each camera.
    #
    @hdebug.debug
    def handleCameraProperties(self, camera_properties):
        self.camera_properties = camera_properties
        self.updateCameraProperties()

    @hdebug.debug
    def handleFeedChanged(self, feed_name):
        feed_name = str(feed_name)
        self.which_feed[self.parameters] = feed_name
        self.camera_frame_display.newFeed(feed_name)

    @hdebug.debug
    def handleOk(self, boolean):
        self.hide()

    ## handleUpdatedParams
    #
    # This signal is sent by the camera when the emgain, shutter state or temperature changes.
    #
    @hdebug.debug
    def handleUpdatedParams(self):
        self.camera_frame_display.updatedParams()
        self.camera_params.updatedParams()

    @hdebug.debug
    def loadGUISettings(self, settings):
        if self.hal_gui:
            halModule.HalModule.loadGUISettings(self, settings)
            self.resize(settings.value(self.hal_type + "_size", self.size()).toSize())

    def newFrame(self, frame, filming):
        self.camera_frame_display.newFrame(frame)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        if parameters in self.which_feed:
            self.camera_frame_display.newParameters(self.parameters, self.which_feed[self.parameters])
        else:
            self.camera_frame_display.newParameters(self.parameters, self.which_camera)
        self.camera_params.newParameters(self.parameters)

    @hdebug.debug
    def saveGUISettings(self, settings):
        if self.hal_gui:
            halModule.HalModule.saveGUISettings(self, settings)
            settings.setValue(self.hal_type + "_size", self.size())
            
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        self.camera_frame_display.startFilm(run_shutters)
        self.camera_params.startFilm()

    @hdebug.debug
    def stopFilm(self, film_writer):
        self.camera_frame_display.stopFilm()
        self.camera_params.stopFilm()

    @hdebug.debug
    def updateCameraProperties(self):
        self.camera_frame_display.updateCameraProperties(self.camera_properties)
        self.camera_params.updateCameraProperties(self.camera_properties)


