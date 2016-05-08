#!/usr/bin/python
#
## @file
#
# A generic wrapper class for a spinning disk without a UI. All parameters are controlled from the Hal parameters editor. 
#
# Jeff Moffitt 5/16
#

from PyQt4 import QtCore, QtGui
import qtWidgets.qtAppIcon as qtAppIcon
import halLib.halModule as halModule
import sc_library.halExceptions as halExceptions

# Debugging
import sc_library.hdebug as hdebug

# spinning disk
import sc_hardware.andor.w1SpinDisk as w1SpinDisk

## SpinningDiskControl
#
# Spinning Disk Control Dialog Box
#
# This is the UI for controlling a generic spinning disk.
#
class SpinningDiskControl(halModule.HalModule):

    ## __init__
    #
    # @param hardware A hardware xml object.
    # @param parameters A parameters object.
    # @param spinning_disk An instance of the hardware class that controls the spinning disk
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent):
        halModule.HalModule.__init__(self)

        print hardware

        # Create spinning disk
        self.spinning_disk = w1SpinDisk.W1SpinningDisk(hardware.get("com_port"), parameters)
                
        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        if self.spinning_disk:
            self.spinning_disk.cleanup()

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug    
    def newParameters(self, parameters):
        if self.spinning_disk:
            try:
                self.spinning_disk.newParameters(parameters) # Pass all parameters
            except halExceptions.HardwareException as error:
                error_message = "newParameters error in spinning disk control: \n" + str(error)
                hdebug.logText(error_message)
                raise halModule.NewParametersException(error_message)

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
