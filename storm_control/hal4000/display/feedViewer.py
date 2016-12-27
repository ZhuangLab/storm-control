#!/usr/bin/python
#
## @file
#
# This handles one or more feed viewers. These are similar to camera
# display(s) except that they can only view the feeds.
#

from PyQt5 import QtCore, QtGui, QtWidgets

# Debugging
import storm_control.sc_library.hdebug as hdebug

import storm_control.hal4000.display.cameraFrameDisplay as cameraFrameDisplay
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.feed_viewer_ui as feedViewerUi

## FeedViewer
#
# This handles the display of single feed.
#
class FeedViewer(QtWidgets.QDialog):

    @hdebug.debug
    def __init__(self, default_feed, parameters, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.default_feed = default_feed
        self.parameters = parameters
        self.which_feed = {}

        # Configure dialog.
        self.ui = feedViewerUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " " + "Feed Viewer")

        self.feed_frame_display = cameraFrameDisplay.CameraFeedDisplay(None,
                                                                       parameters.get(default_feed),
                                                                       default_feed,
                                                                       self.ui.cameraFrame)

        layout = QtWidgets.QGridLayout(self.ui.cameraFrame)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.feed_frame_display)

        self.feed_frame_display.feedChanged.connect(self.handleFeedChanged)
        self.ui.okButton.clicked.connect(self.handleOk)        

    @hdebug.debug
    def closeEvent(self, event):
        event.ignore()
        self.hide()

    @hdebug.debug
    def handleFeedChanged(self, feed_name):
        feed_name = str(feed_name)
        self.which_feed[self.parameters] = feed_name
        self.feed_frame_display.newFeed(feed_name)

    @hdebug.debug
    def handleOk(self, boolean):
        self.hide()

    @hdebug.debug
    def newFrame(self, frame, filming):
        if self.isVisible():
            self.feed_frame_display.newFrame(frame)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        if parameters in self.which_feed:
            self.feed_frame_display.newParameters(self.parameters, self.which_feed[self.parameters])
        else:
            self.feed_frame_display.newParameters(self.parameters, self.default_feed)

    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.feed_frame_display.setSyncMax(sync_max)
        
    @hdebug.debug
    def startFilm(self, run_shutters):
        self.feed_frame_display.startFilm(run_shutters)

    @hdebug.debug
    def stopFilm(self):
        self.feed_frame_display.stopFilm()    
        

## FeedViewers
#
# This class is an interface between HAL and an arbitrary number of
# individual feed viewers.
#
class FeedViewers(QtCore.QObject, halModule.HalModule):
    
    @hdebug.debug
    def __init__(self, hardware, parameters, parent):
        QtCore.QObject.__init__(self, parent)
        halModule.HalModule.__init__(self)

        self.am_filming = False
        self.gui_settings = None
        self.parameters = parameters
        self.parent = parent
        self.run_shutters = False
        self.sync_max = 0
        self.viewers = []

    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "newCycleLength"):
                signal[2].connect(self.handleSyncMax)

    @hdebug.debug
    def handleSyncMax(self, sync_max):
        self.sync_max = sync_max
        for viewer in self.viewers:
            viewer.setSyncMax(self.sync_max)

    ## loadGUISettings
    #
    # We have to override this as we don't want to actually load anything.
    # Each time HAL is re-started we'll start without any open feed viewers.
    #
    @hdebug.debug
    def loadGUISettings(self, settings):
        self.gui_settings = settings

    @hdebug.debug
    def newFrame(self, frame, filming):
        for viewer in self.viewers:
            viewer.newFrame(frame, filming)

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        for viewer in self.viewers:
            viewer.newParameters(parameters)

    @hdebug.debug
    def saveGUISettings(self, settings):
        for i, viewer in enumerate(self.viewers):
            settings.setValue("feed_viewer_" + str(i) + "_pos", viewer.pos())
            settings.setValue("feed_viewer_" + str(i) + "_size", viewer.size())

    @hdebug.debug
    def show(self, boolean = False):
        # Look for closed viewers, and just re-open them.
        for viewer in self.viewers:
            if not viewer.isVisible():
                viewer.show()
                return

        # Create a new viewer. Try and use GUI settings if we can find them.
        index = len(self.viewers)
        new_viewer = FeedViewer("camera1", self.parameters, self.parent)
        new_viewer.newParameters(self.parameters)
        new_viewer.move(self.gui_settings.value("feed_viewer_" + str(index) + "_pos", QtCore.QPoint(200, 200)))
        new_viewer.resize(self.gui_settings.value("feed_viewer_" + str(index) + "_size", new_viewer.size()))

        # Since we might want to create a viewer in the middle of a film we
        # need to configure for that.
        new_viewer.setSyncMax(self.sync_max)
        if self.am_filming:
            new_viewer.startFilm(self.run_shutters)

        new_viewer.show()
        self.viewers.append(new_viewer)

    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        self.am_filming = True
        self.run_shutters = run_shutters
        for viewer in self.viewers:
            viewer.startFilm(run_shutters)

    @hdebug.debug
    def stopFilm(self, film_writer):
        self.am_filming = False
        for viewer in self.viewers:
            viewer.stopFilm()
    
