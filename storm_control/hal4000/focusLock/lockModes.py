#!/usr/bin/env python
"""
These classes implement various focus lock modes. They determine
all the behaviors of the focus lock.

Hazen 05/15
"""
import numpy
import scipy.optimize
import time

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
#        to work correctly is messy. It is also a bit difficult
#        to follow what exactly is going to happen when a
#        a particular method like startLock() is called. Maybe
#        these should just have been different class of objects?
#
class FindSumMixin(object):
    """
    This will run a find sum scan, starting at the z stage minimum and
    moving to the maximum, or until a maximum in the QPD sum signal is
    found that is larger than the requested minimum sum signal.
    """
    fsm_pname = "find_sum"
    
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
        p = parameters.addSubSection(FindSumMixin.fsm_pname)
        p.add(params.ParameterRangeFloat(description = "Step size for find sum search.",
                                         name = "step_size",
                                         value = 1.0,
                                         min_value = 0.1,
                                         max_value = 10.0))

    def getFindSumMaxSum(self):
        return self.fsm_max_sum

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
                self.behaviorDone(True)

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
                    self.behaviorDone(False)

                # Move up one step size.
                else:
                    self.z_stage_functionality.goRelative(self.fsm_step_size)

    def startLockBehavior(self, behavior_name, behavior_params):
        if hasattr(super(), "startLockBehavior"):
            super().startLockBehavior(behavior_name, behavior_params)
            
        if (behavior_name == self.fsm_mode_name):
            self.fsm_max_pos = 0.0
            self.fsm_max_sum = 0.0
            self.fsm_requested_sum = behavior_params["requested_sum"]
            self.fsm_min_sum = 0.1 * self.fsm_requested_sum
            if "fsm_step_size" in behavior_params:
                self.fsm_step_size = behavior_params["fsm_step_size"]
            else:
                self.fsm_step_size = self.parameters.get(self.fsm_pname + ".step_size")

            # Move to z = 0.
            self.fsm_max_z = self.z_stage_functionality.getMaximum()
            self.fsm_min_z = self.z_stage_functionality.getMinimum()
            self.z_stage_functionality.goAbsolute(self.fsm_min_z)


class LockedMixin(object):
    """
    This will try and hold the specified lock target. It 
    also keeps track of the quality of the lock.
    """
    lm_pname = "locked"

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.lm_buffer = None
        self.lm_buffer_length = 1
        self.lm_counter = 0
        self.lm_min_sum = 0.0
        self.lm_mode_name = "locked"
        self.lm_offset_threshold = 0.02
        self.lm_target = 0.0
        self.lm_gain = -0.9

        if not hasattr(self, "behavior_names"):
            self.behavior_names = []

        self.behavior_names.append(self.lm_mode_name)

    @staticmethod
    def addParameters(parameters):
        """
        Add parameters specific to staying in lock.
        """
        p = parameters.addSubSection(LockedMixin.lm_pname)
        p.add(params.ParameterInt(description = "Number of repeats for the lock to be considered good.",
                                  name = "buffer_length",
                                  value = 5))
        
        p.add(params.ParameterFloat(description = "Maximum allowed difference to still be in lock (nm).",
                                    name = "offset_threshold",
                                    value = 20.0))

        p.add(params.ParameterFloat(description = "Minimum sum to be considered locked (AU).",
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
                dz = self.lm_gain * diff
                self.z_stage_functionality.goRelative(dz)
            else:
                self.lm_buffer[self.lm_counter] = 0

            good_lock = bool(numpy.sum(self.lm_buffer) == self.lm_buffer_length)
            self.last_good_z = self.z_stage_functionality.getCurrentPosition()
            if (good_lock != self.good_lock):
                self.setLockStatus(good_lock)

            self.lm_counter += 1
            if (self.lm_counter == self.lm_buffer_length):
                self.lm_counter = 0
            
    def newParameters(self, parameters):
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)

        p = parameters.get(self.lm_pname)
        self.lm_buffer_length = p.get("buffer_length")
        self.lm_buffer = numpy.zeros(self.lm_buffer_length, dtype = numpy.uint8)
        self.lm_counter = 0
        self.lm_min_sum = p.get("minimum_sum")
        self.lm_offset_threshold = 1.0e-3 * p.get("offset_threshold")

    def startLock(self):
        self.lm_counter = 0
        self.lm_buffer = numpy.zeros(self.lm_buffer_length, dtype = numpy.uint8)
        self.behavior = "locked"

    def startLockBehavior(self, behavior_name, behavior_params):
        if hasattr(super(), "startLockBehavior"):
            super().startLockBehavior(behavior_name, behavior_params)

        if (behavior_name == self.lm_mode_name):
            p = self.parameters.get(self.lm_pname)

            if "buffer_length" in behavior_params:
                self.lm_buffer_length = behavior_params["buffer_length"]
            else:
                self.lm_buffer_length = p.get("buffer_length")

            if "minimum_sum" in behavior_params:
                self.lm_min_sum = behavior_params["minimum_sum"]
            else:
                self.lm_min_sum = p.get("minimum_sum")

            if "offset_threshold" in behavior_params:
                self.lm_offset_threshold = 1.0e-3 * behavior_params["offset_threshold"]
            else:
                self.lm_offset_threshold = 1.0e-3 * p.get("offset_threshold")

            # Did the user request a target?
            if "target" in behavior_params:
                self.setLockTarget(behavior_params["target"])

            # If not, use the current QPD offset.
            else:
                self.setLockTarget(self.qpd_state["offset"])

            if "z_start" in behavior_params:
                self.z_stage_functionality.goAbsolute(behavior_params["z_start"])

            self.startLock()


class ScanMixin(object):
    """
    This will do a (local) scan for the z position with the correct
    offset.

    FIXME: Is this the right thing for this behavior to do?
    """
    sm_pname = "scan"

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.sm_min_sum = None
        self.sm_mode_name = "scan"
        self.sm_offset_threshold = None
        self.sm_target = None
        self.sm_z_end = None
        self.sm_z_start = None
        self.sm_z_step = None

        if not hasattr(self, "behavior_names"):
            self.behavior_names = []
            
        self.behavior_names.append(self.sm_mode_name)

    @staticmethod
    def addParameters(parameters):
        """
        Add parameters specific to scan mode.
        """
        p = parameters.addSubSection(ScanMixin.sm_pname)
        p.add(params.ParameterFloat(description = "Minimum sum for finding the correct offset (AU).",
                                    name = "minimum_sum",
                                    value = -1.0))

        p.add(params.ParameterFloat(description = "Maximum allowed difference for finding the correct offset (nm).",
                                    name = "offset_threshold",
                                    value = 100.0))
        
        p.add(params.ParameterFloat(description = "Scan range in microns.",
                                    name = "scan_range",
                                    value = 10.0))
        
        p.add(params.ParameterFloat(description = "Scan step size in microns.",
                                    name = "scan_step",
                                    value = 0.05))

    def handleQPDUpdate(self, qpd_state):
        if hasattr(super(), "handleQPDUpdate"):
            super().handleQPDUpdate(qpd_state)
            
        if (self.behavior == self.sm_mode_name):
            
            diff = 2.0 * self.sm_offset_threshold
            if (qpd_state["sum"] > self.sm_min_sum):
                diff = (qpd_state["offset"] - self.sm_target)
            
            #
            # If we are at a z position where we are getting the correct offset
            # then we are done.
            #
            if (abs(diff) < self.sm_offset_threshold):
                self.behaviorDone(True)
                    
            else:
                
                #
                # If we hit the end of the range and did not find anything then
                # return to the last z position where we had a good lock and stop.
                #
                if (self.z_stage_functionality.getCurrentPosition() > self.sm_z_end):
                    self.z_stage_functionality.goAbsolute(self.last_good_z)
                    self.behaviorDone(False)

                #
                # Otherwise continue to move up.
                #
                else:
                    self.z_stage_functionality.goRelative(self.sm_z_step)

    def startLockBehavior(self, behavior_name, behavior_params):
        if hasattr(super(), "startLockBehavior"):
            super().startLockBehavior(behavior_name, behavior_params)
           

        if (behavior_name == self.sm_mode_name):
            p = self.parameters.get(self.sm_pname)

            # Set minimum sum.
            if "minimum_sum" in behavior_params:
                self.sm_min_sum = behavior_params["minimum_sum"]
            else:
                self.sm_min_sum = p.get("minimum_sum")

            # Set offset threshold.
            if "offset_threshold" in behavior_params:
                self.sm_offset_threshold = 1.0e-3 * behavior_params["offset_threshold"]
            else:
                self.sm_offset_threshold = 1.0e-3 * p.get("offset_threshold")

            # Set scan range.
            #
            # FIXME: User will specify full range or half range size?
            #
            if "scan_range" in behavior_params:
                
                # None means scan the entire range of the z stage.
                if behavior_params["scan_range"] is None or behavior_params["scan_range"] is False:
                    sm_z_range = self.z_stage_functionality.getMaximum() - self.z_stage_functionality.getMinimum()
                else:
                    sm_z_range = behavior_params["scan_range"]
            else:
                sm_z_range = p.get("scan_range")

            # Set z step size.
            if "scan_step" in behavior_params:
                self.sm_z_step = behavior_params["scan_step"]
            else:
                self.sm_z_step = p.get("scan_step")

            # Set z starting and ending positions.
            if "z_center" in behavior_params:
                self.sm_z_end = behavior_params["z_center"] + sm_z_range
                self.sm_z_start = behavior_params["z_center"] - sm_z_range
            else:
                self.sm_z_end = self.last_good_z + sm_z_range
                self.sm_z_start = self.last_good_z - sm_z_range

            # Fix end points is they are outside the range of the z stage.
            if (self.sm_z_end > self.z_stage_functionality.getMaximum()):
                self.sm_z_end = self.z_stage_functionality.getMaximum()
                
            if (self.sm_z_start < self.z_stage_functionality.getMinimum()):
                self.sm_z_start = self.z_stage_functionality.getMinimum()
                
            # Set target offset.
            if "target" in behavior_params:
                self.sm_target = behavior_params["target"]
            else:
                self.sm_target = self.lm_target

            # Move z stage to the starting point.
            self.z_stage_functionality.goAbsolute(self.sm_z_start)


class LockMode(QtCore.QObject):
    """
    The base class for all the lock modes.

    Modes are 'state' of the focus lock. They are called when there
    is a new QPD reading or a new frame (from the camera/feed that
    is being used to time the acquisition).

    The modes have control of the zstage to do the actual stage
    moves. Note that the requests to move the zstage could be
    sent as fast as the QPD reads and/or new frames are arriving,
    so if the zstage is slow it could get overwhelmed by move requests.

    The modes share a single parameter object. The parameters specific
    to a particular mode are stored under a mode specific attribute.

    To avoid name clashes as there are a lot of attributes (too many?),
    sub-class attribute names are all prefixed with a sub-class
    specific string.
    """
    # This signal is emitted when a mode finishes,
    # with True/False for success or failure.
    done = QtCore.pyqtSignal(bool)

    # This is signal is emitted when the lock state
    # changes between bad and good.
    goodLock = QtCore.pyqtSignal(bool)

    # Emitted when the current lock target is changed.
    lockTarget = QtCore.pyqtSignal(float)

    # The current QPD state. This is a class rather than an instance
    # variable so it is still available even when we change lock modes.
    qpd_state = None

    # Z stage functionality. All the classes use the same one.
    z_stage_functionality = None
    
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.behavior = "none"
        self.good_lock = False
        self.last_good_z = None
        self.name = "NA"
        self.parameters = parameters
        self.qpd_state = None

        # These are for testing the performance of the lock, basically
        # how many updates are we handling per second.
        #
        if True:
            self.pf_test = True
            self.pf_test_start_time = None
            self.pf_test_n_events = 0
        else:
            self.pf_test = False
        
        if not hasattr(self, "behavior_names"):
            self.behavior_names = []
            
        self.behavior_names.append(self.behavior)

    def amLocked(self):
        return (self.behavior == "locked")

    def behaviorDone(self, success):
        """
        Behaviors that end should call this method when they have
        finished, and indicate whether they succeeded or failed.

        The mode will go into the idle state and wait for 
        lockControl.LockControl to tell it what to do next.
        """
        self.behavior = "none"
        self.done.emit(success)

    def canHandleTCPMessages(self):
        """
        Modes without any of the mixins cannot handle TCP messages.
        """
        return False
    
    def getName(self):
        """
        Returns the name of the lock mode (as it should appear
        in the lock mode combo box).
        """
        return self.name

    def getQPDState(self):
        return self.qpd_state

    def getWaveform(self):
        """
        Hardware timed modules should return a daqModule.DaqWaveform here.
        """
        pass
        
    def handleNewFrame(self, frame):
        pass
    
    def handleQPDUpdate(self, qpd_state):
        self.qpd_state = qpd_state
        if hasattr(super(), "handleQPDUpdate"):
            super().handleQPDUpdate(qpd_state)

        if self.pf_test:
            self.pf_test_n_events += 1

    def isGoodLock(self):
        return self.good_lock

    def newParameters(self, parameters):
        self.parameters = parameters
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)
        
    def setLockStatus(self, status):
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
        self.setLockStatus(False)

        #
        # The assumption here is that the only super class that will
        # have a startLock() method is the LockedMixin class.
        #
        if hasattr(super(), "startLock"):
            super().startLock()

        #
        # Configure for performance measurement.
        #
        if self.pf_test:
            self.pf_test_start_time = time.time()
            self.pf_test_n_events = 0
        
    def startLockBehavior(self, behavior_name, behavior_params):
        """
        Start a 'behavior' of the lock mode.
        """
        if not behavior_name in self.behavior_names:
            raise LockModeException("Unknown lock behavior '" + behavior_name + "'.")

        self.setLockStatus(False)
        #
        # Basically this searches through the various mixin classes till
        # it finds the one that implements the requested behavior.
        #
        if hasattr(super(), "startLockBehavior"):
            super().startLockBehavior(behavior_name, behavior_params)
        self.behavior = behavior_name

    def stopLock(self):
        self.behavior = "none"
        self.z_stage_functionality.recenter()
        self.setLockStatus(False)

        # Print performance diagnostics.
        if self.pf_test:
            elapsed_time = time.time() - self.pf_test_start_time
            print("> lock performance {0:0d} samples, {1:.2f} samples/second".format(self.pf_test_n_events,
                                                                                     self.pf_test_n_events/elapsed_time))

    def stopFilm(self):
        pass
    
        
class JumpLockMode(LockMode, FindSumMixin, LockedMixin, ScanMixin):
    """
    Sub class for handling locks, jumps and combinations thereof. Basically
    every class that can lock is a sub-class of this class.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.jlm_relock_timer = QtCore.QTimer(self)
        self.jlm_relock_timer.setInterval(200)
        self.jlm_relock_timer.setSingleShot(True)
        self.jlm_relock_timer.timeout.connect(self.handleRelockTimer)

    def canHandleTCPMessages(self):
        """
        Modes with (all) of the mixins can handle TCP messages.
        """
        return True
    
    def handleJump(self, jumpsize):
        """
        Jumps the piezo stage immediately if it is not locked. Otherwise it 
        stops the lock, jumps the piezo stage and starts the relock timer.
        """
        if (self.behavior == "locked"):
            self.behavior = "none"
            self.jlm_relock_timer.start()
        self.z_stage_functionality.goRelative(jumpsize)

    def handleRelockTimer(self):
        """
        Restarts the focus lock when the relock timer fires.
        """
        self.startLock()


#
# These are in the order that they (usually) appear in the combo box.
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

    def startLock(self, target = None):
        super().startLock()
        if target is None:
            
            #
            # If the user changes the mode and then hits the lock button really
            # really fast then self.qpd_state might be None. However this problem
            # is more typically encountered when running unit tests.
            #
            if self.qpd_state is None:
                self.setLockTarget(0)
            else:
                self.setLockTarget(self.qpd_state["offset"])
        else:
            self.setLockTarget(target)

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
        self.aolm_film_on = False
        self.name = "Always On"

    def shouldEnableLockButton(self):
        return True

    def startFilm(self):
        if not self.amLocked():
            self.aolm_film_on = True
            self.startLock()

    def stopFilm(self):
        if self.aolm_film_on:
            self.aolm_film_on = False
            self.stopLock()


class OptimalLockMode(AlwaysOnLockMode):
    """
    At the start of filming the stage is moved in a triangle wave. 
    First it goes up to bracket_step, then down to -bracket_step 
    and then finally back to zero. At each point along the way the 
    focus quality & offset are recorded. When the stage returns to 
    zero, the data is fit with a gaussian and the lock target is 
    set to the offset corresponding to the center of the gaussian.
    """
    def __init__(self, parameters = None, **kwds):
        kwds["parameters"] = parameters
        super().__init__(**kwds)
        self.name = "Optimal"
        self.olm_bracket_step = None
        self.olm_counter = 0
        self.olm_fvalues = None
        self.olm_mode = "none"
        self.olm_pname = "optimal_mode"
        self.olm_quality_threshold = 0
        self.olm_relative_z = None
        self.olm_scan_hold = None
        self.olm_scan_step = None
        self.olm_scan_state = "na"
        self.olm_zvalues = None

        # Add optimal lock specific parameters.
        p = self.parameters.addSubSection(self.olm_pname)
        p.add(params.ParameterRangeFloat(description = "Distance +- z in nanometers",
                                         name = "bracket_step",
                                         value = 1000.0,
                                         min_value = 10.0,
                                         max_value = 10000.0))
        p.add(params.ParameterRangeFloat(description = "Minimum 'quality' signal",
                                         name = "quality_threshold",
                                         value = 0.0,
                                         min_value = 0.0,
                                         max_value = 1000.0))        
        p.add(params.ParameterRangeFloat(description = "Step size in z in nanometers",
                                         name = "scan_step",
                                         value = 100.0,
                                         min_value = 10.0,
                                         max_value = 1000.0))
        p.add(params.ParameterRangeInt(description = "Frames to pause between steps",
                                       name = "scan_hold",
                                       value = 10,
                                       min_value = 1,
                                       max_value = 100))

    def handleNewFrame(self, frame):
        """
        Handles a new frame from the camera. If the mode is optimizing this calculates
        the focus quality of the frame and moves the piezo to its next position.
        """
        if (self.olm_mode == "optimizing"):
            quality = focusQuality.imageGradient(frame)
            if (quality > self.olm_quality_threshold):
                self.olm_zvalues[self.olm_counter] = self.qpd_state["offset"]
                self.olm_fvalues[self.olm_counter] = quality
                self.olm_counter += 1

                if ((self.olm_counter % self.olm_scan_hold) == 0):

                    # Scan up
                    if (self.olm_scan_state == "scan up"):
                        if (self.olm_relative_z >= self.olm_bracket_step):
                            self.olm_scan_state = "scan down"
                        else:
                            self.olm_relative_z += self.olm_scan_step
                            self.z_stage_functionality.goRelative(self.olm_scan_step)
                            
                    # Scan back down                            
                    elif (self.olm_scan_state == "scan down"): 
                        if (self.olm_relative_z <= -self.olm_bracket_step):
                            self.olm_scan_state = "zero"
                        else:
                            self.olm_relative_z -= self.olm_scan_step
                            self.z_stage_functionality.goRelative(-self.olm_scan_step)

                    # Scan back to zero                            
                    else: 
                        if (self.olm_relative_z >= 0.0):
                            n = self.olm_counter - 1

                            # Fit offset data to a 1D gaussian (lorentzian would be better?)
                            zvalues = self.olm_zvalues[0:n]
                            fvalues = self.olm_fvalues[0:n]
                            fitfunc = lambda p, x: p[0] + p[1] * numpy.exp(- (x - p[2]) * (x - p[2]) * p[3])
                            errfunc = lambda p: fitfunc(p, zvalues) - fvalues
                            p0 = [numpy.min(fvalues),
                                  numpy.max(fvalues) - numpy.min(fvalues),
                                  zvalues[numpy.argmax(fvalues)],
                                  9.0] # empirically determined width parameter
                            p1, success = scipy.optimize.leastsq(errfunc, p0[:])
                            if (success == 1):
                                optimum = p1[2]
                            else:
                                print("> fit for optimal lock failed.")
                                # hope that this is close enough
                                optimum = zvalues[numpy.argmax(fvalues)]

                            print("> optimal Target:", optimum)
                            self.olm_mode = "none"
                            self.startLock(target = optimum)
                        else:
                            self.olm_relative_z += self.olm_scan_step
                            self.z_stage_functionality.goRelative(self.olm_scan_step)

    def initializeScan(self):
        """
        Configures all the variables that will be used during 
        the scan to find the optimal lock target.
        """
        self.olm_mode = "optimizing"
        self.olm_relative_z = 0.0
        self.olm_scan_state = "scan up"
        self.olm_counter = 0
        size_guess = round(self.olm_scan_hold * (self.olm_bracket_step / self.olm_scan_step) * 6)
        self.olm_fvalues = numpy.zeros(size_guess)
        self.olm_zvalues = numpy.zeros(size_guess)
                            
    def newParameters(self, parameters):
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)
        p = parameters.get(self.olm_pname)
        self.olm_bracket_step = 0.001 * p.get("bracket_step")
        self.olm_quality_threshold = p.get("quality_threshold")
        self.olm_scan_step = 0.001 * p.get("scan_step")
        self.olm_scan_hold = p.get("scan_hold")

    def startFilm(self):
        if self.amLocked():
            self.behavior = "none"
            self.initializeScan()


class CalibrationLockMode(JumpLockMode):
    """
    No lock, the stage is driven through a pre-determined set of 
    z positions for calibration purposes during filming.
    """
    def __init__(self, parameters = None, **kwds):
        kwds["parameters"] = parameters    
        super().__init__(**kwds)
        self.clm_counter = 0
        self.clm_max_zvals = 0
        self.clm_pname = "calibrate"
        self.clm_zvals = []
        self.name = "Calibrate"

        # Add calibration specific parameters.
        p = self.parameters.addSubSection(self.clm_pname)
        p.add(params.ParameterRangeInt(description = "Frames to pause between steps.",
                                       name = "frames_to_pause",
                                       value = 2,
                                       min_value = 1,
                                       max_value = 100))        
        p.add(params.ParameterRangeInt(description = "Frames before to pause at start.",
                                       name = "deadtime",
                                       value = 20,
                                       min_value = 1,
                                       max_value = 100))
        p.add(params.ParameterRangeFloat(description = "Distance +- z to move in nanometers.",
                                         name = "range",
                                         value = 600,
                                         min_value = 100,
                                         max_value = 5000))
        p.add(params.ParameterRangeFloat(description = "Step size in z in nanometers.",
                                         name = "step_size",
                                         value = 10,
                                         min_value = 1,
                                         max_value = 100))

    def calibrationSetup(self, z_center, deadtime, zrange, step_size, frames_to_pause):
        """
        Configure the variables that will be used to execute the z scan.
        """
        # FIXME: Are these checks a good idea?
        if False:
            if (deadtime <= 0):
                raise LockModeException("Deadtime is too small " + str(deadtime))
            if (zrange < 10):
                raise LockModeException("Range is too small " + str(zrange))
            if (zrange > 1000):
                raise LockModeException("Range is too large " + str(zrange))
            if (step_size <= 0.0):
                raise LockModeException("Negative / zero step size " + str(step_size))
            if (step_size > 100.0):
                raise LockModeException("Step size is to large " + str(step_size))
            if (frames_to_pause <= 0):
                raise LockModeException("Frames to pause is too smale " + str(frames_to_pause))

        def addZval(z_val):
            self.clm_zvals.append(z_val)
            self.clm_max_zvals += 1

        self.clm_zvals = []
        self.clm_max_zvals = 0
        
        # Convert to um.
        zrange = 0.001 * zrange
        step_size = 0.001 * step_size

        # Initial hold.
        for i in range(deadtime-1):
            addZval(z_center)

        # Staircase scan.
        addZval(-zrange)
        z = z_center - zrange
        stop = z_center + zrange - 0.5 * step_size
        while (z < stop):
            for i in range(frames_to_pause-1):
                addZval(0.0)
            addZval(step_size)
            z += step_size

        addZval(-zrange)

        # Final hold.
        for i in range(deadtime-1):
            addZval(z_center)

    def handleNewFrame(self, frame):
        """
        Handles a new frame from the camera. This moves to a new 
        z position if the scan has not been completed.
        """
        if (self.clm_counter < self.clm_max_zvals):
            self.z_stage_functionality.goRelative(self.clm_zvals[self.clm_counter])
            self.clm_counter += 1

    def newParameters(self, parameters):
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)
        p = parameters.get(self.clm_pname)
        self.calibrationSetup(0.0, 
                              p.get("deadtime"), 
                              p.get("range"), 
                              p.get("step_size"), 
                              p.get("frames_to_pause"))

    def startFilm(self):
        self.clm_counter = 0

    def stopFilm(self):
        self.z_stage_functionality.recenter()        

class HardwareZScanLockMode(AlwaysOnLockMode):
    """
    This holds a focus target. Then during filming it does a hardware
    times z scan.
    """
    def __init__(self, parameters = None, **kwds):
        kwds["parameters"] = parameters    
        super().__init__(**kwds)
        self.hzs_film_off = False
        self.hzs_pname = "hardware_z_scan"
        self.hzs_zvals = None
        self.name = "Hardware Z Scan"

        # Add hardware z scan specific parameters.
        p = self.parameters.addSubSection(self.hzs_pname)

        # FIXME: Should be a parameter custom? Both focuslock and illumination
        #        waveforms should be parsed / created / generated by a single
        #        module somewhere else?
        p.add(params.ParameterString(description = "Frame z steps (in microns).",
                                     name = "z_offsets",
                                     value = ""))
        
    def getWaveform(self):
        """
        This is called before startFilm() by lockControl.LockControl. It
        returns the waveform to use during filming as a daqModule.DaqWaveform,
        or None if there is no waveform or one shouldn't be used.
        """
        if self.amLocked() and isinstance(self.hzs_zvals, numpy.ndarray):
            waveform = self.hzs_zvals + self.z_stage_functionality.getCurrentPosition()
            return self.z_stage_functionality.getDaqWaveform(waveform)

    def setZStageFunctionality(self, z_stage_functionality):
        super().setZStageFunctionality(z_stage_functionality)
        if not self.z_stage_functionality.haveHardwareTiming():
            raise LockModeException("Z stage does not support hardware timed scans.")

    def newParameters(self, parameters):
        if hasattr(super(), "newParameters"):
            super().newParameters(parameters)
        p = parameters.get(self.hzs_pname)
        self.hzs_zvals = None
        if (len(p.get("z_offsets")) > 0):
            self.hzs_zvals = numpy.array(list(map(float, p.get("z_offsets").split(","))))

    def shouldEnableLockButton(self):
        return True
    
    def startFilm(self):
        if self.amLocked() and self.hzs_zvals is not None:
            self.behavior = "none"
            self.hzs_film_off = True

    def stopFilm(self):
        if self.hzs_film_off:
            self.hzs_film_off = False
            self.behavior = "locked"


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
