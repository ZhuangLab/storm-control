#!/usr/bin/python
#
## @file
#
# Interface to Logitech dual action joystick.
#
# Hazen 9/12
#

import pywinusb.hid as hid

## DualAction
#
# This class encapsulates the interface to a Logitech dual action 
# joystick. It remains in the project for reference purposes
# but it would not work correctly with HAL. See gamepad310.py for
# an example of a joystick class that works with HAL.
#
class DualAction():

    ## __init__
    #
    # Define arrays for translating joystick events and find the joystick HID.
    #
    def __init__(self):
        self.buttons = [[1,24,0],  # 1
                        [2,40,0],  # 2
                        [3,72,0],  # 3
                        [4,136,0], # 4
                        [5,8,1],   # 5
                        [6,8,2],   # 6
                        [7,8,4],   # 7
                        [8,8,8],   # 8
                        [9,8,16],  # 9
                        [10,8,32]]  # 10
        self.down = False
        self.hats = [["up",0,0],
                     ["left",6,0],
                     ["right",2,0],
                     ["down",4,0]]

        # initialize connection to joystick
        all_hids = hid.find_all_hid_devices()
        self.jdev = False
        for device in all_hids:
            if (device.product_name == "Logitech Dual Action"):
                self.jdev = device

        if not self.jdev:
            print "Logitech Dual Action joystick not found."

    ## dataHandler
    #
    # Processes events from the joystick.
    #
    # @param data A joystick event.
    #
    def dataHandler(self, data):
        print self.translate(data)

    ## shutDown
    #
    # Close the connection to the joystick at program exit.
    #
    def shutDown(self):
        if self.jdev:
            self.jdev.close()

    ## start
    #
    # Open the connection to the joystick and set handler as the callback function.
    #
    # @param handler The function to use to process joystick events.
    #
    def start(self, handler):
        if self.jdev:
            self.jdev.open()
            self.jdev.set_raw_data_handler(handler)
        else:
            print "dual action joystick not connected?"

    ## translate
    #
    # Translate joystick events to our format.
    #
    # @param data A event from the joystick.
    #
    # @return The translated event.
    #
    def translate(self, data):
        # check if it was a button event
        ##JRM If multiple joystick events are generated, this software can generate the wrong signal
        for button in self.buttons:
            if (button[1] == data[5]) and (button[2] == data[6]):
                self.down = True
                return ["Button", button[0]]

        # check if it was a hat event
        for hat in self.hats:
            if (hat[1] == data[5]) and (hat[2] == data[6]):
                self.down = True
                return ["Hat", hat[0]]

        # otherwise it must have been a joystick event
        if not self.down:
            jpos = ["Joystick"]
            for i in range(4):
                tmp = (float(data[i+1])-128.0)/128.0
                jpos.append(tmp)
            return jpos

        self.down = False
        return ["NA"]


#
# Testing
#

if __name__ == "__main__":
    from msvcrt import kbhit
    from time import sleep

    js = DualAction()
    js.start(js.dataHandler)
    while not kbhit():
        sleep(0.5)
    js.shutDown()

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

