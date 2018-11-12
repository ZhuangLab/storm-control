#!/usr/bin/env python
"""
The base class for all of the modules in Steve.

Hazen 10/18
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.hdebug as hdebug


class SteveModule(QtWidgets.QWidget):

    @hdebug.debug
    def __init__(self, comm = None, item_store = None, parameters = None, **kwds):
        super().__init__(**kwds)

        self.comm = comm
        self.item_store = item_store
        self.mosaic_event_coord = None
        self.parameters = parameters
    
#    @hdebug.debug
#    def halMessageSend(self, message):
#        """
#        Sends a message to HAL message via the comm object.
#        """
#        self.comm.sendMessage(message)

    def currentTabChanged(self, tab_index):
        pass

    def mosaicLoaded(self):
        """
        Called once a mosaic has been loaded.
        """
        pass

    def setMosaicEventCoord(self, a_coord):
        """
        a_coord is a coord.Point() object.
        """
        self.mosaic_event_coord = a_coord
