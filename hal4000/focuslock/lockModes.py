#!/usr/bin/python
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

#
# Base Class
#
class LockMode(QtCore.QObject):
    def __init__(self, control_thread, parameters, parent):
        QtCore.QObject.__init__(self, parent)
        self.control_thread = control_thread
        self.locked = False
        self.name = "NA"

    def amLocked(self):
        return self.locked

    def getName(self):
        return self.name

    def handleJump(self, jumpsize):
        pass

    def lockButtonToggle(self):
        pass

    def newFrame(self, frame, offset, power, stage_z):
        pass

    def newParameters(self, parameters):
        pass

    def reset(self):
        pass

    def restartLock(self):
        pass

    def setLockTarget(self, target):
        pass

    def shouldDisplayLockButton(self):
        return False

    def shouldDisplayLockLabel(self):
        return self.amLocked()

    def startLock(self):
        pass

    def stopLock(self):
        pass


#
# Derived Class for handling locks, jumps and combinations thereof
#
class JumpLockMode(LockMode):
    def __init__(self, control_thread, parameters, parent):
        LockMode.__init__(self, control_thread, parameters, parent)
        self.relock_timer = QtCore.QTimer(self)
        self.relock_timer.setInterval(200)
        self.relock_timer.setSingleShot(True)
        self.connect(self.relock_timer, QtCore.SIGNAL("timeout()"), self.restartLock)

    def handleJump(self, jumpsize):
        if self.locked:
            self.control_thread.stopLock()
        self.control_thread.moveStageRel(jumpsize)
        if self.locked:
            self.relock_timer.start()

    def restartLock(self):
        self.control_thread.startLock()

    def setLockTarget(self, target):
        self.control_thread.setTarget(target)

#
# Modes are listed in the order in which they appear on
# the dialog box.
#

# No focus lock
class NoLockMode(LockMode):
    def __init__(self, control_thread, parameters, parent):
        LockMode.__init__(self, control_thread, parameters, parent)
        self.name = "Off"

    def handleJump(self, jumpsize):
        self.control_thread.moveStageRel(jumpsize)


# Auto lock mode - Lock will be on during filming
class AutoLockMode(JumpLockMode):
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.name = "Auto Lock"

    def startLock(self):
        self.control_thread.startLock()
        self.locked = True

    def stopLock(self):
        if self.locked:
            self.control_thread.stopLock()
            self.control_thread.recenter()
            self.locked = False


# Always on lock mode - Lock will start during filming, or when
#   the lock button is pressed (in which case it will always
#   stay on)
class AlwaysOnLockMode(JumpLockMode):
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.button_locked = False
        self.name = "Always On"

    def lockButtonToggle(self):
        if self.button_locked:
            self.button_locked = False
            self.stopLock()
        else:
            self.startLock()
            self.button_locked = True

    def newParameters(self, parameters):
        pass

    def reset(self):
        if self.button_locked:
            self.lockButtonToggle()

    def shouldDisplayLockButton(self):
        return True

    def startLock(self):
        if not self.locked:
            self.control_thread.startLock()
            self.locked = True

    def stopLock(self):
        if self.locked and (not self.button_locked):
            self.control_thread.stopLock()
            self.control_thread.recenter()
            self.locked = False


# Optimal lock mode - At the start of filming the stage is moved
#   in a triangle wave. First it goes up to bracket_step, then down
#   to -bracket_step and then finally back to zero. At each point
#   along the way the focus quality & offset are recorded. When the
#   stage returns to zero, the data is fit with a gaussian and the
#   lock target is set to the offset corresponding to the center
#   of the gaussian.
#
class OptimalLockMode(JumpLockMode):
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

    def getName(self):
        return "Optimal"

    def initScan(self):
        self.cur_z = 0.0
        self.mode = "Optimizing"
        self.scan_state = 1
        self.counter = 0
        size_guess = round(self.scan_hold * (self.bracket_step / self.scan_step) * 6)
        self.fvalues = numpy.zeros(size_guess)
        self.zvalues = numpy.zeros(size_guess)

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

    def newParameters(self, parameters):
        self.quality_threshold = parameters.olock_quality_threshold
        self.qpd_zcenter = parameters.qpd_zcenter
        self.bracket_step = 0.001 * parameters.olock_bracket_step
        self.scan_step = 0.001 * parameters.olock_scan_step
        self.scan_hold = parameters.olock_scan_hold

    def reset(self):
        if self.button_locked:
            self.lockButtonToggle()

    def shouldDisplayLockButton(self):
        return True

    def startLock(self):
        self.initScan()
        self.control_thread.setTarget(self.lock_target)
        self.control_thread.startLock()
        self.locked = True

    def stopLock(self):
        if self.locked:
            self.control_thread.setTarget(self.lock_target)
            if (not self.button_locked):
                self.locked = False
                self.control_thread.stopLock()
                self.control_thread.recenter()


# Calibration lock mode - No lock, the stage is driven through
#   a pre-determined set of z positions for calibration purposes
#   during filming.
class CalibrationLockMode(JumpLockMode):
    def __init__(self, control_thread, parameters, parent):
        JumpLockMode.__init__(self, control_thread, parameters, parent)
        self.counter = 0
        self.max_zvals = 0
        self.name = "Calibrate"
        self.zvals = []

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

    def newFrame(self, frame, offset, power, stage_z):
        if self.counter < self.max_zvals:
            self.control_thread.moveStageRel(self.zvals[self.counter])
            self.counter += 1

    def newParameters(self, parameters):
        #self.calibrationSetup(parameters.qpd_zcenter, 
        self.calibrationSetup(0.0, 
                              parameters.cal_deadtime, 
                              parameters.cal_range, 
                              parameters.cal_step_size, 
                              parameters.cal_frames_to_pause)

    def startLock(self):
        self.counter = 0

#    def stopLock(self):
#        self.control_thread.recenter()


# Z scan lock mode - The stage will move through a series of
#   positions as specified in the calibration file during
#   filming, locking is optional.
class ZScanLockMode(JumpLockMode):
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

    def newParameters(self, parameters):
        self.z_start = parameters.zscan_start
        self.z_step = parameters.zscan_step
        self.z_frames_to_pause = parameters.zscan_frames_to_pause
        self.z_stop = parameters.zscan_stop
        self.z_focus_lock = parameters.zscan_focus_lock

    def startLock(self):
        self.counter = 0
        self.current_z = self.z_start
        self.control_thread.moveStageAbs(self.z_start)
        if self.z_focus_lock:
            self.relock_timer.start()
            self.locked = True

    def stopLock(self):
        if self.z_focus_lock:
            self.control_thread.stopLock()
            self.relock_timer.stop()
            self.locked = False
        self.control_thread.recenter()

#
# For Shu & Graham.
#
# The stage will jump the distance specified with jump control.
# Every 600 frames it will jump back to the zero position, relock,
# and then jump back again. This gives you a focus lock that
# (sort of) works a large distance from a surface.
#
class LargeOffsetLock(JumpLockMode):
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

    def handleJump(self, jumpsize):
        self.jumpsize = jumpsize

    def jumpBackToTarget(self):
        if self.locked:
            self.control_thread.stopLock()
            self.control_thread.moveStageRel(self.jumpsize)

    def newFrame(self, frame, offset, power, stage_z):
        if ((frame.number != 0) and ((frame.number % self.frame_delay) == 0)):
            self.refindLock()

    def newParameters(self, parameters):
        if hasattr(parameters, "jump_down_delay"):
            self.jump_down_timer.setInterval(parameters.jump_down_delay)
        if hasattr(parameters, "frame_delay"):
            self.frame_delay = parameters.frame_delay
        if hasattr(parameters, "jump_up_delay"):
            self.jump_up_timer.setInterval(parameters.jump_up_delay)

    def refindLock(self):
        if self.locked:
            self.control_thread.moveStageRel(-self.jumpsize)
            self.jump_down_timer.start()
        
    def restartLock(self):
        if self.locked:
            self.control_thread.startLock()
            self.jump_up_timer.start()

    def startLock(self):
        self.locked = True
        self.control_thread.startLock()
        self.jump_up_timer.start()

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
