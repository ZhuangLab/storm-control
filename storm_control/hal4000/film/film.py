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

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtdesigner.film_ui as filmUi


class FilmBox(QtWidgets.QGroupBox):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.ui = filmUi.Ui_GroupBox()
        self.ui.setupUi(self)

    def updateUI(self, parameters):
        pass
    
    
class Film(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.logfile_fp = open(module_params.get("directory") + "image_log.txt", "a")

        self.parameters = module_params.getp("parameters")

        # Hardwired default film settings.
        self.parameters.add("acq_mode", params.ParameterSetString("Acquisition mode",
                                                                  "acq_mode",
                                                                  "fixed_length",
                                                                  ["run_till_abort", "fixed_length"]))
        
        self.parameters.add("auto_increment", params.ParameterSetBoolean("Automatically increment movie counter between movies",
                                                                         "auto_increment",
                                                                         True))
        
        self.parameters.add("auto_shutters", params.ParameterSetBoolean("Run shutters during the movie",
                                                                        "auto_shutters",
                                                                        True))
        
        self.parameters.add("directory", params.ParameterStringDirectory("Current working directory",
                                                                         "directory",
                                                                         module_params.get("directory")))
        
        self.parameters.add("filename", params.ParameterString("Current movie file name",
                                                               "filename",
                                                               "movie"))
        
        self.parameters.add("filetype", params.ParameterSetString("Movie file type",
                                                                  "filetype",
                                                                  ".dax",
                                                                  [".dax", ".tiff"]))
        
        self.parameters.add("frames", params.ParameterRangeInt("Movie length in frames",
                                                               "frames",
                                                               10,
                                                               1,
                                                               1000000000))
                                                               
        #self.parameters.add("logfile", params)
        
        self.parameters.add("want_bell", params.ParameterSetBoolean("Sound bell at the end of long movies",
                                                                    "want_bell",
                                                                    True))
        
        self.parameters.add("dax_big_endian", params.ParameterSetBoolean("Save .dax movies using a big endian format",
                                                                         "dax_big_endian",
                                                                         False))
        
        
        self.view = FilmBox()
        self.configure_dict = {"ui_order" : 1,
                               "ui_parent" : "hal.containerWidget",
                               "ui_widget" : self.view}

    def cleanUp(self, qt_settings):
        self.logfile_fp.close()
        
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
