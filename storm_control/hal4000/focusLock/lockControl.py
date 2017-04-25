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

    def handleJump(self, delta_z):
        self.lock_mode.handleJump(delta_z)

    def handleLockStarted(self, on):
        """
        Called when the user clicks the lock button on the GUI.
        """
        if on:
            self.startLock()
        else:
            self.stopLock()
        
    def handleLockTarget(self, new_target):
        self.lock_mode.setLockTarget(new_target)

    def handleModeChanged(self, new_mode):
        """
        new_mode is a focusLock.LockMode object (listed in the mode combo box).
        """
        print(">hmc")
        if self.lock_mode is not None and self.lock_mode.amLocked():
            self.stopLock()
            
        self.lock_mode = new_mode
        self.lock_mode.initialize()
        self.lock_mode.setZStageFunctionality(self.z_stage_functionality)
        self.z_stage_functionality.recenter()
                
    def handleQPDUpdate(self, qpd_dict):
        """
        Basically this is where all the action happens. The current
        mode tells us to move (or not) based on the current QPD signal, 
        then we poll the QPD again.
        """
        self.lock_mode.handleQPDUpdate(qpd_dict)
        self.qpd_functionality.getOffset()

    def isGoodLock(self):
        """
        This is whether or not the focus lock mode has a 'good' 
        lock, not just whether or not it is on.
        """
        return self.lock_mode.isGoodLock()
        
    def newFrame(self, frame):
        self.lock_mode.newFrame(frame)
        
    def setFunctionality(self, name, functionality):
        if (name == "qpd"):
            self.qpd_functionality = functionality
            self.qpd_functionality.qpdUpdate.connect(self.handleQPDUpdate)
        elif (name == "z_stage"):
            self.z_stage_functionality = functionality

    def start(self):
        if (self.qpd_functionality is not None) and (self.z_stage_functionality is not None):
            # Start polling the QPD.
            self.qpd_functionality.getOffset()
        
    def startFilm(self):
        self.lock_mode.startFilm()

    def startLock(self):
        self.lock_mode.startLock()

    def startLockBehavior(self, sub_mode_name, sub_mode_params):
        """
        Not sure if this is the best name, but all the modes have a 'normal'
        functionality as well as the possibility to perform things like a
        scan for sum signal. Which of these is active can be specified by 
        calling this function.
        """
        self.lock_mode.startLock(sub_mode_name, sub_mode_params)

    def stopLock(self):
        self.lock_mode.stopLock()
        
#    def stopFilm(self):
#        self.lock_mode.stopFilm()
