#!/usr/bin/env python
"""
The handles all the UI elements in the Mosaic tab.

Hazen 10/18
"""
import contextlib
import os
from PyQt5 import QtWidgets

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

        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_offset = coord.Point(0.0, 0.0, "um")
        self.current_z = 0.0
        self.directory = self.parameters.get("directory")
        self.filename = self.parameters.get("image_filename")
        self.last_image = None
        self.mmt = None

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

        # Connect view signals.
        self.mosaic_view.changeCenter.connect(self.handleChangeCenter)
        self.mosaic_view.mouseMove.connect(self.handleMouseMove)

        # Standard movie loader.
        self.movie_loader = imageItem.ImageLoader(objectives = self.ui.objectiveGroupBox)
        
        # Send message to request mosaic settings.
        msg = comm.CommMessageMosaicSettings(finalizer_fn = self.handleMosaicSettingsMessage)
        self.comm.sendMessage(msg)

    @hdebug.debug
    def getObjective(self):
        msg = comm.CommMessageObjective(finalizer_fn = self.handleGetObjectiveMessage)
        self.comm.sendMessage(msg)

    def handleChangeCenter(self, a_point):
        self.current_center = a_point
        
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
    def handleTakeMovie(self):
        """
        Take a single movie at the current position.
        """
        movie_pos = coord.Point(self.current_center.x_um - self.current_offset.x_um,
                                self.current_center.y_um - self.current_offset.y_um,
                                "um")
        self.takeMovie(movie_pos)

    @hdebug.debug
    def handleMovieTaken(self):
        """
        Load the (basic) movie and add it to the item store and scene.
        """
        steve_item = self.movie_loader.loadMovie(self.mt.getMovieName())
        self.last_image = steve_item
        self.item_store.addItem(steve_item)
        self.nextMovie()

    @hdebug.debug        
    def initializePopupMenu(self, menu_list):
        self.mosaic_view.initializePopupMenu(menu_list)

    @hdebug.debug
    def nextMovie(self):
        pass
    
    @hdebug.debug
    def setDirectory(self, directory):
        self.directory = directory

    @hdebug.debug
    def takeMovie(self, movie_pos):
        self.mt = self.movie_taker(comm = self.comm,
                                   disconnect = True,
                                   directory = self.directory,
                                   filename = self.filename,
                                   finalizer = self.handleMovieTaken,
                                   pos = movie_pos)
        self.mt.start()        


class MosaicMovieTaker(object):
    """
    Handles moving the stage and acquiring a (basic) movie.
    """
    def __init__(self,
                 comm = None,
                 disconnect = None,
                 directory = None,
                 filename = None,
                 finalizer = None,
                 pos = None,
                 **kwds):
        super().__init__(**kwds)
        self.comm = comm
        self.finalizer = finalizer
        self.movie_message = comm.CommMessageMovie(disconnect = disconnect,
                                                   finalizer = self.handleMovieMessage,
                                                   directory = directory,
                                                   name = filename)
        self.movie_name = os.path.join(self.directory, self.filename)
        self.stage_message = comm.CommMessageStage(disconnect = False,
                                                   finalizer = self.handleStageMessage,
                                                   stage_x = pos.x_um,
                                                   stage_y = pos.y_um)

    def getMovieName(self):
        return self.movie_name

    def handleMovieMessage(self, tcp_message, tcp_message_response):
        self.finalizer()
        
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
            parameters = params.parameters(self.movie_name + ".xml")
            os.remove(self.movie_name + ".xml")
            os.remove(self.movie_name + parameters.get("film.filetype"))
    
    def start(self):
        self.removeOldMovie()
        self.comm.sendMessage(self.stage_message)
