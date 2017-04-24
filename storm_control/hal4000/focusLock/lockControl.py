#!/usr/bin/env python
"""
This class handles focus lock control, i.e. updating the
position if the focus lock is locked, etc.

Hazen 04/17
"""

from PyQt5 import QtCore


class LockControl(QtCore.QObject):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.qpd_functionality = None
        self.z_stage_functionality = None

    def handleQPDUpdate(self, qpd_dict):
        """
        Basically this is where all the action happens. We do something
        based on the current QPD signal, then poll the QPD again.
        """
        self.qpd_functionality.getOffset()
        
    def setFunctionality(self, name, functionality):
        if (name == "qpd"):
            self.qpd_functionality = functionality
            self.qpd_functionality.qpdUpdate.connect(self.handleQPDUpdate)

            # Start polling the QPD.
            self.qpd_functionality.getOffset()

        elif (name == "z_stage"):
            self.z_stage_functionality = functionality
            
