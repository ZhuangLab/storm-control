#!/usr/bin/python
#
## @file
#
# These classes implement various focus lock modes.
#
# Hazen 08/10
#

from PyQt4 import QtCore

# Focus quality determination for the optimal lock.
import numpy
import scipy.optimize
import focuslock.focusQuality as focusQuality

## LockMode
#
# The base class for all the lock modes.
#
class LockMode(QtCore.QObject):
    
    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        QtCore.QObject.__init__(self, parent)
        self.control_thread = control_thread
        self.locked = False
        self.name = "NA"

    ## amLocked
    #
    # @return True/False if the focus lock is currently engaged.
    #
    def amLocked(self):
        return self.locked

    ## getName
    #
    # @return The name of the focus lock mode.
    #
    def getName(self):
        return self.name

    ## handleJump
    #
    # @param jumpsize The amount to jump the piezo stage in um.
    #
    def handleJump(self, jumpsize):
        pass

    ## lockButtonToggle
    #
    # Invert the state of the lock button.
    #
    def lockButtonToggle(self):
        pass

    ## newFrame
    #
    # Handles a new frame from the camera.
    #
    # @param frame A frame object.
    # @param offset The offset signal from the focus lock.
    # @param power The sum signal from the focus lock.
    # @param stage_z The z position of the piezo stage.
    #
    def newFrame(self, frame, offset, power, stage_z):
        pass

    ## newParameters
    #
    # Handles new parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        pass

    ## reset
    #
    # ??
    #
    def reset(self):
        pass

    ## restartLock
    #
    # Restarts the focus lock when the relock timer fires.
    #
    def restartLock(self):
        pass

    ## setLockTarget
    #
    # Sets the focus lock target to the desired value.
    #
    # @param target The desired lock target.
    #
    def setLockTarget(self, target):
        pass

    ## shouldDisplayLockButton
    #
    # @return True/False if a lock button should be displayed for this mode.
    #
    def shouldDisplayLockButton(self):
        return False

    ## shouldDisplayLockLabel
    #
    # @return True/False if a label should be displayed for this mode.
    #
    def shouldDisplayLockLabel(self):
        return self.amLocked()

    ## startLock
    #
    # Start the focus lock.
    #
    def startLock(self):
        pass

    ## stopLock
    #
    # Stop the focus lock.
    #
    def stopLock(self):
        pass


## JumpLockMode
#
# Derived Class for handling locks, jumps and combinations thereof.
#
class JumpLockMode(LockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        LockMode.__init__(self, control_thread, parameters, parent)
        self.relock_timer = QtCore.QTimer(self)
        self.relock_timer.setInterval(200)
        self.relock_timer.setSingleShot(True)
        self.connect(self.relock_timer, QtCore.SIGNAL("timeout()"), self.restartLock)

    ## handleJump
    # 
    # Jumps the piezo stage immediately if it is not locked. Otherwise it stops the
    # lock, jumps the piezo stage and starts the relock timer.
    #
    # @param jumpsize The distance to jump the piezo stage.
    #
    def handleJump(self, jumpsize):
        if self.locked:
            self.control_thread.stopLock()
        self.control_thread.moveStageRel(jumpsize)
        if self.locked:
            self.relock_timer.start()

    ## restartLock
    #
    # Restarts the focus lock when the relock timer fires.
    #
    def restartLock(self):
        self.control_thread.startLock()

    ## setLockTarget
    #
    # Sets the focus lock target to the desired value.
    #
    # @param target The desired lock target.
    #
    def setLockTarget(self, target):
        self.control_thread.setTarget(target)

#
# Modes are listed in the order in which they appear on
# the dialog box.
#

## NoLockMode
#
# No focus lock
#
class NoLockMode(LockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        LockMode.__init__(self, control_thread, parameters, parent)
        self.name = "Off"

    ## handleJump
    #
    # Jumps the pizeo stage immediately by the distance jumpsize.
    #
    # @param jumpsize The distance to jump the stage.
    #
    def handleJump(self, jumpsize):
        self.control_thread.moveStageRel(jumpsize)


## AutoLockMode
#
# Lock will be on during filming, but cannot be turned on manually.
#
class AutoLockMode(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.name = "Auto Lock"

    ## startLock
    #
    # Start the focus lock.
    #
    def startLock(self):
        self.control_thread.startLock()
        self.locked = True

    ## stopLock
    #
    # Stop the focus lock.
    #
    def stopLock(self):
        if self.locked:
            self.control_thread.stopLock()
            self.control_thread.recenter()
            self.locked = False


## AlwaysOnLockMode
#
# Lock will start during filming, or when the lock button is 
# pressed (in which case it will always stay on)
#
class AlwaysOnLockMode(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.button_locked = False
        self.name = "Always On"

    ## lockButtonToggle
    #
    # Sets the button_locked flag and start/stops the focus lock.
    #
    def lockButtonToggle(self):
        if self.button_locked:
            self.button_locked = False
            self.stopLock()
        else:
            self.startLock()
            self.button_locked = True

    ## newParameters
    #
    # This is a noop, not sure why this method is in this class.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        pass

    ## reset
    #
    # Turn the lock off it was turned on using the lock button.
    #
    def reset(self):
        if self.button_locked:
            self.lockButtonToggle()

    ## shouldDisplayLockButton
    #
    # @return True
    #
    def shouldDisplayLockButton(self):
        return True

    ## startLock
    #
    # Starts the focus lock.
    #
    def startLock(self):
        if not self.locked:
            self.control_thread.startLock()
            self.locked = True

    ## stopLock
    #
    # Stops the focus lock.
    #
    def stopLock(self):
        if self.locked and (not self.button_locked):
            self.control_thread.stopLock()
            self.control_thread.recenter()
            self.locked = False


## OptimalLockMode
#
# At the start of filming the stage is moved
# in a triangle wave. First it goes up to bracket_step, then down
# to -bracket_step and then finally back to zero. At each point
# along the way the focus quality & offset are recorded. When the
# stage returns to zero, the data is fit with a gaussian and the
# lock target is set to the offset corresponding to the center
# of the gaussian.
#
class OptimalLockMode(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.bracket_step = None
        self.button_locked = False
        self.cur_z = None
        self.counter = 0
        self.fvalues = None
        self.lock_target = None
        self.mode = "None"
        self.name = "Optimal"
        self.quality_threshold = 0
        self.scan_hold = None
        self.scan_step = None
        self.scan_state = 1
        self.zvalues = None

    ## getName
    #
    # Not sure why this method is in this class.
    #
    # @return "Optimal"
    #
    def getName(self):
        return "Optimal"

    ## initScan
    #
    # Configures all the variables that will be used during the scan
    # to find the optimal lock target.
    #
    def initScan(self):
        self.cur_z = 0.0
        self.mode = "Optimizing"
        self.scan_state = 1
        self.counter = 0
        size_guess = round(self.scan_hold * (self.bracket_step / self.scan_step) * 6)
        self.fvalues = numpy.zeros(size_guess)
        self.zvalues = numpy.zeros(size_guess)

    ## lockButtonToggle
    #
    # Toggle the lock button. This stops the lock and also recenters the piezo.
    #
    def lockButtonToggle(self):
        if self.button_locked:
            self.locked = False
            self.button_locked = False
            self.control_thread.stopLock()
            self.control_thread.recenter()
        else:
            self.control_thread.startLock()
            self.lock_target = self.control_thread.getLockTarget()
            self.button_locked = True
            self.locked = True

    ## newFrame
    #
    # Handles a new frame from the camera. If the mode is optimizing this calculates
    # the focus quality of the frame and moves the piezo to its next position.
    #
    # @param frame A frame object.
    # @param offset The offset signal from the focus lock.
    # @param power The sum signal from the focus lock.
    # @param stage_z The z position of the piezo stage.
    #
    def newFrame(self, frame, offset, power, stage_z):
        if (self.mode == "Optimizing"):
            if frame:
                quality = focusQuality.imageGradient(frame)
                if (quality > self.quality_threshold):
                    self.zvalues[self.counter] = offset
                    self.fvalues[self.counter] = quality
                    self.counter += 1

                    if ((self.counter % self.scan_hold) == 0):
                        if (self.scan_state == 1): # Scan up
                            if (self.cur_z >= self.bracket_step):
                                self.scan_state = 2
                            else:
                                self.cur_z += self.scan_step
                                self.handleJump(self.scan_step)
                        elif (self.scan_state == 2): # Scan back down
                            if (self.cur_z <= -self.bracket_step):
                                self.scan_state = 3
                            else:
                                self.cur_z -= self.scan_step
                                self.handleJump(-self.scan_step)
                        else: # Scan back to zero
                            if (self.cur_z >= 0.0):
                                self.mode = "Locked"
                                n = self.counter - 1

                                # Fit offset data to a*x*x + b*x + c.
                                #m0 = numpy.concatenate((numpy.ones(n),
                                #                        self.zvalues[0:n],
                                #                        self.zvalues[0:n] * self.zvalues[0:n]))
                                #m0 = numpy.reshape(m0, (3, n))
                                #m1 = numpy.dot(numpy.linalg.inv(numpy.dot(m0, numpy.transpose(m0))), m0)
                                #v0 = numpy.dot(m1, self.fvalues[0:n])
                                #optimum = -v0[1]/(2.0 * v0[2])

                                # Fit offset data to a 1D gaussian (lorentzian would be better?)
                                zvalues = self.zvalues[0:n]
                                fvalues = self.fvalues[0:n]
                                fitfunc = lambda p, x: p[0] + p[1] * numpy.exp(- (x - p[2]) * (x - p[2]) * p[3])
                                errfunc = lambda p: fitfunc(p, zvalues) - fvalues
                                p0 = [numpy.min(fvalues),
                                      numpy.max(fvalues) - numpy.min(fvalues),
                                      zvalues[numpy.argmax(fvalues)],
                                      9.0] # empirically determined width parameter
                                p1, success = scipy.optimize.leastsq(errfunc, p0[:])
                                if success == 1:
                                    optimum = p1[2]
                                else:
                                    print "Fit for optimal lock failed."
                                    # hope that this is close enough
                                    optimum = zvalues[numpy.argmax(fvalues)]

                                print "Optimal Target:", optimum
                                self.control_thread.setTarget(optimum)
                            else:
                                self.cur_z += self.scan_step
                                self.handleJump(self.scan_step)

    ## newParameters
    #
    # Handles new parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        self.quality_threshold = parameters.get("olock_quality_threshold")
        self.qpd_zcenter = parameters.get("qpd_zcenter")
        self.bracket_step = 0.001 * parameters.get("olock_bracket_step")
        self.scan_step = 0.001 * parameters.get("olock_scan_step")
        self.scan_hold = parameters.get("olock_scan_hold")

    ## reset
    #
    # Turn the lock off it was turned on using the lock button.
    #
    def reset(self):
        if self.button_locked:
            self.lockButtonToggle()

    ## shouldDisplayLockButton
    #
    # @return True
    #
    def shouldDisplayLockButton(self):
        return True

    ## startLock
    #
    # Call initScan and starts the focus lock.
    #
    def startLock(self):
        self.initScan()
        self.control_thread.setTarget(self.lock_target)
        self.control_thread.startLock()
        self.locked = True

    ## stopLock
    #
    # Stops the focus lock.
    #
    def stopLock(self):
        if self.locked:
            self.control_thread.setTarget(self.lock_target)
            if (not self.button_locked):
                self.locked = False
                self.control_thread.stopLock()
                self.control_thread.recenter()


## CalibrationLockMode
#
# No lock, the stage is driven through a pre-determined set of 
# z positions for calibration purposes during filming.
#
class CalibrationLockMode(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.counter = 0
        self.max_zvals = 0
        self.name = "Calibrate"
        self.zvals = []

    ## calibrationSetup
    #
    # Configure the variables that will be used to execute the z scan.
    #
    # @param z_center The piezo center position of the scan.
    # @param deadtime The deadtime before the start of the scan.
    # @param zrange The distance to scan (the scan goes from -zrange to zrange).
    # @param step_size The distance to step at each step.
    # @param frames_to_pause The number of frames to pause between steps.
    #
    def calibrationSetup(self, z_center, deadtime, zrange, step_size, frames_to_pause):
        # Are these checks a good idea?
        if 0:
            assert deadtime > 0, "calibrationSetup: deadtime is too small" + str(deadtime)
            assert zrange > 10, "calibrationSetup: range is too small" + str(zrange)
            assert zrange < 1000, "calibrationSetup: range is too large" + str(zrange)
            assert step_size > 0.0, "calibrationSetup: negative step size" + str(step_size)
            assert step_size < 100.0, "calibrationSetup: step size is to large" + str(step_size)
            assert frames_to_pause > 0, "calibrationSetup: frames_to_pause it too smale" + str(frames_to_pause)

        def addZval(z_val):
            self.zvals.append(z_val)
            self.max_zvals += 1

        self.zvals = []
        self.max_zvals = 0
        # convert to um
        zrange = 0.001 * zrange
        step_size = 0.001 * step_size

        # initial hold
        for i in range(deadtime-1):
            addZval(z_center)

        # staircase
        addZval(-zrange)
        z = z_center - zrange
        stop = z_center + zrange - 0.5 * step_size
        while (z < stop):
            for i in range(frames_to_pause-1):
                addZval(0.0)
            addZval(step_size)
            z += step_size

        addZval(-zrange)

        # final hold
        for i in range(deadtime-1):
            addZval(z_center)

    ## newFrame
    #
    # Handles a new frame from the camera. This moves to a new z position
    # if the scan has not been completed.
    #
    # @param frame A frame object.
    # @param offset The offset signal from the focus lock.
    # @param power The sum signal from the focus lock.
    # @param stage_z The z position of the piezo stage.
    #
    def newFrame(self, frame, offset, power, stage_z):
        if self.counter < self.max_zvals:
            self.control_thread.moveStageRel(self.zvals[self.counter])
            self.counter += 1

    ## newParameters
    #
    # Handles new parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        #self.calibrationSetup(parameters.qpd_zcenter, 
        self.calibrationSetup(0.0, 
                              parameters.get("cal_deadtime"), 
                              parameters.get("cal_range"), 
                              parameters.get("cal_step_size"), 
                              parameters.get("cal_frames_to_pause"))

    ## startLock
    #
    # Sets the frame counter which is used to index through the list of z positions to zero.
    #
    def startLock(self):
        self.counter = 0

#    def stopLock(self):
#        self.control_thread.recenter()


## ZScanLockMode
#
# The stage will move through a series of positions as specified in 
# the calibration file during filming, locking is optional.
#
class ZScanLockMode(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.counter = 0
        self.current_z = None
        self.name = "Z Scan"
        self.z_start = None
        self.z_step = None
        self.z_frames_to_pause = None
        self.z_stop = None
        self.z_focus_lock = None

    ## newFrame
    #
    # Handles a new frame from the camera. This moves to a new z position
    # if the scan has not been completed.
    #
    # @param frame A frame object.
    # @param offset The offset signal from the focus lock.
    # @param power The sum signal from the focus lock.
    # @param stage_z The z position of the piezo stage.
    #
    def newFrame(self, frame, offset, power, stage_z):
        if abs(self.current_z - self.z_stop) > self.z_step:
            if self.counter == self.z_frames_to_pause:
                self.counter = 0
                self.current_z += self.z_step
                if self.locked:
                    self.relock_timer.stop()
                    self.control_thread.stopLock()
                self.control_thread.moveStageRel(self.z_step)
                if self.locked:
                    self.relock_timer.start()
            self.counter += 1

    ## newParameters
    #
    # Handles new parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        self.z_start = parameters.get("zscan_start")
        self.z_step = parameters.get("zscan_step")
        self.z_frames_to_pause = parameters.get("zscan_frames_to_pause")
        self.z_stop = parameters.get("zscan_stop")
        self.z_focus_lock = parameters.get("zscan_focus_lock")

    ## startLock
    #
    # Reset the piezo stage z position. Reset the frame counter. Start
    # the lock (if necessary).
    #
    def startLock(self):
        self.counter = 0
        self.current_z = self.z_start
        self.control_thread.moveStageAbs(self.z_start)
        if self.z_focus_lock:
            self.relock_timer.start()
            self.locked = True

    ## stopLock
    #
    # Stop the lock & the relock timer. Recenter the piezo.
    #
    def stopLock(self):
        if self.z_focus_lock:
            self.control_thread.stopLock()
            self.relock_timer.stop()
            self.locked = False
        self.control_thread.recenter()

## LargeOffsetLock
#
# For Shu & Graham.
#
# The stage will jump the distance specified with jump control.
# Every 600 frames it will jump back to the zero position, relock,
# and then jump back again. This gives you a focus lock that
# (sort of) works a large distance from a surface.
#
class LargeOffsetLock(JumpLockMode):

    ## __init__
    #
    # @param control_thread A thread object that controls the focus lock.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.frame_delay = 600
        self.name = "Large Offset"

        self.jump_down_timer = QtCore.QTimer(self)
        self.jump_down_timer.setInterval(1000)
        self.jump_down_timer.setSingleShot(True)
        self.jump_down_timer.timeout.connect(self.restartLock)

        self.jump_up_timer = QtCore.QTimer(self)
        self.jump_up_timer.setInterval(2000)
        self.jump_up_timer.setSingleShot(True)
        self.jump_up_timer.timeout.connect(self.jumpBackToTarget)
    
        self.jumpsize = 0.0

    ## handleJump
    #
    # This does not actually jump, it just records the distance to jump.
    #
    def handleJump(self, jumpsize):
        self.jumpsize = jumpsize

    ## jumpBackToTarget
    #
    # Stops the lock and jumps back to the target focal plane.
    #
    def jumpBackToTarget(self):
        if self.locked:
            self.control_thread.stopLock()
            self.control_thread.moveStageRel(self.jumpsize)

    ## newFrame
    #
    # Handles a new frame from the camera. If the frame number matches the
    # delay time then refindLock method is called.
    #
    # @param frame A frame object.
    # @param offset The offset signal from the focus lock.
    # @param power The sum signal from the focus lock.
    # @param stage_z The z position of the piezo stage.
    #
    def newFrame(self, frame, offset, power, stage_z):
        if ((frame.number != 0) and ((frame.number % self.frame_delay) == 0)):
            self.refindLock()

    ## newParameters
    #
    # Handles new parameters.
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        if hasattr(parameters, "jump_down_delay"):
            self.jump_down_timer.setInterval(parameters.get("jump_down_delay"))
        if hasattr(parameters, "frame_delay"):
            self.frame_delay = parameters.get("frame_delay")
        if hasattr(parameters, "jump_up_delay"):
            self.jump_up_timer.setInterval(parameters.get("jump_up_delay"))

    ## refindLock
    #
    # Jump the stage back to a lockable focal plane and starts the timer to jump
    # back to a lockable focus plane.
    #
    def refindLock(self):
        if self.locked:
            self.control_thread.moveStageRel(-self.jumpsize)
            self.jump_down_timer.start()

    ## restartLock        
    #
    # If locked, set the lock target to zero and lock to this target.
    #
    def restartLock(self):
        if self.locked:
            self.control_thread.setTarget(0.0)
            self.control_thread.startLock()
            self.jump_up_timer.start()

    ## startLock
    #
    # Set the lock target to zero, turn on the lock and start the timer to
    # jump to the imaging focal plane.
    #
    def startLock(self):
        self.locked = True
        self.control_thread.setTarget(0.0)
        self.control_thread.startLock()
        self.jump_up_timer.start()

    ## stopLock
    #
    # Turn off the lock and recenter the piezo.
    #
    def stopLock(self):
        if self.locked:
            self.locked = False
            self.control_thread.stopLock()
            self.control_thread.recenter()


#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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
