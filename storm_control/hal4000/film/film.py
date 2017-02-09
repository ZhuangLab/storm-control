#!/usr/bin/env python
"""

Handles filming.

This module is responsible for everything related to filming,
including starting and stopping the cameras, saving the frames,
etc..

Much of the logic in the Python2/PyQt4 HAL is now located in
this module.

Hazen 01/17
"""

from PyQt5 import QtWidgets

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtdesigner.film_ui as filmUi


class FilmBox(QtWidgets.QGroupBox):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ui = filmUi.Ui_GroupBox()
        self.ui.setupUi(self)
    
class Film(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.view = FilmBox()

        self.configure_dict = {"ui_order" : 1,
                               "ui_parent" : "hal.containerWidget",
                               "ui_widget" : self.view}

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):
            if (message.m_type == "configure"):
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "add to ui",
                                                           data = self.configure_dict))


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
