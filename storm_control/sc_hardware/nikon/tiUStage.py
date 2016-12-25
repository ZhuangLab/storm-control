#!/usr/bin/python
#
## @file
#
# Nikon TiU stage communication (using Micro-Manager).
#
# Hazen 4/15
#

import MMCorePy

## TiUStage
#
# Encapsulates control of a Nikon TiU stage.
#
class TiUStage(object):

    ## __init__
    #
    def __init__(self):
        self.dev_name = 'TIXYDrive'
        self.mmc = MMCorePy.CMMCore()
        self.mmc.loadDevice('TIScope', 'NikonTI', 'TIScope')
        self.mmc.loadDevice(self.dev_name, 'NikonTI', self.dev_name)
        self.mmc.initializeAllDevices()
        #self.mmc.setXYStageDevice('TIXYDrive')

    ## getStatus
    #
    def getStatus(self):
        return True

    ## goAbsolute
    #
    # @param x X position in um.
    # @param y Y position in um.
    #
    def goAbsolute(self, x, y):
        self.mmc.setXYPosition(self.dev_name, x, y)

    ## goRelative
    #
    # @param x X position in um.
    # @param y Y position in um.
    #
    def goRelative(self, x, y):
        self.mmc.setRelativeXYPosition(self.dev_name, x, y)

    ## jog
    #
    # @param x_speed Speed the stage should be moving at in x in um/s.
    # @param y_speed Speed the stage should be moving at in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        pass
    
    ## joystickOnOff
    #
    # @param on True/False enable/disable the stage joystick.
    #
    def joystickOnOff(self, on):
        pass

    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)].
    #
    def position(self):
        return [self.mmc.getXPosition(self.dev_name), self.mmc.getYPosition(self.dev_name), 0.0]

    ## setVelocity
    #
    # @param x_vel The maximum stage velocity allowed in x.
    # @param y_vel The maximum stage velocity allowed in y.
    #
    def setVelocity(self, x_vel, y_vel):
        pass

    ## shutDown
    def shutDown(self):
        pass

    ## zero
    #
    # Set the current position as the stage zero position.
    #
    def zero(self):
        self.mmc.setOriginXY(self.dev_name)

