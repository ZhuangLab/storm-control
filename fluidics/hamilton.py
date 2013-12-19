#!/usr/bin/python
#
## @file
#
# Test of serial interface to Hamilton MVP in Din mode
#
# Jeff Moffitt
# 12/17/13
# jeffmoffitt@gmail.com
#

import serial
import sys
import time

class HamiltonClass:
    def __init__(self):
        self.serial = serial.Serial(port = 2, 
                             baudrate = 9600, 
                             bytesize = serial.SEVENBITS, 
                             parity = serial.PARITY_ODD, 
                             stopbits = serial.STOPBITS_ONE, 
                             timeout = 1)
        # Define display options
        self.verbose = False
        self.asciiVerbose = False

        # Define important characters
        self.acknowledge = "\x06"
        self.carriageReturn = "\x13"
        self.negativeAcknowledge = "\x21"
        self.readLength = 64
        
        print "Configured new Hamilton Valves"

    def InquireAndRespond(self, message, dictionary = {}, default = "Unknown"):
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

        # Parse dictionary with response
        returnValue = dictionary.get(actualResponse, default)
        if self.verbose:
            print "Parsed: " + str(actualResponse)
        if returnValue == default:
            return (default, False, response)
        else:
            return (returnValue, True, response)
  
    def AutoAddress(self):
        autoAddressString = "1a\r"
        if self.verbose:
            print "Autoaddressing Hamilton Valves"
            print "Sending: " + autoAddressString
        x = self.serial.write(autoAddressString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(self.readLength);

        if self.verbose:
            print "Hamilton Responded: " + returnString

    def InitializePosition(self):
        initializePosition = "aLXR\r"
        if self.verbose:
            print "Initializing Position"
            print "Sending: " + initializePosition
        x = self.serial.write(initializePosition)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(self.readLength);

        if self.verbose:
            print "Hamilton Responded: " + returnString

    def MoveValve(self, portNumber=1, direction = 0, waitUntilDone = True):
        message = "aLP" + str(direction) + str(portNumber) + "R\r"

        response = self.InquireAndRespond(message)        
        if response[0] == "Negative Acknowledge":
            print "Move failed: " + str(response)

        while waitUntilDone:
            print str(waitUntilDone)

            response = self.IsMovementFinished()
            print "Is done: " + str(response)
            waitUntilDone = ~response[0]
        
##    def WhatIsStatus(self):
##        return self.InquireAndRespond(message ="aE1\r",
##                              dictionary = {"*": False,
##                                            "N": False,
##                                            "Y": True},
##                              default = "Unknown response")

    def IsMovementFinished(self):
        return self.InquireAndRespond(message ="aF\r",
                              dictionary = {"*": False,
                                            "N": False,
                                            "Y": True},
                              default = "Unknown response")
    
    def IsValveOverloaded(self):
        return self.InquireAndRespond(message ="aG\r",
                                      dictionary = {"*": False,
                                                    "N": False,
                                                    "Y": True},
                                      default = "Unknown response")
    def HowIsValveConfigured(self):
        return self.InquireAndRespond(message ="aLQT\r",
                                      dictionary = {"2": "8 ports",
                                                    "3": "6 ports",
                                                    "4": "3 ports",
                                                    "5": "2 ports @180",
                                                    "6": "2 ports @90",
                                                    "7": "4 ports"},
                                      default = "Unknown response")
    def WhereIsValve(self):
        return self.InquireAndRespond(message ="aLQP\r",
                              dictionary = {"1": "Position 1",
                                            "2": "Position 2",
                                            "3": "Position 3",
                                            "4": "Position 4",
                                            "5": "Position 5",
                                            "6": "Position 6",
                                            "7": "Position 7",
                                            "8": "Position 8"},
                              default = "Unknown response")
    def Read(self):
        response = self.serial.read(self.readLength)
        if self.verbose:
            print "Received: " + str(response)
        if self.asciiVerbose:
           print "Ascii response: " + str(self.StringToAsciiArray(response))
        return response
    
    def Write(self, message):
        self.serial.write(message)
        print "Wrote: " + message[:-1] # Display all but final carriage return

    def StringToAsciiArray(self, string):
        asciiCharArray = ""
        for letter in string:
            asciiCharArray += str(ord(letter)) + " "

        return asciiCharArray

    def Close(self):
        self.serial.close()
        if self.verbose:
            print "Closed serial port"
        
if __name__ == '__main__':
    hamilton = HamiltonClass()
    #hamilton.AutoAddress()
    print "How is valve configured:" + str(hamilton.HowIsValveConfigured())
    hamilton.InitializePosition()
    print "Is movement finished: " + str(hamilton.IsMovementFinished())
    time.sleep(5)
    print "Is movement finished: " + str(hamilton.IsMovementFinished())
    print "Valve Position: " + str(hamilton.WhereIsValve())
    print "Moving Valve to 3"
    hamilton.MoveValve(portNumber = 3, direction = 0)
    print "Is movement finished: " + str(hamilton.IsMovementFinished())
    time.sleep(5)
    

    #print hamilton.IsMovementFinished()
    #time.sleep(5)
    #print hamilton.IsMovementFinished()
    #print "Is valve overloaded: " + str(hamilton.IsValveOverloaded())
    #time.sleep(5)
    #hamilton.WhatIsValvePosition()
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

