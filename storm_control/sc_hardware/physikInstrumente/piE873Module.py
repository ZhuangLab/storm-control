#!/usr/bin/env python
"""
HAL module for controlling a Pi controller.
Adapted from Hal module for a tiger controller by Hazen 05/18.

This module connects to a PI controller (model E873) which controls 3
translation stages (model Q545.140) that are assembled in a 3D stage configuration

Alistair 10/19
"""
import math
from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.sc_hardware.baseClasses.stageModule as stageModule
import storm_control.sc_hardware.baseClasses.stageZModule as stageZModule

import storm_control.sc_hardware.physikInstrumente.piE873 as piE873 # tiger

        
class PiStageFunctionality(stageModule.StageFunctionalityNF):
    """
    According to the documentation, 
    https://www.pi-usa.us/fileadmin/user_upload/pi_us/files/product_datasheets/Q-545_Mini_Positioning_Stage_201520192.pdf
    this stage has a maximum velocity of 10mm / second.
    """
    def __init__(self, velocity = None, **kwds):
        super().__init__(**kwds)
        self.max_velocity = 1.0e+3 * velocity # Maximum velocity in um/s (update this, tiger had max 7mm/s but had 1e3 here?)
        
        self.stage.setVelocity(velocity, velocity)

    def calculateMoveTime(self, dx, dy):
        time_estimate = math.sqrt(dx*dx + dy*dy)/self.max_velocity + 1.0
        #print("> stage move time estimate is {0:.3f} seconds".format(time_estimate))
        return time_estimate


class PiZStageFunctionality(stageZModule.ZStageFunctionalityBuffered):
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
        z_pos = -1.0*self.z_position + z_delta  # note move directions are reversed here 
        self.goAbsolute(z_pos)        

    def handleRestartTimer(self):
        self.update_timer.start()
        
    def handleUpdateTimer(self):
        self.mustRun(task = self.position,
                     ret_signal = self.zStagePosition)

    def position(self):
        self.z_position = self.z_stage.zPosition()["z"]
        return -1.0*self.z_position    # note move directions are reversed here 

    def zero(self):
        self.mustRun(task = self.z_stage.zZero)
        self.zStagePosition.emit(0.0)
    
    def zMoveTo(self, z_pos):
        return -1.0*super().zMoveTo(-z_pos)    # note move directions are reversed here 
    
        
#
# Inherit from stageModule.StageModule instead of the base class so we don't
# have to duplicate most of the stage stuff, particularly the TCP control.
#
class PiController(stageModule.StageModule):
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.controller_mutex = QtCore.QMutex() # a shared Mutex for both stages
        self.functionalities = {} # a list of the functionalities 
        configuration = module_params.get("configuration") # get the config parameters from the xml file under <PiController>
        self.controller = piE873.piE873(serialnum = configuration.get("serialnum")) # connect to the controller 
        
        if self.controller.getStatus():
            # Note: We are not checking whether the devices that the user requested
            #       are actually available, we're just assuming that they know what
            #       they are doing.
            #
            devices = configuration.get("devices") 
            """
            devices reads from the configuration properties in the xml for <PiController>
            Example configuration: 
            <configuration>
                <serialnum type="int">0118048626</serialnum>
                <devices>
                  <xy_stage>
                    <velocity type="float">10.0</velocity>
                  </xy_stage>
                  <z_stage>
                    <center type="float">0.0</center>
                    <has_center_bar type="boolean">True</has_center_bar>
                    <maximum type="float">10.0</maximum>
                    <minimum type="float">-10.0</minimum>
                    <warning_high type="float">9.0</warning_high>
                    <warning_low type="float">-9.0</warning_low>	    
                  </z_stage>
                </devices>
            </configuration>
            
            """
            for dev_name in devices.getAttrs():
                # XY stage.
                if (dev_name == "xy_stage"):
                    settings = devices.get(dev_name)
                    # We do this so that the superclass works correctly."
                    self.stage = self.controller
                    self.stage_functionality = PiStageFunctionality(device_mutex = self.controller_mutex,
                                                                    stage = self.stage,
                                                                    update_interval = 500,
                                                                    velocity = settings.get("velocity", 10))
                    self.functionalities[self.module_name + "." + dev_name] = self.stage_functionality
                # Z stage
                elif (dev_name == "z_stage"):
                    settings = devices.get(dev_name)
                    z_stage_fn = PiZStageFunctionality(device_mutex = self.controller_mutex,
                                                       parameters = settings,
                                                       update_interval = 500,
                                                       velocity = settings.get("velocity", 10),
                                                       z_stage = self.controller)
                    self.functionalities[self.module_name + "." + dev_name] = z_stage_fn

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
