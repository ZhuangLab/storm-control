#!/usr/bin/env python
"""
Base class / functionality for controlling a motorized stage.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_library.parameters as params


class StageFunctionality(hardwareModule.BufferedFunctionality):
    isMoving = QtCore.pyqtSignal(bool)
    stagePosition = QtCore.pyqtSignal(dict)

    def __init__(self, stage = None, is_slow = False, **kwds):
        """
        stage - A hardware object that behaves like a stage.

        is_slow - Some stages are particularly slow, they only run at 9600 baud
                  for example. In that case it is probably best not to try and
                  use them for things like screen drag based movement.
        """
        super().__init__(**kwds)
        self.drag_start_x = None
        self.drag_start_y = None
        self.is_slow = is_slow
        self.pixels_to_microns = 1.0
        self.pos_dict = None
        self.stage = stage

    def dragMove(self, x, y):
        """
        Usually used by display.display, units are pixels.
        """
        x = x * self.pixels_to_microns + self.drag_start_x
        y = y * self.pixels_to_microns + self.drag_start_y
        self.maybeRun(task = self.stage.goAbsolute,
                      args = [x, y])

    def dragStart(self):
        #
        # This will not work well if the stage does not know it's
        # current position..
        #
        if self.pos_dict is not None:
            self.drag_start_x = self.pos_dict["x"]
            self.drag_start_y = self.pos_dict["y"]
        else:
            self.drag_start_x = 0
            self.drag_start_y = 0
            
    def getCurrentPosition(self):
        return self.pos_dict

    def goAbsolute(self, x, y):
        """
        Usually used by the stage GUI, units are microns.
        """
        self.mustRun(task = self.stage.goAbsolute,
                     args = [x, y])
    
    def goRelative(self, dx, dy):
        """
        Usually used by the stage GUI, units are microns.
        """
        self.maybeRun(task = self.stage.goRelative,
                      args = [dx, dy])

    def isSlow(self):
        return self.is_slow
        
    def jog(self, x_speed, y_speed):
        """
        Usually used by the joystick to tell the stage to move at
        a certain velocity, nominally in pixels per second.
        """
        xs = x_speed * self.pixels_to_microns
        ys = y_speed * self.pixels_to_microns
        self.maybeRun(task = self.stage.jog,
                      args = [xs, ys])

    def setPixelsToMicrons(self, pixels_to_microns):
        self.pixels_to_microns = pixels_to_microns

    def zero(self):
        self.mustRun(task = self.stage.zero)


class StageFunctionalityNF(StageFunctionality):
    """
    Use this base class for stages that do not provide any feedback about
    whether or not they are moving. These are stages where you have to 
    keep polling them to find out what they are doing. This is often
    suboptimal during automated imaging when you want a fast response,
    of we instead calculate how long it will take the stage to move and
    use a timer.

    Subclasses must provide the calculateMoveTime() method which
    calculates how long (in seconds) it will take the stage to perform
    the requested move.
    """
    positionUpdate = QtCore.pyqtSignal(dict)

    def __init__(self, update_interval = None, **kwds):
        super().__init__(**kwds)
        self.am_moving = False
        self.pos_dict = self.stage.position()

        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(update_interval)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        self.update_timer.start()

        # Moving timer for absolute moves.
        self.moving_timer = QtCore.QTimer()
        self.moving_timer.setSingleShot(True)
        self.moving_timer.timeout.connect(self.handleMovingTimer)

        # We need a 'relay' signal because when self.position() is called
        # in the context of a HardwareWorker it will have stale information,
        # in particular it might think the stage is not moving when it
        # actually is. If the stage is moving we don't want to return
        # whatever position the stage thinks it is at as this will likely
        # be wrong.
        self.positionUpdate.connect(self.handlePositionUpdate)

    def goAbsolute(self, x, y):
        # Notify that the stage is moving.
        self.am_moving = True
        self.isMoving.emit(True)

        # Stop the position update timer. Note that this alone is not
        # sufficient to stop stale stage position information. This
        # timer might have gone off just before self.goAbsolute() was
        # called so there could be a position request queued up in
        # the BufferedFunctionality().
        #
        self.update_timer.stop()
        
        # Tell the stage to move.
        super().goAbsolute(x, y)

        # Figure out how far we have to move in microns and get
        # the stages estimate of how long this will take.
        dx = x - self.pos_dict["x"]
        dy = y - self.pos_dict["y"]
        time_estimate = self.calculateMoveTime(dx, dy)

        # Set interval and start the timer.
        self.moving_timer.setInterval(time_estimate * 1.0e+3)
        self.moving_timer.start()

        # Pretend we already got there..
        self.pos_dict["x"] = x
        self.pos_dict["y"] = y
        self.stagePosition.emit(self.pos_dict)
        
    def handleMovingTimer(self):
        self.isMoving.emit(False)
        self.am_moving = False
        
        # Restart the position update timer.
        self.update_timer.start()

    def handlePositionUpdate(self, pos_dict):
        # Only update and pass on the current stage position if we
        # are not in the middle of a move.
        if not self.am_moving:
            self.pos_dict = pos_dict
            self.stagePosition.emit(self.pos_dict)
            
    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.position,
                     ret_signal = self.positionUpdate)

    def position(self):
        return self.stage.position()
        
    def wait(self):
        self.update_timer.stop()
        super().wait()
        

class StageModule(hardwareModule.HardwareModule):
    """
    Provides a stage functionality whose name is just the module name.

    Some stage controllers can also control additional peripherals.
    Functionalities for these will have names like 'module_name.peripheral'.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.stage = None
        self.stage_functionality = None

        #
        # This is the default timeout for TCP requested moves. If the stage
        # does not respond that the move has completed in this time then we
        # are just going to assume that we missed something.
        #
        self.watchdog_timeout = 10000

    def cleanUp(self, qt_settings):
        if self.stage is not None:
            self.stage_functionality.wait()
            self.stage.shutDown()

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : self.stage_functionality}))

    def pixelSize(self, pixel_size):
        self.stage_functionality.setPixelsToMicrons(pixel_size)

    def processMessage(self, message):
        if self.stage is None:
            return

        if message.isType("configuration"):
            if message.sourceIs("tcp_control"):
                self.tcpConnection(message.getData()["properties"]["connected"])

            elif message.sourceIs("mosaic"):
                self.pixelSize(message.getData()["properties"]["pixel_size"])

        elif message.isType("get functionality"):
            self.getFunctionality(message)
            
        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

        elif message.isType("tcp message"):
            self.tcpMessage(message)

    def startFilm(self, message):
        self.stage_functionality.mustRun(task = self.stage.joystickOnOff,
                                         args = [False])

    def stopFilm(self, message):
        self.stage_functionality.mustRun(task = self.stage.joystickOnOff,
                                         args = [True])
        pos_dict = self.stage_functionality.getCurrentPosition()
        pos_string = "{0:.2f},{1:.2f}".format(pos_dict["x"], pos_dict["y"])
        pos_param = params.ParameterCustom(name = "stage_position",
                                           value = pos_string)
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"acquisition" : [pos_param]}))

    def tcpConnection(self, connected):
        pass
    
    def tcpMessage(self, message):
        tcp_message = message.getData()["tcp message"]
        if tcp_message.isType("Move Stage"):
            if tcp_message.isTest():
                tcp_message.addResponse("duration", 1)
            else:
                #
                # We don't want HAL to finalize this message until
                # the stage has finished the move.
                #
                message.incRefCount()

                #
                # Create a TCPMoveHandler object. This object will store the message until
                # the stage sends a signal that it is no longer moving.
                #
                tcp_move_handler = TCPMoveHandler(hal_message = message,
                                                  stage_functionality = self.stage_functionality,
                                                  watchdog_timeout = self.watchdog_timeout)
                self.stage_functionality.isMoving.connect(tcp_move_handler.handleIsMoving)

                #
                # Tell the stage to move.
                #
                self.stage_functionality.goAbsolute(tcp_message.getData("stage_x"),
                                                    tcp_message.getData("stage_y"))
                #
                # FIXME: After the move we need some way to gaurantee that the stage
                #        reports it's current position, which is hopefully where it
                #        was told to go, and not some stale position. This will be a
                #        problem if the movies are so short that the stages updateTimer()
                #        does not get a chance to go off before we finish taking the
                #        film. However, maybe we don't want to wait the X milliseconds
                #        it would take the stage to update? For TCP moves just return
                #        the position where the stage should be?
                #
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"handled" : True}))

        elif tcp_message.isType("Get Stage Position"):
            if not tcp_message.isTest():
                pos_dict = self.stage_functionality.getCurrentPosition()
                tcp_message.addResponse("stage_x", pos_dict["x"])
                tcp_message.addResponse("stage_y", pos_dict["y"])
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"handled" : True}))


class TCPMoveHandler(QtCore.QObject):

    def __init__(self,
                 hal_message = None,
                 stage_functionality = None,
                 watchdog_timeout = None,
                 **kwds):
        super().__init__(**kwds)
        self.hal_message = hal_message
        self.stage_functionality = stage_functionality

        #
        # Set watch dog timer to fire in X milli-seconds. If this goes off we're
        # just going to assume that the stage has completed it's motion.
        #

        if watchdog_timeout is None:
            print("Error detected in TCPMoveHandler")

        # Heh, this assertion is useless since it happens inside a thread?
        assert watchdog_timeout is not None
                
        self.watchdog_timer = QtCore.QTimer(self)
        self.watchdog_timer.timeout.connect(self.handleWatchdogTimer)
        self.watchdog_timer.setSingleShot(True)
        self.watchdog_timer.start(watchdog_timeout)

        # Add this object as a tag on the message so that it won't get deleted
        # by the garbage collector.
        self.hal_message.tcp_move_handler = self

    def handleIsMoving(self, is_moving):
        #
        # If the stage has stopped moving, decrement the HAL message
        # ref count so that message will get finalized.
        #
        if not is_moving:
            self.hal_message.decRefCount()
            self.stage_functionality.isMoving.disconnect(self.handleIsMoving)

            # Delete the reference to this object so that it will get deleted
            # by the garbage collector.
            self.hal_message.tcp_move_handler = None

    def handleWatchdogTimer(self):
        print("> stage move request timed out")
        #
        # If land here, then we're assuming the stage finished the move
        # but we missed this for some reason.
        #
        self.hal_message.decRefCount()
        self.stage_functionality.isMoving.disconnect(self.handleIsMoving)

        # Delete the reference to this object so that it will get deleted
        # by the garbage collector.
        self.hal_message.tcp_move_handler = None
        
