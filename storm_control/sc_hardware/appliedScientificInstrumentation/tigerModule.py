#!/usr/bin/env python
"""
HAL module for controlling a Tiger controller.

Hazen 05/18
"""
import math
from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.baseClasses.stageModule as stageModule

import storm_control.sc_hardware.appliedScientificInstrumentation.tiger as tiger


class TigerLEDFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):
    def __init__(self, address = None, channel = None, led = None, **kwds):
        super().__init__(**kwds)
        self.address = address
        self.channel = channel
        self.led = led
        self.on = False

    def onOff(self, power, state):
        self.mustRun(task = self.led.setLED,
                     args = [self.address, self.channel, power])
        self.on = state
    
    def output(self, power):
        if self.on:
            self.maybeRun(task = self.led.setLED,
                          args = [self.address, self.channel, power])

        
class TigerStageFunctionality(stageModule.StageFunctionalityNF):
    """
    According to the documentation, this stage has a maximum velocity of 7.5mm / second.
    """
    def __init__(self, velocity = None, **kwds):
        super().__init__(**kwds)
        self.max_velocity = 1.0e+3 * velocity # Maximum velocity in um/s
        
        self.stage.setVelocity(velocity, velocity)

    def calculateMoveTime(self, dx, dy):
        time_estimate = math.sqrt(dx*dx + dy*dy)/self.max_velocity + 1.0
        print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate


#
# Inherit from stageModule.StageModule instead of the base class so we don't
# have to duplicate most of the stage stuff, particularly the TCP control.
#
class TigerController(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.controller_mutex = QtCore.QMutex()
        self.functionalities = {}

        configuration = module_params.get("configuration")
        self.controller = tiger.Tiger(baudrate = configuration.get("baudrate"),
                                      port = configuration.get("port"))
        
        if self.controller.getStatus():

            # Note: We are not checking whether the devices that the user requested
            #       are actually available, we're just assuming that they know what
            #       they are doing.
            #
            devices = configuration.get("devices")
            for dev_name in devices.getAttrs():

                # XY stage.
                if (dev_name == "xy_stage"):
                    settings = devices.get(dev_name)

                    # We do this so that the superclass works correctly."
                    self.stage = self.controller

                    self.stage_functionality = TigerStageFunctionality(device_mutex = self.controller_mutex,
                                                                       stage = self.stage,
                                                                       update_interval = 500,
                                                                       velocity = settings.get("velocity", 7.5))
                    self.functionalities[self.module_name + "." + dev_name] = self.stage_functionality

                elif (dev_name.startswith("led")):
                    settings = devices.get(dev_name)
                    led_fn = TigerLEDFunctionality(address = settings.get("address"),
                                                   channel = settings.get("channel"),
                                                   device_mutex = self.controller_mutex,
                                                   maximum = 100,
                                                   led = self.controller)
                    self.functionalities[self.module_name + "." + dev_name] = led_fn

                else:
                    raise halExceptions.HardwareException("Unknown device " + str(dev_name))

        else:
            self.controller = None
    
    def cleanUp(self, qt_settings):
        if self.controller is not None:
            for fn in self.functionalities.values():
                if hasattr(fn, "wait"):
                    fn.wait()
            self.controller.shutDown()

    def getFunctionality(self, message):
        if message.getData()["name"] in self.functionalities:
            fn = self.functionalities[message.getData()["name"]]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : fn}))

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
