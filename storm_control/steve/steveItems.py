#!/usr/bin/env python
"""
The QGraphicsScene that is the backend of Steve and the base
class for the items that Steve will work with.

Hazen 10/18
"""
from PyQt5 import QtCore, QtGui, QtWidgets


item_id = 0

class SteveItem(object):
    """
    Base class for items that Steve will work with such as images,
    positions and sections.
    """    
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

        self.items = {}
        self.q_scene = QtWidgets.QGraphicsScene()

    def addItem(self, item):
        assert not (item.getItemID() in self.items)
        self.items[item.getItemID()] = item
        gi = item.getGraphicsItem()
        if gi is not None:
            self.q_scene.addItem(gi)

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
