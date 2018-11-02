#!/usr/bin/env python
"""
Handles:

(1) All the UI elements in the Mosaic tab except for 
    the positions list widget. 

(2) Image capture from HAL.


Hazen 10/18
"""
import contextlib
import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.steve.comm as comm
import storm_control.steve.coord as coord
import storm_control.steve.imageItem as imageItem
import storm_control.steve.mosaicView as mosaicView
import storm_control.steve.objectives as objectives
import storm_control.steve.qtdesigner.mosaic_ui as mosaicUi
import storm_control.steve.steveModule as steveModule


def createGrid(nx, ny):
    """
    Create a grid position array.
    """
    direction = 0
    positions = []
    if (nx > 1) or (ny > 1):
        half_x = int(nx/2)
        half_y = int(ny/2)
        for i in range(-half_y, half_y+1):
            for j in range(-half_x, half_x+1):
                if not ((i==0) and (j==0)):
                    if ((direction%2)==0):
                        positions.append([j,i])
                    else:
                        positions.append([-j,i])
            direction += 1
    return positions


def createSpiral(number):
    """
    Create a spiral position array.
    """
    number = number * number
    positions = []
    if (number > 1):
        # spiral outwards
        tile_x = 0.0
        tile_y = 0.0
        tile_count = 1
        spiral_count = 1
        while(tile_count < number):
            i = 0
            while (i < spiral_count) and (tile_count < number):
                if (spiral_count % 2) == 0:
                    tile_y -= 1.0
                else:
                    tile_y += 1.0
                i += 1
                tile_count += 1
                positions.append([tile_x, tile_y])
            i = 0
            while (i < spiral_count) and (tile_count < number):
                if (spiral_count % 2) == 0:
                    tile_x -= 1.0
                else:
                    tile_x += 1.0
                i += 1
                tile_count += 1
                positions.append([tile_x, tile_y])
            spiral_count += 1
    return positions


class Mosaic(steveModule.SteveModule):

    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.current_z = 0.0
        self.directory = self.parameters.get("directory")
        self.extrapolate_count = self.parameters.get("extrapolate_picture_count")
        self.filename = self.parameters.get("image_filename")
        self.fractional_overlap = self.parameters.get("fractional_overlap", 0.05)
        self.last_image = None
        self.mmt = None
        self.movie_queue = []
        self.track_stage_timer = QtCore.QTimer(self)
        self.z_inc = 0.01

        # The idea is that in the future other modules might want to
        # change how movies are taken and loaded. This will hopefully
        # make this easier.
        #
        # This class handles creating a SteveItem() from the movie.
        self.movie_loader = None

        # This class handles taking the movie.
        self.movie_taker = MosaicMovieTaker

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
        self.ui.scaleLineEdit.textEdited.connect(self.handleScaleChange)
        self.ui.trackStageCheckBox.stateChanged.connect(self.handleTrackStage)

        # Connect view signals.
        self.mosaic_view.extrapolateTakeMovie.connect(self.handleExtrapolateTakeMovie)
        self.mosaic_view.mouseMove.connect(self.handleMouseMove)
        self.mosaic_view.scaleChange.connect(self.handleViewScaleChange)

        # Standard movie loader. This handles loading movies acquired by HAL.
        self.movie_loader = imageItem.ImageLoader(objectives = self.ui.objectivesGroupBox)

        # Set loader for loading ImageItems from a mosaic file.
        self.item_store.addLoader(imageItem.ImageItem.data_type,
                                  imageItem.imageItemLoader())

        # Set loader for loading ObjectiveItems from a mosaic file.
        self.item_store.addLoader(objectives.ObjectiveItem.data_type,
                                  objectives.ObjectiveItemLoader(objective_group_box = self.ui.objectivesGroupBox))
        
    def abortIfBusy(self):
        """
        Aborts the current movie taking operation if there is one running.
        """
        if self.mmt is not None:
            self.movie_queue = []
            return True
        else:
            return False

    def addImageItem(self, image_item):
        image_item.setZValue(self.current_z)
        self.item_store.addItem(image_item)
        self.current_z += self.z_inc
        
    def getPositionsGroupBox(self):
        """
        Return the positions group box UI element for the 
        benefit of the Positions() object.
        """
        return self.ui.positionsGroupBox

    def getStagePosition(self):
        msg = comm.CommMessagePosition(finalizer_fn = self.handlePositionMessage)
        self.comm.SendMessage(msg)

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
    def handleGoToPosition(self, ignored):
        msg = comm.CommMessageStage(disconnect = True,
                                    finalizer_fn = self.handleStageMessage,
                                    stage_x = self.mosaic_event_coord.x_um - self.current_offset.x_um,
                                    stage_y = self.mosaic_event_coord.y_um - self.current_offset.y_um)
        self.halMessageSend(msg)

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
        if self.abortIfBusy():
            return

        self.movie_queue = createSpiral(self.extrapolate_count)

        x_um = a_coord.x_um + (a_coord.x_um - self.mosaic_view.extrapolate_start.x_um)
        y_um = a_coord.y_um + (a_coord.y_um - self.mosaic_view.extrapolate_start.y_um)

        self.current_center = coord.Point(x_um - self.current_offset.x_um,
                                          y_um - self.current_offset.y_um,
                                          "um")

        self.mosaic_view.extrapolate_start = None
        self.takeMovie(self.current_center)        
        
    @hdebug.debug
    def handleImageGridButton(self, ignored):
        """
        Handle taking a grid pattern when the 'Acquire' button is clicked.
        """
        if self.abortIfBusy():
            return

        self.movie_queue = createGrid(self.ui.xSpinBox.value(), self.ui.ySpinBox.value())
        x_start_um = self.ui.xStartPosSpinBox.value()
        y_start_um = self.ui.yStartPosSpinBox.value()        
        self.current_center = coord.Point(x_start_um - self.current_offset.x_um,
                                          y_start_um - self.current_offset.y_um,
                                          "um")
        self.takeMovie(self.current_center)

        self.ui.imageGridButton.setText("Abort")
        self.ui.imageGridButton.setStyleSheet("QPushButton { color: red }")

    def handleMouseMove(self, a_point):
        offset_point = coord.Point(a_point.x_um - self.current_offset.x_um,
                                   a_point.y_um - self.current_offset.y_um,
                                   "um")
        self.ui.mosaicLabel.setText("{0:.2f}, {1:.2f}".format(offset_point.x_um, offset_point.y_um))

    @hdebug.debug
    def handleMovieTaken(self):
        """
        Load the (basic) movie and add it to the item store and scene.
        """
        image_item = self.movie_loader.loadMovie(self.mmt.getMovieName())
        self.addImageItem(image_item)
        self.updateCrossHair(*image_item.getPosUm())

        objective = image_item.getObjectiveName()
        self.ui.objectivesGroupBox.changeObjective(objective)
        [obj_um_per_pix, x_offset_um, y_offset_um] = self.ui.objectivesGroupBox.getData(objective)
        self.current_offset = coord.Point(x_offset_um, y_offset_um, "um")
        
        self.last_image = image_item
        self.nextMovie()

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
        if self.abortIfBusy():
            return

        movie_pos = coord.Point(self.mosaic_event_coord.x_um - self.current_offset.x_um,
                                self.mosaic_event_coord.y_um - self.current_offset.y_um,
                                "um")
        self.takeMovie(movie_pos)

    def handleTakeGrid(self):
        """
        Handle taking a grid pattern.
        """
        if self.abortIfBusy():
            return

        self.movie_queue = createGrid(self.ui.xSpinBox.value(), self.ui.ySpinBox.value())
        self.current_center = coord.Point(self.mosaic_event_coord.x_um - self.current_offset.x_um,
                                          self.mosaic_event_coord.y_um - self.current_offset.y_um,
                                          "um")
        self.takeMovie(self.current_center)
        
    def handleTakeSpiral(self, n_pictures):
        """
        Handle taking a spiral pattern.
        """
        if self.abortIfBusy():
            return

        self.movie_queue = createSpiral(n_pictures)
        self.current_center = coord.Point(self.mosaic_event_coord.x_um - self.current_offset.x_um,
                                          self.mosaic_event_coord.y_um - self.current_offset.y_um,
                                          "um")
        self.takeMovie(self.current_center)

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

    @hdebug.debug        
    def initializePopupMenu(self, menu_list):
        self.mosaic_view.initializePopupMenu(menu_list)

    def loadMovies(self, filename_list, frame_number = 0):
        for filename in filename_list:
            image_item = self.movie_loader.loadMovie(os.path.splitext(filename)[0], frame_number)
            self.addImageItem(image_item)
        
    def mosaicLoaded(self):
        """
        Update current z value based on highest image z value.
        """
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getZValue() > self.current_z):
                self.current_z = item.getZValue() + self.z_inc
        
    @hdebug.debug
    def nextMovie(self):
        """
        Take the next movie, or disconnect if there are no more movies to take.
        """
        if (len(self.movie_queue) > 0):

            # Figure out where to take the movie.
            [dx, dy] = self.movie_queue[0]
            [im_x_um, im_y_um] = self.last_image.getSizeUm()
            
            next_x_um = self.current_center.x_um + (1.0 - self.fractional_overlap)*im_x_um*dx
            next_y_um = self.current_center.y_um + (1.0 - self.fractional_overlap)*im_y_um*dy
            movie_pos = coord.Point(next_x_um, next_y_um, "um")

            # Take the movie.
            self.takeMovie(movie_pos)

            # Remove from the queue.
            self.movie_queue = self.movie_queue[1:]
        else:

            # Might not be necessary, but in that case it is basically a NOP.
            self.ui.imageGridButton.setText("Acquire")
            self.ui.imageGridButton.setStyleSheet("QPushButton { color: black }")
        
            self.comm.stopCommunication()
            self.mmt = None

    @hdebug.debug
    def setDirectory(self, directory):
        self.directory = directory

    @hdebug.debug
    def takeMovie(self, movie_pos):
        self.mmt = self.movie_taker(comm_instance = self.comm,
                                    disconnect = False,
                                    directory = self.directory,
                                    filename = self.filename,
                                    finalizer_fn = self.handleMovieTaken,
                                    pos = movie_pos)
        self.mmt.start()

    def updateCrossHair(self, x_pos_um, y_pos_um):

        # Check if the cross-hair should be visible.
        if self.ui.trackStageCheckBox.isChecked():
            self.mosaic_view.setCrossHairPosition(x_pos_um, y_pos_um)
            self.mosaic_view.showCrossHair(True)
        else:
            self.mosaic_view.showCrossHair(False)


class MosaicMovieTaker(object):
    """
    Handles moving the stage and acquiring a (basic) movie.
    """
    def __init__(self,
                 comm_instance = None,
                 disconnect = None,
                 directory = None,
                 filename = None,
                 finalizer_fn = None,
                 pos = None,
                 **kwds):
        super().__init__(**kwds)
        self.comm = comm_instance
        self.finalizer_fn = finalizer_fn
        self.movie_message = comm.CommMessageMovie(disconnect = disconnect,
                                                   finalizer_fn = self.handleMovieMessage,
                                                   directory = directory,
                                                   filename = filename)
        self.movie_name = os.path.join(directory, filename)
        self.stage_message = comm.CommMessageStage(disconnect = False,
                                                   finalizer_fn = self.handleStageMessage,
                                                   stage_x = pos.x_um,
                                                   stage_y = pos.y_um)

    def getMovieName(self):
        return self.movie_name

    def handleMovieMessage(self, tcp_message, tcp_message_response):
        self.finalizer_fn()
        
    def handleStageMessage(self, tcp_message, tcp_message_response):
        """
        Take the movie when the stage message completes.
        """
        self.comm.sendMessage(self.movie_message)

    def removeOldMovie(self):
        """
        Remove old movie.
        """
        with contextlib.suppress(FileNotFoundError):
            parameters = params.parameters(self.movie_name + ".xml", recurse = True)
            os.remove(self.movie_name + parameters.get("film.filetype"))
            os.remove(self.movie_name + ".xml")
    
    def start(self):
        self.removeOldMovie()
        self.comm.sendMessage(self.stage_message)
