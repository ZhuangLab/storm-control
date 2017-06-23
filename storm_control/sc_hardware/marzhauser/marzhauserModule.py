#!/usr/bin/env python
"""
HAL module for controlling a Marzhauser stage.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.marzhauser.marzhauser as marzhauser


class MarzhauserStageFunctionality(stageModule.StageFunctionality):

    def __init__(self, update_interval = None, **kwds):
        super().__init__(**kwds)

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

    def handleUpdateTimer(self):
        """
        Query the stage for its current position.
        """
        self.mustRun(task = self.stage.position)
        #pass

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
        

class MarzhauserStage(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        self.stage = marzhauser.MarzhauserRS232(baudrate = configuration.get("baudrate"),
                                                port = configuration.get("port"))
        if self.stage.getStatus():

            # Set (maximum) stage velocity.
            velocity = configuration.get("velocity")
            self.stage.setVelocity(velocity, velocity)
            self.stage_functionality = MarzhauserStageFunctionality(stage = self.stage,
                                                                    update_interval = 500)

        else:
            self.stage = None
