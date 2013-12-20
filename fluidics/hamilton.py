#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A basic class for serial interface with a series of daisy chained Hamilton MVP devices
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/17/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import serial
import sys
import time

# ----------------------------------------------------------------------------------------
# Class Definition
# ----------------------------------------------------------------------------------------
class HamiltonMVP():
    def __init__(self, verbose = True):
        self.serial = serial.Serial(port = 2, 
                             baudrate = 9600, 
                             bytesize = serial.SEVENBITS, 
                             parity = serial.PARITY_ODD, 
                             stopbits = serial.STOPBITS_ONE, 
                             timeout = 0.1)

        # Define display options
        self.verbose = verbose

        # Define important characters
        self.acknowledge = "\x06"
        self.carriageReturn = "\x13"
        self.negativeAcknowledge = "\x21"
        self.readLength = 64
        self.char_offset = 97 # offset to convert int current_device to ascii addresses (0=a, 1=b, ...)

        # Define default valve
        self.max_valves = 16
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []

        # Configure Device
        self.autoAddress()
        self.autoDetectValves()
        
    # ------------------------------------------------------------------------------------
    # Define Device Addresses: Must be First Command Issued
    # ------------------------------------------------------------------------------------  
    def autoAddress(self):
        auto_address_cmd = "1a\r"
        if self.verbose:
            print "Autoaddressing Hamilton Valves"
        x = self.write(auto_address_cmd)
        response = self.read() # Clear buffer

    # ------------------------------------------------------------------------------------
    # Auto Detect and Configure Valves
    # ------------------------------------------------------------------------------------
    def autoDetectValves(self):
        found_valves = 0
        for valve_ID in range(self.max_valves):
            device_address_character = chr(valve_ID + self.char_offset)  
            if self.verbose:
                print "Detecting device with address: " + str(valve_ID)
            self.valve_names.append(device_address_character)
            
            response = self.initializePosition(valve_ID)
            if response[0] == "Acknowledge":
                response = self.howIsValveConfigured(valve_ID)
                if response[1]:
                    self.valve_configs.append(response[0])
                    found_valves += 1
                    if self.verbose:
                        print "Found " + response[0] + " device at address " + str(valve_ID)
                
        self.num_valves = found_valves

        if self.num_valves == 0:
            self.valve_names = "0"
            print "Error: no valves discovered"

        print "Found " + str(self.num_valves) + " MVP Units"
        for valve_ID in range(self.num_valves):
            print "Device " + self.valve_names[valve_ID] + " is configured with " + self.valve_configs[valve_ID]

        # Wait for final device to stop moving
        self.waitUntilNotMoving(self.num_valves-1)
        
    # ------------------------------------------------------------------------------------
    # Basic I/O with Serial Port
    # ------------------------------------------------------------------------------------
    def inquireAndRespond(self, valve_ID, message, dictionary = {}, default = "Unknown"):
        # Add on current device
        message = self.valve_names[valve_ID] + message
        
        self.write(message)
        response = self.read()
        
        # Parse response into sent message and response
        if len(response) >= len(message):
            repeated_message = response[:(response.find(self.carriageReturn)-1)]
            actual_response = response[(response.find(self.carriageReturn)-1):
                                      (response.rfind(self.carriageReturn))]
            actual_response = actual_response # remove carriage returns
        else:
            return ("Short response", False, response)
                
        # Check for negative acknowledge
        if actual_response == self.negativeAcknowledge:
            return ("Negative Acknowledge", False, response)

        # Check for acknowledge only
        if actual_response == self.acknowledge:
            return ("Acknowledge", True, response)
        
        # Parse dictionary with response
        return_value = dictionary.get(actual_response, default)
        if return_value == default:
            return (default, False, response)
        else:
            return (return_value, True, response)

    # ------------------------------------------------------------------------------------
    # Initialize Position of Device
    # ------------------------------------------------------------------------------------ 
    def initializePosition(self, valve_ID):
        response = self.inquireAndRespond(valve_ID,
                                               message ="LXR\r",
                                               dictionary = {},
                                               default = "Unknown response")
        if self.verbose:
            print "Initialization Response:" + str(response)

        return response
                                
    # ------------------------------------------------------------------------------------
    # Move Valve
    # ------------------------------------------------------------------------------------ 
    def moveValve(self, valve_ID, portNumber=1, direction = 0, waitUntilDone = False):
        message = "LP" + str(direction) + str(portNumber) + "R\r"

        response = self.inquireAndRespond(valve_ID, message)        
        if response[0] == "Negative Acknowledge":
            print "Move failed: " + str(response)

        if waitUntilDone:
            self.waitUntilNotMoving()
            
    # ------------------------------------------------------------------------------------
    # Poll Movement of Valve
    # ------------------------------------------------------------------------------------         
    def isMovementFinished(self, valve_ID):
        return self.inquireAndRespond(valve_ID,
                                      message ="F\r",
                                      dictionary = {"*": False,
                                                    "N": False,
                                                    "Y": True},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Overload Status of Valve
    # ------------------------------------------------------------------------------------       
    def isValveOverloaded(self, valve_ID):
        return self.inquireAndRespond(valve_ID,
                                      message ="G\r",
                                      dictionary = {"*": False,
                                                    "N": False,
                                                    "Y": True},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def howIsValveConfigured(self, valve_ID):
        return self.inquireAndRespond(valve_ID,
                                      message ="LQT\r",
                                      dictionary = {"2": "8 ports",
                                                    "3": "6 ports",
                                                    "4": "3 ports",
                                                    "5": "2 ports @180",
                                                    "6": "2 ports @90",
                                                    "7": "4 ports"},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def whatIsValveConfiguration(self, valve_ID):
        return self.valveConfigurations[self.currentDevice]

    # ------------------------------------------------------------------------------------
    # Poll Valve Location
    # ------------------------------------------------------------------------------------    
    def whereIsValve(self, valve_ID):
        return self.inquireAndRespond(valve_ID,
                                      message ="LQP\r",
                                      dictionary = {"1": "Position 1",
                                                    "2": "Position 2",
                                                    "3": "Position 3",
                                                    "4": "Position 4",
                                                    "5": "Position 5",
                                                    "6": "Position 6",
                                                    "7": "Position 7",
                                                    "8": "Position 8"},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Halt Hamilton Class Until Movement is Finished
    # ------------------------------------------------------------------------------------
    def waitUntilNotMoving(self, valve_ID, pauseTime = 1):
        doneMoving = False
        while not doneMoving:
            response = self.isMovementFinished(valve_ID)
            doneMoving = response[0]
            time.sleep(pauseTime)

    # ------------------------------------------------------------------------------------
    # Determine number of active valves
    # ------------------------------------------------------------------------------------
    def howManyValves(self):
        return self.numDevices

    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------
    def read(self):
        response = self.serial.read(self.readLength)
        if self.verbose:
            print "Received: " + str((response, ""))
        return response

    # ------------------------------------------------------------------------------------
    # Write to Serial Port
    # ------------------------------------------------------------------------------------    
    def write(self, message):
        self.serial.write(message)
        if self.verbose:
            print "Wrote: " + message[:-1] # Display all but final carriage return

    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def close(self):
        self.serial.close()
        if self.verbose:
            print "Closed serial port"
        
    # ------------------------------------------------------------------------------------
    # Reset Hamilton: Readdress and redetect valves
    # ------------------------------------------------------------------------------------  
    def resetHamilton(self):
        # Reset device configuration
        self.deviceNames = []
        self.currentDevice = ""
        self.numDevices = 0
        self.valveConfigurations = []

        # Reconfigure
        self.autoAddress()
        self.autoDetectValves()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
    hamilton = HamiltonMVP(verbose = True)
    #hamilton.AutoAddress()
    #print "How is valve configured:" + str(hamilton.HowIsValveConfigured())
    #hamilton.InitializePosition()
    #print "Is movement finished: " + str(hamilton.IsMovementFinished())
    #time.sleep(5)
    #print "Is movement finished: " + str(hamilton.IsMovementFinished())
    #print "Valve Position: " + str(hamilton.WhereIsValve())
    #print "Moving Valve to 3"
    #hamilton.MoveValve(portNumber = 3, direction = 0)
    #print "Where is valve: " + str(hamilton.WhereIsValve())
    hamilton.close()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

