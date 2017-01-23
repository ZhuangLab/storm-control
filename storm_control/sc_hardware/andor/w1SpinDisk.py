#!/usr/bin/python
#
## @file
#
# A serial interface to the W1 Spinning Disk from Yokogawa/Andor.
#
# Jeffrey Moffitt 5/16
#

import serial
import copy
from PyQt5 import QtCore
from time import sleep

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

# Debugging
import storm_control.sc_library.hdebug as hdebug

## W1Exception
#
# Spinning disk exception.
#
class W1Exception(halExceptions.HardwareException):
    def __init__(self, message):
        halExceptions.HardwareException.__init__(self, message)

## W1SpinningDisk
#
# The W1 spinning disk main control class
#
class W1SpinningDisk(object):

    def __init__(self, parameters, hardware_config):

        # Create serial control thread
        try:
            self.serial_thread = W1SerialThread(hardware_config.get("com_port"), baudrate=115200, timeout = 0.01,
                                                verbose = hardware_config.get("verbose", False))
        except:
            print "Could not create serial port for spinning disk. Is it connected properly?"
            raise W1Exception("W1 Spinning Disk Initialization Error \n" + " Could not properly initialize com_port: " + str(hardware_config.get("com_port")))

        # Connect error signal from serial control thread
        self.serial_thread.error.connect(self.handleSerialThreadError)

        # Start thread
        self.serial_thread.start(QtCore.QThread.NormalPriority)

        # Create a local copy of the current W1 configuration
        self.params = params.StormXMLObject([]) # Create empty parameters object

        # Record internal verbosity (debug purposes only)
        self.verbose = hardware_config.get("verbose")

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

        # Initialize spinning disk parameters
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
    ## cleanup
    #
    # Cleanup class
    #
    def cleanup(self):
        self.serial_thread.cleanup()

    # getMaxSpeed
    #
    # Return the maximum speed of the disk
    #
    def getMaxSpeed(self):
        [value, error] = self.serial_thread.sendCommandGetResponse("MS_MAX,?\r")
        if not error:
            return int(value)
        else:
            error_message = self.error_codes.get(value, "Unknown error")
            raise W1Exception("W1 Error " + value + ": " + error_message)

    # handleSerialThreadError
    #
    # Handle an error message from the serial thread
    #
    # @param error_code
    def handleSerialThreadError(self, error_code):
        error_message = self.error_codes.get(error_code, "Unknown error")
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

## W1SerialThread
#
# A thread to allow asynchronous monitoring of the serial port.
#
class W1SerialThread(QtCore.QThread):
    error = QtCore.pyqtSignal(object) # Signal that an error message was detected on serial port
    
    ## __init__
    #
    # @param com_port The com port for W1 serial communication
    # @param baudrate The baudrate of the com port
    # @param timeout The timeout for the serial port
    # @param parent
    # @param verbose Display progress for debuggin purposes
    #
    def __init__(self, com_port, baudrate = 115200, timeout = 0.001, parent = None, verbose = False):
        QtCore.QThread.__init__(self, parent)

        # Create serial port
        self.com = serial.Serial(port = com_port,
                                 baudrate = baudrate,
                                 timeout = timeout) 

        self.verbose = verbose # For debugging purposes
        self.running = True # Flag for running the loop

        # Create a com port mutex
        self.com_mutex = QtCore.QMutex()

        # Maximum number of reads to check for a com response
        self.max_num_reads = 10
        self.pause_time = 0.1 # time in seconds to wait between com checks for response

        if self.verbose:
            print "Created W1 Serial Thread"

    ## cleanup
    def cleanup(self):
        self.stopThread()
        self.com.close()

    ## sendCommand
    #
    # Send a serial command
    #
    # @param message The message to send on the com port
    #
    def sendCommand(self, message):
        # Lock the com port
        self.com_mutex.lock()

        # Send command
        self.com.write(message)

        # Debug
        if self.verbose:
            print "W1 Serial Thread: Wrote " + message

        # Unlock mutex
        self.com_mutex.unlock()

    ## sendCommandGetResponse
    #
    # Send a serial command and wait for the response
    #
    # @param message The message to send on the com port
    #
    def sendCommandGetResponse(self, message):
        # Lock the com port
        self.com_mutex.lock()

        # Flush previous com port responses
        response = []
        while len(response) > 0:
            response = self.com.readline()

        # Send command
        self.com.write(message)

        # Debug
        if self.verbose:
            print "W1 Serial Thread: Wrote " + message

        # Poll for a response (it could be longer than the timeout period of the port)
        response = []
        num_checks = 0
        while len(response) == 0 and num_checks < self.max_num_reads:
            response = self.com.readline()
            num_checks = num_checks + 1
            #sleep(self.pause_time) # Wait before checking again

        # Debug
        if self.verbose:
            print "W1 Received Response: " + str(response)

        # Unlock mutex
        self.com_mutex.unlock()

        # Check to see if no response was found
        if num_checks >= self.max_num_reads:
            return [None, True] # Response, did an error occur?
        else:
            # Split response and look for proper acknowledge
            split_values = response.split(":")
            value = split_values[0] # Handle rare case that two response are found during timeout
            acknow = split_values[1]
            # Handle error codes
            if acknow == "N\r":
                return [value, True]
            else:
                return [value, False]
    
    # run
    #
    # The major command for reading/writing to the 
    def run(self):
        if self.verbose:
            print "Started W1 Serial Thread"
        while self.running:
            # Lock mutex
            self.com_mutex.lock()

            # Look for a response
            response = self.com.readline()

            # Debug
            if self.verbose:
                print "W1 Serial Thread Monitor: Read " + response

            # If there is one, look for an error code
            if len(response) > 0:
                split_values = response.split(":")
                value = split_values[0] # Handle rare case that two response are found during timeout
                acknow = split_values[1]

                if acknow == "N\r":
                    self.error.emit(value) # Send pyqt signal that an error has occurred

            # Release mutex
            self.com_mutex.unlock()

            # Sleep
            self.msleep(100)

    ## stopThread
    #
    # Stop the focus lock control thread.
    #
    def stopThread(self):
        self.com_mutex.lock()
        self.running = False
        self.com_mutex.unlock()

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
