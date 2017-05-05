#!/usr/bin/env python
"""
The core functionality for a QPD, QPD/Camera or z stage.

Hazen 04/17
"""

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class LockFunctionalityMixin(object):
    """
    Combine this with either a HardwareFunctionality or a
    BufferedFunctionality depending on how responsive the 
    device is. Most of these are to help the focus lock GUI
    render the output of the device properly.
    """
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.parameters = parameters

    def getParameter(self, pname):
        return self.parameters.get(pname)

    def hasParameter(self, pname):
        return self.parameters.has(pname)
    

class QPDFunctionalityMixin(LockFunctionalityMixin):
    """
    QPDs are expected to return the current offset in
    units of microns.

    A QPD must emit a qpdUpdate signal:
      qpdUpdate() - The current QPD state as a dictionary. 
                    {"offset" : offset(microns),
                     "sum" : sum signal (AU),
                     other data..}
    """
    def __init__(self, units_to_microns = None, **kwds):
        super().__init__(**kwds)
        self.units_to_microns = units_to_microns

    def getOffset(self):
        """
        Perform a reading & emit the qpdUpdate signal. The time
        that this takes will determine the focus lock update time,
        so ideally it is not too slow (or too fast), something
        like 1/10th second is good.
        """
        pass
        
    def getType(self):
        return "qpd"
    

class QPDCameraFunctionalityMixin(QPDFunctionalityMixin):

    def adjustAOI(self, dx, dy):
        """
        Adjust the camera AOI.
        """
        pass

    def adjustZeroDist(self, inc):
        """
        Adjust the inter spot distance that will is zero.
        """
        pass

    def changeFitMode(self, mode):
        """
        Change how the spot(s) are fit to measure the offset.
        """
        pass

    def getType(self):
        return "camera"


class ZStageFunctionalityMixin(LockFunctionalityMixin):
    """
    Z stages are expected to work in units of microns.

    A Z stage emits one signal:
    (1) zStagePosition() - The current z stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.z_position = 0.0

    def getCenterPosition(self):
        return self.getParameter("center")
    
    def getCurrentPosition(self):
        return self.z_position

    def getDaqWaveform(self, waveform):
        """
        Scale the analog waveform (a numpy array) that the daq will use to drive 
        the z-stage in hardware timed mode to the correct voltages.

        Returns a daqModule.DaqWaveform object.
        """
        pass

    def getMaximum(self):
        return self.getParameter("maximum")

    def getMinimum(self):
        return self.getParameter("minimum")
    
    def goAbsolute(self, z_pos):
        pass

    def goRelative(self, z_delta):
        pass

    def haveHardwareTiming(self):
        """
        Return True/False if the stage supports hardware timing. What this
        currently means is that the stage is actually driven by a DAQ card, 
        so the DAQ card can control the stage movement timed off a camera.
        Typically only used while filming to z scans.
        """
        return False
    
    def recenter(self):
        self.goAbsolute(self.getCenterPosition())


class LockModule(hardwareModule.HardwareModule):
    pass

        
