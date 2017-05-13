#!/usr/bin/env python
"""
HAL module for Coherent laser control.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.amplitudeModule as amplitudeModule
import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class CoherentLaserFunctionality(amplitudeModule.AmplitudeFunctionalityBuffered):
    """
    Users specify the laser power in units of 0.01mW. For example output(100) 
    will set the laser to output 1mW.
    """
    def __init__(self, laser = None, **kwds):
        super().__init__(**kwds)
        self.on = False
        self.laser = laser

    def onOff(self, power, state):
        # FIXME: We could build up a back-log here if the user
        #        gets carried away toggling the shutter button.
        self.mustRun(task = self.laser.setPower,
                     args = [0.01 * power])
        self.on = state

    def output(self, power):
        if self.on:
            self.maybeRun(task = self.laser.setPower,
                          args = [0.01 * power])

    
class CoherentModule(amplitudeModule.AmplitudeModule):
    """
    The functionality name is just the module name.
    """    
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.film_mode = False
        self.laser = None
        self.laser_functionality = None

        configuration = module_params.get("configuration")
        self.used_during_filming = configuration.get("used_during_filming")

    def cleanUp(self, qt_settings):
        if self.laser_functionality is not None:
            self.laser.shutDown()

    def getFunctionality(self, message):
       if (message.getData()["name"] == self.module_name) and (self.laser_functionality is not None):
           message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                             data = {"functionality" : self.laser_functionality}))

    def setExtControl(self, state):
        self.device_mutex.lock()
        self.laser.setExtControl(state)
        self.device_mutex.unlock()
                
    def startFilm(self, message):
        if message.getData()["film settings"].runShutters():
            if self.used_during_filming and (self.laser_functionality is not None):
                hardwareModule.runHardwareTask(self,
                                               message,
                                               lambda : self.setExtControl(True))
                self.film_mode = True

    def stopFilm(self, message):
        if self.film_mode:
            hardwareModule.runHardwareTask(self,
                                           message,
                                           lambda : self.setExtControl(True))
            self.film_mode = False


class CoherentCube(CoherentModule):
    
    def __init__(self, module_params = None, **kwds):
        kwds["module_params"] = module_params
        super().__init__(**kwds)

        serial_port = module_params.get("configuration").get("port")

        import storm_control.sc_hardware.coherent.cube as cube
        self.laser = cube.Cube(port = serial_port)

        if self.laser.getStatus():
            [pmin, pmax] = self.laser.getPowerRange()
            self.laser_functionality = CoherentLaserFunctionality(device_mutex = self.device_mutex,
                                                                  display_normalized = True,
                                                                  laser = self.laser,
                                                                  minimum = 0,
                                                                  maximum = int(100.0 * pmax),
                                                                  used_during_filming = self.used_during_filming)
        else:
            self.laser = None


class CoherentObis(CoherentModule):
    
    def __init__(self, module_params = None, **kwds):
        kwds["module_params"] = module_params
        super().__init__(**kwds)

        serial_port = module_params.get("configuration").get("port")

        import storm_control.sc_hardware.coherent.obis as obis
        self.laser = obis.Obis(port = serial_port)

        if self.laser.getStatus():
            [pmin, pmax] = self.laser.getPowerRange()
            self.laser_functionality = CoherentLaserFunctionality(device_mutex = self.device_mutex,
                                                                  display_normalized = True,
                                                                  laser = self.laser,
                                                                  minimum = 0,
                                                                  maximum = int(100.0 * pmax),
                                                                  used_during_filming = self.used_during_filming)
        else:
            self.laser = None            
