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

class HamiltonClass:
    def __init__(self):
        self.serial = serial.Serial(port = 2, 
                             baudrate = 9600, 
                             bytesize = serial.SEVENBITS, 
                             parity = serial.PARITY_EVEN, 
                             stopbits = serial.STOPBITS_TWO, 
                             timeout = 1)
        self.verbose = True
        print "Configured new Hamilton Valve"

    def CalculateBCC(self,message):
        mask = 127; # 0b01111111

        BCC = 0 
        for byte in message:
            BCC ^= byte

        BCC = mask & ~BCC

        if self.verbose:
            print "Added BCC: " + str(BCC)
            
        return BCC

    def WriteToHamilton(self, message):
        message.append(3) # <ETX>
        #message.append(self.CalculateBCC(message = message))
        message.append(13) # \r
        message.insert(0,2) # <STX> \x02
        
        if self.verbose:
            print "Writing: " + message
        
        bytesWritten = self.serial.write(message);

        if self.verbose:
            print "Wrote " + str(bytesWritten) + " bytes"

        returnString = self.serial.read(64);
        if self.verbose:
            print "Hamilton Responded: " + returnString
            
    def StartCommunication(self):
        commStartString = "01\x05\r"
        if self.verbose:
            print "Configuring Hamilton Valve"
            print "Sending: " + commStartString
        x = self.serial.write(commStartString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(64);

        if self.verbose:
            print "Hamilton Responded: " + returnString
    
    def StopCommunication(self):
        commStopString = "01\x04\r"
        if self.verbose:
            print "Ending transmission"
            print "Sending: " + commStopString
        x = self.serial.write(commStopString)
        if self.verbose:
            print "Wrote " + str(x) + " bytes" 
        returnString = self.serial.read(64);
        
        if self.verbose:
            print "Hamilton Responded: " + returnString

    def Close(self):
        self.serial.close()
        if self.verbose:
            print "Closed serial port"
    
if __name__ == '__main__':

    hamilton = HamiltonClass()
    hamilton.StartCommunication()

    # Write initialize code to Hamilton
    # message = bytearray( (48, 49, 73, 49) )
    # hamilton.WriteToHamilton(message)

    # Move clockwise
    message = bytearray( (48, 49, 86, 118, 48) )
    hamilton.WriteToHamilton(message)
    
    # Move to position 3
    #message = bytearray( (48, 49, 86, 100, 110, 48, 51) )
    #hamilton.WriteToHamilton(message)
    
    hamilton.StopCommunication()
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

