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
import storm_control.sc_hardware.baseClasses.stageZModule as stageZModule
import storm_control.sc_hardware.baseClasses.voltageZModule as voltageZModule

import storm_control.sc_hardware.appliedScientificInstrumentation.tiger as tiger


class TigerLEDFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):
    def __init__(self, address = None, channel = None, ttl_mode = None, led = None, **kwds):
        """
        ttl_mode is the TTL control mode to use when filming. Usually this is mode 22, which
        requires firmware 3.30 and above. Note also that due to how this mode is implemented
        the power will only get updated when the shutter line goes high, so for always on you
        should include short pulses so that the power updates.
        """
        super().__init__(**kwds)
        self.address = address
        self.channel = channel
        self.led = led
        self.on = False
        self.ttl_mode = ttl_mode

        # Make sure we are mode 0.
        self.mustRun(task = self.led.setTTLMode,
                     args = [self.address, 0])

    def onOff(self, power, state):
        self.mustRun(task = self.led.setLED,
                     args = [self.address, self.channel, power])
        self.on = state
    
    def output(self, power):
        if self.on:
            self.maybeRun(task = self.led.setLED,
                          args = [self.address, self.channel, power])

    def setFilmTTLMode(self, filming):
        if (self.ttl_mode > 0):
            if filming:
                self.mustRun(task = self.led.setTTLMode,
                             args = [self.address, self.ttl_mode])
            else:
                self.mustRun(task = self.led.setTTLMode,
                             args = [self.address, 0])


class TigerStageFunctionality(stageModule.StageFunctionalityNF):
    """
    According to the documentation, this stage has a maximum velocity of 7.5mm / second.
    """
    def __init__(self, velocity = None, **kwds):
        super().__init__(**kwds)
        self.max_velocity = 1.0e+3 * velocity # Maximum velocity in um/s

        self.mustRun(task = self.stage.setVelocity,
                     args = [velocity, velocity])
        
#        self.stage.setVelocity(velocity, velocity)

    def calculateMoveTime(self, dx, dy):
        time_estimate = math.sqrt(dx*dx + dy*dy)/self.max_velocity + 1.0
        #print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate


class TigerVoltageZFunctionality(voltageZModule.VoltageZFunctionality):
    """
    External voltage control of piezo Z stage.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
    
class TigerZStageFunctionality(stageZModule.ZStageFunctionalityBuffered):
    """
    The z sign convention of this stage is the opposite from the expected
    so we have to adjust.
    """
    def __init__(self, update_interval = None, velocity = None, **kwds):
        super().__init__(**kwds)

        self.maximum = self.getParameter("maximum")
        self.minimum = self.getParameter("minimum")

        # Set initial z velocity.
        self.mustRun(task = self.z_stage.zSetVelocity,
                     args = [velocity])
        
        # This timer to restarts the update timer after a move. It appears
        # that if you query the position during a move the stage will stop
        # moving.
        self.restart_timer = QtCore.QTimer()
        self.restart_timer.setInterval(2000)
        self.restart_timer.timeout.connect(self.handleRestartTimer)
        self.restart_timer.setSingleShot(True)

        # Each time this timer fires we'll query the z stage position. We need
        # to do this as the user might use the controller to directly change
        # the stage z position.
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(update_interval)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        self.update_timer.start()
        
    def goAbsolute(self, z_pos):
        # We have to stop the update timer because if it goes off during the
        # move it will stop the move.
        self.update_timer.stop()
        super().goAbsolute(z_pos)
        self.restart_timer.start()

    def goRelative(self, z_delta):
        z_pos = -1.0*self.z_position + z_delta
        self.goAbsolute(z_pos)        

    def handleRestartTimer(self):
        self.update_timer.start()
        
    def handleUpdateTimer(self):
        self.mustRun(task = self.position,
                     ret_signal = self.zStagePosition)

    def position(self):
        self.z_position = self.z_stage.zPosition()["z"]
        return -1.0*self.z_position

    def zero(self):
        self.mustRun(task = self.z_stage.zZero)
        self.zStagePosition.emit(0.0)
    
    def zMoveTo(self, z_pos):
        return -1.0*super().zMoveTo(-z_pos)
    
        
#
# Inherit from stageModule.StageModule instead of the base class so we don't
# have to duplicate most of the stage stuff, particularly the TCP control.
#
class TigerController(stageModule.StageModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.controller_mutex = QtCore.QMutex()
        self.functionalities = {}

        # These are used for the Z piezo stage.
        self.z_piezo_configuration = None
        self.z_piezo_functionality = None

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

                elif (dev_name == "z_piezo"):
                    self.z_piezo_configuration = devices.get(dev_name)

                elif (dev_name == "z_stage"):
                    settings = devices.get(dev_name)
                    z_stage_fn = TigerZStageFunctionality(device_mutex = self.controller_mutex,
                                                          parameters = settings,
                                                          update_interval = 500,
                                                          velocity = settings.get("velocity", 1.0),
                                                          z_stage = self.controller)
                    self.functionalities[self.module_name + "." + dev_name] = z_stage_fn

                elif (dev_name.startswith("led")):
                    settings = devices.get(dev_name)
                    led_fn = TigerLEDFunctionality(address = settings.get("address"),
                                                   channel = settings.get("channel"),
                                                   device_mutex = self.controller_mutex,
                                                   maximum = 100,
                                                   ttl_mode = configuration.get("ttl_mode", -1),
                                                   led = self.controller)
                    self.functionalities[self.module_name + "." + dev_name] = led_fn

                else:
                    raise halExceptions.HardwareException("Unknown device " + str(dev_name))

        else:
            self.controller = None
    
    def cleanUp(self, qt_settings):
        if self.controller is not None:
            if self.z_piezo_functionality is not None:
                self.z_piezo_functionality.goAbsolute(
                    self.z_piezo_functionality.getMinimum())
            
            for fn in self.functionalities.values():
                if hasattr(fn, "wait"):
                    fn.wait()
            self.controller.shutDown()

    def getFunctionality(self, message):
        if message.getData()["name"] in self.functionalities:
            fn = self.functionalities[message.getData()["name"]]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"functionality" : fn}))

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            if (message.getData()["extra data"] == "z_piezo"):
                self.z_piezo_functionality = TigerVoltageZFunctionality(
                    ao_fn = response.getData()["functionality"],
                    parameters = self.z_piezo_configuration.get("parameters"),
                    microns_to_volts = self.z_piezo_configuration.get("microns_to_volts"))
                
                # Configure controller for voltage Z control.
                self.controller_mutex.lock()
                axis = self.z_piezo_configuration.get("axis")
                mode = self.z_piezo_configuration.get("mode")
                self.controller.zConfigurePiezo(axis, mode)
                self.controller_mutex.unlock()
        
                # Add to dictionary of available functionalities.
                self.functionalities[self.module_name + ".z_piezo"] = self.z_piezo_functionality
            
    def processMessage(self, message):
        if message.isType("configure1"):
            if self.z_piezo_configuration is not None:
                self.sendMessage(halMessage.HalMessage(
                    m_type = "get functionality",
                    data = {"name" : self.z_piezo_configuration.get("ao_fn_name"),
                            "extra data" : "z_piezo"}))
            
        elif message.isType("get functionality"):
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

    def startFilm(self, message):
        super().startFilm(message)
        if (message.getData()["film settings"].runShutters()):        
            for fn_name in self.functionalities:
                if ("led" in fn_name):
                    self.functionalities[fn_name].setFilmTTLMode(True)
                    break

    def stopFilm(self, message):
        super().stopFilm(message)
        for fn_name in self.functionalities:
            if ("led" in fn_name):
                self.functionalities[fn_name].setFilmTTLMode(False)
                break

