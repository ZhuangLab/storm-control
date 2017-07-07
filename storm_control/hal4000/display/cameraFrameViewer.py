#!/usr/bin/env python
"""
This class handles most of the functionality of the camera
frame display. This includes:

1. Showing the frames from the camera.
2. Handling scaling.
3. Handling the color table.
4. Handling dragging.
5. Broadcasting the current image.
6. Handling the changing the feed.
7. Handling information, target, and grid.

Hazen 2/17
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.colorTables.colorTables as colorTables
import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.hal4000.qtWidgets.qtCameraGraphicsScene as qtCameraGraphicsScene
import storm_control.hal4000.qtWidgets.qtColorGradient as qtColorGradient
import storm_control.hal4000.qtWidgets.qtRangeSlider as qtRangeSlider

import storm_control.hal4000.qtdesigner.camera_display_ui as cameraDisplayUi


class CameraFrameViewer(QtWidgets.QFrame):
    """
    The camera frame viewer class.

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
    feedChange = QtCore.pyqtSignal(str)
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, display_name = None, feed_name = "camera1", default_colortable = None, **kwds):
        super().__init__(**kwds)

        # General (alphabetically ordered).
        self.broadcast_q_image = False
        self.cam_fn = None
        self.color_gradient = None
        self.color_tables = colorTables.ColorTables(os.path.dirname(__file__) + "/../colorTables/all_tables/")
        self.cycle_length = 0
        self.default_colortable = default_colortable
        self.default_parameters = params.StormXMLObject(validate = False) 
        self.display_name = display_name
        self.display_timer = QtCore.QTimer(self)
        self.filming = False
        self.frame = False
        self.parameters = False
        self.rubber_band_rect = None
        self.show_grid = False
        self.show_info = True
        self.show_target = False
        self.stage_functionality = None

        #
        # Keep track of the default feed_name in the default parameters, these
        # are the parameters that will be used when we change parameter files
        # and the parameters file doesn't specify anything for this view.
        #
        self.default_parameters.add(params.ParameterString(name = "feed_name",
                                                           value = feed_name,
                                                           is_mutable = False))

        # Set current parameters to default parameters.
        self.parameters = self.default_parameters.copy()
        
        # UI setup.
        self.ui = cameraDisplayUi.Ui_Frame()
        self.ui.setupUi(self)

        # Camera frame display.
        self.camera_view = self.ui.cameraGraphicsView
        self.camera_scene = qtCameraGraphicsScene.QtCameraGraphicsScene(parent = self)
        self.camera_widget = qtCameraGraphicsScene.QtCameraGraphicsItem()
        
        self.camera_scene.addItem(self.camera_widget)
        self.camera_view.setScene(self.camera_scene)
        self.camera_view.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(0,0,0)))
        
        # Display range slider.
        self.ui.rangeSlider = qtRangeSlider.QVRangeSlider()
        layout = QtWidgets.QGridLayout(self.ui.rangeSliderWidget)
        layout.setContentsMargins(1,1,1,1)
        layout.addWidget(self.ui.rangeSlider)
        self.ui.rangeSliderWidget.setLayout(layout)
        self.ui.rangeSlider.setEmitWhileMoving(True)

        # Color tables combo box.
        for color_name in sorted(self.color_tables.getColorTableNames()):
            self.ui.colorComboBox.addItem(color_name[:-5])

        self.ui.gridAct = QtWidgets.QAction(self.tr("Show Grid"), self)
        self.ui.infoAct = QtWidgets.QAction(self.tr("Hide Info"), self)
        self.ui.targetAct = QtWidgets.QAction(self.tr("Show Target"), self)

        # The default is not to show the shutter or the record button.
        self.ui.recordButton.hide()
        self.ui.shutterButton.hide()

        # These are always hidden unless we are filming.
        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()

        # FIXME: This only sort of works, the text is still getting cut-off.
        self.ui.feedComboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        
        # Connect signals.
        self.camera_view.horizontalScrollBar().sliderReleased.connect(self.handleScrollBar)
        self.camera_view.newCenter.connect(self.handleNewCenter)
        self.camera_view.newScale.connect(self.handleNewScale)
        self.camera_view.verticalScrollBar().sliderReleased.connect(self.handleScrollBar)

        self.camera_view.dragMove.connect(self.handleDragMove)
        self.camera_view.dragStart.connect(self.handleDragStart)
        self.camera_view.rubberBandChanged.connect(self.handleRubberBandChanged)

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

    def createParameters(self, cam_fn, parameters_from_file):
        """
        Create (initial) parameters for the current feed.

        cam_fn - A camera / feed functionality object.
        parameters_from_file - The parameters that were read from the XML file.
        """
        # Check that we are not writing over something that already exists.
        if (self.parameters.has(self.getFeedName())):
            msg = "Display parameters for " + self.getFeedName() + " already exists."
            raise halExceptions.HalException(msg)

        # Create a sub-section for this camera / feed.
        p = self.parameters.addSubSection(self.getFeedName())

        # Add display specific parameters.
        p.add(params.ParameterFloat(name = "center_x",
                                    value = 0.0,
                                    is_mutable = False))

        p.add(params.ParameterFloat(name = "center_y",
                                    value = 0.0,
                                    is_mutable = False))
            
        p.add(params.ParameterSetString(description = "Color table",
                                        name = "colortable",
                                        value = self.color_tables.getColorTableNames()[0],
                                        allowed = self.color_tables.getColorTableNames()))
                        
        p.add(params.ParameterInt(description = "Display maximum",
                                  name = "display_max",
                                  value = 100))

        p.add(params.ParameterInt(description = "Display minimum",
                                  name = "display_min",
                                  value = 0))

        p.add(params.ParameterSetBoolean(name = "initialized",
                                         value = False,
                                         is_mutable = False))

        p.add(params.ParameterInt(name = "max_intensity",
                                  value = 100,
                                  is_mutable = False,
                                  is_saved = False))

        p.add(params.ParameterInt(name = "scale",
                                  value = 0,
                                  is_mutable = False))
            
        p.add(params.ParameterInt(description = "Frame to display when filming with a shutter sequence",
                                  name = "sync",
                                  value = 0))

        # Set parameters with default values from feed/camera functionality
        if cam_fn.hasParameter("colortable"):
            p.setv("colortable", cam_fn.getParameter("colortable"))
        else:
            p.setv("colortable", self.default_colortable)
        p.setv("display_max", cam_fn.getParameter("default_max"))
        p.setv("display_min", cam_fn.getParameter("default_min"))
        p.setv("max_intensity", cam_fn.getParameter("max_intensity"))

        # If they exist, update with the values that we loaded from a file.
        if parameters_from_file is not None:
            for attr in parameters_from_file.getAttrs():
                p.setv(attr, parameters_from_file.get(attr))

    def getDefaultParameters(self):
        """
        Return a copy of the default parameters. These are used when we change
        parameters and the new parameters don't have a "displayXX" section.
        """
        return self.default_parameters.copy()

    def getFeedName(self):
        """
        Return current feed name.
        """
        return self.parameters.get("feed_name")
    
    def getParameter(self, pname):
        """
        Wrapper to make it easier to get the appropriate parameter value.
        """
        return self.parameters.get(self.getFeedName()).get(pname)

    def getParameters(self):
        """
        Return the current parameters.
        """
        return self.parameters

    def handleAutoScale(self, bool):
        [scalemin, scalemax] = self.camera_widget.getAutoScale()
        if scalemin < 0:
            scalemin = 0
        if scalemax > self.getParameter("max_intensity"):
            scalemax = self.getParameter("max_intensity")
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
            if self.show_info:
                self.handleIntensityInfo(*self.camera_widget.getIntensityInfo())
            # This is a stub. Fill it out when we get Bluetooth up and running again.
            if self.broadcast_q_image:
                pass

    def handleDragMove(self, dx, dy):
        self.stage_functionality.dragMove(dx, dy)

    def handleDragStart(self):
        self.stage_functionality.dragStart()
        
    def handleFeedChange(self, feed_name):
        """
        This sends a message to the new camera / feed that it will respond 
        to with information about how it should be displayed.
        """

        #
        # Disconnect current camera functionality. Anything that results
        # in a change in the camera functionality should pass through
        # this method, otherwise we can end up with multiple camera
        # functionalities connected to handleNewFrame, which will be a
        # mess..
        #
        if self.cam_fn is not None:
            self.cam_fn.newFrame.disconnect(self.handleNewFrame)
            
        self.parameters.setv("feed_name", str(feed_name))
        self.feedChange.emit(feed_name)

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

    def handleIntensityInfo(self, x, y, i):
        self.ui.intensityPosLabel.setText("({0:d},{1:d})".format(x, y, i))
        self.ui.intensityIntLabel.setText("{0:d}".format(i))

    def handleNewCenter(self, cx, cy):
        self.setParameter("center_x", cx)
        self.setParameter("center_y", cy)
        self.camera_widget.setClickPos(*self.cam_fn.transformChipToFrame(cx, cy))

    def handleNewFrame(self, frame):
        if self.filming and (self.getParameter("sync") != 0):
            if((frame.frame_number % self.cycle_length) == (self.getParameter("sync") - 1)):
                self.frame = frame
        else:
            self.frame = frame

    def handleNewScale(self, scale):
        self.setParameter("scale", scale)

    def handleRangeChange(self, scale_min, scale_max):
        if (scale_max == scale_min):
            if (scale_max < float(self.getParameter("max_intensity"))):
                scale_max += 1.0
            else:
                scale_min -= 1.0
        self.setParameter("display_max", int(scale_max))
        self.setParameter("display_min", int(scale_min))
        self.updateRange()

    def handleRubberBandChanged(self, rubber_band_rect, from_scene_point, to_scene_point):
        print(">hrbc", rubber_band_rect)
        print(">hrbc", from_scene_point)
        print(">hrbc", to_scene_point)
        
    def handleScrollBar(self):
        self.camera_view.getCurrentCenter()

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

    def newParameters(self, parameters):
        """
        How this is supposed to work..

        1. Replace current parameters with the new parameters when
           we get the 'new parameters' message.

        2. Wait for the 'configuration' message from the feeds module
           when the setFeedNames() method will get called.

        3. At the end of setFeedNames() Execute a feed change to the 
           new camera / feed, this will send a 'get functionality' 
           message.

        4. The camera / feed will respond with a functionality.

        5. The setCameraFunctionality() method will then handle updating
           the display.
        """
        # FIXME: Check that there are no problems with the new parameters?
        #        We need to error now rather than at 'updated parameters'.
        self.parameters = parameters

        # Add parameters in our default parameters if they don't exist.
        for attr in self.default_parameters.getAttrs():
            if not self.parameters.has(attr):
                self.parameters.add(attr, self.default_parameters.getp(attr).copy())

    def setCameraFunctionality(self, camera_functionality):
        """
        This method gets called when the view changes it's current feed. The
        sequence is that a 'get functionality' message is sent. When
        the display module gets the updated functionality it calls this 
        method.
        """

        # Give the correct functionality to the shutter button.
        if camera_functionality.isCamera():
            self.ui.shutterButton.setCameraFunctionality(camera_functionality)
        else:
            self.ui.shutterButton.setCameraFunctionality(camera_functionality.getCameraFunctionality())

        # A sanity check that this is the right feed.
        assert (self.getFeedName() == camera_functionality.getCameraName())

        # A sanity check that the old camera functionality is disconnected.
        if self.cam_fn is not None:
            try:
                self.cam_fn.newFrame.disconnect(self.handleNewFrame)
            except TypeError:
                pass
            else:
                msg = "Old camera functionality was not disconnected."
                raise halExceptions.HalException(msg)
                
        # Connect new camera functionality.
        self.cam_fn = camera_functionality
        self.cam_fn.newFrame.connect(self.handleNewFrame)

        #
        # Add a sub-section for this camera / feed if we don't already have one.
        #
        # The camera / feed provides default values about how it's images should
        # be displayed. These are what we'll use if don't already have some other
        # values.
        #
        parameters_from_file = None
        need_to_initialize = False

        # Check if we have anything at all for this feed.
        if not self.parameters.has(self.getFeedName()):
            need_to_initialize = True

        #
        # Check if all we have are values from a parameter file that we loaded.
        # In this case we will only have some of the parameters and some of
        # them will not be of the correct type.
        #
        # We're doing this by checking for "max_intensity" as this should not
        # have been saved, so if it exists then the parameters must have been
        # initialized properly.
        #
        # In order to initialize them properly we make a copy of the current
        # values, then delete the section, recreate it correctly and update
        # it with the current values.
        #
        else:
            feed_params = self.parameters.get(self.getFeedName())
            if not feed_params.has("max_intensity"):
                need_to_initialize = True
                parameters_from_file = feed_params.copy()
                self.parameters.delete(self.getFeedName())

        if need_to_initialize:
            self.createParameters(self.cam_fn, parameters_from_file)

        # Configure the QtCameraGraphicsItem.
        color_table = self.color_tables.getTableByName(self.getParameter("colortable"))
        self.camera_widget.newColorTable(color_table)
        self.camera_widget.newConfiguration(self.cam_fn)
        self.updateRange()

        # Configure the QtCameraGraphicsView.
        self.camera_view.newConfiguration(self.cam_fn, self.parameters.get(self.getFeedName()))

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

        self.ui.syncSpinBox.setValue(self.getParameter("sync"))

    def setFeedNames(self, feed_names):
        """
        This updates feed selector combo box with a list of 
        the feeds that are currently available.
        """
        # Disconnect signal.
        self.ui.feedComboBox.currentIndexChanged[str].disconnect()

        # Update combo box with the new feed names.
        self.ui.feedComboBox.clear()
        if (len(feed_names) > 1):
            for feed_name in sorted(feed_names):
                self.ui.feedComboBox.addItem(feed_name)
            self.ui.feedComboBox.setCurrentIndex(self.ui.feedComboBox.findText(self.getFeedName()))
            self.ui.feedComboBox.show()
        else:
            self.ui.feedComboBox.hide()

        # Reconnect signal.
        self.ui.feedComboBox.currentIndexChanged[str].connect(self.handleFeedChange)

        # Switch to the correct feed.
        self.handleFeedChange(self.getFeedName())

    def setParameter(self, pname, pvalue):
        """
        Wrapper to make it easier to set the appropriate parameter value.
        """
        feed_params = self.parameters.get(self.getFeedName())
        feed_params.set(pname, pvalue)
        return pvalue

    def setStageFunctionality(self, stage_functionality):
        self.stage_functionality = stage_functionality
        self.camera_view.enableStageDrag(True)
        
    def setSyncMax(self, sync_max):
        self.cycle_length = sync_max
        self.ui.syncSpinBox.valueChanged.disconnect(self.handleSync)
        self.ui.syncSpinBox.setMaximum(sync_max)
        self.ui.syncSpinBox.valueChanged.connect(self.handleSync)        

    def showRecord(self, show):
        self.ui.recordButton.setVisible(show)
        
    def startFilm(self, film_settings):
        self.filming = True
        if film_settings.runShutters():
            self.ui.syncLabel.show()
            self.ui.syncSpinBox.show()

        self.ui.recordButton.startFilm(film_settings)
        self.ui.shutterButton.startFilm()
            
    def stopFilm(self):
        self.filming = False
        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()

        self.ui.recordButton.stopFilm()
        self.ui.shutterButton.stopFilm()

#    def updatedParameters(self):
#        """
#        This is called when we get the 'updated parameters' message.
#        It indicates that the new parameters are good and we can go
#        ahead and update the display accordingly.
#        """
#        self.handleFeedChange(self.parameters.get("feed_name"))
            
    def updateRange(self):
        self.ui.scaleMax.setText(str(self.getParameter("display_max")))
        self.ui.scaleMin.setText(str(self.getParameter("display_min")))
        self.camera_widget.newRange(self.getParameter("display_min"), self.getParameter("display_max"))


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
