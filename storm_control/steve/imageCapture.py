#!/usr/bin/env python
"""
This module handles communicating with HAL to capture images. The
captured images are directly added to the item store.

Hazen 10/18
"""
import contextlib
import os
import warnings
from PyQt5 import QtCore, QtGui

import storm_control.sc_library.parameters as params

import storm_control.steve.comm as comm
import storm_control.steve.coord as coord
import storm_control.steve.imageItem as imageItem


def createGrid(nx, ny, include_center = False):
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
                if ((i==0) and (j==0)) and not include_center:
                    continue
                else:
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


class MovieCapture(QtCore.QObject):
    """
    The interface that all the modules use to capture images using HAL. The idea is
    that there is only one of these. Clients change how this handles behaves when
    taking and loading images by calling setMovieLoaderTaker().

    This handles dealing with the offset for the current objective. Clients should not
    include this offset in the movie positions that they request.
    """
    captureComplete = QtCore.pyqtSignal(object)
    sequenceComplete = QtCore.pyqtSignal()
    
    def __init__(self, comm = None, item_store = None, parameters = None, **kwds):
        super().__init__(**kwds)

        self.comm = comm
        self.current_center = coord.Point(0.0, 0.0, "um")
        self.current_z = 0.0
        self.directory = parameters.get("directory")
        self.extrapolate_count = parameters.get("extrapolate_picture_count")
        self.filename = parameters.get("image_filename")
        self.fractional_overlap = parameters.get("fractional_overlap", 0.05)
        self.grid_size = []
        self.item_store = item_store
        self.last_image = None
        self.movie_queue = []
        self.objectives = None
        self.smc = None
        self.z_inc = 0.01

        # The idea is that in the future other modules might want to
        # change how movies are taken and loaded. This will hopefully
        # make this easier.
        #
        # This class handles creating a SteveItem() from the movie.
        self.movie_loader = None

        # This class handles taking the movie.
        self.movie_taker = None
        
    def abortIfBusy(self):
        """
        Aborts the current movie taking operation if there is one running.
        """
        if self.smc is not None:
            self.movie_queue = []
            return True
        else:
            return False

    def addImageItem(self, image_item):
        image_item.setZValue(self.current_z)
        self.item_store.addItem(image_item)
        self.current_z += self.z_inc

    def getGridSize(self):
        """
        Return the current grid size.
        """
        # This is set by the mosaic module, but other modules need to
        # know the values to take the proper size grid.
        return self.grid_size

    def handleMovieTaken(self):
        """
        Load the (basic) movie and add it to the item store and scene.
        """
        image_item = self.loadMovie(self.smc.getMovieName())
        self.captureComplete.emit(image_item)

        # Update current objective.
        objective = image_item.getObjectiveName()
        self.objectives.changeObjective(objective)
        
        self.last_image = image_item
        self.nextMovie()

    def loadMovie(self, movie_name, frame_number = 0):
        """
        Load a singe movie, add it to the scene and also return it as a ImageItem.
        """
        image_item = self.movie_loader.loadMovie(movie_name, frame_number)
        self.addImageItem(image_item)
        return image_item

    def loadMovies(self, movie_names, frame_number):
        """
        Load multiple movies.
        """
        for movie_name in movie_names:
            self.loadMovie(os.path.splitext(movie_name)[0], frame_number)

    def postInitialization(self, objectives = None):
        """
        This is called after the object is created to provide some additional modules
        that this object needs to work. These modules are not available when the 
        object is initially created.
        """
        self.objectives = objectives

    def mosaicLoaded(self):
        """
        Update current z value based on highest image z value.
        """
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getZValue() > self.current_z):
                self.current_z = item.getZValue() + self.z_inc
        
    def nextMovie(self):
        """
        Take the next movie, or disconnect if there are no more movies to take.
        """
        if (len(self.movie_queue) > 0):

            # Figure out where to take the movie.
            elt = self.movie_queue[0]
            if isinstance(elt, list):
                [dx, dy] = elt
                [im_x_um, im_y_um] = self.last_image.getSizeUm()
            
                next_x_um = self.current_center.x_um + (1.0 - self.fractional_overlap)*im_x_um*dx
                next_y_um = self.current_center.y_um + (1.0 - self.fractional_overlap)*im_y_um*dy
                movie_pos = coord.Point(next_x_um, next_y_um, "um")

            else:
                self.current_center = elt
                movie_pos = elt

            # Remove from the queue.
            self.movie_queue = self.movie_queue[1:]
            
            # Take the movie, checking for failure to communicate with HAL.
            if not self.takeSingleMovie(movie_pos):
                self.movie_queue = []
                self.smc = None
                self.sequenceComplete.emit()

        else:        
            self.comm.stopCommunication()
            self.smc = None

            self.sequenceComplete.emit()

    def setDirectory(self, directory):
        self.directory = directory
        
    def setGridSize(self, grid_size):
        self.grid_size = grid_size

    def setMovieLoaderTaker(self, movie_loader = None, movie_taker = None):
        if self.smc is None:
            if movie_loader is not None:
                self.movie_loader = movie_loader
            if movie_taker is not None:
                self.movie_taker = movie_taker
        else:
            QtGui.QMessageBox.information(self,
                                          "Movie taking/loading cannot be changed during acquisition",
                                          "")

    def takeMovies(self, movie_queue):
        """
        movie_queue is a list of coord.Point() objects or relative offset in units
        of the width of the current picture, [1,2] for example.
        """
        if not self.abortIfBusy():
            self.movie_queue = movie_queue
            self.nextMovie()
        
    def takeSingleMovie(self, movie_pos):
        """
        This takes a single movie as the specified position corrected 
        for the current offset.

        Clients should not use this method, they should always takeMovies().
        """
        current_offset = self.objectives.getCurrentOffset()

        # Bail out if we don't have any objectives information. This
        # probably means HAL is not running or we can't talk to it.
        if current_offset is None:
            return
        
        pos = coord.Point(movie_pos.x_um - current_offset.x_um,
                          movie_pos.y_um - current_offset.y_um,
                          "um")
        
        self.smc = self.movie_taker(comm_instance = self.comm,
                                    disconnect = False,
                                    directory = self.directory,
                                    filename = self.filename,
                                    finalizer_fn = self.handleMovieTaken,
                                    pos = pos)
        return self.smc.start()


class SingleMovieCapture(object):
    """
    Handles communicating with HAL to move the stage and acquire a single movie.
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
            os.remove(self.movie_name + imageItem.getCameraExtension(parameters) + parameters.get("film.filetype"))

        with contextlib.suppress(FileNotFoundError):            
            os.remove(self.movie_name + ".xml")
            print("Removing", self.movie_name + ".xml")
    
    def start(self):
        self.removeOldMovie()
        return self.comm.sendMessage(self.stage_message)
