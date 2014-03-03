#!/usr/bin/python
#
## @file
#
# Dummy classes for use when you have some but not all 
# of the focus lock functionality.
#
# Hazen 12/09
#

import time

## QPD
#
# A fake QPD class.
#
class QPD():

    ## __init__
    #
    # Creates the fake QPD object.
    #
    def __init__(self):
        pass

    ## qpdScan
    #
    # @return [1000.0, 0.0, 0.0]
    #
    def qpdScan(self):
        time.sleep(0.05)
        return [1000.0, 0.0, 0.0]

    ## shutDown
    #
    # NOP.
    #
    def shutDown(self):
        pass

## NanoP
#
# Fake nano-positioner class.
#
class NanoP():

    ## __init__
    #
    # Create the fake nano-positioner object.
    #
    def __init__(self):
        pass

    ## zMoveTo
    #
    # @param position The position to move to.
    #
    def zMoveTo(self, position):
        pass

    ## shutDown
    #
    # NOP.
    #
    def shutDown(self):
        pass

## IrLaser
#
# Fake IR laser class.
#
class IRLaser():

    ## __init__
    #
    # Create the fake IR laser object.
    #
    def __init__(self):
        pass

    ## havePowerControl
    #
    # @return False
    #
    def havePowerControl(self):
        return False

    ## on
    #
    # NOP
    #
    def on(self, power):
        pass

    ## off
    #
    # NOP
    #
    def off(self):
        pass
    
#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
