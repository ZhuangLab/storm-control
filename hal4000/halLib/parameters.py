#!/usr/bin/python
#
# Handles parsing settings xml files and getting/setting 
# the resulting settings. Primarily designed for use
# by the hal acquisition program.
#
# Hazen 12/09
#

import copy
from xml.dom import minidom, Node

default_params = 0

def setDefaultShutter(shutters_filename):
    global default_params
    if default_params:
        default_params.shutters = shutters_filename

class Parameters:
    # Dynamically create the class by processing the 
    # parameters xml file.
    def __init__(self, parameters_file):
        max_channels = 8
        xml = minidom.parse(parameters_file)
        settings = xml.getElementsByTagName("settings").item(0)
        for node in settings.childNodes:
            if node.nodeType == Node.ELEMENT_NODE:
                # single parameter setting
                if len(node.childNodes) == 1:
                    slot = node.nodeName
                    # default power settings
                    if slot == "default_power":
                        if not hasattr(self, "default_power"):
                            self.on_off_state = []
                            self.default_power = []
                            for i in range(max_channels):
                                self.default_power.append(1.0)
                                self.on_off_state.append(0)
                        power = float(node.firstChild.nodeValue)
                        channel = int(node.attributes.item(0).value)
                        self.default_power[channel] = power
                    # power buttons
                    elif slot == "button":
                        if not hasattr(self, "power_buttons"):
                            self.power_buttons = []
                            for i in range(max_channels):
                                self.power_buttons.append([])
                        name = node.firstChild.nodeValue
                        channel = int(node.attributes.item(1).value)
                        power = float(node.attributes.item(0).value)
                        self.power_buttons[channel].append([name, power])
                    # all the other settings
                    else:
                        value = node.firstChild.nodeValue
                        type = node.attributes.item(0).value
                        if type == "int":
                            setattr(self, slot, int(value))
                        elif type == "int-array":
                            text_array = value.split(",")
                            int_array = []
                            for elt in text_array:
                                int_array.append(int(elt))
                            setattr(self, slot, int_array)
                        elif type == "float":
                            setattr(self, slot, float(value))
                        elif type == "float-array":
                            text_array = value.split(",")
                            float_array = []
                            for elt in text_array:
                                float_array.append(float(elt))
                            setattr(self, slot, float_array)
                        elif type == "string-array":
                            setattr(self, slot, value.split(","))
                        else: # everything else is assumed to be a string
                            setattr(self, slot, value)
                # multiple parameter settings.
                else:
                    print "multi parameter setting unimplemented."
#                    print node.nodeName, len(node.childNodes)

        #
        # Store as the default, if the default does not exist.
        # If the default does exist, then fill in all the
        # missing parameters with values from the default.
        # This way only the default starting file has to have all
        # the parameters.
        #
        use_as_default = 0
        if hasattr(self, "use_as_default"):
            use_as_default = self.use_as_default

        global default_params
        if default_params:
            for k, v in default_params.__dict__.iteritems():
                if not hasattr(self, k):
                    setattr(self, k, copy.copy(v))
        
        if use_as_default or (not default_params):
            default_params = copy.deepcopy(self)

        #
        # Acquisition program specific.
        #
        if hasattr(self, "x_start"):
            # Define some other useful derivative parameters
            self.x_pixels = self.x_end - self.x_start + 1
            self.y_pixels = self.y_end - self.y_start + 1
            self.ROI = [self.x_start, self.x_end, self.y_start, self.y_end]
            self.binning = [self.x_bin, self.y_bin]

            # And a few random other things
            self.exposure_value = 0
            self.accumulate_value = 0
            self.kinetic_value = 0
            self.bytesPerFrame = 2 * self.x_pixels * self.y_pixels/(self.x_bin * self.y_bin)
            self.actual_temperature = 0
            self.notes = ""
            self.extension = self.extensions[0]

        self.parameters_file = parameters_file


#
# Testing
# 

if __name__ == "__main__":
    test = Parameters("settings_test_1.xml")
    print test.x_start, test.x_end, test.x_pixels, test.frames
    print test.default_power, len(test.default_power)
    print test.power_buttons, len(test.power_buttons)

#    test = Parameters("settings_test_2.xml")
#    print test.x_start, test.x_end, test.x_pixels, test.frames
#    test = Parameters("shutters.xml")


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
