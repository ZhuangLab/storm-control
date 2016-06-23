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
from collections import deque
from PyQt4 import QtCore

# Debugging
import sc_library.hdebug as hdebug


## W1Exception
#
# Spinning disk exception.
#
class W1Exception(halExceptions.HardwareException):
    def __init__(self, message):
        halExceptions.HardwareException.__init__(self, message)

## SerialObject
#
#
#
class SerialObject:
    _COUNTER = 0 # A unique id for each sent serial command
    
    def __init__(self, command):
        self.command = command
        self.response = None
        self.id = SerialObject._COUNTER
        self.error = None
        
        # Increment counter
        SerialObject._COUNTER += 1

    def getCommand(self):
        return self.command

    def getResponse(self):
        return self.response

    def getID(self):
        return self.id

    def getError(self):
        return self.error

    def setError(self, error_message):
        self.error = error_message

## W1SpinningDisk
#
# The W1 spinning disk main control class
#
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

        # Create thread
        self.serial_thread = W1SerialThread(self.com)
        # Start thread
        self.serial_thread.start(QtCore.QThread.NormalPriority)

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

        # Run new parameters to configure the spinning disk with these defaults
        self.newParameters(parameters)

    def getMaxSpeed(self):
        [success, value] = self.writeAndReadResponse("MS_MAX,?\r")
        return int(value)

    # handleSerialError
    #
    # Handle an error signal from the serial port thread
    #
    # @param error The error string
    def handleSerialError(self, error):
        error_message = self.error_codes.get(value, "Unknown error")
        raise W1Exception("W1 Error " + value + ": " + error_message)

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
                        self.serial_thread.addToQueue(SerialObject("BF_ON\r"))
                    else:
                        self.serial_thread.addToQueue(SerialObject("BF_OFF\r"))
                elif key == "spin_disk":
                    if p.get("spin_disk"):
                        self.serial_thread.addToQueue(SerialObject("MS_RUN\r"))
                    else:
                        self.serial_thread.addToQueue(SerialObject("MS_STOP\r"))
                elif key == "disk":
                    if p.get("disk") == "50-micron pinholes":
                        self.serial_thread.addToQueue(SerialObject("DC_SLCT,1\r"))
                    elif p.get("disk") == "25-micron pinholes":
                        self.serial_thread.addToQueue(SerialObject("DC_SLCT,2\r"))
                elif key == "disk_speed":
                    self.serial_thread.addToQueue(SerialObject("MS,"+str(p.get("disk_speed"))+"\r"))
                elif key == "dichroic_mirror":
                    dichroic_num = self.dichroic_mirror_config[p.get("dichroic_mirror")]
                    self.serial_thread.addToQueue(SerialObject("DMM_POS,1,"+str(dichroic_num)+"\r"))
                elif key == "filter_wheel_pos1" or key == "filter_wheel_pos2":
                    filter1_num = self.filter_wheel_1_config[p.get("filter_wheel_pos1")]
                    filter2_num = self.filter_wheel_2_config[p.get("filter_wheel_pos2")]
                    self.serial_thread.addToQueue(SerialObject("FW_POS,0," + str(filter1_num) + "," + str(filter2_num) + "\r"))
                elif key == "camera_dichroic_mirror":
                    camera_dichroic_num = self.camera_dichroic_config[p.get("camera_dichroic_mirror")]
                    self.serial_thread.addToQueue(SerialObject("PT_POS,1," + str(camera_dichroic_num) + "\r"))
                elif key == "aperture":
                    self.serial_thread.addToQueue(SerialObject("AP_WIDTH,1,"+str(p.get("aperture"))+"\r"))
                else:
                    print str(key) + " is not a valid parameter for the W1"

        # Make deep copy of the passed parameters so that the spinning disk remembers its current configuration
        self.params = copy.deepcopy(p)   

class W1SerialThread(QtCore.QThread):
    response = QtCore.pyqtSignal(obj)
    
    ## __init__
    #
    # @param com A serial object used for reading/writing serial commands to the W1
    #
    #
    @hdebug.debug
    def __init__(self, com, parent = None):
        QtCore.QThread.__init__(self, parent)

        self.com = com # The com_port for serial communication

        self.command_queue = deque() # A list of serial commands to write

    # run
    #
    # The major command for reading/writing to the 
    def run(self):

        if len(self.command_queue) > 0:
            new_command = self.command_queue.popleft() # Remove from the front of the list

            # Write the message
            self.com.write(new_command.getCommand())

            # Poll for a response (it could be longer than the timeout period of the port)
            response = []
            num_checks = 0
            while len(response) == 0 and num_checks < self.max_num_reads:
                response = self.com.readline()
                num_checks = num_checks + 1

            # Handle empty response
            if num_checks >= self.max_num_reads:
                new_command.setError("1")
            else:

                # Split response and look for proper acknowledge
                [value, acknow] = response.split(":")
                
                # Handle error codes
                if acknow == "N\r":
                    new_command.setError(value)
                else:
                    new_command.setResponse(value)

            # Emit a signal that a response has been generated
            self.response.emt(new_command)

        else:
            self.msleep(1) # Wait for a few ms before trying another command

    # addToQueue
    #
    # Add a serial command to the serial port queue
    #
    # @param command A serial command
    #
    def addToQueue(self, command):
        self.command_queue.append(command)
        

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
