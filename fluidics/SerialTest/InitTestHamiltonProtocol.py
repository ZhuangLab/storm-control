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
        self.verbose = True
        self.asciiVerbose = True

        # Define important characters
        self.acknowledge = "\x06"
        self.carriageReturn = "\x13"
        self.negativeAcknowledge = "\x21"
        
        print "Configured new Hamilton Valve"

    def InquireAndRespond(self, message, dictionary, default):
        self.Write(message = message)
        response = self.Read()

        # Parse response into sent message and response
        if len(response) >= len(message):
            repeatedMessage = response[:response.find(self.carriageReturn)]
            actualResponse = response[response.find(self.carriageReturn):
                                      response.rfind(self.carriageReturn)]
            actualResponse = actualResponse[1:-1] # remove carriage returns
        else:
            return ("Short response", False, response)
                
        # Check for negative awcknowledge
        if actualResponse == self.negativeAcknowledge:
            return ("Negative Acknowledge", False, response)

        # Parse dictionary with response
        returnValue = dictionary.get(actualResponse, default)
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
        returnString = self.serial.read(64);

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
        returnString = self.serial.read(64);

        if self.verbose:
            print "Hamilton Responded: " + returnString

    def MoveToPort(self, portNumber):
        moveToString = "aLP1" + str(portNumber) + "R\r"
        if self.verbose:
            print "Moving to port " + str(portNumber)
            print "Issuing: " + moveToString

        x = self.serial.write(moveToString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(64)
        if self.verbose:
            print "Hamilton Responded: " + returnString
                        
    def WhatIsValvePosition(self):
        inquiryString = "aLPQR\r"
        if self.verbose:
            print "Valve location inquiry"
            print "Issuing: " + inquiryString

        x = self.serial.write(inquiryString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(64)
        if self.verbose:
            print "Hamilton Responded: " + returnString

    def WhatIsStatus(self):
        inquiryString = "aE1R\r"
        if self.verbose:
            print "Status inquiry"
            print "Issuing: " + inquiryString
        x = self.serial.write(inquiryString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes"
        returnString = self.serial.read(64)
        if self.verbose:
            print "Hamilton Responded: " + returnString

    def IsMovementFinished(self):
        return self.InquireAndRespond(message ="aF\r",
                              dictionary = {"*": False,
                                            "N": False,
                                            "Y": True},
                              default = "Unknown response")
    
    def IsValveOverloaded(self):
        return self.InquireAndRespond(message ="aLQT\r",
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

    def Read(self):
        response = self.serial.read(64)
##        if self.verbose:
##            print "Received: " + str(response)
##        if self.asciiVerbose:
##            print "Ascii response: " + str(self.StringToAsciiArray(response))
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
    hamilton.AutoAddress()
    hamilton.InitializePosition()
    #hamilton.WhatIsStatus()
    print hamilton.IsMovementFinished()
    time.sleep(5)
    print hamilton.IsMovementFinished()
    print "Is valve overloaded: " + str(hamilton.IsValveOverloaded())
    print "How is valve configured:" + str(hamilton.HowIsValveConfigured())
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

