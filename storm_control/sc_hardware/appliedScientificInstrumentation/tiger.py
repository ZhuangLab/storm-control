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
        pass

    def joystickOnOff(self, on):
        if on:
            self.commWithResp("J X+ Y+")
        else:
            self.commWithResp("J X- Y-")

    def position(self):
        #try:
        [self.x, self.y] = map(lambda x: float(x)*self.unit_to_um, 
                               self.commWithResp("W X Y").split(" ")[1:3])
        #except:
        #    hdebug.logText("  Warning: Bad position from ASI stage.")
        return {"x" : self.x,
                "y" : self.y}

    def setVelocity(self, x_vel, y_vel):
        """
        Set the maximum speed in mm/sec.
        """
        self.commWithResp("S X={0:.2f} Y={1:.2f}".format(x_vel, y_vel))

    def zero(self):
        self.commWithResp("Z")


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


