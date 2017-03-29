#!/usr/bin/env python
"""
This class handles handles displaying camera data using the
appropriate qtCameraWidget class. It is also responsible for 
displaying the camera record and shutter buttons as well as
choosing the color table, scaling, etc..

Hazen 2/17
"""
import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.colorTables.colorTables as colorTables
import storm_control.hal4000.feeds.feeds as feeds
import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.hal4000.qtWidgets.qtCameraGraphicsScene as qtCameraGraphicsScene

import storm_control.hal4000.qtWidgets.qtColorGradient as qtColorGradient
#import storm_control.hal4000.qtWidgets.qtCameraWidget as qtCameraWidget
import storm_control.hal4000.qtWidgets.qtRangeSlider as qtRangeSlider

import storm_control.hal4000.qtdesigner.camera_display_ui as cameraDisplayUi


class BaseFrameDisplay(QtWidgets.QFrame):
    """
    The base frame display class.

    Handles the qtCameraWidget which displays the image as well as other
    GUI elements such as the display range slide, color table chooser, etc..

    This class also keeps track of the display settings for every camera
    and every feed. It is responsible for the 'display' sections of the
    parameters file.

    <displayn>
      <cameran>
        <colortable></colortable>
        <display_max></display_max>
        <display_min></display_min>
        <sync></sync>
      <cameran>
      ..
      <feedn>
        <colortable></colortable>
        <display_max></display_max>
        <display_min></display_min>
        <sync></sync>
      </feedn>
    </displayn>

    I'm not sure whether these shouldn't be feed specific instead of 
    display specific? That would also make it easier to include them
    in the parameters editor.
    """
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, display_name = None, feed_name = "camera1", **kwds):
        super().__init__(**kwds)

        # General (alphabetically ordered).
        self.color_gradient = None
        self.color_tables = colorTables.ColorTables(os.path.dirname(__file__) + "/../colorTables/all_tables/")
        self.cycle_length = 1
        self.display_name = display_name
        self.display_timer = QtCore.QTimer(self)
#        self.feed_name = feed_name
        self.filming = False
        self.frame = False
        self.parameters = params.StormXMLObject(validate = False)
        self.show_grid = False
        self.show_info = True
        self.show_target = False

        # Keep track of the current feed_name in parameters.
        self.parameters.add(params.ParameterString(name = "feed_name",
                                                   value = feed_name,
                                                   is_mutable = False))
        
        # UI setup.
        self.ui = cameraDisplayUi.Ui_Frame()
        self.ui.setupUi(self)

        # Camera frame display.
        self.camera_scene = qtCameraGraphicsScene.QtCameraGraphicsScene(parent = self)
        self.camera_widget = qtCameraGraphicsScene.QtCameraGraphicsItem()
        self.camera_scene.addItem(self.camera_widget)
        self.ui.cameraGraphicsView.setScene(self.camera_scene)

        self.ui.cameraGraphicsView.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))
        #self.camera_scene.sceneRectChanged.connect(self.ui.cameraGraphicsView.handleRectChanged)
        
        # Display range slider.
        self.ui.rangeSlider = qtRangeSlider.QVRangeSlider()
        layout = QtWidgets.QGridLayout(self.ui.rangeSliderWidget)
        layout.setContentsMargins(1,1,1,1)
        layout.addWidget(self.ui.rangeSlider)
        self.ui.rangeSliderWidget.setLayout(layout)
        self.ui.rangeSlider.setEmitWhileMoving(True)

        # Color tables combo box.
        for color_name in self.color_tables.getColorTableNames():
            self.ui.colorComboBox.addItem(color_name[:-5])

        self.ui.gridAct = QtWidgets.QAction(self.tr("Show Grid"), self)
        self.ui.infoAct = QtWidgets.QAction(self.tr("Hide Info"), self)
        self.ui.targetAct = QtWidgets.QAction(self.tr("Show Target"), self)

        self.ui.cameraShutterButton.hide()
        self.ui.recordButton.hide()

        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()

#        self.camera_widget = qtCameraWidget.QCameraWidget(parent = self.ui.cameraScrollArea)
#        self.ui.cameraScrollArea.setWidget(self.camera_widget)
#        self.ui.cameraScrollArea.setStyleSheet("QScrollArea { background-color: black } ")


        # Connect signals.
#        self.camera_widget.intensityInfo.connect(self.handleIntensityInfo)

        self.ui.autoScaleButton.clicked.connect(self.handleAutoScale)
        self.ui.colorComboBox.currentIndexChanged[str].connect(self.handleColorTableChange)
        self.ui.feedComboBox.currentIndexChanged[str].connect(self.handleFeedChange)
        self.ui.gridAct.triggered.connect(self.handleGrid)
        self.ui.infoAct.triggered.connect(self.handleInfo)        
        self.ui.rangeSlider.doubleClick.connect(self.handleAutoScale)        
        self.ui.rangeSlider.rangeChanged.connect(self.handleRangeChange)
        self.ui.syncSpinBox.valueChanged.connect(self.handleSync)
        self.ui.targetAct.triggered.connect(self.handleTarget)

        # Display timer, the display updates at approximately 10Hz.
        self.display_timer.setInterval(100)
        self.display_timer.timeout.connect(self.handleDisplayTimer)
        self.display_timer.start()
        
    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.ui.infoAct)
        menu.addAction(self.ui.targetAct)
        menu.addAction(self.ui.gridAct)
        menu.exec_(event.globalPos())

    def feedConfig(self, data):
        """
        This method gets called when any of the views changes it's 
        current feed or 'display00' changes the current camera.
        """
        feed_name = data["feed_name"]
        feed_info = data["feed_info"]

        #
        # Add a sub-section for this camera / feed if we don't already have one.
        #
        # The camera / feed provides default values about how it's images should
        # be displayed. These are what we'll use if don't already have some other
        # values.
        #
        if not self.parameters.has(feed_name):

            # Create a sub-section for this camera / feed.
            p = self.parameters.addSubSection(feed_name)

            # Add display specific parameters.
            p.add(params.ParameterSetString(description = "Color table",
                                            name = "colortable",
                                            value = feed_info["colortable"],
                                            allowed = self.color_tables.getColorTableNames()))
                        
            p.add(params.ParameterInt(description = "Display maximum",
                                      name = "display_max",
                                      value = feed_info["default_max"]))

            p.add(params.ParameterInt(description = "Display minimum",
                                      name = "display_min",
                                      value = feed_info["default_min"]))

            p.add(params.ParameterInt(name = "max_intensity",
                                      value = feed_info["max_intensity"],
                                      is_mutable = False,
                                      is_saved = False))

            p.add(params.ParameterInt(description = "Frame to display when filming with a shutter sequence",
                                      name = "sync",
                                      value = 0))

            p.add(params.ParameterInt(name = "sync_max",
                                      value = 0,
                                      is_mutable = False,
                                      is_saved = False))

        #
        # Update UI settings if the feed / camera that we got configuration
        # information for is the current feed / camera.
        #
        if (self.getFeedName() == feed_name):

            # Configure the QtCameraGraphicsItem.
            color_table = self.color_tables.getTableByName(self.getParameter("colortable"))
            self.camera_widget.newColorTable(color_table)
            self.camera_widget.newConfiguration(feed_info)
            self.updateRange()

            # Configure the QtCameraGraphicsView.
            #self.ui.cameraGraphicsView.setMaxViewable(feed_info["x_pixels"], feed_info["y_pixels"])
            self.ui.cameraGraphicsView.newConfiguration(feed_info)
            
            # Color gradient.
            if self.color_gradient is not None:
                self.color_gradient.newColorTable(color_table)
            else:
                self.color_gradient = qtColorGradient.QColorGradient(colortable = color_table,
                                                                     parent = self.ui.colorFrame)
                layout = QtWidgets.QGridLayout(self.ui.colorFrame)
                layout.setContentsMargins(2,2,2,2)
                layout.addWidget(self.color_gradient)
                
            self.ui.colorComboBox.setCurrentIndex(self.ui.colorComboBox.findText(self.getParameter("colortable")[:-5]))

            # General settings.
            self.ui.rangeSlider.setRange([0.0, self.getParameter("max_intensity"), 1.0])
            self.ui.rangeSlider.setValues([float(self.getParameter("display_min")),
                                           float(self.getParameter("display_max"))])

            self.setSyncMax(self.getParameter("sync_max"))
            self.ui.syncSpinBox.setValue(self.getParameter("sync"))

    def getDisplayName(self):
        return self.display_name

    def getFeedName(self):
        return self.parameters.get("feed_name")
    
    def getParameter(self, pname):
        """
        Wrapper to make it easier to get the appropriate parameter value.
        """
        return self.parameters.get(self.getFeedName()).get(pname)

    def getParameters(self):
        return self.parameters
    
    def handleAutoScale(self, bool):
        [scalemin, scalemax] = self.camera_widget.getAutoScale()
        if scalemin < 0:
            scalemin = 0
        if scalemax > self.max_intensity:
            scalemax = self.max_intensity
        self.ui.rangeSlider.setValues([float(scalemin), float(scalemax)])

    def handleColorTableChange(self, table_name):
        table_name = str(table_name)
        self.setParameter("colortable", table_name + ".ctbl")
        color_table = self.color_tables.getTableByName(self.getParameter("colortable"))
        self.camera_widget.newColorTable(color_table)
        self.color_gradient.newColorTable(color_table)

    def handleDisplayTimer(self):
        if self.frame:
            self.camera_widget.updateImageWithFrame(self.frame)

    def handleFeedChange(self, feed_name):
        """
        This sends a message to the new camera / feed that it will
        respond to with information about it should be displayed.
        """
        self.parameters.set("feed_name", str(feed_name))
        self.guiMessage.emit(halMessage.HalMessage(m_type = "get feed config",
                                                   data = {"display_name" : self.display_name,
                                                           "feed_name" : self.getFeedName()}))

    def handleGrid(self, boolean):
        if self.show_grid:
            self.show_grid = False
            self.ui.gridAct.setText("Show Grid")
        else:
            self.show_grid = True
            self.ui.gridAct.setText("Hide Grid")
        self.camera_widget.setShowGrid(self.show_grid)

    def handleInfo(self, boolean):
        if self.show_info:
            self.show_info = False
            self.ui.infoAct.setText("Show Info")
            self.ui.intensityPosLabel.hide()
            self.ui.intensityIntLabel.hide()
        else:
            self.show_info = True
            self.ui.infoAct.setText("Hide Info")
            self.ui.intensityPosLabel.show()
            self.ui.intensityIntLabel.show()
        self.camera_widget.setShowInfo(self.show_info)

    def handleIntensityInfo(self, x, y, i):
        self.ui.intensityPosLabel.setText("({0:d},{1:d})".format(x, y, i))
        self.ui.intensityIntLabel.setText("{0:d}".format(i))

    def handleRangeChange(self, scale_min, scale_max):
        if (scale_max == scale_min):
            if (scale_max < float(self.getParameter("max_intensity"))):
                scale_max += 1.0
            else:
                scale_min -= 1.0
        self.setParameter("display_max", int(scale_max))
        self.setParameter("display_min", int(scale_min))
        self.updateRange()

    def handleSync(self, sync_value):
        self.setParameter("sync", sync_value)

    def handleTarget(self, boolean):
        if self.show_target:
            self.show_target = False
            self.ui.targetAct.setText("Show Target")
        else:
            self.show_target = True
            self.ui.targetAct.setText("Hide Target")
        self.camera_widget.setShowTarget(self.show_target)

    def newFrame(self, frame):
        if (frame.which_camera == self.getFeedName()):
            if self.filming and (self.getParameter("sync") != 0):
                if((frame.number % self.cycle_length) == (self.getParameter("sync") - 1)):
                    self.frame = frame
            else:
                self.frame = frame

    def newParametersEnd(self):
        """
        This is called when we get the 'updated parameters' message.
        It indicates that the new parameters are good and we can go
        ahead and update the display accordingly.
        """
        self.handleFeedChange(self.parameters.get("feed_name"))

    def newParametersStart(self, parameters):
        """
        How this is supposed to work..

        1. Replace current parameters with the new parameters when
           we get the 'new parameters' message.

        2. Wait for the 'updated parameters' message.

        3. Execute a feed change to the new camera / feed,
           this will send a 'get feed config' message.

        4. The camera / feed will respond to the message with 
           the correct frame size, etc. for display.

        5. The viewFeedConfig() method will then handle actually
           updating everything.
        """
        # FIXME: Check that there are no problems with the new parameters?
        #        We need to error now rather than at 'updated parameters'.
        self.parameters = parameters

    def setFeeds(self, feeds_info):
        """
        This updates feed selector combo box with a list of 
        the feeds that are currently available.
        """
        # Disconnect signal.
        self.ui.feedComboBox.currentIndexChanged[str].disconnect()

        # Update combo box with the new feed names.
        self.ui.feedComboBox.clear()
        if (len(feeds_info) > 1):
            for feed_name in sorted(feeds_info):
                self.ui.feedComboBox.addItem(feed_name)
            self.ui.feedComboBox.setCurrentIndex(self.ui.feedComboBox.findText(self.getFeedName()))
            self.ui.feedComboBox.show()
        else:
            self.ui.feedComboBox.hide()

        # Reconnect signal.
        self.ui.feedComboBox.currentIndexChanged[str].connect(self.handleFeedChange)

    def setParameter(self, pname, pvalue):
        """
        Wrapper to make it easier to set the appropriate parameter value.
        """
        feed_params = self.parameters.get(self.getFeedName())
        feed_params.set(pname, pvalue)
        return pvalue
            
    def setSyncMax(self, sync_max):
        self.setParameter("sync_max", sync_max)
        self.ui.syncSpinBox.disconnect()
        self.ui.syncSpinBox.setMaximum(sync_max)
        self.ui.syncSpinBox.valueChanged.connect(self.handleSync)        
        
    def startFilm(self, film_settings):
        self.filming = True
        if film_settings["run_shutters"]:
            self.ui.syncLabel.show()
            self.ui.syncSpinBox.show()
        if self.ui.cameraShutterButton.isVisible():
            self.ui.cameraShutterButton.setEnabled(False)
            
    def stopFilm(self):
        self.filming = False
        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()
        if self.ui.cameraShutterButton.isVisible():
            self.ui.cameraShutterButton.setEnabled(True)
                
    def updateRange(self):
        self.ui.scaleMax.setText(str(self.getParameter("display_max")))
        self.ui.scaleMin.setText(str(self.getParameter("display_min")))
        self.camera_widget.newRange(self.getParameter("display_min"), self.getParameter("display_max"))


class CameraFrameDisplay(BaseFrameDisplay):
    """
    Add handling of interaction with the feeds, i.e. mouse drags,
    ROI selection, etc..

    FIXME:
      1. Dragging should not be specific to the main display?
      2. Dragging should only work for the cameras, not feeds?
    """
    def __init__(self, show_record = False, **kwds):
        super().__init__(**kwds)

#        self.camera_widget.setDragEnabled(True)
        
        if show_record:
            self.ui.recordButton.show()
                
        # Signals
        #self.camera_widget.displayCaptured.connect(self.handleDisplayCaptured)
        #self.camera_widget.dragStart.connect(self.handleDragStart)
        #self.camera_widget.dragMove.connect(self.handleDragMove)
        #self.camera_widget.roiSelection.connect(self.handleROISelection)

        self.ui.cameraShutterButton.clicked.connect(self.handleCameraShutter)
        self.ui.recordButton.clicked.connect(self.handleRecord)

    def handleFeedChange(self, feed_name):
        self.parameters.set("feed_name", str(feed_name))
        [camera, feed] = feeds.getCameraFeedName(feed_name)

        # This will get the updated feed information.
        if feed is not None:
            self.guiMessage.emit(halMessage.HalMessage(m_type = "get feed information",
                                                       data = {"display_name" : self.display_name,
                                                               "feed_name" : self.getFeedName()}))

        # This will get the correct camera.
        self.guiMessage.emit(halMessage.HalMessage(m_type = "set current camera",
                                                   data = {"display_name" : self.display_name,
                                                           "camera" : camera}))

    def handleCameraShutter(self, boolean):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "shutter clicked",
                                                   data = {"display_name" : self.display_name,
                                                           "feed_name" : self.getFeedName()}))

    def handleDisplayCaptured(self, a_pixmap):
        #self.frameCaptured.emit(self.feed_name, a_pixmap)
        pass

    def handleDragStart(self):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "drag start",
                                                   level = 3,
                                                   data = {"display_name" : self.display_name,
                                                           "feed_name" : self.getFeedName()}))

    def handleDragMove(self, x_disp, y_disp):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "drag move",
                                                   level = 3,
                                                   data = {"display_name" : self.display_name,
                                                           "feed_name" : self.getFeedName(),
                                                           "x_disp" : x_disp,
                                                           "y_disp" : y_disp}))

    def handleRecord(self, boolean):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "record clicked",
                                                   data = {"display_name" : self.display_name}))
        
    def handleROISelection(self, select_rect):
        #self.ROISelection.emit(self.feed_name, select_rect)
        pass

    def handleSync(self, sync_value):
        """
        Handles setting the sync parameter. This parameter is used in
        shutter sequences to specify which frame in the sequence should
        be displayed, or just any random frame.

        FIXME: Do we need this? It doesn't do anything..
        """
        super.handleSync(self, sync_value)
        #self.setParameter("sync", sync_value)

    def startFilm(self, film_settings):
        super().startFilm(film_settings)
        if self.ui.recordButton.isVisible():
            self.ui.recordButton.setText("Stop")
            if film_settings["save_film"]:
                self.ui.recordButton.setStyleSheet("QPushButton { color: red }")
            else:
                self.ui.recordButton.setStyleSheet("QPushButton { color: orange }")

    def stopFilm(self):
        super().stopFilm()
        if self.ui.recordButton.isVisible():
            self.ui.recordButton.setText("Record")
            self.ui.recordButton.setStyleSheet("QPushButton { color: black }")

#    def updateCameraProperties(self, camera_properties):
#        if self.feed_name in camera_properties:
#            if "have_shutter" in camera_properties[self.feed_name]:
#                self.ui.cameraShutterButton.show()
#            else:
#                self.ui.cameraShutterButton.hide()
#        else:
#            self.ui.cameraShutterButton.hide()

#    def updatedParams(self):
#        if self.getParameter("shutter", False):
#            self.ui.cameraShutterButton.setText("Close Shutter")
#            self.ui.cameraShutterButton.setStyleSheet("QPushButton { color: green }")
#        else:
#            self.ui.cameraShutterButton.setText("Open Shutter")
#            self.ui.cameraShutterButton.setStyleSheet("QPushButton { color: black }")


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
