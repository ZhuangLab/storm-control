#!/usr/bin/python
#
## @file
#
# This file contains the Channel class.
#
# Hazen 04/14
#

from PyQt4 import QtCore

import illumination.illuminationChannelUI as illuminationChannelUI

## Channel
#
# This class is responsible for orchestrating the behaviour of a
# a single channel.
#
class Channel(QtCore.QObject):

    ## __init__
    #
    # @param channel_id The id number for this channel.
    # @param channel A channelXML object describing the channel.
    # @param parameters A parameters XML object.
    # @param hardware_modules An array of hardware module objects.
    # @param channels_box The UI group box where the channels will be drawn.
    #
    def __init__(self, channel_id, channel, parameters, hardware_modules, channels_box):
        QtCore.QObject.__init__(self, channels_box)

        self.amplitude_range = 1.0
        self.channel_id = channel_id
        self.channel_ui = False
        self.display_normalized = False
        self.filming = False
        self.filming_disabled = False
        self.max_amplitude = 1.0
        self.min_amplitude = 0.0
        self.name = channel.description
        self.parameters = False
        self.shutter_data = []
        self.used_for_film = False
        self.was_on = False

        # Create variables for communication with the various hardware modules.
        # This will add the attributes in the list to this class.
        bad_module = False
        for name in ["amplitude_modulation", "analog_modulation", "digital_modulation", "mechanical_shutter"]:

            h_module = False

            # Test if the XML file has the attribute of interest.
            if hasattr(channel, name):

                # Get the data for the attribute.
                a_control = getattr(channel, name)

                # Get the corresponding hardware / control module that will be used for this attribute.
                h_module = hardware_modules[a_control.uses]

                # Initialize the hardware / control module with the parameters for this channel.
                h_module.initialize(name, self.channel_id, a_control.parameters)

                # Check if the hardware / control module actual works.
                if not h_module.getStatus():
                    bad_module = True

            # Add the attribute to the class.
            setattr(self, name, h_module)

        # Configure the UI.
        # If we have amplitude modulation then this is an adjustable channel with slider.
        if self.amplitude_modulation:
            self.display_normalized = channel.amplitude_modulation.display_normalized
            self.min_amplitude = self.amplitude_modulation.getMinAmplitude(self.channel_id)
            self.max_amplitude = self.amplitude_modulation.getMaxAmplitude(self.channel_id)
            self.amplitude_range = float(self.max_amplitude - self.min_amplitude)
            self.channel_ui = illuminationChannelUI.ChannelUIAdjustable(self.name,
                                                                        channel.color,
                                                                        self.min_amplitude,
                                                                        self.max_amplitude,
                                                                        channels_box)
            self.channel_ui.updatePowerText("NS")

        # Otherwise it is a basic channel with on only a on/off radio button.
        else:
            self.channel_ui = illuminationChannelUI.ChannelUI(self.name,
                                                              channel.color,
                                                              channels_box)

        if bad_module:
            self.channel_ui.disableChannel()
        else:
            self.channel_ui.onOffChange.connect(self.handleOnOffChange)
            self.channel_ui.powerChange.connect(self.handleSetPower)

    ## cleanup
    #
    def cleanup(self):
        self.channel_ui.setOnOff(False)
    
    ## getAmplitude
    #
    # Return the current channel amplitude as a string. This is
    # always normalized.
    #
    # @return The current amplitude of the channel (as a string).
    #
    def getAmplitude(self):
        power = self.channel_ui.getAmplitude()
        return "{0:.4f}".format((power - self.min_amplitude)/self.amplitude_range)

    ## getHeight
    #
    # @return The height of the channel UI element.
    #
    def getHeight(self):
        return self.channel_ui.height()

    ## getWidth
    #
    # @return The width of the channel UI element.
    def getWidth(self):
        return self.channel_ui.width()

    ## getName
    #
    # @return The name of the channel.
    #
    def getName(self):
        return self.name

    ## handleOnOffChange
    #
    # Handles a request to turn the channel on / off. These all
    # come from the UI. They are ignored when we are filming.
    #
    # @param on True/False on/off.
    #
    def handleOnOffChange(self, on):
        if self.filming:
            return

        if on:
            if self.amplitude_modulation:
                self.amplitude_modulation.amplitudeOn(self.channel_id, 
                                                      self.channel_ui.getAmplitude())
        
            if self.analog_modulation:
                self.analog_modulation.analogOn(self.channel_id)

            if self.digital_modulation:
                self.digital_modulation.digitalOn(self.channel_id)

            if self.mechanical_shutter:
                self.mechanical_shutter.shutterOn(self.channel_id)

        else:
            if self.amplitude_modulation:
                self.amplitude_modulation.amplitudeOff(self.channel_id)
        
            if self.analog_modulation:
                self.analog_modulation.analogOff(self.channel_id)
                
            if self.digital_modulation:
                self.digital_modulation.digitalOff(self.channel_id)

            if self.mechanical_shutter:
                self.mechanical_shutter.shutterOff(self.channel_id)

    ## handleSetPower
    #
    # Handles requests to set the current channel power to a new value.
    # These all come from the UI. The current power is always whatever
    # the current value of the slider is.
    #
    # @param new_power The new channel power setting.
    #
    def handleSetPower(self, new_power):
        if self.display_normalized:
            power_string = "{0:.4f}".format((new_power - self.min_amplitude)/self.amplitude_range)
        else:
            power_string = "{0:d}".format(new_power)
        self.channel_ui.updatePowerText(power_string)

        if self.amplitude_modulation:
            self.amplitude_modulation.setAmplitude(self.channel_id, new_power)

        if self.mechanical_shutter:
            if (new_power == self.min_amplitude):
                self.mechanical_shutter.shutterOn(self.channel_id)
            else:
                self.mechanical_shutter.shutterOff(self.channel_id)

    ## newParameters
    #
    # @param parameters A parameters XML object.
    #
    # @return [old on/off setting, old power]
    #
    def newParameters(self, parameters):

        # Calculate new power in slider units if necessary.
        new_power = parameters.default_power[self.channel_id]
        if self.display_normalized:
            new_power = int(round(new_power * self.amplitude_range + self.min_amplitude))

        # Update channel settings.
        [old_on, old_power] = self.channel_ui.newSettings(parameters.on_off_state[self.channel_id],
                                                          new_power)

        # Update buttons.
        self.channel_ui.setupButtons(parameters.power_buttons[self.channel_id])

        # Update shutter data, if available.
        if (parameters.shutter_frames != 0):
            self.shutter_data = parameters.shutter_data[self.channel_id]

        # Normalize power, if necessary.
        if self.display_normalized:
            old_power = float(old_power - self.min_amplitude)/self.amplitude_range

        return [old_on, old_power]

    ## newShutters
    #
    # This both sets the internal shutter data store and converts it
    # to the appropriate scale based on the analog modulation settings.
    #
    # @param shutter_data A array containing the shutter data.
    #
    # @return The processed shutter data.
    #
    def newShutters(self, shutter_data):
        self.shutter_data = shutter_data
        if self.analog_modulation:
            for i in range(len(self.shutter_data)):
                self.shutter_data[i] = self.analog_modulation.powerToVoltage(self.channel_id, self.shutter_data[i])

        return self.shutter_data

    ## remoteIncPower
    #
    # Handles power increment requests that come from outside of the illumination UI.
    # This is "bounced" off the UI slider, for range checking.
    #
    # @param power_inc The channel power increment (0.0 - 1.0).
    #
    def remoteIncPower(self, power_inc):
        self.channel_ui.remoteIncPower(int(round(power_inc * self.amplitude_range)))

    ## remoteSetPower
    #
    # Handles power requests that come from outside of the illumination UI.
    # This is "bounced" off the UI slider, for range checking.
    #
    # @param new_power The channel power setting (0.0 - 1.0).
    #
    def remoteSetPower(self, new_power):        
        self.channel_ui.remoteSetPower(int(round(new_power * self.amplitude_range + self.min_amplitude)))

    ## setHeight
    #
    # @param height Changes the height of the channel UI.
    #
    def setHeight(self, height):
        self.channel_ui.resize(self.channel_ui.width(), height)

    ## setPosition
    #
    # @param x The x location of the channel UI.
    # @param y The y location of the channel UI.
    #
    # @return The width of the channel UI.
    #
    def setPosition(self, x, y):
        self.channel_ui.move(x, y)
        return self.channel_ui.width()

    ## setupFilm
    #
    # Called at the before of filming to get the channel setup.
    #
    def setupFilm(self):

        # Figure out if this channel is used for filming.
        self.used_for_film = False
        if any((y > 0.0) for y in self.shutter_data):
            self.used_for_film = True

        # Add analog waveform data.
        if self.analog_modulation:
            self.analog_modulation.analogAddChannel(self.channel_id, self.shutter_data)

        # Add digital waveform data.
        if self.digital_modulation:
            self.digital_modulation.digitalAddChannel(self.channel_id, self.shutter_data)

    ## startFilm
    #
    # Called at the start of filming.
    #
    def startFilm(self):
        if self.channel_ui.isEnabled():
            self.was_on = self.channel_ui.isOn()

            if self.used_for_film:
                self.channel_ui.setOnOff(True)
                self.channel_ui.startFilm()
                if self.amplitude_modulation:
                    self.amplitude_modulation.setAmplitude(self.channel_id, 
                                                           self.channel_ui.getAmplitude())
            else:
                self.channel_ui.disableChannel()
                self.filming_disabled = True

        self.filming = True

    ## stopFilm
    #
    # Called at the end of filming to reset things.
    #
    def stopFilm(self):
        self.filming = False
        if self.filming_disabled:
            self.channel_ui.enableChannel()
            self.filming_disabled = False
        else:
            self.channel_ui.stopFilm()
            self.channel_ui.setOnOff(self.was_on)

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
