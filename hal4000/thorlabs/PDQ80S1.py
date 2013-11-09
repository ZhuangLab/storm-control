#!/usr/bin/python
#
## @file
#
# Communicates with Thorlabs PDQ80S1 quadrant photodiode detector system.
#
# Hazen 3/09
#

from ctypes import *
import time
import os

pdq = 0
## loadPDQ
#
# Load the Thorlabs DLL for communicating with the quadrant photo-diode.
#
def loadPDQ():
    global pdq
    if (pdq == 0):
        if os.path.exists("xUSB.dll"):
            pdq = cdll.LoadLibrary("xUSB")
        else:
            pdq = cdll.LoadLibrary("thorlabs/xUSB")

instantiated = 0
## PDQ80S1
#
# PDQ80S1 interface class.
#
class PDQ80S1:

    ## __init__
    #
    # @param interval The read rate in milliseconds?
    #
    def __init__(self, interval = 5):
        global instantiated
        assert instantiated == 0, "Attempt to instantiate two PDQ80S1 qpd instances."
        instantiated = 1

        loadPDQ()
        self.interval = interval
        self.initialize()

    ## doScan
    #
    # @param points The number of times to get a reading from the QPD.
    #
    def doScan(self, points):
        assert points > 0, "qpdScan: points less than 1 " + str(points)
        assert points < 255, "qpdScan: points greater than 255 " + str(points)
        sensor_data_type = c_short * 12
        sensor_data = sensor_data_type()
        x_ref = 0.0
        y_ref = 0.0
        s_ref = 0.0
        x_diff = 0.0
        y_diff = 0.0
        sum = 0.0
        for i in range(points):
            assert pdq.PDQReadScan(sensor_data, 12, 1000) == 1, "PDQReadScan failed."
            #
            # This check was put in to see if we ever got spurious reads.
            # We just average them in anyway, as we mostly only seem to
            # get them when the stage jumps a large distance to a new position,
            # so presumably they are only transiently a problem.
            #
            good = 1
            if i != 0:
                if abs(x_ref - sensor_data[0]) > 40:
                    good = 0
                    print "doScan (qpd), bad x", x_ref, sensor_data[0]
                if abs(y_ref - sensor_data[1]) > 40:
                    good = 0
                    print "doScan (qpd), bad y", y_ref, sensor_data[1]
                if abs(s_ref - sensor_data[2]) > 40:
                    good = 0
                    print "doScan (qpd), bad sum", s_ref, sensor_data[2]
            if good:
                x_ref = sensor_data[0]
                y_ref = sensor_data[1]
                s_ref = sensor_data[2]
            x_diff += sensor_data[0]
            y_diff += sensor_data[1]
            sum += sensor_data[2]
                
        return [x_diff/points, y_diff/points, sum/points]

    ## initialize
    #
    # Initialize the QPD and set the scan interval.
    #
    def initialize(self):
        assert pdq.USBinitPDQ80S1() == 0, "USBinitPDQ80S1 failed."
        self.setScanInterval(self.interval)

    ## getScanParameters
    #
    # @return An array containing the scan parameters.
    #
    def getScanParameters(self):
        # the default seems to be a 10ms scan time.
        scan_parameters_type = c_ubyte * 3
        scan_parameters = scan_parameters_type()
        assert pdq.PDQRetrieveScanParameters(scan_parameters) == 0, "PDQRetrieveScanParameters failed."
        return [scan_parameters[0], scan_parameters[1], scan_parameters[2]]

    ## qpdScan
    #
    # @param points The number of readings to get from the QPD.
    #
    def qpdScan(self, points):
        #
        # Originally I tried to scan for a fixed number of points
        # but then you have the problem that if you miss one you'll
        # hang forever. Presumably that was the idea behind the timeout
        # parameter in PDQReadScan, but it is either meaningless or
        # not in milliseconds as the documentation suggests?
        #
#        assert pdq.PDQStartScan(c_ubyte(points)) == 0, "PDQStartScan failed."
        assert pdq.PDQStartScan(0) == 0, "PDQStartScan failed."
        scan_data = self.doScan(points)
        #
        # PDQStopScan can fail, perhaps because the USB device gets behind?
        # We try to save things by basically turning it off, turning it
        # back on and trying again.
        #
#        assert pdq.PDQStopScan() == 0, "PDQStopScan failed."
        resp = pdq.PDQStopScan()
        while resp != 0:
            print "  PDQStopScan failed, attempting to re-initialize the device"
            time.sleep(0.1)
            assert pdq.USBUninit() == 0, "USBUninit failed."
            self.initialize()
            assert pdq.PDQStartScan(0) == 0, "PDQStartScan failed."
            self.doScan(points)
            resp = pdq.PDQStopScan()
        return scan_data

    ## setScanInterval
    #
    # @param interval An integer time in milliseconds that is greater than zero.
    #
    def setScanInterval(self, interval):
        # interval is a integer time in milliseconds > 0
        assert interval > 0, "setScanInterval: interval is too small " + str(interval)
        assert pdq.PDQSendScanInterval(c_uint(interval), 0) == 0, "PDQSendScanInterval failed."

    ## shutDown
    #
    # Shut down the connection to the QPD.
    #
    def shutDown(self):
        assert pdq.USBUninit() == 0, "USBUninit failed."
        global instantiated
        instantiated = 0


# testing

if __name__ == "__main__":
    def take_data(filename, interval, points):
        data_fp = open(filename, "w")
        qpd = PDQ80S1(interval = interval)
        for i in range(10):
            print " ", i
            data = qpd.qpdScan(points)
            print data[0], data[1], data[2]
            data_fp.write("{0:.4f} {1:.4f} {2:.4f}\n".format(data[0], data[1], data[2]))
        qpd.shutDown()
        data_fp.close()

    if 0:
        take_data("data_1.txt", 5, 10)

    if 1:
        qpd = PDQ80S1()
        for i in range(10000):
            if ((i % 100)==0):
                print i, qpd.qpdScan(10)
            else:
                qpd.qpdScan(10)
        qpd.shutDown()


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
