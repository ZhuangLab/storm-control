#!/usr/bin/python
#
## @file
#
# Control of various Nikon TiU accessories (using Micro-Manager).
#
# Hazen 4/15
#

import MMCorePy

## TiUMisc
#
# Encapsulates control of various TiU accessories.
#
class TiUMisc(object):

    ## __init__
    #
    def __init__(self):
        self.mmc = MMCorePy.CMMCore()
        self.mmc.loadDevice('TIScope', 'NikonTI', 'TIScope')
        self.mmc.loadDevice('TIDiaShutter', 'NikonTI', 'TIDiaShutter')
        self.mmc.loadDevice('TIFilterBlock1', 'NikonTI', 'TIFilterBlock1')
        self.mmc.loadDevice('TITIRF', 'NikonTI', 'TITIRF')
        self.mmc.initializeAllDevices()

        self.tirf_scale = 1000.0

    ## getBrightFieldShutter
    #
    # @return True - Open / False - Closed
    #
    def getBrightFieldShutter(self):
        if (self.mmc.getProperty('TIDiaShutter', 'State') == "1"):
            return True
        else:
            return False

    ## getFilterWheel
    #
    # @return Current position of the filter wheel.
    #
    def getFilterWheel(self):
        return int(self.mmc.getProperty('TIFilterBlock1', 'State'))

    ## getTirfPosition
    #
    # @return Current tirf position.
    #
    def getTirfPosition(self):
        return float(self.mmc.getProperty('TITIRF', 'Position')) / self.tirf_scale

    ## isTirfBusy
    #
    # @return True/False if the tirf motor is busy.
    #
    def isTirfBusy(self):
        return self.mmc.deviceBusy('TITIRF')

    ## setBrightFieldShutter
    #
    # @param state True - Open / False - Closed
    #
    def setBrightFieldShutter(self, state):
        if state:
            self.mmc.setProperty('TIDiaShutter', 'State', str(1))
        else:
            self.mmc.setProperty('TIDiaShutter', 'State', str(0))
        
    ## setFilterWheel
    #
    # @param state The filter wheel position.
    #
    def setFilterWheel(self, state):
        self.mmc.setProperty('TIFilterBlock1', 'State', str(state))

    ## setTirfPosition
    #
    # @param position The tirf position.
    #
    def setTirfPosition(self, position):
        self.mmc.setProperty('TITIRF', 'Position', str(position * self.tirf_scale))

