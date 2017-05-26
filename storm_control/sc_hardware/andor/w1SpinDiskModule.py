#!/usr/bin/env python
"""
HAL module to interface with the W1 Spinning Disk from Yokogawa/Andor.

Jeffrey Moffitt 5/16
Hazen 5/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule
import storm_control.sc_hardware.andor.w1SpinningDisk as w1SpinningDisk

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params


class W1Control(object):
    """
    Control of the W1 spinning disk. 
    """
    def __init__(self, w1 = None, configuration = None, **kwds):
        super().__init__(**kwds)
        self.w1 = w1

        # Query W1 for it's maximum speed.
        max_speed = self.w1.commandResponse("MS_MAX,?")
        assert max_speed is not None

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

        # Create parameters
        self.parameters = params.StormXMLObject()

        self.parameters.add(params.ParameterSetBoolean(description = "Bypass spinning disk for brightfield mode?",
                                                       name = "bright_field_bypass",
                                                       value = False))

        self.parameters.add(params.ParameterSetBoolean(description = "Spin the disk?",
                                                       name = "spin_disk",
                                                       value = True))
        
        # Disk properties
        self.parameters.add(params.ParameterSetString(description = "Disk pinhole size",
                                                      name = "disk",
                                                      value = "50-micron pinholes",
                                                      allowed = ["50-micron pinholes", "25-micron pinholes"]))

        self.parameters.add(params.ParameterRangeInt(description = "Disk speed (RPM)",
                                                     name = "disk_speed",
                                                     value = max_speed,
                                                     min_value = 1,
                                                     max_value = max_speed))

        # Dichroic mirror position
        values = sorted(self.dichroic_mirror_config.keys())
        self.parameters.add(params.ParameterSetString(description = "Dichroic mirror position",
                                                      name = "dichroic_mirror",
                                                      value = values[0],
                                                      allowed = values))

        # Filter wheel positions
        values = sorted(self.filter_wheel_1_config.keys())
        self.parameters.add(params.ParameterSetString(description = "Camera 1 Filter Wheel Position (1-10)",
                                                      name = "filter_wheel_pos1",
                                                      value = values[0],
                                                      allowed = values))

        values = sorted(self.filter_wheel_2_config.keys())
        self.parameters.add(params.ParameterSetString(description = "Camera 2 Filter Wheel Position (1-10)",
                                                      name = "filter_wheel_pos2",
                                                      value = values[0],
                                                      allowed = values))

        # Camera dichroic positions
        values = sorted(self.camera_dichroic_config.keys())
        self.parameters.add(params.ParameterSetString(description = "Camera dichroic mirror position (1-3)",
                                                      name = "camera_dichroic_mirror",
                                                      value = values[0],
                                                      allowed = values))

        # Aperature settings
        self.parameters.add(params.ParameterRangeInt(description = "Aperture value (1-10; small to large)",
                                                     name = "aperture",
                                                     value = 10,
                                                     min_value = 1,
                                                     max_value = 10))

        self.newParameters(self.parameters, initialization = True)

    def getParameters(self):
        return self.parameters
    
    def newParameters(self, parameters, initialization = False):

        if initialization:
            changed_p_names = parameters.getAttrs()
        else:
            changed_p_names = params.difference(parameters, self.parameters)

        p = parameters
        for pname in changed_p_names:

            # Update our current parameters.
            self.parameters.setv(pname, p.get(pname))

            # Configure the W1.
            if (pname == "bright_field_bypass"):
                if p.get("bright_field_bypass"):
                    self.w1.commandResponse("BF_ON", 1)
                else:
                    self.w1.commandResponse("BF_OFF", 1)

            elif (pname == "spin_disk"):
                if p.get("spin_disk"):
                    self.w1.commandResponse("MS_RUN", 3)
                else:
                    self.w1.commandResponse("MS_STOP", 1)
                    
            elif (pname == "disk"):
                if (p.get("disk") == "50-micron pinholes"):
                    self.w1.commandResponse("DC_SLCT,1", 3)
                elif (p.get("disk") == "25-micron pinholes"):
                    self.w1.commandResponse("DC_SLCT,2", 3)

            elif (pname == "disk_speed"):
                self.w1.commandResponse("MS,"+str(p.get("disk_speed")), 1)

            elif (pname == "dichroic_mirror"):
                dichroic_num = self.dichroic_mirror_config[p.get("dichroic_mirror")]
                self.w1.commandResponse("DMM_POS,1,"+str(dichroic_num), 1)

            elif (pname == "filter_wheel_pos1") or (pname == "filter_wheel_pos2"):
                filter1_num = self.filter_wheel_1_config[p.get("filter_wheel_pos1")]
                filter2_num = self.filter_wheel_2_config[p.get("filter_wheel_pos2")]
                self.w1.commandResponse("FW_POS,0," + str(filter1_num) + "," + str(filter2_num), 0.1)

            elif (pname == "camera_dichroic_mirror"):
                camera_dichroic_num = self.camera_dichroic_config[p.get("camera_dichroic_mirror")]
                self.w1.commandResponse("PT_POS,1," + str(camera_dichroic_num), 1)

            elif (pname == "aperture"):
                self.w1.commandResponse("AP_WIDTH,1,"+str(p.get("aperture")), 0.5)

            else:
                print(">> Warning", str(pname), " is not a valid parameter for the W1")


class W1SpinDiskModule(hardwareModule.HardwareModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.control = None
        self.w1 = None

        configuration = module_params.get("configuration")
        self.w1 = w1SpinningDisk.W1SpinningDisk(baudrate = configuration.get("baudrate"),
                                                port = configuration.get("port"))
        if self.w1.getStatus():
            self.control = W1Control(w1 = self.w1,
                                     configuration = configuration)

    def cleanUp(self, qt_settings):
        if self.control is not None:
            self.w1.shutDown()

    def processMessage(self, message):

        if self.control is None:
            return

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.control.getParameters()}))

        #
        # FIXME? Maybe we want do this at 'update parameters' as we don't
        #        do any error checking.
        #
        elif message.isType("new parameters"):
            hardwareModule.runHardwareTask(self,
                                           message,
                                           lambda : self.updateParameters(message))

    def updateParameters(self, message):
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"old parameters" : self.control.getParameters().copy()}))
        p = message.getData()["parameters"].get(self.module_name)
        self.control.newParameters(p)
        message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                          data = {"new parameters" : self.control.getParameters()}))

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
