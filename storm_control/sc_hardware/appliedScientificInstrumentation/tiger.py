#!/usr/bin/env python
"""
RS-232 interface to an ASI tiger controller.

Hazen 05/18
"""
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232
import storm_control.sc_library.hdebug as hdebug


class Tiger(RS232.RS232):
    """
    Tiger controller interface class.
    """
    def __init__(self, **kwds):
        """
        Connect to the tiger controller at the specified port.
        """
        self.live = True
        self.unit_to_um = 0.1
        self.um_to_unit = 1.0/self.unit_to_um

        # FIXME: Why are we storing the position?
        self.x = 0
        self.y = 0
        self.z = 0

        # Try and connect to the controller.
        try:
            super().__init__(**kwds)
            assert not (self.commWithResp("WHO") == None)

        except (AttributeError, AssertionError):
            print(traceback.format_exc())
            self.live = False
            print("Tiger controller is not connected? Controller is not on?")
            print("Failed to connect to the tiger controller at port", kwds["port"])

    def goAbsolute(self, x, y):
        self.commWithResp("M X={0:.1f} Y={1:.1f}".format(x * self.um_to_unit, y * self.um_to_unit))

    def goRelative(self, x, y):
        self.commWithResp("R X={0:.1f} Y={1:.1f}".format(x * self.um_to_unit, y * self.um_to_unit))

    def jog(self, x_speed, y_speed):
        # Stage velocities are in units of mm/sec.
        vx = x_speed * self.um_to_unit * 1.0e-3
        vy = y_speed * self.um_to_unit * 1.0e-3
        self.commWithResp("VE X={0:.3f} Y={1:.3f}".format(vx, vy))

    def joystickOnOff(self, on):
        # This also turns off the stage motors to disable position
        # feedback control during movies.
        if on:
            self.commWithResp("J X+ Y+")
            self.commWithResp("MC X+ Y+ Z+")
        else:
            self.commWithResp("J X- Y-")
            self.commWithResp("MC X- Y- Z-")

    def position(self):
        [self.x, self.y] = map(lambda x: float(x)*self.unit_to_um, 
                               self.commWithResp("W X Y").split(" ")[1:3])
        return {"x" : self.x,
                "y" : self.y}

    def setLED(self, address, channel, power):
        self.commWithResp(address + "LED " + channel + "={0:0d}".format(int(power)))

    def setTTLMode(self, address, mode):
        self.commWithResp(address + "TTL X={0:0d}".format(int(mode)))

    def setVelocity(self, x_vel, y_vel):
        """
        Set the maximum X/Y speed in mm/sec.
        """
        self.commWithResp("S X={0:.2f} Y={1:.2f}".format(x_vel, y_vel))

    def zero(self):
        self.commWithResp("H X Y")

    def zConfigurePiezo(self, axis, mode):
        self.commWithResp("PM " + str(axis) + "=" + str(mode))
        
    def zMoveTo(self, z):
        """
        Move the z stage to the specified position (in microns).
        """
        self.commWithResp("M Z={0:.2f}".format(z * self.um_to_unit))

    def zPosition(self):
        """
        Query for current z position in microns.
        """
        new_z = self.z
        try:
            temp = self.commWithResp("W Z")
            new_z = float(temp.split(" ")[1])*self.unit_to_um
        except ValueError:
            print("Tiger.zPosition(): could not parse -", temp, "-")            
        self.z = new_z
        return {"z" : self.z}

    def zSetVelocity(self, z_vel):
        """
        Set the maximum Z speed in mm/sec.
        """
        self.commWithResp("S Z={0:.2f}".format(z_vel))
        
    def zZero(self):
        self.commWithResp("H Z")
        

if (__name__ == "__main__"):
    import time
    
    stage = Tiger(port = "COM4", baudrate = 115200)
    print(stage.position())

    stage.goRelative(100,0)
    time.sleep(0.5)
    print(stage.position())

    stage.goAbsolute(0,0)
    time.sleep(0.5)
    print(stage.position())
    
    stage.shutDown()


