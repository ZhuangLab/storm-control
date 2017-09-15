#!/usr/bin/env python
"""
Ludl stage communication.

Hazen 02/14

Edited 5/15 to add Z piezo and TCP/IP protocol
George Emanuel 5/15
"""

import http.client
import sys

import storm_control.sc_library.parameters as params

class Ludl(object):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.live = False
        self.unit_to_um = 0.05
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0
        self.y = 0
        self.z = 0

    def getStatus(self):
        return self.live
        
    def goAbsolute(self, x, y):
        newx = str(int(round(x * self.um_to_unit)))
        newy = str(int(round(y * self.um_to_unit)))
        self._command("Move x=" + newx + ",y=" + newy)

    def goRelative(self, dx, dy):
        newx = str(int(round(dx * self.um_to_unit)))
        newy = str(int(round(dy * self.um_to_unit)))
        self._command("Movrel x=" + newx + ",y="+newy)

    def info(self):
        return self._command("Ver")

    def jog(self, x_speed, y_speed):
        # FIXME: It looks like this stage does not support this type of movement?
        pass
    
#        x_speed = x_speed * self.um_to_unit
#        y_speed = y_speed * self.um_to_unit
#        self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    def joystickOnOff(self, on):
        if on:
            self._command("Joystick X+ Y+")
        else:
            self._command("Joystick X- Y-")
     
    def position(self):
        response = None
        try:
            response = self._command("WHERE X Y B")[0].split(" ")
            self.x = int(response[1]) * self.unit_to_um
            self.y = int(response[2]) * self.unit_to_um
            self.z = int(response[3]) * self.unit_to_um
        except ValueError:
            # Ignore these. One common source is the stage not having a z-axis.
            pass
        except:
            print("Error in Ludl position:", sys.exc_info()[0])
            print("Response was:", response)

        return {"x" : self.x,
                "y" : self.y,
                "z" : self.z}

    def setVelocity(self, x_vel, y_vel):
        """
        Set the maximum velocity in LUDL units.

        (Rough) measurements with stspeed = 50000:
        10000 - about 10 seconds to move 5mm.
        25000 - about 3.5 seconds to move 5mm.
        """
        self._command("Speed x=" + str(x_vel))
        self._command("Speed y=" + str(y_vel))

    def status(self):
        return self._command("Status")

    def zero(self):
        self._command("Here x=0 y=0 b=0")

    def zMoveTo(self, z):
        self._command("Move B=" + str(int(round(z * self.um_to_unit))))

    def zMoveRelative(self, dz):
        self._command("Moverel B=" + str(int(round(dz * self.um_to_unit))))

    def zPosition(self):
        return int(self._command("WHERE B")[0].split(" ")[1])*self.unit_to_um


class LudlRS232(Ludl):
    """
    Encapsulates control of a XY Ludl stage, communicating through serial.
    """
    def __init__(self, port="COM19", timeout = None, baudrate = 115200, wait_time = 0.02, **kwds):
        super().__init__(**kwds)

        import storm_control.sc_hardware.serial.RS232 as RS232

        # Open connection.
        self.connection = RS232.RS232(baudrate = baudrate,
                                      end_of_line = "\r",
                                      port = port,
                                      timeout = timeout,
                                      wait_time = wait_time)

        # Test connection.
        self.live = True
        try:
            test = self._command("Ver")
        except AttributeError:
            self.live = False
        if not self.live:
            print("Ludl Stage is not connected? Stage is not on?")

        #Set to analog mode?
        if (self.live):
            #set z piezo to be controlled by serial     
            #self._command("CAN 3, 83, 267, 0")
            self._command("stspeed x=50000, y=50000")

    def _command(self, command):
        response = self.connection.commWithResp(command)
        if response:
            return response.split("\r")

    def shutDown(self):
        """
        Closes the RS-232 port.
        """
        if self.live:
            self.connection.shutDown()

    
class LudlTCP(Ludl):
    """
    Encapsulates control of a XY Ludl stage, communicating through TCP/IP.
    """
    def __init__(self, ip_address="192.168.100.1", **kwds):
        super().__init__(**kwds)
        self.encoding = 'utf-8'
        self.ip_address = ip_address
        self.connection = http.client.HTTPConnection(self.ip_address, timeout=10)
        
        # Test connection.
        self.live = True

        try:
            test = self._command("Ver")
        except:
            print("Error in LudlTCP init:", sys.exc_info())
            self.live = False
        if not self.live:
            print("Ludl Stage is not connected? Stage is not on?")

        if (self.live):
#            self._command("CAN 3, 83, 267, 0")
            #
            # FIXME? If this is really the starting speed then it
            #        is larger than the maximum speed, is that a
            #        good idea?
            #
            self._command("stspeed x=50000")
            self._command("stspeed y=50000")

    def _command(self, command):
        try:
            self.connection.request("GET", self.formCommand(command))
            response = self.connection.getresponse().read().decode(self.encoding).split("\r")[2].strip()
            return ["A: " + response]
        except http.client.CannotSendRequest:
            print("Stage connection lost, attempting re-connection.")
            self.connection.close()
            self.connection = http.client.HTTPConnection(self.ip_address, timeout=1)

    def formCommand(self, command):
        """
        Creates a properly formatted command.
        """
        msg = "/conajx.asp?&ECMD1=\"" + command + "\""
        return msg
        #return msg.encode(self.encoding)
    
    def shutDown(self):
        """
        Closes the HTTP connection.
        """
        if self.live:
            self.connection.close()


#
# Testing
# 

if (__name__ == "__main__"):
    import time

    stage = LudlRS232("COM29")
    #stage = LudlTCP()
    
    if stage.getStatus():
        print(stage.position())

        if True:
            stage.zero()
            time.sleep(0.5)
            stage.goRelative(1000.0, 1000.0)
            for i in range(10):
                start_time = time.time()
                status = stage.status()
                print(i, status, time.time() - start_time)
            time.sleep(1.0)
            print(stage.status())
            print(stage.position())
            stage.goAbsolute(0.0, 0.0)
            time.sleep(1.0)
            print(stage.position())
        
    stage.shutDown()

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
