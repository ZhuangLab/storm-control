#!/usr/bin/env python
"""
This is used to check the raw events that come from the joystick.

Hazen 9/12
Jeff 9/12
"""
import pywinusb.hid as hid


class Gamepad310(object):
    """
    Encapsulates the interface to a Logitech gamepad joystick.
    """
    def __init__(self, **kwds):
        """
        Find the joystick in the list of HID devices.
        """
        super().__init__(self, **kwds)
        
        # initialize connection to joystick
        all_hids = hid.find_all_hid_devices()
        self.jdev = False
        for device in all_hids:
            if (device.product_name == "Logitech Dual Action"):
                self.jdev = device
                
        if not self.jdev:
            print("Gamepad 310 joystick not found.")

    def dataHandler(self, data):
        """
        Print the data from the joystick.
        """
        print(data)

    def shutDown(self):
        """
        Close the connection to the joystick at program exit.
        """
        if self.jdev:
            self.jdev.close()

    def start(self, handler):
        """
        Open the connection to the joystick and set function to handle joystick events.
        """
        if self.jdev:
            self.jdev.open()
            self.jdev.set_raw_data_handler(handler)
        else:
            print("Dual action joystick not connected?")


if (__name__ == "__main__"):
    from msvcrt import kbhit
    from time import sleep

    js = Gamepad310()
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

