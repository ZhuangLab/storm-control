#!/usr/bin/env python
"""
Generic Obis laser control (RS-232 over USB).

Hazen 7/10
"""
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232

class Obis(RS232.RS232):
    """
    This controls a Coherent Obis laser using RS-232.
    """
    def __init__(self, **kwds):
        """
        Connect to the laser at the specified port and verify that the laser is responding.
        """
        # Add Obis RS232 default settings.
        kwds["baudrate"] = 9600
        kwds["end_of_line"] = "\r"
        kwds["wait_time"] = 0.05
        
        self.on = False
        self.pmin = 0.0
        self.pmax = 5.0
            
        try:
            # Open port.
            super().__init__(**kwds)

            # See if the laser is connected.
            assert not(self.commWithResp("?SYSTem:INFormation:MODel?") == None)

        # FIXME: This should not catch everything!
        except AttributeError:
            print(traceback.format_exc())
            self.live = False
            print("Failed to connect to Obis Laser at port", kwds["port"])
            print("Perhaps it is turned off or the COM ports have")
            print("been scrambled?")

        if self.live:
            [self.pmin, self.pmax] = self.getPowerRange()
            self.setExtControl(False)
            if (not self.getLaserOnOff()):
                self.setLaserOnOff(True)
            

    #def respToFloat(self, resp, start):
    #    return float(resp[start:-1])
    def getExtControl(self):
        """
        Return True/False the laser can be controlled with an external voltage.
        """
        self.sendCommand("SOURce:AM:SOURce?")
        response = self.waitResponse()
        if ("CWP" in response) or ("CWC" in response):
            return False
        else:
            return True

    def getLaserOnOff(self):
        """
        Return True/False the laser is on/off.
        """
        self.sendCommand("SOURce:AM:STATe?")
        resp = self.waitResponse()
        if ("ON" in resp):
            self.on = True
            return True
        else:
            self.on = False
            return False

    def getPowerRange(self):
        """
        Return [minimum power, maximum power].
        """
        self.sendCommand("SOURce:POWer:LIMit:LOW?")
        pmin = 1000.0 * float(self.waitResponse()[:-6])
        self.sendCommand("SOURce:POWer:LIMit:HIGH?")
        pmax = 1000.0 * float(self.waitResponse()[:-6])
        return [pmin, pmax]

    def getPower(self):
        """
        Return the current laser power.
        """
        self.sendCommand("SOURce:POWer:NOMinal?")
        return float(self.waitResponse()[:-1])

    def setExtControl(self, mode):
        """
        Turn on/off external control mode.
        """
        if mode:
            self.sendCommand("SOURce:AM:EXTernal DIGital")
        else:
            self.sendCommand("SOURce:AM:INTernal CWP")
        self.waitResponse()

    def setLaserOnOff(self, on):
        """
        Turn the laser on/off.
        """
        if on and (not self.on):
            self.sendCommand("SOURce:AM:STATe ON")
            self.waitResponse()
            self.on = True
        if (not on) and self.on:
            self.sendCommand("SOURce:AM:STATe OFF")
            self.waitResponse()
            self.on = False

    def setPower(self, power_in_mw):
        """
        power_in_mw - The desired laser power in mW.
        """
        if power_in_mw > self.pmax:
            power_in_mw = self.pmax
        self.sendCommand("SOURce:POWer:LEVel:IMMediate:AMPLitude " + str(0.001*power_in_mw))
        self.waitResponse()

    def shutDown(self):
        """
        Turn the laser off and close the RS-232 port.
        """
        if self.live:
            self.setLaserOnOff(False)
        super().shutDown()


#
# Testing
#
if (__name__ == "__main__"):
    import time
    
    obis = Obis(port = "COM19")
    if obis.getStatus():
        print(obis.getPowerRange())
        print(obis.getLaserOnOff())
        obis.setPower(200.0)
        time.sleep(10)
        obis.shutDown()

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

