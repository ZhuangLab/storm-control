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
class HamiltonMVP:
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

        # Define default valve
        self.maxDevices = 16
        self.deviceNames = []
        self.currentDevice = ""
        self.numDevices = 0
        self.valveConfigurations = []

        # Configure Device
        self.AutoAddress()
        self.AutoDetectValves()        

    # ------------------------------------------------------------------------------------
    # Auto Detect and Configure Valves
    # ------------------------------------------------------------------------------------
    def AutoDetectValves(self):
        charOffset = 97;
        for deviceID in range(self.maxDevices):
            deviceAddressCharacter = chr(deviceID + charOffset)  
            self.currentDevice = deviceAddressCharacter
            if self.verbose:
                print "Detecting device with address: " + self.currentDevice

            response = self.InitializePosition()
            if response[0] == "Acknowledge":
                response = self.HowIsValveConfigured()
                if response[1]:
                    self.deviceNames.append(self.currentDevice)
                    self.valveConfigurations.append(response[0])
                    if self.verbose:
                        print "Found " + response[0] + " device at address " + self.currentDevice

        self.numDevices = len(self.deviceNames)

        if self.numDevices == 0:
            self.deviceNames = "0"
            print "Error: no valves discovered"
        else:
            self.currentDevice = self.deviceNames[0]

        print "Found " + str(self.numDevices) + " MVP Units"
        for deviceID in range(self.numDevices):
            print "Device " + self.deviceNames[deviceID] + " is configured with " + self.valveConfigurations[deviceID]

        # Wait for initialization movement to finish before progressing
        self.currentDevice = self.deviceNames[-1]
        self.WaitUntilNotMoving()
        self.currentDevice = self.deviceNames[0]
        
    # ------------------------------------------------------------------------------------
    # Basic I/O with Serial Port
    # ------------------------------------------------------------------------------------
    def InquireAndRespond(self, message, dictionary = {}, default = "Unknown"):
        # Add on current device
        message = self.currentDevice + message
        
        self.Write(message = message)
        response = self.Read()
        
        # Parse response into sent message and response
        if len(response) >= len(message):
            repeatedMessage = response[:(response.find(self.carriageReturn)-1)]
            actualResponse = response[(response.find(self.carriageReturn)-1):
                                      (response.rfind(self.carriageReturn))]
            actualResponse = actualResponse # remove carriage returns
        else:
            return ("Short response", False, response)
                
        # Check for negative acknowledge
        if actualResponse == self.negativeAcknowledge:
            return ("Negative Acknowledge", False, response)

        # Check for acknowledge only
        if actualResponse == self.acknowledge:
            return ("Acknowledge", True, response)
        
        # Parse dictionary with response
        returnValue = dictionary.get(actualResponse, default)
        if returnValue == default:
            return (default, False, response)
        else:
            return (returnValue, True, response)

    # ------------------------------------------------------------------------------------
    # Define Device Addresses: Must be First Command Issued
    # ------------------------------------------------------------------------------------  
    def AutoAddress(self):
        autoAddressString = "1a\r"
        if self.verbose:
            print "Autoaddressing Hamilton Valves"
        x = self.Write(autoAddressString)
        response = self.Read() # Clear buffer

    # ------------------------------------------------------------------------------------
    # Initialize Position of Device
    # ------------------------------------------------------------------------------------ 
    def InitializePosition(self):
        responseTuple = self.InquireAndRespond(message ="LXR\r",
                                               dictionary = {},
                                               default = "Unknown response")
        if self.verbose:
            print "Initialization Response:" + str(responseTuple)

        return responseTuple
    # ------------------------------------------------------------------------------------
    # Move Valve
    # ------------------------------------------------------------------------------------ 
    def MoveValve(self, portNumber=1, direction = 0, waitUntilDone = False):
        message = "LP" + str(direction) + str(portNumber) + "R\r"

        response = self.InquireAndRespond(message)        
        if response[0] == "Negative Acknowledge":
            print "Move failed: " + str(response)

        if waitUntilDone:
            self.WaitUntilNotMoving()
            
    # ------------------------------------------------------------------------------------
    # Poll Movement of Valve
    # ------------------------------------------------------------------------------------         
    def IsMovementFinished(self):
        return self.InquireAndRespond(message ="F\r",
                              dictionary = {"*": False,
                                            "N": False,
                                            "Y": True},
                              default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Overload Status of Valve
    # ------------------------------------------------------------------------------------       
    def IsValveOverloaded(self):
        return self.InquireAndRespond(message ="G\r",
                                      dictionary = {"*": False,
                                                    "N": False,
                                                    "Y": True},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Valve Configuration
    # ------------------------------------------------------------------------------------  
    def HowIsValveConfigured(self):
        return self.InquireAndRespond(message ="LQT\r",
                                      dictionary = {"2": "8 ports",
                                                    "3": "6 ports",
                                                    "4": "3 ports",
                                                    "5": "2 ports @180",
                                                    "6": "2 ports @90",
                                                    "7": "4 ports"},
                                      default = "Unknown response")

    # ------------------------------------------------------------------------------------
    # Poll Valve Location
    # ------------------------------------------------------------------------------------    
    def WhereIsValve(self):
        return self.InquireAndRespond(message ="LQP\r",
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
    def WaitUntilNotMoving(self, pauseTime = 1):
        doneMoving = False
        while not doneMoving:
            response = self.IsMovementFinished()
            doneMoving = response[0]
            time.sleep(pauseTime)

    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------
    def Read(self):
        response = self.serial.read(self.readLength)
        if self.verbose:
            print "Received: " + str((response, ""))
        return response

    # ------------------------------------------------------------------------------------
    # Write to Serial Port
    # ------------------------------------------------------------------------------------    
    def Write(self, message):
        self.serial.write(message)
        if self.verbose:
            print "Wrote: " + message[:-1] # Display all but final carriage return

    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def Close(self):
        self.serial.close()
        if self.verbose:
            print "Closed serial port"

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
    hamilton = HamiltonMVP()
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
    hamilton.Close()

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

