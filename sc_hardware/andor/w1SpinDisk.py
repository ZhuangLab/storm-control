#!/usr/bin/python
#
## @file
#
# A serial interface to the W1 Spinning Disk from Yokogawa/Andor.
#
# Jeffrey Moffitt 5/16
#

import sc_library.halExceptions as halExceptions
import serial
import copy
import sc_library.parameters as params

## W1Exception
#
# Spinning disk exception.
#
class W1Exception(halExceptions.HardwareException):
    def __init__(self, message):
        halExceptions.HardwareException.__init__(self, message)

class W1SpinningDisk:

    def __init__(self, parameters, hardware_config):

        # Create serial port
        try:
            self.com = serial.Serial(port = hardware_config.get("com_port"),
                                     baudrate = 115200,
                                     timeout = .5) # The timeout duration needs to be set to allow sufficient time for long commands to run
        except:
            print "Could not create serial port for spinning disk. Is it connected properly?"
            raise W1Exception("W1 Spinning Disk Initialization Error \n" + " Could not properly initialize com_port: " + str(com_port))

        # Create a local copy of the current W1 configuration
        self.params = params.StormXMLObject([]) # Create empty parameters object

        # Record internal verbosity (debug purposes only)
        self.verbose = hardware_config.get("verbose")

        # Set number of reads before issuing a serial communication error
        self.max_num_reads = 30 # This number in combination with the timeout for the serial port needs to produce a long enough delay
                                # for the longest command

        # Create dictionaries for the configuration of the filter wheels and two dichroic mirror sets
        self.filter_wheel_1_config = {}
        values = hardware_config.get("filter_wheel_1")
        filter_names = values.split(",")
        for pos, filter_name in enumerate(filter_names):
            self.filter_wheel_1_config[filter_name] = pos + 1

        self.filter_wheel_2_config = {}
        values = hardware_config.get("filter_wheel_2")
        filter_names = values.split(",")
        for pos, filter_name in enumerate(filter_names):
            self.filter_wheel_2_config[filter_name] = pos + 1

        self.dichroic_mirror_config = {}
        values = hardware_config.get("dichroic_mirror")
        dichroic_names = values.split(",")
        for pos, dichroic_name in enumerate(dichroic_names):
            self.dichroic_mirror_config[dichroic_name] = pos + 1

        self.camera_dichroic_config = {}
        values = hardware_config.get("camera_dichroic")
        camera_dichroic_names = values.split(",")
        for pos, camera_dichroic in enumerate(camera_dichroic_names):
            self.camera_dichroic_config[camera_dichroic] = pos + 1

        if self.verbose:
            print "W1 Configuration: "
            print self.filter_wheel_1_config
            print self.filter_wheel_2_config
            print self.camera_dichroic_config
            print self.dichroic_mirror_config

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
                            "30302": "Shutter unopenable error"}

        self.initializeParameters(parameters)

    def cleanup(self):
        self.com.close()

    def initializeParameters(self, parameters):
        # Add spinning disk sub section
        sd_params = parameters.addSubSection("spinning_disk")

        # Add basic parameters
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
        sd_params.add("dichroic_mirror", params.ParameterSetString("Dichroic mirror position",
                                                                   "dichroic_mirror",
                                                                   "DMPT405/488/561/640/755",
                                                                   self.dichroic_mirror_config.keys()))

        # Filter wheel positions
        sd_params.add("filter_wheel_pos1", params.ParameterSetString("Camera 1 Filter Wheel Position (1-10)",
                                                                    "filter_wheel_pos1",
                                                                    "zet405/488/561/647-656/752m",
                                                                    self.filter_wheel_1_config.keys()))

        sd_params.add("filter_wheel_pos2", params.ParameterSetString("Camera 2 Filter Wheel Position (1-10)",
                                                                    "filter_wheel_pos2",
                                                                    "blocked",
                                                                    self.filter_wheel_2_config.keys()))

        # Camera dichroic positions
        sd_params.add("camera_dichroic_mirror", params.ParameterSetString("Camera dichroic mirror position (1-3)",
                                                                          "camera_dichroic_mirror",
                                                                          "Glass",
                                                                          self.camera_dichroic_config.keys()))

        # Aperature settings
        sd_params.add("aperture", params.ParameterRangeInt("Aperture value (1-10; small to large)",
                                                            "aperture",
                                                            10,1,10))

        # Run new parameters to configure the spinning disk with these defaults
        self.newParameters(parameters)

    def getMaxSpeed(self):
        [success, value] = self.writeAndReadResponse("MS_MAX,?\r")
        return int(value)
        
    def newParameters(self, parameters):
        p = parameters.get("spinning_disk")

        # Update all parameters of the spinning disk, checking to see if parameters need updated
        for key in p.getAttrs():
            if not (key in self.params.getAttrs()) or not (self.params.get(key) == p.get(key)):
                if key == "bright_field_bypass":
                    if p.get("bright_field_bypass"):
                        self.writeAndReadResponse("BF_ON\r")
                    else:
                        self.writeAndReadResponse("BF_OFF\r")
                elif key == "spin_disk":
                    if p.get("spin_disk"):
                        self.writeAndReadResponse("MS_RUN\r")
                    else:
                        self.writeAndReadResponse("MS_STOP\r")
                elif key == "disk":
                    if p.get("disk") == "50-micron pinholes":
                        self.writeAndReadResponse("DC_SLCT,1\r")
                    elif p.get("disk") == "25-micron pinholes":
                        self.writeAndReadResponse("DC_SLCT,2\r")
                elif key == "disk_speed":
                      self.writeAndReadResponse("MS,"+str(p.get("disk_speed"))+"\r")
                elif key == "dichroic_mirror":
                      dichroic_num = self.dichroic_mirror_config[p.get("dichroic_mirror")]
                      self.writeAndReadResponse("DMM_POS,1,"+str(dichroic_num)+"\r")
                elif key == "filter_wheel_pos1" or key == "filter_wheel_pos2":
                      filter1_num = self.filter_wheel_1_config[p.get("filter_wheel_pos1")]
                      filter2_num = self.filter_wheel_2_config[p.get("filter_wheel_pos2")]
                      self.writeAndReadResponse("FW_POS,0," + str(filter1_num) + "," + str(filter2_num) + "\r")
                elif key == "camera_dichroic_mirror":
                      camera_dichroic_num = self.camera_dichroic_config[p.get("camera_dichroic_mirror")]
                      self.writeAndReadResponse("PT_POS,1," + str(camera_dichroic_num) + "\r")
                elif key == "aperture":
                    self.writeAndReadResponse("AP_WIDTH,1,"+str(p.get("aperture"))+"\r")
                else:
                    print str(key) + " is not a valid parameter for the W1"

        # Make deep copy of the passed parameters so that the spinning disk remembers its current configuration
        self.params = copy.deepcopy(p)

    def writeAndReadResponse(self, message):
        # Debug code
        if self.verbose:
            print "Wrote: " + message

        # Write the message
        self.com.write(message)

        # Poll for a response (it could be longer than the timeout period of the port)
        response = []
        num_checks = 0
        while len(response) == 0 and num_checks < self.max_num_reads:
            response = self.com.readline()
            num_checks = num_checks + 1

        # Debug code
        if self.verbose:
            print "Response (" + str(num_checks) + "): " + response

        # Handle empty response
        if num_checks >= self.max_num_reads:
            raise W1Exception("Serial communication error with W1")

        # Split response and look for proper acknowledge
        [value, acknow] = response.split(":")
        
        # Handle error codes
        if acknow == "N\r":
            error_message = self.error_codes.get(value, "Unknown error")

            raise W1Exception("W1 Error " + value + ": " + error_message)

        else:
            return [True, value]


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
