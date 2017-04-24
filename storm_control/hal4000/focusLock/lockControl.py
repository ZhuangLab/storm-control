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
        self.lock_mode = None
        self.qpd_functionality = None
        self.z_stage_functionality = None

    def amLocked(self):
        """
        This is whether or not the focus lock mode has a 'good' 
        lock, not just whether or not it is on.
        """
        return self.lock_mode.amLocked()
        
    def handleQPDUpdate(self, qpd_dict):
        """
        Basically this is where all the action happens. The current
        mode tells us to move (or not) based on the current QPD signal, 
        then we poll the QPD again.
        """
        self.lock_mode.handleQPDUpdate(qpd_dict)
        self.qpd_functionality.getOffset()

    def newFrame(self, frame):
        self.lock_mode.newFrame(frame)
        
    def setFunctionality(self, name, functionality):
        if (name == "qpd"):
            self.qpd_functionality = functionality
            self.qpd_functionality.qpdUpdate.connect(self.handleQPDUpdate)
        elif (name == "z_stage"):
            self.z_stage_functionality = functionality

        if (self.qpd_functionality is not None) and (self.z_stage_functionality is not None):
            # Start polling the QPD.
            self.qpd_functionality.getOffset()

    def setLockMode(self, new_mode):
        self.lock_mode = new_mode
        self.lock_mode.setZStageFunctionality(self.z_stage_functionality)
        
    def startFilm(self):
        self.lock_mode.startFilm()

    def stopFilm(self):
        self.lock_mode.stopFilm()
