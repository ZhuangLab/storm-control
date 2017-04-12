#!/usr/bin/env python
"""
Handles the management of one or more camera / feed displays.

Hazen 3/17
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.cameraControl as cameraControl
import storm_control.hal4000.display.cameraViewers as cameraViewers
import storm_control.hal4000.feeds.feeds as feeds

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class Display(halModule.HalModule):
    """
    Controller for one or more displays of camera / feed data.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.have_stage = False
        self.is_classic = (module_params.get("ui_type") == "classic")
        self.parameters = module_params.get("parameters")
        self.qt_settings = qt_settings
        self.show_gui = True
        self.window_title = module_params.get("setup_name")
        
        self.viewers = []

        #
        # There is always at least one display by default.
        #
        if self.is_classic:
            self.viewers.append(cameraViewers.ClassicViewer(module_name = self.getNextViewerName()))
        else:
            camera_viewer = cameraViewers.DetachedViewer(module_name = self.getNextViewerName())
            camera_viewer.halDialogInit(self.qt_settings, self.window_title + " camera viewer")        
            self.viewers.append(camera_viewer)
        
        self.viewers[0].guiMessage.connect(self.handleGuiMessage)
        
        # Default color table to use. This is used by feeds.feeds in the feed_info structure.
        halMessage.addMessage("default colortable",
                              validator = {"data" : {"colortable" : [True, str]},
                                           "resp" : None})

        # These are sent when the user selects an ROI on a View with the rubber
        # band selection, 'chip' coordinates.
        halMessage.addMessage("display ROI selection",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "feed_name" : [True, str],
                                                     "x1" : [True, int],
                                                     "x2" : [True, int],
                                                     "y1" : [True, int],
                                                     "y2" : [True, int]},
                                           "resp" : None})

        # This message comes from one of the viewers when the user is trying to
        # get the stage to move by dragging on the display.
        halMessage.addMessage("drag move",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "feed_name" : [True, str],
                                                     "x_disp" : [True, int],
                                                     "y_disp" : [True, int]},
                                           "resp" : None})

        # This message comes from one of the viewers when the user first clicks
        # to initiate stage movement by dragging on the display.
        halMessage.addMessage("drag start",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "feed_name" : [True, str]},
                                           "resp" : None})

        # This message only comes from viewers, it is used to get the configuration
        # of a camera mostly, for the benefit of the camera parameters display.
        halMessage.addMessage("get camera configuration",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "camera" : [True, str]},
                                           "resp" : {"camera" : [True, str],
                                                     "config" : [True, cameraControl.CameraConfiguration]}})
        
        # This message comes from the viewers, it is used to get the initial
        # display settings for a camera or feed.
        halMessage.addMessage("get feed information",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "feed_name" : [True, str]},
                                           "resp" : {"feed_name" : [True, str],
                                                     "feed_info" : [True, feeds.CameraFeedInfo]}})

        # Unhide / create a new camera viewer.
        halMessage.addMessage("new camera viewer",
                              validator = {"data" : None, "resp" : None})

        # Unhide / create a new feed viewer.
        halMessage.addMessage("new feed viewer",
                              validator = {"data" : None, "resp" : None})
                              
        # Change the EMCCD gain.
        halMessage.addMessage("set emccd gain",
                              validator = {"data" : {"camera" : [True, str],
                                                     "emccd gain" : [True, int]},
                                           "resp" : None})
        
        # This message comes from the shutter button.
        halMessage.addMessage("shutter clicked",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "camera" : [True, str]},
                                           "resp" : None})
        
    def cleanUp(self, qt_settings):
        for viewer in self.viewers:
            viewer.cleanUp(qt_settings)

    def getNextViewerName(self):
        return "display{0:02d}".format(len(self.viewers))

    def handleGuiMessage(self, message):
        #
        # Over write source so that message will appear to HAL to come from
        # this module and not one display or params viewers.
        #
        message.source = self
        self.newMessage.emit(message)
        
    def handleResponse(self, message, response):
        if message.isType("get camera configuration"):
            for viewer in self.viewers:
                if (viewer.getViewerName() == message.getData()["display_name"]):
                    viewer.messageGetCameraConfiguration(response.getData()["config"])

        elif message.isType("get feed information"):
            for viewer in self.viewers:
                if (viewer.getViewerName() == message.getData()["display_name"]):
                    viewer.messageGetFeedInformation(response.getData()["feed_info"])

    def processMessage(self, message):

        if message.isType("camera emccd gain"):
            for viewer in self.viewers:
                viewer.messageCameraEMCCDGain(message.getData()["camera"],
                                              message.getData()["emccd gain"])

        elif message.isType("camera shutter"):
            for viewer in self.viewers:
                viewer.messageCameraShutter(message.getData()["camera"],
                                            message.getData()["state"])

        elif message.isType("camera temperature"):
            for viewer in self.viewers:
                viewer.messageCameraTemperature(message.getData()["camera"],
                                                message.getData()["state"],
                                                message.getData()["temperature"])

        elif message.isType("configure1"):
            
            # Let everyone know what the default color table is.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "default colortable",
                                                       data = {"colortable" : self.parameters.get("colortable")}))

            # The ClassicViewer might need to tell other modules to
            # incorporate some of it's UI elements.
            self.viewers[0].messageConfigure1()

            # Add a menu option(s) to generate more viewers.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to menu",
                                                       data = {"item name" : "Feed Viewer",
                                                               "item msg" : "new feed viewer"}))
            if not self.is_classic:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to menu",
                                                           data = {"item name" : "Camera Viewer",
                                                                   "item msg" : "new camera viewer"}))

            # Enable stage dragging if there is a stage.
            if "stage" in message.getData()["all_modules"]:
                self.have_stage = True
                self.viewers[0].enableStageDrag(self.have_stage)

        elif message.isType("configure2"):
            # This is where the default viewer requests camera and feed information.
            self.viewers[0].messageConfigure2()

        elif message.isType("feeds information"):
            for viewer in self.viewers:
                viewer.messageFeedsInformation(message.getData()["feeds"])

        elif message.isType("new camera viewer"):
            self.newCameraViewer()

        elif message.isType("new feed viewer"):
            self.newFeedViewer()

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            for viewer in self.viewers:
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"old parameters" : viewer.getParameters().copy()}))
                viewer.messageNewParameters(p.get(viewer.getViewerName(),
                                                  viewer.getDefaultParameters()))
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"new parameters" : viewer.getParameters()}))

        elif message.isType("start"):
            self.show_gui = message.getData()["show_gui"]
            if self.show_gui:
                self.viewers[0].showIfVisible()

            #
            # Heh, need to send this message again because the QtCameraGraphicsView won't know how
            # to scale the frames until it gets rendered and can correctly calculate it's size.
            #
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "get feed information",
                                                       data = {"display_name" : self.viewers[0].getViewerName(),
                                                               "feed_name" : self.viewers[0].getFeedName()}))

        elif message.isType("start film"):
            for viewer in self.viewers:
                viewer.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            for viewer in self.viewers:
                viewer.stopFilm()
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"parameters" : viewer.getParameters()}))

        elif message.isType("updated parameters"):
            for viewer in self.viewers:
                viewer.messageUpdatedParameters(message.getData()["parameters"])

#    def processL2Message(self, message):
#        for viewer in self.viewers:
#            viewer.messageNewFrame(message.getData()["frame"])

    def newCameraViewer(self):

        # First look for an existing viewer that is just hidden.
        found_existing_viewer = False
        for viewer in self.viewers:
            if isinstance(viewer, cameraViewers.DetachedViewer) and not viewer.isVisible():
                viewer.show()
                found_existing_viewer = True

        # If none exists, create a new feed viewer.
        if not found_existing_viewer:
            feed_viewer = cameraViewers.DetachedViewer(module_name = self.getNextViewerName())
            feed_viewer.halDialogInit(self.qt_settings, self.window_title + " camera viewer")
            feed_viewer.guiMessage.connect(self.handleGuiMessage)
            feed_viewer.showViewer(self.show_gui)
            self.viewers.append(feed_viewer)

        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "get feeds information"))
    
    def newFeedViewer(self):

        # First look for an existing viewer that is just hidden.
        found_existing_viewer = False
        for viewer in self.viewers:
            if isinstance(viewer, cameraViewers.FeedViewer) and not viewer.isVisible():
                viewer.show()
                found_existing_viewer = True
                
        # If none exists, create a new feed viewer.
        if not found_existing_viewer:
            feed_viewer = cameraViewers.FeedViewer(module_name = self.getNextViewerName())
            feed_viewer.halDialogInit(self.qt_settings, self.window_title + " feed viewer")        
            feed_viewer.guiMessage.connect(self.handleGuiMessage)
            feed_viewer.showViewer(self.show_gui)
            self.viewers.append(feed_viewer)

        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "get feeds information"))

        
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
