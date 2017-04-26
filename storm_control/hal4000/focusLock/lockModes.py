#!/usr/bin/env python
"""
These classes implement various focus lock modes. They determine
all the behaviors of the focus lock.

Hazen 05/15
"""
import numpy
import scipy.optimize

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

# Focus quality determination for the optimal lock.
import storm_control.hal4000.focusLock.focusQuality as focusQuality


class LockModeException(halExceptions.HalException):
    pass


#
# Mixin classes provide various locking and scanning behaviours.
# The idea is that these are more or less self-contained and setting
# the lock modes 'mode' attribute will switch between them.
#
# These are active when the 'behavior' attribute corresponds to
# their name.
#
# FIXME: Was this actually a good idea? Getting the inheritance
#        to work correctly is messy. Maybe these should just
#        have been different class of objects?
#
class FindSumMixin(object):
    """
    This will run a find sum scan, starting at the z stage minimum and
    moving to the maximum, or until a maximum in the QPD sum signal is
    found that is larger than the requested minimum sum signal.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.fsm_max_pos = 0.0
        self.fsm_max_sum = 0.0
        self.fsm_max_z = 0.0
        self.fsm_min_sum = 0.0
        self.fsm_min_z = 0.0
        self.fsm_mode_name = "find_sum"
        self.fsm_requested_sum = 0.0
        self.fsm_step_size = 0.0

        if not hasattr(self, "behavior_names"):
            self.behavior_names = []
            
        self.behavior_names.append(self.fsm_mode_name)

    @staticmethod
    def addParameters(parameters):
        """
        Add parameters specific to finding sum.
        """
        parameters.add(params.ParameterRangeFloat(description = "Step size for find sum search.",
                                                  name = "fsm_step_size",
                                                  value = 1.0,
                                                  min_value = 0.1,
                                                  max_value = 10.0))

    def handleQPDUpdate(self, qpd_state):
        if hasattr(super(), "handleQPDUpdate"):
            super().handleQPDUpdate(qpd_state)
            
        if (self.behavior == self.fsm_mode_name):
            power = qpd_state["sum"]
            z_pos = self.z_stage_functionality.getCurrentPosition()

            # Check if the current power is greater than the
            # maximum we've seen so far.
            if (power > self.fsm_max_sum):
                self.fsm_max_sum = power
                self.fsm_max_pos = z_pos

            # Check if the power has started to go back down, if it has
            # then we've hopefully found the maximum.
            if (self.fsm_max_sum > self.fsm_requested_sum) and (power < (0.5 * self.fsm_max_sum)):
                self.z_stage_functionality.goAbsolute(self.fsm_max_pos)
                self.done.emit(True)
            else:
                # Are we at the maximum z?
                if (z_pos >= self.fsm_max_z):

                    # Did we find anything at all?
                    if (self.fsm_max_sum > self.fsm_min_sum):
                        self.z_stage_functionality.goAbsolute(self.fsm_max_pos)

                    # Otherwise just go back to the center position.
                    else:
                        self.z_stage_functionality.recenter()

                    # Emit signal for failure.
                    self.done.emit(False)

                # Move up one step size.
                else:
                    self.z_stage_functionality.goRelative(self.fsm_step_size)

    def startLockBehavior(self, behavior_name, behavior_params):
        if (behavior_name == self.fsm_mode_name):
            self.fsm_max_pos = 0.0
            self.fsm_max_sum = 0.0
            self.fsm_requested_sum = behavior_params["requested_sum"]
            self.fsm_min_sum = 0.1 * self.fsm_requested_sum
            if "fsm_step_size" in behavior_params:
                self.fsm_step_size = behavior_params["fsm_step_size"]
            else:
                self.fsm_step_size = self.parameters.get("fsm_step_size")

            # Move to z = 0.
            self.fsm_max_z = self.z_stage_functionality.getMaximum()
            self.fsm_min_z = self.z_stage_functionality.getMinimum()
            self.z_stage_functionality.goAbsolute(self.fsm_min_z)


class LockedMixin(object):
    """
    This will try and hold the specified lock target. It 
    also keeps track of the quality of the lock.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.lm_buffer = None
        self.lm_buffer_length = 1
        self.lm_counter = 0
        self.lm_min_sum = 0.0
        self.lm_mode_name = "locked"
        self.lm_offset_threshold = 0.01
        self.lm_target = 0.0

        if not hasattr(self, "behavior_names"):
            self.behavior_names = []

        self.behavior_names.append(self.lm_mode_name)

    @staticmethod
    def addParameters(parameters):
        """
        Add parameters specific to staying in lock.
        """
        parameters.add(params.ParameterInt(description = "Number of repeats for the lock to be considered good.",
                                           name = "buffer_length",
                                           value = 5))
        
        parameters.add(params.ParameterFloat(description = "Maximum allowed difference to still be in lock.",
                                             name = "offset_threshold",
                                             value = 0.1))

        parameters.add(params.ParameterFloat(description = "Minimum sum to be considered locked.",
                                             name = "minimum_sum",
                                             value = -1.0))

    def getLockTarget(self):
        return self.lm_target
        
    def handleQPDUpdate(self, qpd_state):
        if hasattr(super(), "handleQPDUpdate"):
            super().handleQPDUpdate(qpd_state)

        if (self.behavior == self.lm_mode_name):
            if (qpd_state["sum"] > self.lm_min_sum):
                diff = (qpd_state["offset"] - self.lm_target)
                if (abs(diff) < self.lm_offset_threshold):
                    self.lm_buffer[self.lm_counter] = 1
                else:
                    self.lm_buffer[self.lm_counter] = 0

                # Simple proportional control.
                dz = 0.9 * diff
                self.z_stage_functionality.goRelative(dz)
            else:
                self.lm_buffer[self.lm_counter] = 0

            good_lock = (numpy.sum(self.lm_buffer) == self.lm_buffer_length)
            if (good_lock != self.good_lock):
                self.setLockStatus(good_lock)

            self.lm_counter += 1
            if (self.lm_counter == self.lm_buffer_length):
                self.lm_counter = 0

    def initializeLMBuffer(self):
        self.lm_buffer = numpy.zeros(self.lm_buffer_length, dtype = numpy.uint8)
            
    def newParameters(self, parameters):
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)
            
        self.lm_buffer_length = parameters.get("buffer_length")
        self.lm_min_sum = parameters.get("minimum_sum")
        self.lm_offset_threshold = parameters.get("offset_threshold")
                
    def startLockBehavior(self, behavior_name, behavior_params):
        if (behavior_name == self.lm_mode_name):
            self.lm_counter = 0

            if "buffer_length" in behavior_params:
                self.lm_buffer_length = behavior_params["buffer_length"]
            else:
                self.lm_buffer_length = self.parameters.get("buffer_length")

            if "minimum_sum" in behavior_params:
                self.lm_min_sum = behavior_params["minimum_sum"]
            else:
                self.lm_min_sum = self.parameters.get("minimum_sum")

            if "offset_threshold" in behavior_params:
                self.lm_offset_threshold = behavior_params["offset_threshold"]
            else:
                self.lm_offset_threshold = parameters.get("offset_threshold")
            
            # Did the user request a target?
            if "target" in behavior_params:
                self.setLockTarget(behavior_params["target"])

            # If not, use the current QPD offset.
            else:
                self.setLockTarget(self.qpd_state["offset"])

            if "z_start" in behavior_params:
                self.z_stage_functionality.goAbsolute(behavior_params["z_start"])

            self.initializeLMBuffer()
    

class LockMode(QtCore.QObject):
    """
    The base class for all the lock modes.

    Modes are 'state' of the focus lock. They are called when there
    is a new QPD reading or a new frame (from the camera/feed that
    is being used to time the acquisition).

    The modes have control of the zstage to do the actual stage
    moves. Note that the requests to move the zstage are queued so
    if the zstage is slow it could get overwhelmed by move requests.

    The modes share a single parameter object. The parameters specific
    to a particular mode are stored under the modes 'name' attribute.
    """
    # This signal is emitted when a mode finishes,
    # with True/False for success or failure.
    done = QtCore.pyqtSignal(bool)

    # This is signal is emitted when the lock state
    # changes between bad and good.
    goodLock = QtCore.pyqtSignal(bool)

    # Emitted when the current lock target is changed.
    lockTarget = QtCore.pyqtSignal(float)

    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.behavior = "none"
        self.good_lock = False
        self.name = "NA"
        self.parameters = parameters
        self.qpd_state = None
        self.z_stage_functionality = None

        if not hasattr(self, "behavior_names"):
            self.behavior_names = []
            
        self.behavior_names.append(self.behavior)

    def amLocked(self):
        return (self.behavior == "locked")
    
    def getName(self):
        """
        Returns the name of the lock mode (as it should appear
        in the lock mode combo box).
        """
        return self.name

    def getQPDState(self):
        return self.qpd_state

    def handleNewFrame(self, frame):
        pass
    
    def handleQPDUpdate(self, qpd_state):
        self.qpd_state = qpd_state
        if hasattr(super(), "handleQPDUpdate"):
            super().handleQPDUpdate(qpd_state)
            
    def initialize(self):
        """
        This is called when the mode becomes the 'active' mode.
        """
        pass

    def isGoodLock(self):
        return self.good_lock

    def newParameters(self, parameters):
        self.parameters = parameters
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)

    def setLockStatus(self, status):
        print(">sll", status)
        self.good_lock = status
        self.goodLock.emit(status)
        
    def setLockTarget(self, target):
        self.lockTarget.emit(target)
        self.lm_target = target

    def setZStageFunctionality(self, z_stage_functionality):
        self.z_stage_functionality = z_stage_functionality

    def shouldEnableLockButton(self):
        return False

    def startFilm(self):
        pass

    def startLock(self):
        pass
        
    def startLockBehavior(self, behavior_name, behavior_params):
        """
        Start a 'behavior' of the lock mode.
        """
        if not behavior_name in self.behavior_names:
            raise LockModeException("Unknown lock behavior '" + sub_mode_name + "'.")

        self.setLockStatus(False)
        super().startLockBehavior(behavior_name, behavior_params)
        self.behavior = behavior_name

    def stopLock(self):
        self.behavior = "none"
        self.z_stage_functionality.recenter()
        self.setLockStatus(False)

    def stopFilm(self):
        pass
    
        
class JumpLockMode(LockMode, FindSumMixin, LockedMixin):
    """
    Sub class for handling locks, jumps and combinations thereof. Basically
    every class that can lock is a sub-class of this class.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.relock_timer = QtCore.QTimer(self)
        self.relock_timer.setInterval(200)
        self.relock_timer.setSingleShot(True)
        self.relock_timer.timeout.connect(self.handleRelockTimer)

    def handleJump(self, jumpsize):
        """
        Jumps the piezo stage immediately if it is not locked. Otherwise it 
        stops the lock, jumps the piezo stage and starts the relock timer.
        """
        if (self.behavior == "locked"):
            self.behavior = "none"
            self.relock_timer.start()
        self.z_stage_functionality.goRelative(jumpsize)
        
    def handleRelockTimer(self):
        """
        Restarts the focus lock when the relock timer fires.
        """
        self.startLock()


#
# These are in the order that they usually appear in the combo box.
#
class NoLockMode(LockMode):
    """
    No focus lock.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.name = "No lock"

    def getLockTarget(self):
        return 0.0

    def handleJump(self, jumpsize):
        """
        Jumps the pizeo stage immediately by the distance jumpsize.
        """
        self.z_stage_functionality.goRelative(jumpsize)


class AutoLockMode(JumpLockMode):
    """
    Lock will be on during filming, but cannot be turned on manually.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.name = "Auto Lock"
    
    def startFilm(self):
        self.startLock()

    def startLock(self):
        self.setLockStatus(False)
        self.initializeLMBuffer()
        self.setLockTarget(self.qpd_state["offset"])
        self.behavior = "locked"

    def stopFilm(self):
        self.stopLock()
        self.z_stage_functionality.recenter()


class AlwaysOnLockMode(AutoLockMode):
    """
    Lock will start during filming, or when the lock button is 
    pressed (in which case it will always stay on)
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.film_on = False
        self.name = "Always On"

    def shouldEnableLockButton(self):
        return True

    def startFilm(self):
        if not self.amLocked():
            self.film_on = True
            self.startLock()

    def stopFilm(self):
        if self.film_on:
            self.film_on = False
            self.stopLock()
    

#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
