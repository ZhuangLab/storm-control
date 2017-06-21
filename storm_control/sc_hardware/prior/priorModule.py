#!/usr/bin/env python
"""
HAL module for controlling a Prior stage and/or other
accessories that are connected to the Prior controller.

Hazen 06/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.filterWheelModule as filterWheelModule
import storm_control.sc_hardware.baseClasses.stageModule as stageModule

import storm_control.sc_hardware.prior.prior as prior


#
# The filter wheel is 1 indexed, but HAL expects zero indexing.
#
class PriorFilterWheelFunctionality(filterWheelModule.FilterWheelFunctionalityBuffered):

    def __init__(self, prior_controller = None, wheel_number = None, **kwds):
        super().__init__(**kwds)
        self.prior_controller = prior_controller
        self.wheel_number = wheel_number

        self.current_position = self.prior_controller.getFilter(self.wheel_number) - 1

    def setCurrentPosition(self, position):
        self.maybeRun(task = self.prior_controller.changeFilter,
                      args = [self.wheel_number, position + 1])
        self.current_position = position


#
# Inherit from stageModule.StageModule instead of the base class so we don't
# have to duplicate most of the stage stuff, particularly the TCP control.
#
class PriorController(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.controller_mutex = QtCore.QMutex()
        self.focus_functionality = None
        self.fwheel1_functionality = None
        self.fwheel2_functionality = None

        configuration = module_params.get("configuration")
        self.controller = prior.Prior(baudrate = configuration.get("baudrate"),
                                      port = configuration.get("port"))
        
        if self.controller.getStatus():

            # Do have an actual XY stage connected?
            if self.controller.hasDevice("stage"):
                # If we do, set the (maximum) stage velocity.
                velocity = configuration.get("velocity")
                self.stage.setVelocity(velocity, velocity)
                #self.stage_functionality = MarzhauserStageFunctionality(stage = self.stage,
                #                                                        update_interval = 500)

            # Do we have filter wheel 1?
            if self.controller.hasDevice("filter_1"):
                self.fwheel1_functionality = PriorFilterWheelFunctionality(device_mutex = self.controller_mutex,
                                                                           maximum = configuration.get("filter_wheel1.maximum"),
                                                                           prior_controller = self.controller,
                                                                           wheel_number = 1)

            # Do we have filter wheel 2?
            if self.controller.hasDevice("filter_2"):
                self.fwheel1_functionality = PriorFilterWheelFunctionality(device_mutex = self.controller_mutex,
                                                                           maximum = configuration.get("filter_wheel2.maximum"),
                                                                           prior_controller = self.controller,
                                                                           wheel_number = 2)
    
    def cleanUp(self, qt_settings):
        if self.controller is not None:
            if self.stage_functionality is not None:
                self.stage_functionality.wait()
            self.controller.shutDown()

    def getFunctionality(self, message):
        if (message.getData()["name"] == self.module_name + ".stage"):
            if self.stage_functionality is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.stage_functionality}))
                
        elif (message.getData()["name"] == self.module_name + ".focus"):
            if self.focus_functionality is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.focus_functionality}))
                
        elif (message.getData()["name"] == self.module_name + ".filter_wheel1"):
            if self.fwheel1_functionality is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.fwheel1_functionality}))
                
        elif (message.getData()["name"] == self.module_name + ".filter_wheel2"):
            if self.fwheel2_functionality is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.fwheel2_functionality}))                

    def processMessage(self, message):
        if message.isType("get functionality"):
            self.getFunctionality(message)

        #
        # The rest of the message are only relevant if we actually have a XY stage.
        #
        if self.stage_functionality is None:
            return

        if message.isType("configuration"):
            if message.sourceIs("tcp_control"):
                self.tcpConnection(message.getData()["properties"]["connected"])

            elif message.sourceIs("mosaic"):
                self.pixelSize(message.getData()["properties"]["pixel_size"])

        elif message.isType("start film"):
            self.startFilm(message)

        elif message.isType("stop film"):
            self.stopFilm(message)

        elif message.isType("tcp message"):
            self.tcpMessage(message)
