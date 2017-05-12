#!/usr/bin/env python
"""
HAL module to interface with the W1 Spinning Disk from Yokogawa/Andor.

Jeffrey Moffitt 5/16
Hazen 5/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.serial.RS232 as RS232

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params


class W1Exception(halExceptions.HardwareException):
    """
    Spinning disk exception.
    """
    def __init__(self, message):
        halExceptions.HardwareException.__init__(self, message)


class W1Functionality(hardwareModule.BufferedFunctionality):
    """
    Control of the W1 spinning disk. 

    This is only a functionality for convenience. It is not 
    shared with other HAL modules.
    """
    def __init__(self, w1 = None, configuration = None, **kwds):
        super().__init__(**kwds)
        self.w1 = w1

        # Query W1 for it's maximum speed.
        max_speed = self.w1.commWithResp("MS_MAX,?")

        # Create dictionaries for the configuration of the
        # filter wheels and two dichroic mirror sets.
        self.filter_wheel_1_config = {}
        values = configuration.get("filter_wheel_1")
        filter_names = values.split(",")
        for pos, filter_name in enumerate(filter_names):
            self.filter_wheel_1_config[filter_name] = pos + 1

        self.filter_wheel_2_config = {}
        values = configuration.get("filter_wheel_2")
        filter_names = values.split(",")
        for pos, filter_name in enumerate(filter_names):
            self.filter_wheel_2_config[filter_name] = pos + 1

        self.dichroic_mirror_config = {}
        values = configuration.get("dichroic_mirror")
        dichroic_names = values.split(",")
        for pos, dichroic_name in enumerate(dichroic_names):
            self.dichroic_mirror_config[dichroic_name] = pos + 1

        self.camera_dichroic_config = {}
        values = configuration.get("camera_dichroic")
        camera_dichroic_names = values.split(",")
        for pos, camera_dichroic in enumerate(camera_dichroic_names):
            self.camera_dichroic_config[camera_dichroic] = pos + 1

        # Define error codes
        self.error_codes = {"30005": "Command name error",
                            "30006": "Command argument number error",
                            "30007": "Command argument value error",
                            "30141": "Command argument value error",
                            "30012": "Interlock alarm is on",
                            "30133": "Interlock alarm is on",
                            "30014": "Electricity alarm is on",
                            "30015": "Shutter alarm is on",
                            "30016": "Actuator alarm is on",
                            "30017": "Disk alarm is on",
                            "30018": "Data error alarm is on",
                            "30019": "Other alarm is on",
                            "30021": "Designated system is not defined",
                            "30022": "Designated system does not exist",
                            "30023": "Designated system is not detected",
                            "30031": "Waiting for initialization to complete",
                            "30032": "Under maintenance mode",
                            "30201": "External SYNC signal is under use",
                            "30204": "Disk rotation stopped",
                            "30301": "Shutter error",
                            "30302": "Shutter unopenable error",
                            "1": "Unknown serial communication error"}

        # Create parameters
        self.parameters = params.StormXMLObject()

        sd_params.add("bright_field_bypass", params.ParameterSetBoolean("Bypass spinning disk for brightfield mode?",
                                                                        "bright_field_bypass", False))

        sd_params.add("spin_disk", params.ParameterSetBoolean("Spin the disk?",
                                                              "spin_disk", True))

        # Disk properties
        sd_params.add("disk", params.ParameterSetString("Disk pinhole size",
                                                        "disk",
                                                        "50-micron pinholes",
                                                        ["50-micron pinholes", "25-micron pinholes"]))

        max_speed = self.getMaxSpeed()
        sd_params.add("disk_speed", params.ParameterRangeInt("Disk speed (RPM)",
                                                             "disk_speed",
                                                             max_speed, 1, max_speed))

        # Dichroic mirror position
        values = sorted(self.dichroic_mirror_config.keys())
        sd_params.add("dichroic_mirror", params.ParameterSetString("Dichroic mirror position",
                                                                   "dichroic_mirror",
                                                                   values[0],
                                                                   values))

        # Filter wheel positions
        values = sorted(self.filter_wheel_1_config.keys())
        sd_params.add("filter_wheel_pos1", params.ParameterSetString("Camera 1 Filter Wheel Position (1-10)",
                                                                    "filter_wheel_pos1",
                                                                    values[0],
                                                                    values))

        values = sorted(self.filter_wheel_2_config.keys())
        sd_params.add("filter_wheel_pos2", params.ParameterSetString("Camera 2 Filter Wheel Position (1-10)",
                                                                    "filter_wheel_pos2",
                                                                    values[0],
                                                                    values))

        # Camera dichroic positions
        values = sorted(self.camera_dichroic_config.keys())
        sd_params.add("camera_dichroic_mirror", params.ParameterSetString("Camera dichroic mirror position (1-3)",
                                                                          "camera_dichroic_mirror",
                                                                          values[0],
                                                                          values))

        # Aperature settings
        sd_params.add("aperture", params.ParameterRangeInt("Aperture value (1-10; small to large)",
                                                            "aperture",
                                                            10,1,10))

    # newParameters
    #
    # Update the spinning disk parameters (if different from current configuration)
    #
    # @param parameters A parameters object
    def newParameters(self, parameters):
        p = parameters.get("spinning_disk")

        # Update all parameters of the spinning disk, checking to see if parameters need updated
        for key in p.getAttrs():
            if not (key in self.params.getAttrs()) or not (self.params.get(key) == p.get(key)):
                if key == "bright_field_bypass":
                    if p.get("bright_field_bypass"):
                        self.serial_thread.sendCommand("BF_ON\r")
                        sleep(1)
                    else:
                        self.serial_thread.sendCommand("BF_OFF\r")
                        sleep(1)
                elif key == "spin_disk":
                    if p.get("spin_disk"):
                        self.serial_thread.sendCommand("MS_RUN\r")
                        sleep(3)
                    else:
                        self.serial_thread.sendCommand("MS_STOP\r")
                        sleep(1)
                elif key == "disk":
                    if p.get("disk") == "50-micron pinholes":
                        self.serial_thread.sendCommand("DC_SLCT,1\r")
                        sleep(3)
                    elif p.get("disk") == "25-micron pinholes":
                        self.serial_thread.sendCommand("DC_SLCT,2\r")
                        sleep(3)
                elif key == "disk_speed":
                    self.serial_thread.sendCommand("MS,"+str(p.get("disk_speed"))+"\r")
                    sleep(1)
                elif key == "dichroic_mirror":
                    dichroic_num = self.dichroic_mirror_config[p.get("dichroic_mirror")]
                    self.serial_thread.sendCommand("DMM_POS,1,"+str(dichroic_num)+"\r")
                    sleep(1)
                elif key == "filter_wheel_pos1" or key == "filter_wheel_pos2":
                    filter1_num = self.filter_wheel_1_config[p.get("filter_wheel_pos1")]
                    filter2_num = self.filter_wheel_2_config[p.get("filter_wheel_pos2")]
                    self.serial_thread.sendCommand("FW_POS,0," + str(filter1_num) + "," + str(filter2_num) + "\r")
                    sleep(0.1)
                elif key == "camera_dichroic_mirror":
                    camera_dichroic_num = self.camera_dichroic_config[p.get("camera_dichroic_mirror")]
                    self.serial_thread.sendCommand("PT_POS,1," + str(camera_dichroic_num) + "\r")
                    sleep(1)
                elif key == "aperture":
                    self.serial_thread.sendCommand("AP_WIDTH,1,"+str(p.get("aperture"))+"\r")
                    sleep(0.5)
                else:
                    print str(key) + " is not a valid parameter for the W1"

        # Make deep copy of the passed parameters so that the spinning disk remembers its current configuration
        self.params = copy.deepcopy(p)   


class W1SpinDiskModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.w1_fn = None

        configuration = module_params.get("configuration")
        self.w1_tty = RS232.RS232(baudrate = configuration.get("baudrate"),
                                  port = configuration.get("port"))
        if self.w1_tty:
            self.w1_fn = W1Functionality(w1 = self.w1_tty,
                                         configuration = configuration)

    def cleanUp(self, qt_settings):
        if self.w1_fn is not None:
            self.w1_fn.wait()
            self.w1_tty.shutDown()
                        
        
#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
