#!/usr/bin/python
#
## @file
#
# Test communiction with Nikon TI microscope.
#
# Hazen 04/14
#

import MMCorePy
import time

mmc1 = MMCorePy.CMMCore()
mmc1.loadDevice('TIScope', 'NikonTI', 'TIScope')
mmc1.loadDevice('TITIRF', 'NikonTI', 'TITIRF')
mmc1.loadDevice('TIFilterBlock1', 'NikonTI', 'TIFilterBlock1')
mmc1.initializeAllDevices()

mmc2 = MMCorePy.CMMCore()
mmc2.loadDevice('TIScope', 'NikonTI', 'TIScope')
mmc2.loadDevice('TIXYDrive', 'NikonTI', 'TIXYDrive')
mmc2.initializeAllDevices()

mmc3 = MMCorePy.CMMCore()
mmc3.loadDevice('TIScope', 'NikonTI', 'TIScope')
mmc3.loadDevice('TIZDrive', 'NikonTI', 'TIZDrive')
mmc3.initializeAllDevices()

time.sleep(0.5)

mmc2.setXYStageDevice('TIXYDrive')
print mmc2.getXPosition('TIXYDrive'), mmc2.getYPosition('TIXYDrive')
print mmc3.getPosition('TIZDrive')

def valToType(val):
    if (val == 0):
        return "None"
    if (val == 1):
        return "String"
    if (val == 2):
        return "Float"
    if (val == 3):
        return "Int"

def listProps(mmcore, dev_label):
    dev_props = mmcore.getDevicePropertyNames(dev_label)
    for prop in dev_props:
        print prop, valToType(mmcore.getPropertyType(dev_label, prop)), mmcore.getProperty(dev_label, prop)
        if mmcore.hasPropertyLimits(dev_label, prop):
            print "  ", mmcore.getPropertyLowerLimit(dev_label, prop), mmc1.getPropertyUpperLimit(dev_label, prop)
    print ""

listProps(mmc1, 'TITIRF')
listProps(mmc1, 'TIFilterBlock1')
listProps(mmc2, 'TIXYDrive')



#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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
