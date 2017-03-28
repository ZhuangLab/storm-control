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
    """
    Controller for one or more displays of camera / feed data.

    This sends the following messages:
     'get feed config'
     'set current camera'
    """
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

        # This message comes from the record button.
        halMessage.addMessage("record clicked")
        
        # This message only comes from view[0], the default display.
        halMessage.addMessage("set current camera")

    def addParametersResponse(self, message, view):        
        if False:
            print("")
            print("app", view.getDisplayName())
            print(view.getParameters().toString(all_params = True))
            print("")
        message.addResponse(halMessage.HalMessageResponse(source = view.getDisplayName(),
                                                          data = {"parameters" : view.getParameters()}))

    def broadcastParameters(self):
        for view in self.views:
            if False:
                print("")
                print("bp", view.getDisplayName())
                print(view.getParameters().toString(all_params = True))
                print("")
                
            #
            # We use a temporary module when we send the parameters so that the
            # settings module organizes them by the display name instead of
            # putting them all in a single section called "display".
            #
            dummy_hal_module = halModule.HalModule(module_name = view.getDisplayName())
            self.newMessage.emit(halMessage.HalMessage(source = dummy_hal_module,
                                                       m_type = "current parameters",
                                                       data = {"parameters" : view.getParameters()}))

    def cleanUp(self, qt_settings):
        for dialog in self.dialogs:
            if dialog is not None:
                dialog.cleanUp(qt_settings)
        
    def getNextViewName(self):
        return "display{0:02d}".format(len(self.views))
    
    def handleGuiMessage(self, message_data):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = message_data[0],
                                                   level = message_data[1],
                                                   data = message_data[2]))

    def handleResponse(self, message, response):
        """
        The only message that we expect a response for is a 'get feed config' message.
        """
        if (message.getType() == "get feed config"):
            self.viewFeedConfig(response)

    def processL1Message(self, message):
            
        if (message.getType() == "add to ui"):
            if self.dialogs[0] is not None:
                [module, parent_widget] = message.data["ui_parent"].split(".")
                if (module == self.module_name):
                    self.dialogs[0].addParamsWidget(message.data["ui_widget"])

        elif (message.getType() == "configure1"):
            if self.dialogs[0] is None:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = {"ui_parent" : "hal.cameraFrame",
                                                                   "ui_widget" : self.views[0]}))

            # Set the 'current camera', i.e. the camera that is being displayed
            # in the main view and also in the parameters box to camera1.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "set current camera",
                                                       data = {"camera" : "camera1"}))

        #
        # 'set current camera' is sent after the 'configure1' message. The
        # camera response comes after the 'configure2' message, so the parameters
        # should be initialized by 'configure3'.
        #
        elif (message.getType() == "configure3"):
            for view in self.views:
                if False:
                    print("")
                    print("bp", view.getDisplayName())
                    print(view.getParameters().toString(all_params = True))
                    print("")
                    
                #
                # We use a temporary module when we send the parameters so that the
                # settings module organizes them by the display name instead of
                # putting them all in a single section called "display".
                #
                dummy_hal_module = halModule.HalModule(module_name = view.getDisplayName())
                self.newMessage.emit(halMessage.HalMessage(source = dummy_hal_module,
                                                           m_type = "initial parameters",
                                                           data = {"parameters" : view.getParameters()}))

        elif (message.getType() == "current camera"):
            self.viewFeedConfig(message)

        elif (message.getType() == "feed list"):
            for view in self.views:
                view.setFeeds(message.getData()["feeds"])

        elif (message.getType() == "new parameters"):
            p = message.getData()["parameters"]
            for view in self.views:
                old_parameters = view.getParameters().copy()
                view.newParameters(p.get(view.getDisplayName()))
                message.addResponse(halMessage.HalMessageResponse(source = view.getDisplayName(),
                                                                  data = {"old parameters" : old_parameters,
                                                                          "new parameters" : viw.getParameters()}))

        elif (message.getType() == "start"):
            if self.dialogs[0] is not None:
                self.dialogs[0].showIfVisible()

        elif (message.getType() == "start film"):
            for view in self.views:
                view.startFilm(message.getData()["film_settings"])

        elif (message.getType() == "stop film"):
            for view in self.views:
                view.stopFilm()
                message.addResponse(halMessage.HalMessageResponse(source = view.getDisplayName(),
                                                                  data = {"parameters" : view.getParameters()}))

    def processL2Message(self, message):
        for view in self.views:
            view.newFrame(message.getData()["frame"])

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
