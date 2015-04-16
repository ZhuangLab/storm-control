#!/usr/bin/python
#
## @file
#
# Voltage control (using National Instruments DAQ) of a
# Mad City Labs piezo Z stage.
#
# Hazen 11/14
#

import sc_hardware.nationalInstruments.nicontrol as nicontrol


## MCLVZControl
#
# Class for controlling MCL Z piezo stage via a DAQ.
#
class MCLVZControl(object):

    ## __init__
    #
    # @param board The DAQ board to use.
    # @param line The analog output line.
    # @param scale (Optional) Conversion from microns to volts (default is 10.0/250.0).
    #
    def __init__(self, board, line, scale = 10.0/250.0):
        #self.board = board
        #self.line = line
        self.scale = scale
        self.ni_task = nicontrol.AnalogOutput(board, line)
        self.ni_task.startTask()

    ## shutDown
    #
    def shutDown(self):
        self.ni_task.stopTask()
        self.ni_task.clearTask()
        #pass

    ## zMoveTo
    #
    # @param z Position to move piezo (in um).
    #
    def zMoveTo(self, z):
        try:
            #nicontrol.setAnalogLine(self.board, self.line, z * self.scale)
            self.ni_task.output(z * self.scale)
        except AssertionError as e:
            print "Caught outputVoltage error:", type(e), str(e)
            self.ni_task.stopTask()
            self.ni_task.clearTask()
            self.ni_task.startTask()

#
# Testing
# 

if __name__ == "__main__":
    stage = MCLVZControl("USB-6002", 0)
    stage.zMoveTo(50.0)
        

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
