#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A basic class for the control of the new MVP valves from Hamilton: MVP4
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 11/20/21
# jeffrey.moffitt@childrens.harvard.edu
#
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time
import importlib
import serial

from storm_control.fluidics.valves.valve import AbstractValve

# ----------------------------------------------------------------------------------------
# HamiltonMVP Class Definition
# ----------------------------------------------------------------------------------------
class AValveChain(AbstractValve):
    def __init__(self,
                 parameters = None):

        # Define attributes
        self.com_port = parameters.get("valves_com_port")
        self.verbose = parameters.get("verbose", True)

        
        # Create serial port 
        self.serial = serial.Serial(port = self.com_port, 
                                    baudrate = 9600, 
                                    timeout = 0.1)
        
        # Define valve and port properties
        self.max_valves = 16            # Maximum number of daisy chains
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []
        self.max_ports_per_valve = []
        self.current_port = []

        # Configure device
        self.autoDetectValves()
        
    # ------------------------------------------------------------------------------------
    # Auto Detect and Configure Valves: Devices are detected by acknowledgement of
    # initialization command
    # ------------------------------------------------------------------------------------
    def autoDetectValves(self):
        print("----------------------------------------------------------------------")
        print("Opening the Hamilton MVP4 Valve Daisy Chain")
        print("   " + "COM Port: " + str(self.com_port))
        for valve_ID in range(self.max_valves): # Loop over all possible valves

            # Generate valve ID
            valve_name = str(valve_ID + 1)

            if self.verbose:
                print("Looking for device " + valve_name)

            self.valve_names.append(valve_name) # Save device characters

            # Send initialization command to valve: if it acknowledges, then it exists
            found_valve = self.initializeValve(valve_ID)
            if found_valve:
                # Determine valve configuration
                valve_config = self.howIsValveConfigured(valve_ID)

                if valve_config[1]: # Indicates successful response
                    self.valve_configs.append(valve_config)
                    self.max_ports_per_valve.append(self.numPortsPerConfiguration(valve_config))
                    self.current_port.append(0)
                    
                    if self.verbose:
                        print("Found " + valve_config + " device at address " + str(valve_ID))
            else:
                break
            
        self.num_valves = len(self.valve_configs)

        if self.num_valves == 0:
            self.valve_names = "0"
            print("Error: no valves discovered")
            return False # Return failure

        # Display found valves
        print("Found " + str(self.num_valves) + " Hamilton MVP4 Valves")
        for valve_ID in range(self.num_valves):
            print("   " + "Device " + self.valve_names[valve_ID] + " is configured with " + self.valve_configs[valve_ID])

        print("Initializing valves...")
        
        # Wait for final device to stop moving
        self.waitUntilNotMoving(self.num_valves-1)
        
        return True
        
    # ------------------------------------------------------------------------------------
    # Change Port Position
    # ------------------------------------------------------------------------------------ 
    def changePort(self, valve_ID, port_ID, direction = 0, wait_until_done = False):
        # Check validity if valve and port IDs
        if not self.isValidValve(valve_ID):
            return False
        if not self.isValidPort(valve_ID, port_ID):
            return False
        
        if direction == 0:
            message = "h2400" + str(port_ID+1) + "R\r"
        else:
            message = "h2500" + str(port_ID+1) + "R\r"
        
        response = self.inquireAndRespond(valve_ID, message)        

        self.current_port[valve_ID] = port_ID

        if wait_until_done:
            self.waitUntilNotMoving()
            
        return True

    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def close(self):
        self.serial.close()
        if self.verbose: print("Closed hamilton valves")
     
    # ------------------------------------------------------------------------------------
    # Initialize Port Position of Given Valve
    # ------------------------------------------------------------------------------------ 
    def initializeValve(self, valve_ID):
        response = self.inquireAndRespond(valve_ID,
                                          message ="ZR\r",
                                          dictionary = {},
                                          default = None)
        if self.verbose:
            if response[1]: print("Initialized Valve: " + str(valve_ID+1))
            else: print("Did not find valve: " + str(valve_ID+1))
        return response[1]

    # ------------------------------------------------------------------------------------
    # Basic I/O with Serial Port
    #  This function returns a response tuple used by this class
    #     (dictionary entry, affirmative response?, raw response string)
    # ------------------------------------------------------------------------------------
    def inquireAndRespond(self, valve_ID, message, dictionary = {}, default = "Unknown"):

        # Check if the valve_ID valve is initialized
        if not self.isValidValve(valve_ID):
            return ("", False, "")
        
        # Prepend address of provided valve (0=a, 1=b, ...) 
        message = "/" + self.valve_names[valve_ID] + message

        # Write message and read response
        self.write(message)
        actual_response = self.read()
        
        # Handle no response
        if len(actual_response) < 2:
            return (default, False, actual_response)
        
        # Handle status value
        status = chr(actual_response[2])
                
        # Extract data values, if provided
        data_start = 3
        data_end = actual_response.find('\x03'.encode())

        if data_start == data_end:
            return (default, True, actual_response)
        else:
            data = actual_response[data_start:data_end].decode()
            # Parse provided dictionary with data
            return_value = dictionary.get(data, default)
            
            if return_value == default:
                return (default, False, actual_response)
            else:
                return (return_value, True, actual_response)
                                    
    # ------------------------------------------------------------------------------------
    # Generate Default Port Names
    # ------------------------------------------------------------------------------------  
    def getDefaultPortNames(self, valve_ID):
        if not self.isValidValve(valve_ID):
            return ("")
        default_names = []
        for port_ID in range(self.max_ports_per_valve[valve_ID]):
            default_names.append("Port " + str(port_ID+1))
        return default_names

    # ------------------------------------------------------------------------------------
    # Generate Rotation Direction Labels
    # ------------------------------------------------------------------------------------  
    def getRotationDirections(self, valve_ID):
        if not self.isValidValve(valve_ID):
            return ("")
        return ("Clockwise", "Counter Clockwise")

    # ------------------------------------------------------------------------------------
    # Get Valve Status
    # ------------------------------------------------------------------------------------    
    def getStatus(self, valve_ID):
        return (self.whereIsValve(valve_ID), not self.isMovementFinished(valve_ID))

    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def howIsValveConfigured(self, valve_ID):
        response =  self.inquireAndRespond(valve_ID,
                                          message ="?21000\r",
                                          dictionary = {"3": "8 ports",
                                                        },
                                          default = "Unknown response")
        return response[0]

    # ------------------------------------------------------------------------------------
    # Determine number of active valves
    # ------------------------------------------------------------------------------------
    def howManyValves(self):
        return self.num_valves

    # ------------------------------------------------------------------------------------
    # Poll Movement of Valve
    # ------------------------------------------------------------------------------------         
    def isMovementFinished(self, valve_ID):
        # Create moving message
        message = "/" + self.valve_names[valve_ID] + "Q\r"

        # Write message and read response
        self.write(message)
        actual_response = self.read()
            
        # Handle status value
        status = chr(actual_response[2])
        if status == "@":
            return False
        else:
            return True
        
    # ------------------------------------------------------------------------------------
    # Check if Port is Valid
    # ------------------------------------------------------------------------------------
    def isValidPort(self, valve_ID, port_ID):
        if not self.isValidValve(valve_ID):
            return False
        elif not (port_ID < self.max_ports_per_valve[valve_ID]):
            if self.verbose:
                print(str(port_ID) + " is not a valid port on valve " + str(valve_ID))
            return False
        else:
            return True

    # ------------------------------------------------------------------------------------
    # Check if Valve is Valid
    # ------------------------------------------------------------------------------------       
    def isValidValve(self, valve_ID):
        if not (valve_ID < self.max_valves):
            if self.verbose:
                print(str(valve_ID) + " is not a valid valve")
            return False
        else:
            return True
        
    # ------------------------------------------------------------------------------------
    # Convert Port Configuration String to Number of Ports
    # ------------------------------------------------------------------------------------  
    def numPortsPerConfiguration(self, configuration_string):
        return {"8 ports": 8,
                "6 ports": 6,
                "3 ports": 3,
                "2 ports @180": 2,
                "2 ports @90": 2,
                "4 ports": 4}.get(configuration_string, 0)
    
    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------
    def read(self):
       # response = self.serial.readline().decode()
        response = self.serial.readline()

        if self.verbose:
            print("Received: " + str((response, "")))
        return response

    # ------------------------------------------------------------------------------------
    # Reset Chain: Readdress and redetect valves
    # ------------------------------------------------------------------------------------  
    def resetChain(self):
        # Reset device configuration
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []
        self.max_ports_per_valve = []

        # Configure Device
        self.autoDetectValves()
    
    # ------------------------------------------------------------------------------------
    # Halt Hamilton Class Until Movement is Finished
    # ------------------------------------------------------------------------------------
    def waitUntilNotMoving(self, valve_ID, pause_time = 1):
        doneMoving = False
        while not doneMoving:
            if self.isMovementFinished(valve_ID):
                doneMoving = True
            else:
                time.sleep(pause_time)
    
    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def whatIsValveConfiguration(self, valve_ID):
        if not self.isValidValve(valve_ID):
            return ""
        else:
            return self.valve_configs[valve_ID]

    # ------------------------------------------------------------------------------------
    # Poll Valve Location
    # ------------------------------------------------------------------------------------    
    def whereIsValve(self, valve_ID):
        response = self.inquireAndRespond(valve_ID,
                                      message ="?24000\r",
                                      dictionary = {"1": "Port 1",
                                                    "2": "Port 2",
                                                    "3": "Port 3",
                                                    "4": "Port 4",
                                                    "5": "Port 5",
                                                    "6": "Port 6",
                                                    "7": "Port 7",
                                                    "8": "Port 8"},
                                      default = "Unknown Port")
        return response[0]

    # ------------------------------------------------------------------------------------
    # Write to Serial Port
    # ------------------------------------------------------------------------------------    
    def write(self, message):
        self.serial.write(message.encode())
        if self.verbose:
            print("Wrote: " + message[:-1]) # Display all but final carriage return

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if (__name__ == '__main__'):
    hamilton = APump(verbose = True)

    for valve_ID in range(hamilton.howManyValves()):
        text = "Valve " + str(valve_ID+1)
        text = " is configured with " + hamilton.howIsValveConfigured(valve_ID)
    
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

