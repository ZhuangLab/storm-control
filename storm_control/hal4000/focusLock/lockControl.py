#!/usr/bin/env python
"""
This class handles focus lock control, i.e. updating the
position if the focus lock is locked, etc.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage


class LockControl(QtCore.QObject):
    controlMessage = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.current_state = None
        self.lock_mode = None
        self.offset_fp = None
        self.qpd_functionality = None
        self.timing_functionality = None
        self.working = False
        self.z_stage_functionality = None

        # Qt timer for checking focus lock
        self.check_focus_timer = QtCore.QTimer()
        self.check_focus_timer.setSingleShot(True)
        self.check_focus_timer.timeout.connect(self.handleCheckFocusLock)
        
    def getLockModeName(self):
        return self.lock_mode.getName()
    
    def getLockTarget(self):
        return self.lock_mode.getLockTarget()

    def getQPDSumSignal(self):
        return self.lock_mode.getQPDState()["sum"]

    def handleCheckFocusLock(self):
        """
        This handles the 'Check Focus Lock' TCP message.
        """

        # Return if we have a good lock.
        if self.isGoodLock():
            self.handleDone(True)

        else:
            self.current_state["num_checks"] -= 1

            # Start a scan if we still don't have a good lock.
            if (self.current_state["num_checks"] == 0):
                tcp_message = self.current_state["tcp_message"]
            
                # Start (find offset) scan mode.
                if tcp_message.getData("focus_scan"):
                    slb_dict = {"scan_range" : tcp_message.getData("scan_range")}
                    if tcp_message.getData("z_center") is not None:
                        slb_dict["z_center"] = tcp_message.getData("z_center")
                    self.startLockBehavior("scan", slb_dict)

                # Otherwise just return that we were not successful.
                else:
                    self.handleDone(False)

            # Wait 100ms and try again.
            #
            # FIXME: It would be better if this waited a certain number of QPD
            #        updates instead of a fixed length of time.
            #
            else:
                self.check_focus_timer.start(100)

    def handleDone(self, success):
        """
        Called by the lock mode when a behavior finishes.

        Note: self.current_state will only not be None if we are handling 
              a HAL TCP message.
        """
        if self.current_state is not None:

            # Add the TCP message response.
            tcp_message = self.current_state["tcp_message"]
            
            if tcp_message.isType("Check Focus Lock"):
                tcp_message.addResponse("focus_status", success)

            elif tcp_message.isType("Find Sum"):
                tcp_message.addResponse("focus_status", success)
                if success:
                    tcp_message.addResponse("found_sum", self.lock_mode.getFindSumMaxSum())
                
            else:
                raise Exception("No response handling for " + tcp_message.getType())

            # Relock if we were locked.
            if self.current_state["locked"]:
                self.startLock(lock_target = self.current_state["lock_target"])

            # This lets HAL know we have handled this message.
            self.current_state["message"].decRefCount()

            self.current_state = None

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

        Note: The only way to activate the 'locked' behavior is with the GUI.
              When you change lock modes the GUI will turn off the 'locked'
              behavior.
        """
        if self.lock_mode is not None:
            self.lock_mode.done.disconnect(self.handleDone)

        self.lock_mode = new_mode

        # FIXME: We only need to do this once, maybe not that big a deal.
        self.lock_mode.setZStageFunctionality(self.z_stage_functionality)
        
        self.lock_mode.done.connect(self.handleDone)
        self.z_stage_functionality.recenter()

    def handleNewFrame(self, frame):
        if self.offset_fp is not None:
            frame_number = frame.frame_number + 1
            pos_dict = self.lock_mode.getQPDState()
            offset = pos_dict["offset"]
            power = pos_dict["sum"]
            stage_z = self.z_stage_functionality.getCurrentPosition()
            self.offset_fp.write("{0:d} {1:.6f} {2:.6f} {3:.6f}\n".format(frame_number,
                                                                          offset,
                                                                          power,
                                                                          stage_z))

        self.lock_mode.handleNewFrame(frame)

    def handleQPDUpdate(self, qpd_dict):
        """
        Basically this is where all the action happens. The current
        mode tells us to move (or not) based on the current QPD signal, 
        then we poll the QPD again by calling the getOffset() method.
        """
        # Even if the current QPD reading is bad the mode needs to know, so
        # just pass the QPD reading through here.
        #
        # Reasons:
        #
        # 1. If the QPD is always bad then the mode will have self.qpd_state
        #    as 'None' and this will be a problem when we query for state
        #    at the end of a film.
        #
        # 2. If the QPD reading goes bad the mode will keep a stale value
        #    of the QPD state.
        #
        self.lock_mode.handleQPDUpdate(qpd_dict)

        # Poll QPD again.
        self.qpd_functionality.getOffset()

    def handleTCPMessage(self, message):
        """
        Handles TCP messages from tcpControl.TCPControl.
        """
        if not self.working:
            return False

        if not self.lock_mode.canHandleTCPMessages():
            return False
        
        tcp_message = message.getData()["tcp message"]
        if tcp_message.isType("Check Focus Lock"):
            if tcp_message.isTest():
                tcp_message.addResponse("duration", 2)
                
            else:
                # Record current state.
                assert (self.current_state == None)
                self.current_state = {"locked" : self.lock_mode.amLocked(),
                                      "lock_target" : self.lock_mode.getLockTarget(),
                                      "num_checks" : tcp_message.getData("num_focus_checks") + 1,
                                      "message" : message,
                                      "tcp_message" : tcp_message}

                # Start checking the focus lock.
                self.handleCheckFocusLock()

                # Increment the message reference count so that HAL
                # knows that it has not been fully processed.
                message.incRefCount()

            return True

        elif tcp_message.isType("Find Sum"):
            if tcp_message.isTest():
                tcp_message.addResponse("duration", 10)
                
            else:

                # Check if we already have enough sum signal.
                if (self.getQPDSumSignal() > tcp_message.getData("min_sum")):
                    tcp_message.addResponse("focus_status", True)
                    tcp_message.addResponse("found_sum", self.getQPDSumSignal())

                # If not, start scanning.
                else:
                     
                    # Record current state.
                    assert (self.current_state == None)
                    self.current_state = {"locked" : self.lock_mode.amLocked(),
                                          "lock_target" : self.lock_mode.getLockTarget(),
                                          "message" : message,
                                          "tcp_message" : tcp_message}
                
                    # Start find sum mode.
                    self.startLockBehavior("find_sum",
                                           {"requested_sum" : tcp_message.getData("min_sum")})
                
                    # Increment the message reference count so that HAL
                    # knows that it has not been fully processed.
                    message.incRefCount()

            return True

        elif tcp_message.isType("Set Lock Target"):
            if not tcp_message.isTest():
                self.lock_mode.setLockTarget(tcp_message.getData("lock_target"))
            return True
        
        return False
    
    def isGoodLock(self):
        """
        This is whether or not the focus lock mode has a 'good' 
        lock, not just whether or not it is on.
        """
        return self.lock_mode.isGoodLock()
        
    def setFunctionality(self, name, functionality):
        if (name == "qpd"):
            self.qpd_functionality = functionality
            self.qpd_functionality.qpdUpdate.connect(self.handleQPDUpdate)
        elif (name == "z_stage"):
            self.z_stage_functionality = functionality

    def setTimingFunctionality(self, functionality):
        if self.working:
            self.timing_functionality = functionality.getCameraFunctionality()
            self.timing_functionality.newFrame.connect(self.handleNewFrame)

    def start(self):
        if (self.qpd_functionality is not None) and (self.z_stage_functionality is not None):
            self.working = True
            # Start polling the QPD.
            self.qpd_functionality.getOffset()
        
    def startFilm(self, film_settings):
        # Open file to save the lock status at each frame.
        if self.working:
            if film_settings.isSaved():
                self.offset_fp = open(film_settings.getBasename() + ".off", "w")
                self.offset_fp.write(" ".join(["frame", "offset", "power", "stage-z"]) + "\n")

            # Check for a waveform from a hardware timed lock mode that uses the DAQ.
            waveform = self.lock_mode.getWaveform()
            if waveform is not None:
                self.controlMessage.emit(halMessage.HalMessage(m_type = "daq waveforms",
                                                               data = {"waveforms" : [waveform]}))
                
            self.lock_mode.startFilm()
        
    def startLock(self, lock_target = None):
        if self.working:
            self.lock_mode.startLock(lock_target)

    def startLockBehavior(self, sub_mode_name, sub_mode_params):
        """
        Not sure if this is the best name, but all the modes have a 'normal'
        functionality as well as the possibility to perform things like a
        scan for sum signal. Which of these is active can be specified by 
        calling this function.
        """
        if self.working:
            self.lock_mode.startLockBehavior(sub_mode_name, sub_mode_params)

    def stopFilm(self):
        if self.working:
            if self.offset_fp is not None:
                self.offset_fp.close()
                self.offset_fp = None
            self.lock_mode.stopFilm()

        self.timing_functionality.newFrame.disconnect(self.handleNewFrame)
        self.timing_functionality = None

    def stopLock(self):
        if self.working:
            self.lock_mode.stopLock()
