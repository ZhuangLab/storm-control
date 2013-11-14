#!/usr/bin/python
#
## @file
#
# This controls the IX3 microscope using micro-manager.
#
# Hazen 11/13
#

import MMCorePy
import time
import traceback

active = True

def initialize(device_name):
    mmc.loadDevice(device_name, "OlympusIX83", device_name)
    mmc.initializeDevice(device_name)

try:
    # Start micro-manager core & connect to the IX3 controller.
    mmc = MMCorePy.CMMCore()

    # Initialize the devices that we are going to use.
    devs = ["Olympus IX83", 
            "Dichroic 2",
            "DiaShutter",
            "EpiShutter 2",
            "FocusDrive",
            "Light Path",
            "TransmittedIllumination 2"]
    for dev in devs:
        initialize(dev)
    mmc.waitForSystem()
    mmc.enableDebugLog(False)
    mmc.enableStderrLog(False)

except:
    print traceback.format_exc()
    print "Error talking to the ix3 controller via micro-manager."
    active = False

## getBrightness
#
# @return The current lamp brightness (0-255).
#
def getBrightness():
    return int(mmc.getProperty("TransmittedIllumination 2",
                               "Brightness"))


## getDiaShutter
#
# @return True/False if the bright field shutter is open.
#
def getDiaShutter():
    mmc.setShutterDevice("DiaShutter")
    return mmc.getShutterOpen()

## getEpiShutter
#
# @return True/False if the epi shutter is open.
#
def getEpiShutter():
    mmc.setShutterDevice("EpiShutter 2")
    return mmc.getShutterOpen()

## getFilterPosition
#
# @return The current filter position for turret 2.
#
def getFilterPosition():
    return int(mmc.getState("Dichroic 2"))

## getLightPath
#
# @return The current light path.
#
def getLightPath():
    return int(mmc.getState("Light Path"))

## getZPosition
#
# @return The current focus motor position
def getZPosition():
    mmc.setFocusDevice("FocusDrive")
    return mmc.getPosition("FocusDrive")

## setBrightness
#
# @param brightness An integer between 0-255.
#
def setBrightness(brightness):
    mmc.setProperty("TransmittedIllumination 2",
                    "Brightness",
                    int(brightness))
    
## setDiaShutter
#
# Open/close the bright field shutter.
#
# @param shutter_open True/False.
#
def setDiaShutter(shutter_open):
    mmc.setShutterDevice("DiaShutter") 
    if shutter_open:
        mmc.setShutterOpen(True)
    else:
        mmc.setShutterOpen(False)

## setEpiShutter
#
# Open/close the bright epi shutter.
#
# @param shutter_open True/False.
#
def setEpiShutter(shutter_open):
    mmc.setShutterDevice("EpiShutter 2") 
    if shutter_open:
        mmc.setShutterOpen(True)
    else:
        mmc.setShutterOpen(False)

## setFilterPosition
#
# @param position The filter position for turret 2.
#
def setFilterPosition(position):
    mmc.setState("Dichroic 2", int(position))

## setLightPath
#
# @param light_path The desired light path (0-2).
#
def setLightPath(light_path):
    mmc.setState("Light Path", int(light_path))

## setZPosition
#
# @param z_position The desired z position in microns.
#
def setZPosition(z_position):
    return mmc.setPosition("FocusDrive", z_position)

## shutDown
#
# Close the connection to the ix3 microscope at program exit.
#
def shutDown():
    mmc.unloadAllDevices()


# testing.
if (__name__ == "__main__"):

    if 0:
        device  = "Olympus IX83"
        print "Device Properties for:", device
        for i, name in enumerate(mmc.getDevicePropertyNames(device)):
            print i, name

    if 1:
        time.sleep(1)
        print "stage z:", getZPosition()
        setZPosition(1000.0)
        time.sleep(1)
        print "stage z:", getZPosition()
        setZPosition(0.0)

    if 0:
        for i in range(10):
            print i, getBrightness()
            setBrightness(10*(i+1))
            time.sleep(2)
    
    if 0:
        setDiaShutter(False)
        setEpiShutter(False)
        setLightPath(0)
        time.sleep(2)
        print "dia shutter:", getDiaShutter()
        print "epi shutter:", getEpiShutter()
        print "light path:", getLightPath()
        time.sleep(2)
        shutDown()

    if 0:
        for i in range(5):
            setEpiShutter(False)
            time.sleep(1)
            print getEpiShutter()
            time.sleep(1)
            setEpiShutter(True)
            time.sleep(1)
            print getEpiShutter()
            time.sleep(1)

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
 
