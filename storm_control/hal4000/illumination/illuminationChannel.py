#!/usr/bin/env python
"""
This controls a single channel.

Hazen 04/17
"""

import numpy

from PyQt5 import QtCore

import storm_control.hal4000.illumination.illuminationChannelUI as illuminationChannelUI


class Channel(QtCore.QObject):
    """
    This class is responsible for orchestrating the behaviour of a
    a single channel.
    """
    def __init__(self, channel_id = 0, channel = None, hardware_modules = None, **kwds):
        super().__init__(**kwds)

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
        self.used_for_film = False
        self.was_on = False
        self.bad_module = False

        # Create variables for communication with the various hardware modules.
        # This will add the attributes in the list to this class.
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
                    self.bad_module = True

            # Add the attribute to the class.
            setattr(self, name, h_module)

        # Configure the UI.
        # If we have amplitude modulation then this is an adjustable channel with slider.
        if self.amplitude_modulation:
            self.display_normalized = channel.amplitude_modulation.display_normalized
            self.min_amplitude = self.amplitude_modulation.getMinAmplitude(self.channel_id)
            self.max_amplitude = self.amplitude_modulation.getMaxAmplitude(self.channel_id)
            self.amplitude_range = float(self.max_amplitude - self.min_amplitude)
            self.channel_ui = illuminationChannelUI.ChannelUIAdjustable(name = self.name,
                                                                        color = channel.color,
                                                                        minimum = self.min_amplitude,
                                                                        maximum = self.max_amplitude,
                                                                        parent = self.parent())
            self.channel_ui.updatePowerText("NS")

        # Otherwise it is a basic channel with on only a on/off radio button.
        else:
            self.channel_ui = illuminationChannelUI.ChannelUI(name = self.name,
                                                              color = channel.color,
                                                              parent = self.parent())

        if self.bad_module:
            self.channel_ui.disableChannel()
        else:
            self.channel_ui.onOffChange.connect(self.handleOnOffChange)
            self.channel_ui.powerChange.connect(self.handleSetPower)

    def cleanup(self):
        self.channel_ui.setOnOff(False)
    
    def getAmplitude(self):
        """
        Return the current channel amplitude as a string. This is
        always normalized.
        """
        power = self.channel_ui.getAmplitude()
        return "{0:.4f}".format((power - self.min_amplitude)/self.amplitude_range)

    def getChannelId(self):
        return self.channel_id

    def getHeight(self):
        return self.channel_ui.height()

    def getWidth(self):
        return self.channel_ui.width()

    def getX(self):
        return self.channel_ui.x()

    def getName(self):
        return self.name

    def handleOnOffChange(self, on):
        """
        Handles a request to turn the channel on / off. These all
        come from the UI. They are ignored when we are filming.
        
        As a side effect this records the on/off setting in the
        'on_off_state' property of the parameters.
        """
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

        self.parameters.get("on_off_state")[self.channel_id] = on

    def handleSetPower(self, new_power):
        """
        Handles requests to set the current channel power to a new value.
        These all come from the UI. The current power is always whatever
        the current value of the slider is.
        
        As a side effect this records the current power setting in
        'default_power' property of the parameters.
        """
        if self.display_normalized:
            power = (new_power - self.min_amplitude)/self.amplitude_range
            power_string = "{0:.4f}".format((new_power - self.min_amplitude)/self.amplitude_range)
        else:
            power = new_power
            power_string = "{0:d}".format(new_power)
        self.parameters.get("default_power")[self.channel_id] = power
        self.channel_ui.updatePowerText(power_string)

        if self.amplitude_modulation:
            self.amplitude_modulation.setAmplitude(self.channel_id, new_power)

        if (self.channel_ui.isOn()):
            if self.mechanical_shutter:
                if (new_power == self.min_amplitude):
                    self.mechanical_shutter.shutterOff(self.channel_id)
                else:
                    self.mechanical_shutter.shutterOn(self.channel_id)

    def newParameters(self, parameters):
        self.parameters = parameters

        # Calculate new power in slider units if necessary.
        new_power = parameters.get("default_power")[self.channel_id]
        if self.display_normalized:
            new_power = int(round(new_power * self.amplitude_range + self.min_amplitude))

        # Update channel settings.
        self.channel_ui.newSettings(parameters.get("on_off_state")[self.channel_id],
                                    new_power)

        # Update buttons.
        self.channel_ui.setupButtons(parameters.get("power_buttons")[self.channel_id])

    def newShutters(self, waveform):
        """
        Return the waveform properly scaled for the hardware.
        """
        if self.analog_modulation:
            return self.analog_modulation.waveformToVoltage(self.channel_id, waveform)
        else:
            return waveform

    def remoteIncPower(self, power_inc):
        """
        Handles power increment requests that come from outside of the illumination UI.
        This is "bounced" off the UI slider, for range checking.
        """
        self.channel_ui.remoteIncPower(int(round(power_inc * self.amplitude_range)))

    def remoteSetPower(self, new_power):
        """
        Handles power requests that come from outside of the illumination UI.
        This is "bounced" off the UI slider, for range checking.
        """
        self.channel_ui.remoteSetPower(int(round(new_power * self.amplitude_range + self.min_amplitude)))

    def setHeight(self, height):
        self.channel_ui.resize(self.channel_ui.width(), height)

    def setPosition(self, x, y):
        self.channel_ui.move(x, y)
        return self.channel_ui.width()

    def setupFilm(self, waveform):
        """
        Called before of filming to get the channel setup.
        """
        # Figure out if this channel is used for filming.
        self.used_for_film = False
        if (numpy.count_nonzero(waveform) > 0):
            self.used_for_film = True

        # Add analog waveform data.
        if self.analog_modulation:
            self.analog_modulation.analogAddChannel(self.channel_id, waveform)

        # Add digital waveform data.
        if self.digital_modulation:
            self.digital_modulation.digitalAddChannel(self.channel_id, waveform)

    def startFilm(self):
        """
        Called at the start of filming.
        """
        if not self.bad_module:
            if self.channel_ui.isEnabled(): # Enabled only if live view
                self.was_on = self.channel_ui.isOn() # Record state to restore after movie

            if self.used_for_film:
                self.channel_ui.enableChannel() # Turn on channel (if live view turned it off)
                self.channel_ui.setOnOff(True)
                self.channel_ui.startFilm()
                if self.amplitude_modulation:
                    self.amplitude_modulation.setAmplitude(self.channel_id, 
                                                           self.channel_ui.getAmplitude())
            else:
                self.channel_ui.disableChannel()
                self.filming_disabled = True
                
        self.filming = True

#    def startLiveView(self, live_view):
#        """
#        Configure illumination for live view.
#        """
#        if not self.bad_module and live_view:
#            # Enable the channel
#            self.channel_ui.enableChannel()
#            self.channel_ui.setOnOff(self.was_on)
#
#        if not live_view:
#            self.channel_ui.disableChannel()
    
    def stopFilm(self):
        """
        Called at the end of filming to reset things.
        """
        self.filming = False
        
        if self.filming_disabled:
            self.channel_ui.enableChannel(self.was_on)
            self.filming_disabled = False
        else:
            self.channel_ui.stopFilm()
            self.channel_ui.setOnOff(self.was_on)

#    def stopLiveView(self, live_view):
#        """
#        Cleanup illumination settings at the end of the live view
#        """
#        if not self.bad_module and live_view:
#            # record state of the channel
#            self.was_on = self.channel_ui.isOn()
#            self.channel_ui.disableChannel()

#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
