#!/usr/bin/env python
"""
A serial interface to the W1 Spinning Disk from Yokogawa/Andor.

Jeffrey Moffitt 5/16
Hazen Babcock 5/17
"""

import storm_control.sc_hardware.serial.RS232 as RS232


class W1SpinningDisk(RS232.RS232):

    def __init__(self, **kwds):
        super().__init__(**kwds)

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

    def commandResponse(self, command, timeout = 0.1):

        # Clear buffer of old responses.
        self.tty.timeout = 0
        while (len(self.readline()) > 0):
            pass
        
        # Set timeout.
        self.tty.timeout = timeout

        # Send the command and wait timeout time for a response.
        self.writeline(command)
        response = self.readline()

        # Check that we got a message within the timeout.
        if (len(response) > 0):
            [value, code] = response.split(":")[:2]

            # Did we get an error?
            if (code == "N\r"):
                try:
                    print(">> Warning w1 error", self.error_codes[value])
                except KeyError:
                    print(">> Warning unknown w1 error", value)                    
                return None            
            else:
                return value

        else:
            return None


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
