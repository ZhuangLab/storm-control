#!/usr/bin/env python
"""
Handles:

(1) All the UI elements in the Mosaic tab except for 
    the positions list widget. 

(2) Image capture from HAL.


Hazen 10/18
"""
import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.hal4000.qtWidgets.qtRangeSlider as qtRangeSlider

import storm_control.steve.comm as comm
import storm_control.steve.coord as coord
import storm_control.steve.imageCapture as imageCapture
import storm_control.steve.imageItem as imageItem
import storm_control.steve.mosaicView as mosaicView
import storm_control.steve.objectives as objectives
import storm_control.steve.qtdesigner.mosaic_ui as mosaicUi
import storm_control.steve.steveModule as steveModule


class Mosaic(steveModule.SteveModule):

    mosaicRequestPositions = QtCore.pyqtSignal(object)

    @hdebug.debug
    def __init__(self, image_capture = None, **kwds):
        super().__init__(**kwds)

#        self.current_center = coord.Point(0.0, 0.0, "um")
#        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.extrapolate_count = self.parameters.get("extrapolate_picture_count")
        self.filename = self.parameters.get("image_filename")
        self.fractional_overlap = self.parameters.get("fractional_overlap", 0.05)
        self.image_capture = image_capture
        self.track_stage_timer = QtCore.QTimer(self)

        # Configure stage tracking timer.
        self.track_stage_timer.setInterval(500)
        self.track_stage_timer.setSingleShot(True)
        self.track_stage_timer.timeout.connect(self.handleTrackStageTimer)

        # Create UI.
        self.ui = mosaicUi.Ui_Form()
        self.ui.setupUi(self)

        # Set up view.
        self.mosaic_view = mosaicView.MosaicView()
        layout = QtWidgets.QGridLayout(self.ui.mosaicFrame)
        layout.addWidget(self.mosaic_view)
        self.ui.mosaicFrame.setLayout(layout)
        self.mosaic_view.show()
        self.mosaic_view.setScene(self.item_store.getScene())

        # Create a validator for scaleLineEdit.
        self.scale_validator = QtGui.QDoubleValidator(1.0e-6, 1.0e+6, 6, self.ui.scaleLineEdit)
        self.ui.scaleLineEdit.setValidator(self.scale_validator)

        # Connect UI signals.
        self.ui.getStagePosButton.clicked.connect(self.handleGetStagePosButton)
        self.ui.imageGridButton.clicked.connect(self.handleImageGridButton)
        self.ui.scaleLineEdit.textChanged.connect(self.handleScaleChange)
        self.ui.trackStageCheckBox.stateChanged.connect(self.handleTrackStage)
        self.ui.xSpinBox.valueChanged.connect(self.handleXYSpinBox)
        self.ui.ySpinBox.valueChanged.connect(self.handleXYSpinBox)
        self.ui.genPosButton.clicked.connect(self.handleGenPosButton)
        self.ui.getStagePosPosButton.clicked.connect(self.handleGetStagePosForPosButton)
        self.ui.posGridSpinX.valueChanged.connect(self.handleXYGridSpinBox)
        self.ui.posGridSpinY.valueChanged.connect(self.handleXYGridSpinBox)

        # Connect view signals.
        self.mosaic_view.extrapolateTakeMovie.connect(self.handleExtrapolateTakeMovie)
        self.mosaic_view.mouseMove.connect(self.handleMouseMove)
        self.mosaic_view.scaleChange.connect(self.handleViewScaleChange)

        # Connect image capture signals.
        self.image_capture.captureComplete.connect(self.handleCaptureComplete)
        self.image_capture.sequenceComplete.connect(self.handleSequenceComplete)

        # Set loader for loading ImageItems from a mosaic file.
        self.item_store.addLoader(imageItem.ImageItem.data_type,
                                  imageItem.ImageItemLoader())

        # Set starting image grid size.
        self.handleXYSpinBox(None)

        # Set starting scale.
        self.ui.scaleLineEdit.setText("0.15")

    def getPositionsGroupBox(self):
        """
        Return the positions group box UI element for the 
        benefit of the Positions() object.
        """
        return self.ui.positionsGroupBox

    def getStagePosition(self):
        msg = comm.CommMessagePosition(finalizer_fn = self.handlePositionMessage)
        self.comm.sendMessage(msg)

    def getStagePositionForPositions(self):
        msg = comm.CommMessagePosition(finalizer_fn = self.handlePositionMessageForPosition)
        self.comm.sendMessage(msg)

    def handleAdjustContrast(self, ignored):
        objective_name = self.ui.objectivesGroupBox.getCurrentName()
        if objective_name is None:
            return
        
        # Determine the current contrast. We're assuming that all the
        # images taken with the same objective have the same contrast.
        current_contrast = None
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getObjectiveName() == objective_name):
                current_contrast = item.getContrast()
                break

        # Maybe there are no images taken with this objective. Use
        # some arbitrary defaults instead.
        if current_contrast is None:
            current_contrast = [0, 16000]
 
        # Prepare and display dialog
        dialog = qtRangeSlider.QRangeSliderDialog(self,
                                                  "Adjust Contrast",
                                                  slider_range = [0, 65000,1],
                                                  values = current_contrast,
                                                  slider_type = "vertical")

        if dialog.exec_():
            new_contrast = dialog.getValues() # Get values
            print("Adjusted Contrast: " + str(new_contrast))
            for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
                if (item.getObjectiveName() == objective_name):
                    item.setContrast(*new_contrast)
                    
    @hdebug.debug
    def handleGetStagePosButton(self, ignored):
        self.getStagePosition()

    @hdebug.debug
    def handleGetStagePosForPosButton(self, ignored):
        self.getStagePositionForPositions()


    @hdebug.debug
    def handleGenPosButton(self, ignored):
        position_dict = {'x_center': self.ui.posCenterSpinX.value(), 
                         'y_center': self.ui.posCenterSpinY.value(), 
                         'x_grid': self.ui.posGridSpinX.value(), 
                         'y_grid': self.ui.posGridSpinY.value(), 
                         'grid_spacing': self.ui.positionGridSpacing.value()}
        self.mosaicRequestPositions.emit(position_dict)

    @hdebug.debug
    def handleGoToPosition(self, ignored):

        # Include the offset in the stage position under the assumption
        # that this is where the user is going to want to start taking
        # pictures.
        current_offset = self.ui.objectivesGroupBox.getCurrentOffset()
        if current_offset is None:
            return
        
        msg = comm.CommMessageStage(disconnect = True,
                                    finalizer_fn = self.handleStageMessage,
                                    stage_x = self.mosaic_event_coord.x_um - current_offset.x_um,
                                    stage_y = self.mosaic_event_coord.y_um - current_offset.y_um)
        self.comm.sendMessage(msg)

    def handleCaptureComplete(self, image_item):
        self.updateCrossHair(*image_item.getPosUm())

    def handleExtrapolate(self, ignored):
        """
        This is called when the extrapolate action is selected from the context menu.
        """
        self.mosaic_view.extrapolate_start = coord.Point(self.mosaic_event_coord.x_um,
                                                         self.mosaic_event_coord.y_um,
                                                         "um")

    def handleExtrapolateTakeMovie(self, a_coord):
        """
        This is called on the next right click after the extrapolate action was selected.
        """
        movie_queue = []

        # Starting point.
        x_um = a_coord.x_um + (a_coord.x_um - self.mosaic_view.extrapolate_start.x_um)
        y_um = a_coord.y_um + (a_coord.y_um - self.mosaic_view.extrapolate_start.y_um)
        movie_queue.append(coord.Point(x_um, y_um, "um"))

        # Spiral.
        movie_queue += imageCapture.createSpiral(self.extrapolate_count)

        self.mosaic_view.extrapolate_start = None
        self.image_capture.takeMovies(movie_queue)
        
    @hdebug.debug
    def handleImageGridButton(self, ignored):
        """
        Handle taking a grid pattern when the 'Acquire' button is clicked.
        """
        movie_queue = []

        # Starting point.
        x_start_um = self.ui.xStartPosSpinBox.value()
        y_start_um = self.ui.yStartPosSpinBox.value()        
        movie_queue.append(coord.Point(x_start_um, y_start_um, "um"))

        # Grid.
        movie_queue += imageCapture.createGrid(self.ui.xSpinBox.value(), self.ui.ySpinBox.value())

        self.ui.imageGridButton.setText("Abort")
        self.ui.imageGridButton.setStyleSheet("QPushButton { color: red }")
        
        self.image_capture.takeMovies(movie_queue)

    def handleMouseMove(self, a_point):

        # Not sure whether I should include the offset here.
#        offset_point = coord.Point(a_point.x_um - self.current_offset.x_um,
#                                   a_point.y_um - self.current_offset.y_um,
#                                   "um")

        offset_point = coord.Point(a_point.x_um, a_point.y_um, "um")
        
        self.ui.mosaicLabel.setText("{0:.2f}, {1:.2f}".format(offset_point.x_um, offset_point.y_um))


    def handlePositionMessageForPosition(self, tcp_message, tcp_message_response):
        stage_x = float(tcp_message_response.getResponse("stage_x"))
        self.ui.posCenterSpinX.setValue(stage_x)
        
        stage_y = float(tcp_message_response.getResponse("stage_y"))
        self.ui.posCenterSpinY.setValue(stage_y)


    def handlePositionMessage(self, tcp_message, tcp_message_response):
        stage_x = float(tcp_message_response.getResponse("stage_x"))
        self.ui.xStartPosSpinBox.setValue(stage_x)
        
        stage_y = float(tcp_message_response.getResponse("stage_y"))
        self.ui.yStartPosSpinBox.setValue(stage_y)

        self.updateCrossHair(stage_x, stage_y)

    def handleRemoveLastPicture(self, ignored):
        """
        This removes the last picture that was added.
        """
        # Identify last image.
        last_id = -1
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getItemID() > last_id):
                last_id = item.getItemID()

        # Remove image.
        if (last_id >= 0):
            self.item_store.removeItem(last_id)

    def handleScaleChange(self, new_text):
        """
        This is called when the user changes the scale text.
        """
        new_scale = float(new_text)
        if (new_scale <= 0.0):
            new_scale = 1.0e-6
        self.mosaic_view.setScale(new_scale)

    def handleSequenceComplete(self):
        self.ui.imageGridButton.setText("Acquire")
        self.ui.imageGridButton.setStyleSheet("QPushButton { color: black }")        

    def handleStageMessage(self, tcp_message, tcp_message_response):
        stage_x = float(tcp_message_response.getData("stage_x"))
        self.ui.xStartPosSpinBox.setValue(stage_x)
        
        stage_y = float(tcp_message_response.getData("stage_y"))
        self.ui.yStartPosSpinBox.setValue(stage_y)

        # Update stage position cross-hair.
        self.updateCrossHair(stage_x, stage_y)
        
    @hdebug.debug        
    def handleTakeMovie(self, ignored):
        """
        Handle movies triggered from the context menu and the space bar key.
        """
        self.image_capture.takeMovies([coord.Point(self.mosaic_event_coord.x_um,
                                                   self.mosaic_event_coord.y_um,
                                                   "um")])

    def handleTakeGrid(self):
        """
        Handle taking a grid pattern.
        """
        movie_queue = []

        # Starting point.
        movie_queue.append(coord.Point(self.mosaic_event_coord.x_um,
                                        self.mosaic_event_coord.y_um,
                                        "um"))
        
        # Grid.
        movie_queue += imageCapture.createGrid(self.ui.xSpinBox.value(), self.ui.ySpinBox.value())
        
        self.image_capture.takeMovies(movie_queue)
        
    def handleTakeSpiral(self, n_pictures):
        """
        Handle taking a spiral pattern.
        """
        movie_queue = []

        # Starting point.
        movie_queue.append(coord.Point(self.mosaic_event_coord.x_um,
                                        self.mosaic_event_coord.y_um,
                                        "um"))

        # Spiral.
        movie_queue += imageCapture.createSpiral(n_pictures)
        
        self.image_capture.takeMovies(movie_queue)

    def handleTrackStage(self, state):
        if (state == QtCore.Qt.Checked):
            self.track_stage_timer.start()
            self.getStagePosition()
        else:
            self.mosaic_view.showCrossHair(False)
            
    def handleTrackStageTimer(self):
        if self.ui.trackStageCheckBox.isChecked():
            self.track_stage_timer.start()
            self.getStagePosition()

    def handleViewScaleChange(self, new_value):
        """
        This is called when the user uses the scroll wheel.
        """
        self.ui.scaleLineEdit.setText("{0:.6f}".format(new_value))

    def handleXYSpinBox(self, ignored):
        self.image_capture.setGridSize([self.ui.xSpinBox.value(),
                                        self.ui.ySpinBox.value()])


    def handleXYGridSpinBox(self, ignored):
        x = self.ui.posGridSpinX.value()
        if (x%2==0):
            self.ui.posGridSpinX.setValue(x-1)
        y = self.ui.posGridSpinY.value()
        if (y%2==0):
            self.ui.posGridSpinY.setValue(y-1)

    @hdebug.debug        
    def initializePopupMenu(self, menu_list):
        self.mosaic_view.initializePopupMenu(menu_list)

    def mosaicLoaded(self):
        self.mosaic_view.centerOn(0,0)
        
    def updateCrossHair(self, x_pos_um, y_pos_um):

        # Check if the cross-hair should be visible.
        if self.ui.trackStageCheckBox.isChecked():
            self.mosaic_view.setCrossHairPosition(x_pos_um, y_pos_um)
            self.mosaic_view.showCrossHair(True)
        else:
            self.mosaic_view.showCrossHair(False)

