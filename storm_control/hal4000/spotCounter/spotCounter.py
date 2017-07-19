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
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.spotCounter.displaySpots as displaySpots

# The module that actually does the analysis.
import storm_control.hal4000.spotCounter.findSpots as findSpots

# UI.
import storm_control.hal4000.qtdesigner.spotcounter_ui as spotcounterUi


class Analyzer(QtCore.QObject):
    """
    Manages the analysis of a single camera feed.
    """
    totalCount = QtCore.pyqtSignal(int)
    
    def __init__(self,
                 camera_fn = None,
                 parameters = None,
                 pixel_size = None,
                 shutters_info = None,
                 spot_counter = None,
                 **kwds):
        super().__init__(**kwds)
        self.camera_fn = camera_fn
        self.filming = False
        self.spot_counter = spot_counter
        self.threshold = parameters.get("threshold")
        self.total_counts = 0

        self.spot_graph = displaySpots.SpotGraph(shutters_info = shutters_info)
        self.spot_picture = displaySpots.SpotPicture(camera_fn = camera_fn,
                                                     pixel_size = pixel_size,
                                                     scale_bar_len = parameters.get("scale_bar_len"),
                                                     shutters_info = shutters_info)

        self.camera_fn.newFrame.connect(self.handleNewFrame)
        self.spot_counter.imageProcessed.connect(self.handleProcessedImage)

    def cleanUp(self):
        self.camera_fn.newFrame.disconnect(self.handleNewFrame)
        self.spot_counter.imageProcessed.disconnect(self.handleProcessedImage)
        
    def getCameraName(self):
        return self.camera_fn.getCameraName()

    def getCounts(self):
        return self.total_counts

    def getSpotGraph(self):
        return self.spot_graph

    def getSpotPicture(self):
        return self.spot_picture
    
    def handleNewFrame(self, frame):
        self.spot_counter.newFrameToAnalyze(self.camera_fn.getCameraName(),
                                            frame,
                                            self.threshold)
        
    def handleProcessedImage(self, frame_analysis):
        if (frame_analysis.getCameraName() == self.camera_fn.getCameraName()):

            # Update counts total.
            self.total_counts += frame_analysis.getCounts()
            
            # Always update the spot count graph.
            if True:
                self.spot_graph.updatePoint(frame_analysis.getFrameNumber(),
                                            frame_analysis.getCounts())

            # Only update the image and total counts if we are filming.
            if self.filming:
                self.spot_picture.updateImage(frame_analysis.getFrameNumber(),
                                              frame_analysis.getLocalizations())

                self.totalCount.emit(self.total_counts)

    def savePicture(self, basename):
        self.spot_picture.savePicture(basename + "_" + self.camera_fn.getParameter("extension"))

    def setMaxSpots(self, max_spots):
        self.spot_graph.setMaxSpots(max_spots)
        
    def setShuttersInfo(self, shutters_info):
        self.spot_graph.setShuttersInfo(shutters_info)
        self.spot_picture.setShuttersInfo(shutters_info)

    def startFilm(self, film_settings):
        self.filming = True
        self.total_counts = 0
        self.spot_graph.clearGraph()
        self.spot_picture.clearPicture()
        self.totalCount.emit(self.total_counts)

    def stopFilm(self):
        self.filming = False


class SpotCounterView(halDialog.HalDialog):
    """
    Manages the spot counter GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.analyzers = []
        self.cur_analyzer = None
        self.parameters = None

        # UI setup.
        self.ui = spotcounterUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.countsLabel1.setText("0")
        self.ui.countsLabel2.setText("0")
        
        self.ui.analyzerComboBox.currentIndexChanged.connect(self.handleAnalyzerChange)
        self.ui.maxSpinBox.valueChanged.connect(self.handleMaxSpinBox)

        self.graph_layout = QtWidgets.QHBoxLayout(self.ui.graphFrame)
        self.graph_layout.setContentsMargins(0,0,0,0)
        
        self.setEnabled(False)

    def handleAnalyzerChange(self, index):

        # Disconnect old analyzer.
        if self.cur_analyzer is not None:
            self.cur_analyzer.totalCount.disconnect(self.handleTotalCount)
        
        # Remove previous analyzer from the display.
        self.graph_layout.takeAt(0)

        # Add the new analyzers display widgets.
        self.cur_analyzer = self.analyzers[index]
        self.graph_layout.addWidget(self.cur_analyzer.getSpotGraph())
        self.ui.imageScrollArea.setWidget(self.cur_analyzer.getSpotPicture())

        # Connect new analyzer.
        self.cur_analyzer.totalCount.connect(self.handleTotalCount)

        # Save current analyzer in the parameters.
        self.parameters.setv("which_camera", self.cur_analyzer.getCameraName())

    def handleMaxSpinBox(self, new_max):
        for analyzer in self.analyzers:
            analyzer.setMaxSpots(new_max)
        self.parameters.setv("max_spots", new_max)

    def handleTotalCount(self, total_count):
        self.ui.countsLabel1.setText(str(total_count))
        self.ui.countsLabel2.setText(str(total_count))

    def newAnalyzers(self, parameters, analyzers):
        #
        # This method is the first one that will get called
        # when the parameters change. We set everything up here.
        #

        # Clean up.
        self.ui.analyzerComboBox.clear()
        self.handleTotalCount(0)

        # Configure combo box.
        cur_analyzer = 0
        self.ui.analyzerComboBox.currentIndexChanged.disconnect(self.handleAnalyzerChange)
        if (len(analyzers) == 1):
            self.ui.analyzerComboBox.hide()
        else:
            self.ui.analyzerComboBox.show()
            for i, analyzer in enumerate(analyzers):
                if (parameters.get("which_camera") == analyzer.getCameraName()):
                    cur_analyzer = i
                self.ui.analyzerComboBox.addItem(analyzer.getCameraName())
            
        self.ui.analyzerComboBox.currentIndexChanged.connect(self.handleAnalyzerChange)        

        self.parameters = parameters
        self.analyzers = analyzers
        self.handleAnalyzerChange(cur_analyzer)

        self.ui.maxSpinBox.setValue(self.parameters.get("max_spots"))
        
        self.setEnabled(True)
        
        
class SpotCounter(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.analyzers = []
        self.basename = None
        self.feed_names = []
        self.number_fn_requested = 0
        self.pixel_size = 0.1
        self.shutters_info = None

        configuration = module_params.get("configuration")

        self.spot_counter = findSpots.SpotCounter(max_threads = configuration.get("max_threads"),
                                                  max_size = configuration.get("max_size"))

        self.view = SpotCounterView(module_name = self.module_name,
                                    configuration = configuration)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " spot counter")

        # Spot counter parameters.
        self.parameters = params.StormXMLObject()
        
        self.parameters.add(params.ParameterRangeInt(description = "Maximum counts for the spotcounter graph",
                                                     name = "max_spots",
                                                     value = 500,
                                                     min_value = 0,
                                                     max_value = 1000,
                                                     is_mutable = False,
                                                     is_saved = False))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Scale bar length in nm",
                                                       name = "scale_bar_len",
                                                       value = 2000,
                                                       min_value = 100,
                                                       max_value = 10000))

        self.parameters.add(params.ParameterRangeInt(description = "Spot detection threshold (camera counts)",
                                                     name = "threshold",
                                                     value = 250,
                                                     min_value = 1,
                                                     max_value = 10000))

        self.parameters.add(params.ParameterString(description = "Which camera to display.",
                                                   name = "which_camera",
                                                   value = "",
                                                   is_mutable = False,
                                                   is_saved = False))

    def cleanUp(self, qt_settings):
        self.cleanUpAnalyzers()
        self.spot_counter.cleanUp()
        self.view.cleanUp(qt_settings)

    def cleanUpAnalyzers(self):
        for analyzer in self.analyzers:
            analyzer.cleanUp()
            
    def handleResponses(self, message):
        
        if message.isType("get functionality"):
            assert (len(message.getResponses()) == 1)
            for response in message.getResponses():
                fn = response.getData()["functionality"]

                # Only analyze data from a camera.
                if fn.isCamera():
                    self.analyzers.append(Analyzer(camera_fn = fn,
                                                   parameters = self.parameters,
                                                   pixel_size = self.pixel_size,
                                                   shutters_info = self.shutters_info,
                                                   spot_counter = self.spot_counter))

                self.number_fn_requested -= 1

            if (self.number_fn_requested == 0):
                self.view.newAnalyzers(self.parameters,
                                       self.analyzers)
                
    def processMessage(self, message):

        if message.isType("changing parameters"):
            if not message.getData()["changing"]:
                self.newAnalyzers()
            
        elif message.isType("configuration"):

            if message.sourceIs("feeds"):
                self.feed_names = []
                for name in message.getData()["properties"]["feed names"]:
                    self.feed_names.append(name)

            elif message.sourceIs("illumination"):
                self.shutters_info = message.getData()["properties"]["shutters info"]
                for analyzer in self.analyzers:
                    analyzer.setShuttersInfo(self.shutters_info)
                
            elif message.sourceIs("mosaic"):
                self.pixel_size = message.getData()["properties"]["pixel_size"]

        elif message.isType("configure1"):

            # Broadcast initial parameters.
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.parameters}))

            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Spot Counter",
                                                           "item data" : "spot counter"}))

        elif message.isType("new parameters"):
            #
            # Just record the new parameters here. Then when we get a 'configuration' message
            # from feeds.feeds we'll get the names of the new feeds. And finally when we get
            # the 'changing parameters' message we'll update the analyzers.
            #
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.parameters.copy()}))
            self.parameters = message.getData()["parameters"].get(self.module_name)
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.parameters}))
            
        elif message.isType("show"):
            if (message.getData()["show"] == "spot counter"):
                self.view.show()

        elif message.isType("start"):
            self.newAnalyzers()
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("start film"):
            film_settings = message.getData()["film settings"]
            if film_settings.isSaved():
                self.basename = film_settings.getBasename()

            for analyzer in self.analyzers:
                analyzer.startFilm(film_settings)

        elif message.isType("stop film"):
            total_spots = 0
            for analyzer in self.analyzers:
                analyzer.stopFilm()
                total_spots += analyzer.getCounts()
                if self.basename is not None:
                    analyzer.savePicture(self.basename)

            self.basename = None
            
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.parameters.copy()}))

            counts_param = params.ParameterInt(name = "spot_counts",
                                               value = total_spots)
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"acquisition" : [counts_param]}))

    def newAnalyzers(self):

        # Disconnect old analyzers.
        self.cleanUpAnalyzers()
        
        #
        # Create new analyzers after a parameter change, or when HAL
        # starts. This is done by requesting functionalities for all
        # the available feeds.
        #
        self.analyzers = []
        for name in self.feed_names:
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : name}))
            self.number_fn_requested += 1

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

