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
from PyQt5 import QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.steve.comm as comm
import storm_control.steve.coord as coord
import storm_control.steve.imageItem as imageItem
import storm_control.steve.mosaicView as mosaicView
import storm_control.steve.objectives as objectives
import storm_control.steve.qtdesigner.mosaic_ui as mosaicUi
import storm_control.steve.steveModule as steveModule


class Mosaic(steveModule.SteveModule):

    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.current_z = 0.0
        self.directory = self.parameters.get("directory")
        self.filename = self.parameters.get("image_filename")
        self.last_image = None
        self.mmt = None
        self.z_inc = 0.01

        # The idea is that in the future other modules might want to
        # change how movies are taken and loaded. This will hopefully
        # make this easier.
        #
        # This class handles creating a SteveItem() from the movie.
        self.movie_loader = None

        # This class handles taking the movie.
        self.movie_taker = MosaicMovieTaker
        
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
        self.ui.scaleLineEdit.textEdited.connect(self.handleScaleChange)

        # Connect view signals.
        self.mosaic_view.mouseMove.connect(self.handleMouseMove)
        self.mosaic_view.scaleChange.connect(self.handleViewScaleChange)

        # Standard movie loader. This handles loading movies acquired by HAL.
        self.movie_loader = imageItem.ImageLoader(objectives = self.ui.objectivesGroupBox)

        # Set mosaic file loader. This handles loading ImageItems from a mosaic file.
        self.item_store.addLoader(imageItem.ImageItem.data_type, imageItem.imageItemLoader)
        
        # Send message to request mosaic settings.
        msg = comm.CommMessageMosaicSettings(finalizer_fn = self.handleMosaicSettingsMessage)
        self.halMessageSend(msg)
        
    @hdebug.debug
    def getObjective(self):
        msg = comm.CommMessageObjective(finalizer_fn = self.handleGetObjectiveMessage)
        self.halMessageSend(msg)

    def getPositionsGroupBox(self):
        """
        Return the positions group box UI element for the 
        benefit of the Positions() object.
        """
        return self.ui.positionsGroupBox
        
    @hdebug.debug
    def handleGetObjectiveMessage(self, tcp_message, tcp_message_response):
        objective = tcp_message_response.getResponse("objective")
        self.ui.objectivesGroupBox.changeObjective(objective)
        [obj_um_per_pix, x_offset, y_offset] = self.ui.objectivesGroupBox.getData(objective)
        self.current_offset = coord.Point(x_offset, y_offset, "um")

    @hdebug.debug
    def handleMosaicSettingsMessage(self, tcp_message, tcp_message_response):
        i = 1
        while tcp_message_response.getResponse("obj" + str(i)) is not None:
            data = tcp_message_response.getResponse("obj" + str(i)).split(",")
            self.ui.objectivesGroupBox.addObjective(data)
            i += 1

        # Send message to get current objective.
        if (i > 1):
            self.getObjective()

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
        steve_item = self.movie_loader.loadMovie(self.mt.getMovieName())
        steve_item.setZValue(self.current_z)
        self.current_z += self.z_inc
        self.last_image = steve_item
        self.item_store.addItem(steve_item)
        self.nextMovie()

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

    @hdebug.debug        
    def handleTakeMovie(self, ignored):
        """
        Handle movies triggered from the context menu.
        """
        movie_pos = coord.Point(self.mosaic_event_coord.x_um - self.current_offset.x_um,
                                self.mosaic_event_coord.y_um - self.current_offset.y_um,
                                "um")
        self.takeMovie(movie_pos)
        
    def handleViewScaleChange(self, new_value):
        """
        This is called when the user uses the scroll wheel.
        """
        self.ui.scaleLineEdit.setText("{0:.6f}".format(new_value))

    @hdebug.debug        
    def initializePopupMenu(self, menu_list):
        self.mosaic_view.initializePopupMenu(menu_list)

    def mosaicLoaded(self):
        """
        Update current z value based on highest image z value.
        """
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getZValue() > self.current_z):
                self.current_z = item.getZValue() + self.z_inc
        
    @hdebug.debug
    def nextMovie(self):
        pass
    
    @hdebug.debug
    def setDirectory(self, directory):
        self.directory = directory

    @hdebug.debug
    def takeMovie(self, movie_pos):
        self.mt = self.movie_taker(comm_instance = self.comm,
                                   disconnect = True,
                                   directory = self.directory,
                                   filename = self.filename,
                                   finalizer_fn = self.handleMovieTaken,
                                   pos = movie_pos)
        self.mt.start()


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
        print("hsm")
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
        print("start")
        self.removeOldMovie()
        self.comm.sendMessage(self.stage_message)
