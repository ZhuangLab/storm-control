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
        self.stage_functionality = None
        self.window_title = module_params.get("setup_name")
        
        self.viewers = []

        #
        # There is always at least one display by default.
        #
        if self.is_classic:
            self.viewers.append(cameraViewers.ClassicViewer(module_name = self.getNextViewerName(),
                                                            default_colortable = self.parameters.get("colortable")))
        else:
            camera_viewer = cameraViewers.DetachedViewer(module_name = self.getNextViewerName(),
                                                         default_colortable = self.parameters.get("colortable"))
            camera_viewer.halDialogInit(self.qt_settings, self.window_title + " camera viewer")        
            self.viewers.append(camera_viewer)
        
        self.viewers[0].guiMessage.connect(self.handleGuiMessage)

        # This message comes from the shutter button.
        halMessage.addMessage("shutter clicked",
                              validator = {"data" : {"display_name" : [True, str],
                                                     "camera" : [True, str]},
                                           "resp" : None})
        
    def cleanUp(self, qt_settings):
        for viewer in self.viewers:
            viewer.cleanUp(qt_settings)

    def findChild(self, qt_type, name, options):
        """
        Overwrite the halModule version as the 'child' could only
        be in the one of the viewers.
        """
        for view in self.viewers:
            print("display", view)
            m_child = view.findChild(qt_type, name, options)
            if m_child is not None:
                return m_child

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
        if message.isType("get functionality"):
            if (message.getData()["extra data"] == "stage_fn"):
                stage_fn = response.getData()["functionality"]

                # Drag motion is disabled for stages that declare themselves to be slow.
                if stage_fn.isSlow():
                    return

                self.stage_functionality = stage_fn
                for viewer in self.viewers:
                    viewer.setStageFunctionality(self.stage_functionality)
            else:
                for viewer in self.viewers:
                    if (viewer.getViewerName() == message.getData()["extra data"]):
                        viewer.setCameraFunctionality(response.getData()["functionality"])

        elif message.isType("get feed names"):
            for viewer in self.viewers:
                if (viewer.getViewerName() == message.getData()["extra data"]):
                    viewer.setFeedNames(response.getData()["feed names"])

    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("feeds"):
                feed_names = message.getData()["properties"]["feed names"]
                for viewer in self.viewers:
                    viewer.setFeedNames(feed_names)

            elif message.sourceIs("illumination"):
                shutters_info = message.getData()["properties"]["shutters info"]
                for viewer in self.viewers:
                    viewer.setSyncMax(shutters_info.getFrames())

            elif message.sourceIs("stage"):
                stage_fn_name = message.getData()["properties"]["stage functionality name"]
                self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                       data = {"name" : stage_fn_name,
                                                               "extra data" : "stage_fn"}))

        elif message.isType("configure1"):
            
            # The ClassicViewer might need to tell other modules to
            # incorporate some of it's UI elements.
            self.viewers[0].configure1()

            # Add a menu option(s) to generate more viewers.
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Feed Viewer",
                                                           "item data" : "new feed viewer"}))
            if not self.is_classic:
                self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                       data = {"item name" : "Camera Viewer",
                                                               "item data" : "new camera viewer"}))

        elif message.isType("current parameters"):
            for viewer in self.viewers:
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"parameters" : viewer.getParameters().copy()}))
                
        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            for viewer in self.viewers:
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"old parameters" : viewer.getParameters().copy()}))
                viewer.newParameters(p.get(viewer.getViewerName(),
                                           viewer.getDefaultParameters()))
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"new parameters" : viewer.getParameters()}))

        elif message.isType("show"):
            if (message.getData()["show"] == "new camera viewer"):
                self.newCameraViewer()
            elif (message.getData()["show"] == "new feed viewer"):
                self.newFeedViewer()

        elif message.isType("start"):
            self.show_gui = message.getData()["show_gui"]
            self.viewers[0].showViewer(self.show_gui)

        elif message.isType("start film"):
            for viewer in self.viewers:
                viewer.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            for viewer in self.viewers:
                viewer.stopFilm()
                message.addResponse(halMessage.HalMessageResponse(source = viewer.getViewerName(),
                                                                  data = {"parameters" : viewer.getParameters()}))

#        elif message.isType("updated parameters"):
#            for viewer in self.viewers:
#                viewer.updatedParameters(message.getData()["parameters"])

    def newCameraViewer(self):
        self.newViewer(cameraViewers.DetachedViewer, "camera viewer")

    def newFeedViewer(self):
        self.newViewer(cameraViewers.FeedViewer, "feed viewer")

    def newViewer(self, v_type, v_name):
        #
        # FIXME: If you create a viewer during a film it is not going to
        #        to be in filming mode, and you won't be able to change
        #        things like sync_max.
        #
        
        # First look for an existing viewer that is just hidden.
        found_existing_viewer = False
        for viewer in self.viewers:
            if isinstance(viewer, v_type) and not viewer.isVisible():
                viewer.show()
                found_existing_viewer = True

        # If none exists, create a viewer of the requested type.
        if not found_existing_viewer:
            viewer = v_type(module_name = self.getNextViewerName(),
                            default_colortable = self.parameters.get("colortable"))
            viewer.halDialogInit(self.qt_settings, self.window_title + " " + v_name)
            viewer.guiMessage.connect(self.handleGuiMessage)
            if self.stage_functionality is not None:
                viewer.setStageFunctionality(self.stage_functionality)
            viewer.showViewer(self.show_gui)
            self.viewers.append(viewer)

            self.sendMessage(halMessage.HalMessage(m_type = "get feed names",
                                                   data = {"extra data" : viewer.getViewerName()}))


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
