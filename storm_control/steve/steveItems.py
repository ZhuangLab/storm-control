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

    def loadItem(self, mosaic_file_data):
        pass

    def saveItem(self, mosaic_file_fp):
        pass
    
    
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
        directory = os.path.dirname(mosaic_filename)
        with open(mosaic_filename) as fp:
            for line in fp:
                data = line.strip().split(",")
                data_type = data[0]
                if data_type in self.item_loaders:
                    #self.item_loaders[data_type](directory, *data[1:])
                    self.addItem(self.item_loaders[data_type](directory, *data[1:]))
                else:
                    warnings.warn("No loading function for " + data_type)

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
