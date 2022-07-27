#!/usr/bin/env python
"""
HAL module for controlling a Marzhauser stage.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.marzhauser.marzhauser as marzhauser

import math
import time

class MarzhauserStageFunctionality(stageModule.StageFunctionality):
    """
    These stages are nice because they respond quickly to commands
    and they also provide feedback about whether or not they are
    moving.
    """
    def __init__(self, update_interval = None, **kwds):
        super().__init__(**kwds)
        self.querying = False

        # Each time this timer fires we'll 'query' the stage for it's
        # current position.
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(update_interval)
        self.updateTimer.timeout.connect(self.handleUpdateTimer)
        self.updateTimer.start()

        # Connect to our own stagePosition signal in order to store
        # the current position.
        self.stagePosition.connect(self.handleStagePosition)
        
        # This thread will poll the serial port for responses from
        # the stage to the commands we're sending.
        self.polling_thread = MarzhauserPollingThread(device_mutex = self.device_mutex,
                                                      is_moving_signal = self.isMoving,
                                                      sleep_time = 100,
                                                      stage = self.stage,
                                                      stage_position_signal = self.stagePosition)
        self.polling_thread.startPolling()

    def handleStagePosition(self, pos_dict):
        self.pos_dict = pos_dict
        self.querying = False

    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        #
        # The purpose of the self.querying flag is to prevent build up of
        # position update requests. If there is already one in process there
        # is no point in starting another one.
        #
        if not self.querying:
            self.querying = True
            self.mustRun(task = self.stage.position)

    def wait(self):
        self.updateTimer.stop()
        self.polling_thread.stopPolling()
        super().wait()


class MarzhauserPollingThread(QtCore.QThread):
    """
    Handles polling the Marzhauser stage for responses to 
    serial commands.
    """
    def __init__(self,
                 device_mutex = None,
                 is_moving_signal = None,
                 sleep_time = None,
                 stage = None,
                 stage_position_signal = None,
                 **kwds):
        super().__init__(**kwds)
        self.device_mutex = device_mutex
        self.is_moving_signal = is_moving_signal
        self.sleep_time = sleep_time         
        self.stage = stage
        self.stage_position_signal = stage_position_signal

    def run(self):
        self.running = True
        while(self.running):
            self.device_mutex.lock()
            responses = self.stage.readline()
            self.device_mutex.unlock()
            
            # Parse response. The expectation is that it is one of two things:
            #
            # (1) A status string like "#@--" that indicates that the stage
            #     is or is not moving (statusaxis).
            #
            # (2) The current position "X.XX Y.YY ..".
            #

            for resp in responses.split("\r"):

                # The response was no response.
                if (len(resp) == 0):
                    continue
                
                # Check for 'statusaxis' response form.
                elif (len(resp) == 5):
                    if (resp[:2] == "@@"):
                        self.is_moving_signal.emit(False)
                    else:
                        self.is_moving_signal.emit(True)

                # Otherwise try and parse as a position.
                else:
                    resp = resp.split(" ")
                    if (len(resp) >= 2):
                        are_floats = True
                        try:
                            [sx, sy] = map(float, resp[:2])
                        except ValueError:
                            are_floats = False
                        if are_floats:
                            self.stage_position_signal.emit({"x" : sx * self.stage.unit_to_um,
                                                             "y" : sy * self.stage.unit_to_um})

            # Sleep for ~ x milliseconds.
            self.msleep(self.sleep_time)

    def startPolling(self):
        self.start(QtCore.QThread.NormalPriority)

    def stopPolling(self):
        self.running = False
        self.wait()
   
class MarzhauserStageFunctionalityNF(stageModule.StageFunctionalityNF):
    """
    Make a class where polling behavior is turned off for the Marzhauser stage
    This is to limit polling in case of a COM port problem
    Use the StageModule.StageFunctionalityNF but turn off the position timer
    """           
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.getInitialPosition()

    def calculateMoveTime(self, dx, dy):
        # FIXME: These are just the values from the LUDL stage.
        time_estimate = math.sqrt(dx*dx + dy*dy)/10000.0 + 1.0
        #print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate   
    
    def position(self):
        """
        for non position polling marzhauser, just return the position dictionary
        """
        return self.pos_dict
    
    def getInitialPosition(self):
        """
        For non polling marzhauser implementation 
        Call at startup to get the initial pos_dict
        This may not be the most robust way of doing it
        """
        for i in range(3): # First clear the read buffer
            self.stage.readline()
            time.sleep(0.1)
        self.stage.position() # send the position command
        time.sleep(0.1)
        pos = list(map(float,self.stage.readline().split(' '))) # read and parse the position
        self.pos_dict = {}
        self.pos_dict["x"] = pos[0] # lets hope their are only two return values and they came back in x,y order
        self.pos_dict["y"] = pos[1]
        
    def goRelative(self, dx, dy):
        """
        Usually used by the stage GUI, units are microns.
        """
        self.maybeRun(task = self.stage.goRelative,
                      args = [dx, dy])
                      
        # Pretend we already got there..
        # Update the pos_dict in case the user is using the stage GUI
        self.pos_dict["x"] = self.pos_dict["x"] - dx
        self.pos_dict["y"] = self.pos_dict["y"] - dy
        
    def zero(self):
        self.mustRun(task = self.stage.zero)
        self.pos_dict["x"] = 0
        self.pos_dict["y"] = 0

class MarzhauserStage(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        polling = configuration.get("polling", default = True)
        
        self.stage = marzhauser.MarzhauserRS232(baudrate = configuration.get("baudrate"),
                                                port = configuration.get("port"))
        if self.stage.getStatus():
            # Set (maximum) stage velocity.
            velocity = configuration.get("velocity")
            self.stage.setVelocity(velocity, velocity)

            if polling:
                print('\tstage polling is on')
                self.stage_functionality = MarzhauserStageFunctionality(device_mutex = QtCore.QMutex(),
                                                                        stage = self.stage,
                                                                        update_interval = 500)
            else:
                print('\tstage polling is off')
                self.stage_functionality = MarzhauserStageFunctionalityNF(device_mutex = QtCore.QMutex(),
                                                                        stage = self.stage,
                                                                        update_interval = 500)

            # Allow to enable or disable joystick from the configuration file
            joystick = configuration.get("joystick", default = True)
            self.stage.joystickOnOff(joystick)

        else:
            self.stage = None
