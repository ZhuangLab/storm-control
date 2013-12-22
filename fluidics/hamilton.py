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
    def __init__(self, COM_port = 2, verbose = True, simulate = False, num_simulated_valves = 0):

        # Define attributes
        self.verbose = verbose
        self.simulate = simulate
        self.num_simulated_valves = num_simulated_valves
        
        # Create serial port
        if not self.simulate:
            self.serial = serial.Serial(port = COM_port, 
                                 baudrate = 9600, 
                                 bytesize = serial.SEVENBITS, 
                                 parity = serial.PARITY_ODD, 
                                 stopbits = serial.STOPBITS_ONE, 
                                 timeout = 0.1)
        
        # Define important characters
        self.acknowledge = "\x06"
        self.carriage_return = "\x13"
        self.negative_acknowledge = "\x21"
        self.read_length = 64
        self.char_offset = 97 # offset to convert int current_device to ascii addresses (0=a, 1=b, ...)

        # Define default valve
        self.max_valves = 16
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []
        self.max_ports_per_valve = []
        self.current_port = []

        # Configure Device
        self.autoAddress()
        self.autoDetectValves()
        
    # ------------------------------------------------------------------------------------
    # Define Device Addresses: Must be First Command Issued
    # ------------------------------------------------------------------------------------  
    def autoAddress(self):
        if not self.simulate:
            auto_address_cmd = "1a\r"
            if self.verbose:
                print "Autoaddressing Hamilton Valves"
            x = self.write(auto_address_cmd)
            response = self.read() # Clear buffer
        else:
            print "Simulating Hamilton MVP"            

    # ------------------------------------------------------------------------------------
    # Auto Detect and Configure Valves: Devices are detected by acknowledgement of
    # initialization command
    # ------------------------------------------------------------------------------------
    def autoDetectValves(self):
        if not self.simulate:
            for valve_ID in range(self.max_valves): # Loop over all possible valves
                # Generate address character (0=a, 1=b, ...)
                device_address_character = chr(valve_ID + self.char_offset)  
                if self.verbose:
                    print "Looking for device with address: " + str(valve_ID) + "=" + device_address_character
                self.valve_names.append(device_address_character) # Save device characters

                # Send initialization command to valve: if it acknowledges, then it exists
                response = self.initializeValve(valve_ID) 
                if response[0] == "Acknowledge":
                    response = self.howIsValveConfigured(valve_ID)

                    if response[1]: # Indicates successful response
                        self.valve_configs.append(response[0])
                        self.max_ports_per_valve.append(self.numPortsPerConfiguration(response[0]))
                        self.current_port.append(0)

                        found_valves += 1
                        
                        if self.verbose:
                            print "Found " + response[0] + " device at address " + str(valve_ID)

                elif response[0] == "Negative Acknowledge": # Final device found
                    break
                
            self.num_valves = found_valves

            if self.num_valves == 0:
                self.valve_names = "0"
                print "Error: no valves discovered"
                return False # Return failure

            if self.verbose:
                print "Found " + str(self.num_valves) + " MVP Units"
                for valve_ID in range(self.num_valves):
                    print "Device " + self.valve_names[valve_ID] + " is configured with " + self.valve_configs[valve_ID]
            
            # Wait for final device to stop moving
            self.waitUntilNotMoving(self.num_valves-1)
            
            return True
        
        else: # Simulation code
            for valve_ID in range(self.num_simulated_valves):
                self.valve_configs.append(self.howIsValveConfigured(valve_ID)[0])
                self.max_ports_per_valve.append(self.numPortsPerConfiguration(self.howIsValveConfigured(valve_ID)[0]))
                self.current_port.append(0)
            self.num_valves = self.num_simulated_valves
            print "Created " + str(self.num_simulated_valves) + " simulated valves"
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
        if len(response) >= len(message):
            repeated_message = response[:(response.find(self.carriage_return)-1)]
            actual_response = response[(response.find(self.carriage_return)-1):
                                      (response.rfind(self.carriage_return))]
            #actual_response = actual_response # remove carriage returns
        else:
            return ("Short response", False, response)
                
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
    # Initialize Position of Valve
    # ------------------------------------------------------------------------------------ 
    def initializeValve(self, valve_ID):
        if not self.simulate:
            response = self.inquireAndRespond(valve_ID,
                                              message ="LXR\r",
                                              dictionary = {},
                                              default = "")
            if self.verbose:
                print "Initialization Response:" + str(response)

            if response[1]: # Acknowledged response
                self.current_port[valve_ID] = 0 # Reset position
            
            return response[1]
        else:
            return True
                                
    # ------------------------------------------------------------------------------------
    # Move Valve
    # ------------------------------------------------------------------------------------ 
    def moveValve(self, valve_ID, port_ID, direction = 0, waitUntilDone = False):
        # Check validity if valve and port IDs
        if not self.isValidValve(valve_ID):
            return False
        if not self.isValidPort(valve_ID, port_ID):
            return False
        
        if not self.simulate:
            message = "LP" + str(direction) + str(portNumber) + "R\r"

            response = self.inquireAndRespond(valve_ID, message)        
            if response[0] == "Negative Acknowledge":
                print "Move failed: " + str(response)

            if waitUntilDone:
                self.waitUntilNotMoving()

            if response[1]: #Acknowledged move
                self.current_port[valve_ID] = port_ID
                
            return response[1]
        else: ## simulation code
            self.current_port[valve_ID] = port_ID
            return True

    # ------------------------------------------------------------------------------------
    # Poll Movement of Valve
    # ------------------------------------------------------------------------------------         
    def isMovementFinished(self, valve_ID):
        if not self.simulate:
            return self.inquireAndRespond(valve_ID,
                                          message ="F\r",
                                          dictionary = {"*": False,
                                                        "N": False,
                                                        "Y": True},
                                          default = "Unknown response")
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
    # Check if Valve is Valid
    # ------------------------------------------------------------------------------------       
    def isValidValve(self, valve_ID):
        if not (valve_ID < (self.max_valves - 1)):
            if self.verbose:
                print str(valve_ID) + " is not a valid valve"
            return False
        else:
            return True
    
    # ------------------------------------------------------------------------------------
    # Check if Port is Valid
    # ------------------------------------------------------------------------------------
    def isValidPort(self, valve_ID, port_ID):
        if not self.isValidValve(valve_ID):
            return False
        elif not (port-ID < (self.max_ports_per_valve[valve_ID] - 1)):
            if self.verbose:
                print str(port_ID) + " is not a valid port on valve " + str(valve_ID)
            return False
        else:
            return True
        
    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def howIsValveConfigured(self, valve_ID):
        if not self.simulate:
            return self.inquireAndRespond(valve_ID,
                                          message ="LQT\r",
                                          dictionary = {"2": "8 ports",
                                                        "3": "6 ports",
                                                        "4": "3 ports",
                                                        "5": "2 ports @180",
                                                        "6": "2 ports @90",
                                                        "7": "4 ports"},
                                          default = "Unknown response")
        else: ## simulation code
            return ("8 ports", True, "Simulation")
        
    # ------------------------------------------------------------------------------------
    # Convert Port Configuration String to Number of Ports
    # ------------------------------------------------------------------------------------  
    def numPortsPerConfiguration(self, configuration_string):
        return {"8 ports": 8,
                "6 ports": 6,
                "3 ports": 3,
                "2 ports @180": 2,
                "2 ports @90": 2,
                "4 ports": 2}.get(configuration_string, 0)

    # ------------------------------------------------------------------------------------
    # Generate Default Port Names
    # ------------------------------------------------------------------------------------  
    def getDefaultPortNames(self, valve_ID):
        if not self.isValidValve(valve_ID):
            return ("")
        default_names = []
        for port_num in range(self.max_ports_per_valve[valve_ID]):
            default_names.append("Port " + str(port_num))
        return default_names

    # ------------------------------------------------------------------------------------
    # Generate Rotation Direction Labels
    # ------------------------------------------------------------------------------------  
    def getRotationDirections(self, valve_ID):
        if not self.isValidValve(valve_ID):
            return ("")
        return ("Clockwise", "Counter Clockwise")
    
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
            return self.inquireAndRespond(valve_ID,
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
        else: ## simulation code
            return ({"1": "Port 1",
                    "2": "Port 2",
                    "3": "Port 3",
                    "4": "Port 4",
                    "5": "Port 5",
                    "6": "Port 6",
                    "7": "Port 7",
                    "8": "Port 8"}.get(str(self.current_port[valve_ID]+1)),
                    True,
                    "Simulation")

    # ------------------------------------------------------------------------------------
    # Get Valve Status
    # ------------------------------------------------------------------------------------    
    def getStatus(self, valve_ID):
        return (self.whereIsValve(valve_ID)[0],
                not self.isMovementFinished(valve_ID))

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
        return self.num_valves

    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------
    def read(self):
        response = self.serial.read(self.read_length)
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
        if not self.simulate:
            self.serial.close()
            if self.verbose:
                print "Closed serial port"
        else: ## simulation code
            print "Closed simulated class"
        
    # ------------------------------------------------------------------------------------
    # Reset Hamilton: Readdress and redetect valves
    # ------------------------------------------------------------------------------------  
    def resetHamilton(self):
        # Reset device configuration
        self.valve_names = []
        self.num_valves = 0
        self.valve_configs = []
        self.max_ports_per_valve = []

        # Configure Device
        self.autoAddress()
        self.autoDetectValves()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
    hamilton = HamiltonMVP(verbose = True, simulate = True, num_simulated_valves = 3)
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

