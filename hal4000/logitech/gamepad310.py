#!/usr/bin/python
#
# Interface to Logitech gamepad 310 joystick.
#
# The joystick needs to be in "direct input" mode.
# This is done using the switch on the back of the joystick.
#
# Hazen 9/12
# Jeff 9/12
#

import pywinusb.hid as hid

class Gamepad310():
    def __init__(self):
        # initialize internal variables
        self.buttons = [["A", False, 2], #[name, state bit]
                        ["B", False, 3],
                        ["X", False, 1],
                        ["Y", False, 4]]
        self.actions = [["left joystick press", False, 7], #[name, state, bit]
                        ["right joystick press", False, 8],
                        ["left upper trigger", False, 1],
                        ["right upper trigger", False, 2],
                        ["left lower trigger", False, 3],
                        ["right lower trigger", False, 4],
                        ["back", False, 5],
                        ["start", False, 6]]
        self.hats = [["up", False], #[name, state]
                     ["right",False],
                     ["down",False],
                     ["left",False]]
        self.hats_dictionary = {0: [True, False, False, False], 
                                1: [True, True, False, False],
                                2: [False, True, False, False],
                                3: [False, True, True, False],
                                4: [False, False, True, False],
                                5: [False, False, True, True],
                                6: [False, False, False, True],
                                7: [True, False, False, True],
                                8: [False, False, False, False]}
        self.joysticks = [["right joystick", [128, 128]], #[name, [state 1, state 2]]
                         ["left joystick", [128, 128]]]
        self.data = [0, 128, 127, 128, 127, 8, 0, 0, 255] #default data
        self.events_to_send = []
        
        # initialize connection to joystick
        all_hids = hid.find_all_hid_devices()
        self.jdev = False
        for device in all_hids:
            if (device.product_name == "Logitech Dual Action"):
                self.jdev = device
                
        if not self.jdev:
            print "Gamepad 310 joystick not found."

    def dataHandler(self, data):
        # delete previous events
        self.events_to_send = []
        
        # look for differences between previous data and current data
        data_diff = [0,0,0,0,0,0,0,0,0]
        for i in range(len(data)):
            data_diff[i] = data[i] - self.data[i]
        
        if any(data_diff[1:5]):
            self.translateJoystick(data)
        if data_diff[5]:
            self.translateHatAndButtons(data)
        if data_diff[6]:
            self.translateAction(data)
        # remember data for the next instance
        self.data = data
        print self.events_to_send
        return self.events_to_send        
        
    def shutDown(self):
        if self.jdev:
            self.jdev.close()

    def start(self, handler):
        if self.jdev:
            self.jdev.open()
            self.jdev.set_raw_data_handler(handler)
        else:
            print "dual action joystick not connected?"

    def translateAction(self, data):
        # translate action data
        for index, action in enumerate(self.actions):
            # mask appropriate bit to find value of action button
            bit = 1 << (action[2] - 1)
            new_action_value = (data[6] & bit) == bit
            old_action_value = action[1]

            # generate event
            if new_action_value & (not old_action_value):
                self.events_to_send.append([action[0], "Press"])
            elif (not new_action_value) & old_action_value:
                self.events_to_send.append([action[0], "Release"])

            # update self
            self.actions[index][1] = new_action_value
            
    def translateHatAndButtons(self, data):        
        # translate button data
        for index, button in enumerate(self.buttons):
            # mask appropriate bit to find value of action button
            bit = 1 << (button[2] - 1)
            new_button_value = ((data[5]>>4) & bit) == bit # shift to left most bits then mask
            old_button_value = button[1]
            # generate event
            if new_button_value & (not old_button_value):
                self.events_to_send.append([button[0], "Press"])
            elif (not new_button_value) & old_button_value:
                self.events_to_send.append([button[0], "Release"])

            # update self
            self.buttons[index][1] = new_button_value
            
        # translate hat data
        hat_state = self.hats_dictionary[data[5]&15] # remove the button data in the last 4 bits
        
        # generate Event
        for index, old_hat in enumerate(self.hats):
            if hat_state[index] & (not old_hat[1]):
                self.events_to_send.append([old_hat[0], "Press"])
            elif (not hat_state[index])& old_hat[1]:
                self.events_to_send.append([old_hat[0], "Release"])
            # update hats
            self.hats[index][1] = hat_state[index]
        
    def translateJoystick(self, data):        
        # translate joystick data
        new_j_data = [data[3:5], data[1:3]] # deal data to each joystick
        for index, joystick in enumerate(self.joysticks):
            if (new_j_data[index][0] != joystick[1][0]) | (new_j_data[index][1] != joystick[1][1]):
                x = (float(new_j_data[index][0]) - 128.0)/128.0
                y = (float(new_j_data[index][1]) - 128.0)/128.0
                self.events_to_send.append([joystick[0], [x, y]])
            # update joysticks
            self.joysticks[index][1] = new_j_data[index]
#
# Testing
#

if __name__ == "__main__":
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

