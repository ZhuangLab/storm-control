#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A basic class for serial interface with a series of daisy chained Hamilton MVP devices
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/17/13
# jeffmoffitt@gmail.com
#
# TODO: Simulated port should be in a different class
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time

from storm_control.fluidics.valves.valve import AbstractValve

# ----------------------------------------------------------------------------------------
# HamiltonMVP Class Definition
# ----------------------------------------------------------------------------------------
class HamiltonMVP(AbstractValve):
    def __init__(self,
                 com_port = "COM2",
                 num_simulated_valves = 0,
                 verbose = False):

        # Define attributes
        self.com_port = com_port
        self.verbose = verbose
        self.num_simulated_valves = num_simulated_valves

        # Determine simulation mode
        self.simulate = (self.num_simulated_valves > 0)
        
        # Create serial port (if not in simulation mode)
        if not self.simulate:
            import serial
            self.serial = serial.Serial(port = self.com_port, 
                                        baudrate = 9600, 
                                        bytesize = serial.SEVENBITS, 
                                        parity = serial.PARITY_ODD, 
                                        stopbits = serial.STOPBITS_ONE, 
                                        timeout = 0.1)
        
        # Define important serial characters
        self.acknowledge = "\x06"
        self.carriage_return = "\x13"
        self.negative_acknowledge = "\x21"
        self.read_length = 64
        self.char_offset = 97           # offset to convert int current_device
                                        # to ascii addresses (0=a, 1=b, ...)

        # Define valve and port properties
        self.max_valves = 16            # Maximum number of daisy chains
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []
        self.max_ports_per_valve = []
        self.current_port = []

        # Configure device
        self.autoAddress()
        self.autoDetectValves()
        
    # ------------------------------------------------------------------------------------
    # Define Device Addresses: Must be First Command Issued
    # ------------------------------------------------------------------------------------  
    def autoAddress(self):
        if not self.simulate:
            auto_address_cmd = "1a\r"
            if self.verbose:
                print("Addressing Hamilton Valves")
            x = self.write(auto_address_cmd)
            response = self.read() # Clear buffer
        else:
            print("Simulating Hamilton MVP")

    # ------------------------------------------------------------------------------------
    # Auto Detect and Configure Valves: Devices are detected by acknowledgement of
    # initialization command
    # ------------------------------------------------------------------------------------
    def autoDetectValves(self):
        if not self.simulate:
            print("----------------------------------------------------------------------")
            print("Opening the Hamilton MVP Valve Daisy Chain")
            print("   " + "COM Port: " + str(self.com_port))
            for valve_ID in range(self.max_valves): # Loop over all possible valves

                # Generate address character (0=a, 1=b, ...)
                device_address_character = chr(valve_ID + self.char_offset)  

                if self.verbose:
                    print("Looking for device with address: " + str(valve_ID) + "=" + device_address_character)

                self.valve_names.append(device_address_character) # Save device characters

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
            print("Found " + str(self.num_valves) + " Hamilton MVP Valves")
            for valve_ID in range(self.num_valves):
                print("   " + "Device " + self.valve_names[valve_ID] + " is configured with " + self.valve_configs[valve_ID])

            print("Initializing valves...")
            
            # Wait for final device to stop moving
            self.waitUntilNotMoving(self.num_valves-1)
            
            return True
        
        else: # Simulation code
            for valve_ID in range(self.num_simulated_valves):
                self.valve_configs.append(self.howIsValveConfigured(valve_ID))
                self.max_ports_per_valve.append(self.numPortsPerConfiguration(self.howIsValveConfigured(valve_ID)))
                self.current_port.append(0)
            self.num_valves = self.num_simulated_valves
            print("Created " + str(self.num_simulated_valves) + " simulated Hamilton MVP valves")
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
        
        if not self.simulate:
            # Compose message and increment port_ID (starts at 1)
            message = "LP" + str(direction) + str(port_ID+1) + "R\r"

            response = self.inquireAndRespond(valve_ID, message)        
            if response[0] == "Negative Acknowledge":
                print("Move failed: " + str(response))

            if response[1]: #Acknowledged move
                self.current_port[valve_ID] = port_ID

            if wait_until_done:
                self.waitUntilNotMoving()
                
            return response[1]
        else: ## simulation code
            self.current_port[valve_ID] = port_ID
            return True

    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def close(self):
        if not self.simulate:
            self.serial.close()
            if self.verbose: print("Closed hamilton valves")
        else: ## simulation code
            if self.verbose: print("Closed simulated hamilton valves")
     
    # ------------------------------------------------------------------------------------
    # Initialize Port Position of Given Valve
    # ------------------------------------------------------------------------------------ 
    def initializeValve(self, valve_ID):
        if not self.simulate:
            response = self.inquireAndRespond(valve_ID,
                                              message ="LXR\r",
                                              dictionary = {},
                                              default = "")
            if self.verbose:
                if response[1]: print("Initialized Valve: " + str(valve_ID+1))
                else: print("Did not find valve: " + str(valve_ID+1))
            return response[1]
        else:
            return True

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
        message = self.valve_names[valve_ID] + message

        # Write message and read response
        self.write(message)
        response = self.read()
        
        # Parse response into sent message and response
        repeated_message = response[:(response.find(self.carriage_return)-1)]
        actual_response = response[(response.find(self.carriage_return)-1):
                                  (response.rfind(self.carriage_return))]
        #actual_response = actual_response # remove carriage returns
                
        # Check for negative acknowledge
        if actual_response == self.negative_acknowledge:
            return ("Negative Acknowledge", False, response)

        # Check for acknowledge 
        if actual_response == self.acknowledge:
            return ("Acknowledge", True, response)
        
        # Parse provided dictionary with response
        return_value = dictionary.get(actual_response, default)
        if return_value == default:
            return (default, False, response)
        else:
            return (return_value, True, response)
                                
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
        if not self.simulate:
            response =  self.inquireAndRespond(valve_ID,
                                              message ="LQT\r",
                                              dictionary = {"2": "8 ports",
                                                            "3": "6 ports",
                                                            "4": "3 ports",
                                                            "5": "2 ports @180",
                                                            "6": "2 ports @90",
                                                            "7": "4 ports"},
                                              default = "Unknown response")
            return response[0]
        else: ## simulation code
            return "8 ports"

    # ------------------------------------------------------------------------------------
    # Determine number of active valves
    # ------------------------------------------------------------------------------------
    def howManyValves(self):
        return self.num_valves

    # ------------------------------------------------------------------------------------
    # Poll Movement of Valve
    # ------------------------------------------------------------------------------------         
    def isMovementFinished(self, valve_ID):
        if not self.simulate:
            response = self.inquireAndRespond(valve_ID,
                                              message ="F\r",
                                              dictionary = {"*": False,
                                                            "N": False,
                                                            "Y": True},
                                              default = "Unknown response")
            return response[0]
        else: ## simulation code
            return ("Y", True, "Simulation")

    # ------------------------------------------------------------------------------------
    # Poll Overload Status of Valve
    # ------------------------------------------------------------------------------------       
    def isValveOverloaded(self, valve_ID):
        if not self.simulate:
            return self.inquireAndRespond(valve_ID,
                                          message ="G\r",
                                          dictionary = {"*": False,
                                                        "N": False,
                                                        "Y": True},
                                          default = "Unknown response")
        else: ## simulation code
            return ("N", False, "Simulation")

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
        response = self.serial.read(self.read_length).decode()
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
        self.autoAddress()
        self.autoDetectValves()
    
    # ------------------------------------------------------------------------------------
    # Halt Hamilton Class Until Movement is Finished
    # ------------------------------------------------------------------------------------
    def waitUntilNotMoving(self, valve_ID, pause_time = 1):
        doneMoving = False
        while not doneMoving:
            doneMoving = self.isMovementFinished(valve_ID)
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
        if not self.simulate:
            response = self.inquireAndRespond(valve_ID,
                                          message ="LQP\r",
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
        else: ## simulation code
            return {"1": "Port 1",
                    "2": "Port 2",
                    "3": "Port 3",
                    "4": "Port 4",
                    "5": "Port 5",
                    "6": "Port 6",
                    "7": "Port 7",
                    "8": "Port 8"}.get(str(self.current_port[valve_ID]+1))

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
    hamilton = HamiltonMVP(verbose = True)

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

