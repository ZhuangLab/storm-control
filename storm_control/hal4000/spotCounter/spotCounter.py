#!/usr/bin/env python
"""
Spot counter. This performs real time analysis of the frames from
camera. It uses a fairly simple object finder. It's purpose is to
provide the user with a rough idea of the quality of the data
that they are taking.

Hazen 05/17
"""

import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halModule as halModule

# The module that actually does the analysis.
import storm_control.hal4000.qtWidgets.qtSpotCounter as qtSpotCounter

# UI.
import storm_control.hal4000.qtdesigner.spotcounter_ui as spotcounterUi


class Analyzer(QtCore.QObject):
    """
    Manages the analysis of a single camera feed.
    """
    def __init__(self, camera_fn = None, pixel_size = None, shutters_info = None):
        super().__init__(**kwds)
        self.camera_fn = camera_fn
        self.pixel_size = pixel_size
        self.shutters_info = shutters_info

    def getCameraName(self):
        return self.camera_fn.getCameraName()
        
    def setShuttersInfo(self, shutters_info):
        self.shutters_info = shutters_info

    def startFilm(self, film_settings):
        pass

    def stopFilm(self):
        pass
    

class SpotCounterView(halDialog.HalDialog):
    """
    Manages the spot counter GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)

        # UI setup.
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)

    def newAnalyzers(self, analyzers):
        pass


class SpotCounter(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.analyzers = []
        self.number_fn_requested = 0
        self.pixel_size = 0.1
        self.shutters_info = None

        configuration = module_params.get("configuration")

        self.view = SpotCounterView(module_name = self.module_name,
                                    configuration = configuration)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " spot counter")

        # Spot counter parameters.
        self.parameters = params.StormXMLObject()

        spotc_params.add("cell_size", params.ParameterRangeInt("Cell size for background subtraction",
                                                               "cell_size", 32, 8, 128,
                                                               is_mutable = False,
                                                               is_saved = False))
        
        spotc_params.add("max_spots", params.ParameterRangeInt("Maximum counts for the spotcounter graph",
                                                               "max_spots", 500, 0, 1000,
                                                               is_mutable = False,
                                                               is_saved = False))
        
        spotc_params.add("min_spots", params.ParameterRangeInt("Minimum counts for the spotcounter graph",
                                                               "min_spots", 0, 0, 1000,
                                                               is_mutable = False,
                                                               is_saved = False))
        
        spotc_params.add("scale_bar_len", params.ParameterRangeFloat("Scale bar length in nm",
                                                                     "scale_bar_len", 1000, 100, 10000))
        
        spotc_params.add("threshold", params.ParameterRangeInt("Spot detection threshold (camera counts)",
                                                               "threshold", 250, 1, 10000))
        

    def handleResponses(self, message):
        if message.isType("get functionality"):
            assert (len(message.getResponses()) == 1)
            for response in message.getResponses():
                fn = response.getData()["functionality"]

                # Only analyze data from a camera.
                if fn.isCamera():
                    self.analyzers.append(Analyzer(camera_fn = fn,
                                                   pixel_size = self.pixel_size,
                                                   shutters_info = self.shutters_info))

                self.number_fn_requested -= 1

            if (self.number_fn_requested == 0):
                self.view.newAnalyzers(self.analyzers)
                
    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("feeds"):
                self.analyzers = []
                for name in message.getData()["properties"]["feed names"]:
                    self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                           data = {"name" : name}))
                    self.number_fn_requested += 1

            elif message.sourceIs("illumination"):
                self.shutters_info = message.getData()["properties"]["shutters info"]
                for analyzer in self.analyzers:
                    analyzer.setShuttersInfo(self.shutters_info)
                
            elif message.sourceIs("mosaic"):
                self.pixel_size = message.getData()["properties"]["pixel_size"]

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Spot Counter",
                                                           "item data" : "spot counter"}))

        elif message.isType("show"):
            if (message.getData()["show"] == "spot counter"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("start film"):
            for analyzer in self.analyzers:
                analyzer.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            for analyzer in self.analyzers:
                analyzer.stopFilm()

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

