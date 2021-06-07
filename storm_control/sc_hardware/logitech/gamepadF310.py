#!/usr/bin/env python
"""
Interface to a Logitech gamepad F310 joystick. 

The joystick needs to be in "direct input" mode.
This is done using the switch on the back of the joystick.

Hazen 9/12
Jeff 9/12
Jeff 6/21
"""
import pywinusb.hid as hid


class GamepadF310(object):
    """
    This class encapsulates the interface to a Logitech joystick. 
    """
    def __init__(self, verbose = False, **kwds):
        """
        Create the arrays for translating the joystick objects and try and
        find the joystick among the HID devices that are attached to the computer.
        """
        super().__init__(**kwds)
        
        # initialize internal variables
        self.buttons_triggers = [["A", False, 1], #[name, state bit]
                                 ["B", False, 2],
                                 ["X", False, 3],
                                 ["Y", False, 4],
                                 ["left upper trigger", False, 5],
                                 ["right upper trigger", False, 6],
                                 ["back", False, 7],
                                 ["start", False, 8]]
        self.lower_trigger = [["left lower trigger", False]]
        self.joystick_press = [["left joystick press", False, 1],
                               ["right joystick press", False, 2]]

        self.hats = [["up", False], #[name, state]
                     ["right",False],
                     ["down",False],
                     ["left",False]]
        self.hats_dictionary = {0: [False, False, False, False], 
                                1: [True, False, False, False], # up
                                2: [True, True, False, False], # up + right
                                3: [False, True, False, False], # right
                                4: [False, True, True, False], # down + right
                                5: [False, False, True, False], # down
                                6: [False, False, True, True], # down  + left
                                7: [False, False, False, True], # left
                                8: [True, False, False, True]} # up + left
        
        self.joysticks = [["right joystick", [128, 128]], #[name, [state 1, state 2]]
                         ["left joystick", [128, 128]]]

        self.joystick_threshold = 0.02 # Minimimum absolute displacement
        
        self.data = [0, 128, 128, 128, 128, 128, 128, 128, 128, 0, 128, 0, 0, 0, 0] #default data
        self.events_to_send = []
        self.verbose = verbose
        
        # initialize connection to joystick
        all_hids = hid.find_all_hid_devices()
        self.jdev = False
        if self.verbose:
            print("Searching for HID devices")
        for device in all_hids:
            if self.verbose:
                print(device.product_name)
            if (device.product_name == "Controller (Gamepad F310)"):
                self.jdev = device
                
        if not self.jdev:
            print("Gamepad 310 joystick not found.")

    def dataHandler(self, data):
        """
        Translates joystick events into our internal format, but
        only if they are different from previous events.
        """
        # delete previous events
        self.events_to_send = []
        
        # look for differences between previous data and current data
        data_diff = [0]*len(self.data)
        for i in range(len(data)):
            data_diff[i] = data[i] - self.data[i]
                        
        if any(data_diff[1:9]):
            self.translateJoystick(data)
        if data_diff[10]:
            self.translateLowerLeftTrigger(data)
        if data_diff[11]:
            self.translateButtonsAndUpperTriggers(data)
        if data_diff[12]:
            self.translateHatsAndJoystickPress(data)
        
        # remember data for the next instance
        self.data = data
        if self.verbose:
            print(self.events_to_send)
        return self.events_to_send

    def shutDown(self):
        """
        Close the connection to the joystick at program exit.
        """
        if self.jdev:
            self.jdev.close()

    def start(self, handler):
        """
        Open the connection to the joystick and set the joystict event callback function.
        """
        if self.jdev:
            self.jdev.open()
            self.jdev.set_raw_data_handler(handler)
        else:
            print("Dual action joystick not connected?")

    def translateHatsAndJoystickPress(self, data):
        # First, handle the joystick press
        local_data = data[12]
        for index, action in enumerate(self.joystick_press):
            bit = 1 << (action[2]-1)
            new_action_value = (local_data & bit) == bit
            old_action_value = action[1]
            
            # generate event
            if new_action_value & (not old_action_value):
                self.events_to_send.append([action[0], "Press"])
            elif (not new_action_value) & old_action_value:
                self.events_to_send.append([action[0], "Release"])
            
            # Update the old values
            self.joystick_press[index][1] = new_action_value
            
        # Second, handle the hats
        hat_data = local_data >> 2                
        hat_state = self.hats_dictionary[hat_data]

        # generate Event
        for index, old_hat in enumerate(self.hats):
            if hat_state[index] & (not old_hat[1]):
                self.events_to_send.append([old_hat[0], "Press"])
            elif (not hat_state[index])& old_hat[1]:
                self.events_to_send.append([old_hat[0], "Release"])
            # update hats
            self.hats[index][1] = hat_state[index]

    def translateButtonsAndUpperTriggers(self, data):
        """
        Translate all buttons, joystick presses, and the upper triggers.
        """
        # translate button data
        for index, button in enumerate(self.buttons_triggers):
            # mask appropriate bit to find value of action button
            bit = 1 << (button[2] - 1)
            new_button_value = ((data[11]) & bit) == bit # shift to left most bits then mask
            old_button_value = button[1]
            # generate event
            if new_button_value & (not old_button_value):
                self.events_to_send.append([button[0], "Press"])
            elif (not new_button_value) & old_button_value:
                self.events_to_send.append([button[0], "Release"])

            # update self
            self.buttons_triggers[index][1] = new_button_value
            
    def translateLowerLeftTrigger(self, data):
        new_trigger_value = data[10]>128
        # Toggle the value between pressed and not pressed
        current_trigger_value = self.lower_trigger[0][1]
        if not current_trigger_value and new_trigger_value:
            self.events_to_send.append([self.lower_trigger[0][0], "Press"])
        elif current_trigger_value and not new_trigger_value:
            self.events_to_send.append([self.lower_trigger[0][0], "Release"])
        
        # Update the current trigger value
        self.lower_trigger[0][1] = new_trigger_value

    def translateJoystick(self, data):
        """
        Translate joystick displacement events. The displacement value from the joystick is
        normalized to (-1.0 to 1.0).
        """
        # translate joystick data
        new_j_data = [[data[5], data[7]], [data[1], data[3]]] # deal data to each joystick
        for index, joystick in enumerate(self.joysticks):
            if (new_j_data[index][0] != joystick[1][0]) | (new_j_data[index][1] != joystick[1][1]):
                x = (float(new_j_data[index][0]) - 128.0)/128.0
                y = -(float(new_j_data[index][1]) - 128.0)/128.0 # Force invert y
                
                # Move only if the change is large enough--address modest sticking of joystick
                if (abs(x) > self.joystick_threshold) | (abs(y) > self.joystick_threshold):
                    self.events_to_send.append([joystick[0], [x, y]])
            # update joysticks
            self.joysticks[index][1] = new_j_data[index]


if (__name__ == "__main__"):
    from msvcrt import kbhit
    from time import sleep

    js = GamepadF310(verbose = True)
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

