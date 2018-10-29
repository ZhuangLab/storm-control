#!/usr/bin/env python
"""
The QGraphicsScene that is the backend of Steve and the base
class for the items that Steve will work with.

Hazen 10/18
"""
import os
import warnings

from PyQt5 import QtCore, QtGui, QtWidgets


item_id = 0

class SteveItem(object):
    """
    Base class for items that Steve will work with such as images,
    positions and sections.
    """

    # This is type name to use when saving/loading mosaic files.
    data_type = "none"
    
    def __init__(self, **kwds):
        super().__init__(**kwds)

        global item_id
        self.item_id = item_id
        item_id += 1

        self.graphics_item = None

    def getGraphicsItem(self):
        return self.graphics_item

    def getItemID(self):
        return self.item_id

    def saveItem(self, directory, name_no_extension):
        """
        Sub-classes should override to specify how to save. At
        minimum this method must return a single line of comma
        separated text describing the object."
        """
        warnings.warn("saveItem() is not implemented for '" + str(self.data_type) + "'")
    
    
class SteveItemsStore(object):
    """
    Stores all the items that Steve uses in mosaics, etc..
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.item_loaders = {}
        self.items = {}
        self.q_scene = QtWidgets.QGraphicsScene()

    def addItem(self, item):
        assert not (item.getItemID() in self.items)
        self.items[item.getItemID()] = item
        gi = item.getGraphicsItem()
        if gi is not None:
            self.q_scene.addItem(gi)

    def addLoader(self, loader_name, loader_fn):
        self.item_loaders[loader_name] = loader_fn

    def getScene(self):
        return self.q_scene

    def itemIterator(self, item_type = None):
        for elt in self.items.values():
            if item_type is None:
                yield elt
            elif isinstance(elt, item_type):
                yield elt
            else:
                continue

    def loadMosaic(self, mosaic_filename):
        """
        Handles loading mosaic files into Steve. The modules that work with
        the different types of SteveItems specify the function to use in
        order to properly load a particular type of SteveItem.
        """
        # Figure out how many lines for a progress bar.
        line_count = 0
        with open(mosaic_filename) as fp:
            for line in fp:
                line_count += 1

        progress_bar = QtWidgets.QProgressDialog("Loading Files...",
                                                 "Abort Load",
                                                 0,
                                                 line_count)
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)
        
        # Load mosaic.
        directory = os.path.dirname(mosaic_filename)
        with open(mosaic_filename) as fp:
            for i, line in enumerate(fp):
                progress_bar.setValue(i)
                if progress_bar.wasCanceled():
                    return False
                
                data = line.strip().split(",")
                data_type = data[0]
                if data_type in self.item_loaders:
                    #self.item_loaders[data_type](directory, *data[1:])
                    self.addItem(self.item_loaders[data_type](directory, *data[1:]))
                else:
                    warnings.warn("No loading function for " + data_type)

        return True

    def removeItem(self, item_id):
        gi = self.items[item_id].getGraphicsItem()
        if gi is not None:
            self.q_scene.removeItem(gi)
        self.items.pop(item_id)

    def removeItemType(self, item_type):
        new_dict = {}
        for elt in self.items.values():
            if not isinstance(elt, item_type):
                new_dict[elt.getItemID()] = elt
            else:
                gi = elt.getGraphicsItem()
                if gi is not None:
                    self.q_scene.removeItem(gi)
        self.items = new_dict

    def saveMosaic(self, mosaic_filename):
        """
        Save the current SteveItems in mosaic file.
        """
        progress_bar = QtWidgets.QProgressDialog("Saving Files...",
                                                 "Abort Save",
                                                 0,
                                                 len(self.items))
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)
        
        directory = os.path.dirname(mosaic_filename)
        name_no_extension = os.path.splitext(os.path.basename(mosaic_filename))[0]

        with open(mosaic_filename, "w") as fp:
            for i, elt in enumerate(self.itemIterator()):
                progress_bar.setValue(i)
                if progress_bar.wasCanceled():
                    break
                    
                line = elt.saveItem(directory, name_no_extension)
                if line is not None:
                    fp.write(elt.data_type + "," + line + "\r\n")

        progress_bar.close()
