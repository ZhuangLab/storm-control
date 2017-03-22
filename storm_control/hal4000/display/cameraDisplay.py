#!/usr/bin/env python
"""
Handles the management of one or more camera / feed displays.

Hazen 3/17
"""

from PyQt5 import QtWidgets

import storm_control.hal4000.display.cameraFrameDisplay as cameraFrameDisplay
import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtdesigner.camera_detached_ui as cameraDetachedUi


class DisplayDialog(halDialog.HalDialog):
    """
    These are the dialog boxes that show the camera image. In detached mode
    there is at least one of these.
    """
    def __init__(self, module_params = None, qt_settings = None, camera_view = None, **kwds):
        super().__init__(**kwds)

        # Create UI
        self.ui = cameraDetachedUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Configure UI.
        self.setWindowTitle(module_params.get("setup_name") + " Main Display")
        super().halDialogInit(qt_settings)

        camera_layout = QtWidgets.QGridLayout(self.ui.cameraFrame)
        camera_layout.setContentsMargins(0,0,0,0)
        camera_layout.addWidget(camera_view)
        camera_view.setParent(self.ui.cameraFrame)

        self.params_layout = QtWidgets.QGridLayout(self.ui.cameraParamsFrame)
        self.params_layout.setContentsMargins(0,0,0,0)

        self.halDialogInit(qt_settings)

    def addParamsWidget(self, camera_params_widget):
        """
        Add the camera params widget to the UI.
        """
        self.params_layout.addWidget(camera_params_widget)


class Display(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        self.parameters = module_params.get("parameters")
        
        self.dialogs = []
        self.views = []

        #
        # There is always at least one display by default. Also, this display
        # has additional functionality that the other displays won't have.
        #
        view_name = self.getNextViewName()
        if (module_params.get("ui_type") == "classic"):
            self.views.append(cameraFrameDisplay.CameraFrameDisplay(display_name = view_name,
                                                                    show_record = True))
            self.dialogs.append(None)
        else:
            self.views.append(cameraFrameDisplay.CameraFrameDisplay(display_name = view_name,
                                                                    show_record = False))
            self.dialogs.append(DisplayDialog(module_name = view_name,
                                              module_params = module_params,
                                              qt_settings = qt_settings,
                                              camera_view = self.views[0]))
        
        self.views[0].guiMessage.connect(self.handleGuiMessage)

        # This message comes from the viewers, it is used to get the initial
        # display settings for a camera or feed.
        halMessage.addMessage("get feed config", check_exists = False)

        # This message only comes from view[0], the default display.
        halMessage.addMessage("set current camera")

    def getNextViewName(self):
        return "display{0:02d}".format(len(self.views))
    
    def handleGuiMessage(self, message):
        self.newMessage.emit(message)

    def handleResponse(self, response):
        """
        The only message that we expect a response for is a 'get feed config' message.
        """
        if (response.getType() == "get feed config"):
            self.viewFeedConfig(response)

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            
            if (message.getType() == "add to ui"):
                if self.dialogs[0] is not None:
                    [module, parent_widget] = message.data["ui_parent"].split(".")
                    if (module == self.module_name):
                        self.dialogs[0].addParamsWidget(message.data["ui_widget"])

            elif (message.getType() == "configure"):
                if self.dialogs[0] is None:
                    self.newMessage.emit(halMessage.HalMessage(source = self,
                                                               m_type = "add to ui",
                                                               data = {"ui_parent" : "hal.cameraFrame",
                                                                       "ui_widget" : self.views[0]}))

                #
                # Broadcasting this message tells all the modules that camera1 is the
                # 'current camera', this is primarily for the benefit of display.paramsDisplay.
                #
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "set current camera",
                                                           data = {"camera" : "camera1"}))
                
            elif (message.getType() == "current camera"):
                self.viewFeedConfig(message)

            elif (message.getType() == "feed list"):
                for view in self.views:
                    view.setFeeds(message.getData()["feeds"])

            elif (message.getType() == "start"):
                if self.dialogs[0] is not None:
                    self.dialogs[0].showIfVisible()

    def viewFeedConfig(self, message):
        data = message.getData()

        # Add default color table information.
        data["colortable"] = self.parameters.get("colortable")
        
        for view in self.views:
            view.feedConfig(data)


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
