#!/usr/bin/env python
"""

Handles the primary camera display. In detached mode
this is the one with the record button.

Hazen 2/17

"""

from PyQt5 import QtWidgets

import storm_control.hal4000.display.cameraFrameDisplay as cameraFrameDisplay
import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtdesigner.camera_detached_ui as cameraDetachedUi


class DisplayDialog(halDialog.HalDialog):
    """
    In detached view mode this is the dialog that shows the camera image.
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

        self.params_layout = QtWidgets.QGridLayout(self.ui.cameraParamsFrame)
        self.params_layout.setContentsMargins(0,0,0,0)

    def addParamsWidget(self, camera_params_widget):
        """
        Add the camera params widget to the UI.
        """
        self.params_layout.addWidget(camera_params_widget)


class Display(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        
        if module_params.get("ui_type") == "classic")
            self.view = cameraFrameDisplay.CameraFrameDisplay(module_params = None,
                                                              show_record = True,
                                                              **kwds)
            self.dialog = None
        else:
            self.view = cameraFrameDisplay.CameraFrameDisplay(module_params = None,
                                                              show_record = True,
                                                              **kwds)
            self.dialog = DisplayDialog(module_name = module_name,
                                        module_params = module_params,
                                        qt_settings = qt_settings,
                                        camera_view = self.view,
                                        **kwds)
        
        self.view.guiMessage.connect(self.handleGuiMessage)

    def handleGuiMessage(self, message):
        self.newMessage.emit(message)

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            
            if (message.m_type == "add to ui"):
                if self.dialog is not None:
                    [module, parent_widget] = message.data["ui_parent"].split(".")
                    if (module == self.module_name):
                        self.dialog.addParamsWidget(message.data["ui_widget"])

            elif (message.m_type == "configure"):
                if self.dialog is not None:
                    self.dialog.showIfVisible()

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
