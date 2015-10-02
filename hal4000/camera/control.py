#!/usr/bin/python
#
## @file
#
# A thin layer between HAL and a cameraControl object.
#
# Hazen 09/15
#

from PyQt4 import QtCore

import sc_library.hdebug as hdebug

import camera.feeds as feeds

class Camera(QtCore.QObject):
    cameraProperties = QtCore.pyqtSignal(object)
    newFrames = QtCore.pyqtSignal(object)
    reachedMaxFrames = QtCore.pyqtSignal()
    updatedParams = QtCore.pyqtSignal()

    @hdebug.debug
    def __init__(self, hardware, parameters):
        QtCore.QObject.__init__(self)
        
        self.acq_mode = None
        self.cameras = []
        self.feed_controller = None
        self.filming = False
        self.frames_to_take = None
        self.key = 0
        self.parameters = parameters
        self.writer = None

        # Setup camera control.
        module_name = hardware.get("module_name")
        cameraControl = __import__('camera.' + module_name, globals(), locals(), [module_name], -1)
        self.camera_control = cameraControl.ACameraControl(hardware.get("parameters", False), parent = self)

        self.camera_control.newData.connect(self.handleNewData)

        for i in range(self.camera_control.getNumberOfCameras()):
            self.cameras.append("camera" + str(i+1))
        
    @hdebug.debug
    def cameraInit(self):
        self.camera_control.cameraInit()

    @hdebug.debug
    def close(self):
        self.stopCamera()
        self.camera_control.quit()

    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "cameraShutter"):
                signal[2].connect(self.handleShutter)
            elif (signal[1] == "emGainChange"):
                signal[2].connect(self.handleEmGain)

    @hdebug.debug
    def getFeedNamesToSave(self):
        return self.feed_controller.getFeedNamesToSave()
    
    def getFilmSize(self):
        return self.writer.totalFilmSize()

    @hdebug.debug
    def getNumberOfCameras(self):
        return len(self.cameras)

    @hdebug.debug
    def getSignals(self):
        return [["camera", "cameraProperties", self.cameraProperties],
                ["camera", "updatedParams", self.updatedParams]]

    @hdebug.debug
    def handleEmGain(self, which_camera, em_gain):
        if not self.filming:
            self.stopCamera()
            which_camera = str(which_camera)
            self.camera_control.setEMCCDGain(which_camera, em_gain)
            self.parameters.set(which_camera + ".emccd_gain", em_gain)
            self.startCamera()
        
    def handleNewData(self, frames, key):
        if (key == self.key):
            reached_max_frames = False

            # Create feeds.
            feeds = []
            for frame in frames:
                feeds += self.feed_controller.newFrame(frame)

            # Save the frames if we are filming.
            if self.filming:
                for feed in feeds:
                    if (self.acq_mode == "fixed_length") and feed.master:
                        if (feed.number <= self.frames_to_take):
                            if self.writer is not None:
                                self.writer.saveFrame(feed)
                    else:
                        if self.writer is not None:
                            self.writer.saveFrame(feed)

                    if (self.acq_mode == "fixed_length") and feed.master and (feed.number == self.frames_to_take):
                        reached_max_frames = True

            # Send frames to HAL.
            self.newFrames.emit(feeds)

            # Emit max frames signal.
            #
            # The signal is emitted here because if it is emitted before
            # newData then you never see that last frame in the movie, which
            # is particularly problematic for single frame movies.
            #
            if reached_max_frames:
                self.reachedMaxFrames.emit()

    @hdebug.debug
    def handleShutter(self, which_camera):
        if not self.filming:
            self.stopCamera()
            which_camera = str(which_camera)
            state = self.camera_control.toggleShutter(which_camera)
            self.parameters.set(which_camera + ".shutter", state)
            self.startCamera()

    @hdebug.debug
    def moduleInit(self):
        self.cameraProperties.emit(self.camera_control.getProperties())
    
    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        self.camera_control.newParameters(self.parameters)
        for which_camera in self.cameras:

            # Get acquisition timing information.
            [exposure_value, cycle_value] = self.camera_control.getAcquisitionTimings(which_camera)
            self.parameters.set([which_camera + ".exposure_value", which_camera + ".cycle_value"], [exposure_value, cycle_value])
            if (which_camera == "camera1"):
                self.parameters.set("seconds_per_frame", cycle_value)

            # Get camera shutter stage.
            self.parameters.set(which_camera + ".shutter", self.camera_control.getShutterState(which_camera))

        self.feed_controller = feeds.newFeedController(self.cameras, self.parameters)

    @hdebug.debug
    def startCamera(self):
        self.key += 1
        self.updateTemperature()
        self.feed_controller.startFeeds()
        self.camera_control.startCamera(self.key)
        self.updatedParams.emit()

    @hdebug.debug
    def startFilm(self, writer, film_settings):
        self.filming = True
        self.writer = writer
        self.acq_mode = film_settings.acq_mode
        self.frames_to_take = film_settings.frames_to_take - 1
        self.feed_controller.startFilm()
        self.camera_control.startFilm(film_settings)

    @hdebug.debug
    def stopCamera(self):
        self.camera_control.stopCamera()

        # When we first start, feed_controller will be None.
        if self.feed_controller is not None:
            self.feed_controller.stopFeeds()

    @hdebug.debug
    def stopFilm(self):
        self.camera_control.stopFilm()
        self.feed_controller.stopFilm()
        self.filming = False

    def updateTemperature(self):
        for which_camera in self.cameras:
            if ("have_temperature" in self.camera_control.getProperties()[which_camera]):
                self.camera_control.getTemperature(which_camera, self.parameters)

