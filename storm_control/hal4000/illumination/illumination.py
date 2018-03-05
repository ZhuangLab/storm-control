#!/usr/bin/env python
"""
Illumination control.

Hazen 04/17
"""

import os

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halFunctionality as halFunctionality
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.illumination.illuminationChannel as illuminationChannel
import storm_control.hal4000.illumination.illuminationParameters as illuminationParameters
import storm_control.hal4000.illumination.xmlParser as xmlParser

# UI.
import storm_control.hal4000.qtdesigner.illumination_ui as illuminationUi


class IlluminationFunctionality(halFunctionality.HalFunctionality):

    def __init__(self,
                 get_channel_names = None,
                 remote_inc_power = None,
                 remote_set_power = None,
                 **kwds):
        super().__init__(**kwds)
        
        assert(callable(get_channel_names))
        assert(callable(remote_inc_power))
        assert(callable(remote_set_power))
        
        self.getChannelNames = get_channel_names
        self.remoteIncPower = remote_inc_power
        self.remoteSetPower = remote_set_power
        

#
# FIXME: The parameters object is shared with all of the channels. It
#        would probably be better to only have one copy here.
#
class IlluminationView(halDialog.HalDialog):
    """
    Manages the illumination GUI.
    """
    guiMessage = QtCore.pyqtSignal(object)
    
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)

        self.channel_name_to_id = {}
        self.channels = []
        self.channels_by_name = {}
        self.parameters = params.StormXMLObject()
        self.power_fp = None
        self.running_shutters = False
        self.shutters_info = False
        self.timing_functionality = None
        self.waveforms = []
        self.xml_directory = os.path.dirname(os.path.dirname(__file__))

        # UI setup.
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)

        number_channels = len(configuration.getAttrs())
        
        # Default power setting.
        #
        # FIXME: This assumes that all the channels are normalized
        #        so that the maximum power is 1.0.
        #
        default_power = []
        for i in range(number_channels):
            default_power.append(1.0)
        self.parameters.add(illuminationParameters.ParameterDefaultPowers(description = "Power",
                                                                          name = "default_power",
                                                                          value = default_power,
                                                                          is_mutable = False))

        # Default on/off state.
        on_off_state = []
        for i in range(number_channels):
            on_off_state.append(False)
        self.parameters.add(illuminationParameters.ParameterOnOffStates(description = "On/Off",
                                                                        name = "on_off_state",
                                                                        value = on_off_state,
                                                                        is_mutable = False))


        # Default buttons.
        buttons = []
        for i in range(number_channels):
            buttons.append([["Max", 1.0], ["Low", 0.1]])
        self.parameters.add(illuminationParameters.ParameterPowerButtons(description = "Buttons",
                                                                         name = "power_buttons",
                                                                         value = buttons))

        # Default shutters file.
        filename = os.path.join(self.xml_directory, "shutters_default.xml")
        self.parameters.add(params.ParameterStringFilename(description = "Shutters file name",
                                                           name= "shutters",
                                                           value = filename,
                                                           use_save_dialog = False))

        # Illumination channels setup.
        layout = QtWidgets.QHBoxLayout(self.ui.powerControlBox)
        layout.setContentsMargins(1,1,1,1)
        layout.setSpacing(1)
        for i, cname in enumerate(sorted(configuration.getAttrs())):
            a_instance = illuminationChannel.Channel(channel_id = i,
                                                     configuration = configuration.get(cname),
                                                     parent = self.ui.powerControlBox)
            self.channel_name_to_id[a_instance.getName()] = i
            self.channels.append(a_instance)
            self.channels_by_name[a_instance.getName()] = a_instance
            layout.addWidget(a_instance.channel_ui)

    def cleanUp(self, qt_settings):
        for channel in self.channels:
            channel.cleanup()

        super().cleanUp(qt_settings)

    def getChannelNames(self):
        names = []
        for channel in self.channels:
            names.append(channel.getName())
        return names

    def getChannelPowers(self):
        powers = []
        for channel in self.channels:
            powers.append(channel.getAmplitude())
        return powers

    def getFunctionalities(self):
        # Send requests for functionalities that the channels need.
        for channel in self.channels:
            for fn_name in channel.getFunctionalityNames():
                self.guiMessage.emit(halMessage.HalMessage(source = None,
                                                           m_type = "get functionality",
                                                           data = {"name" : fn_name,
                                                                   "extra data" : channel.getName()}))

    def getParameters(self):
        return self.parameters

    def getShuttersInfo(self):
        return self.shutters_info

    def handleNewFrame(self, frame_number):
        """
        This called during timing by TimingFunctionality provided by timing.timing.
        """
        if self.power_fp is not None:
            frame_number = str(frame_number + 1)
            self.power_fp.write(frame_number + " " + " ".join(self.getChannelPowers()) + "\n")
            
    def newParameters(self, parameters):
        """
        Calls channels newParameters method, then updates the size of 
        the dialog as appropriate to fit all of the channels.
        """
        current_position = self.pos()

        # A sanity check that settings.settings is not giving us bad parameters.
        for attr in parameters.getAttrs():
            assert(type(self.parameters.getp(attr)) == type(parameters.getp(attr)))
        
        self.parameters = parameters
                
        for channel in self.channels:
            channel.newParameters(self.parameters)

        #
        # If the number of buttons change, this can cause the dialog to jump
        # so we need to keep track of it's current position and reset to
        # that position.
        #
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        self.move(current_position)

        # Update shutters file by sending a message so that film.film also updates.
        self.guiMessage.emit(halMessage.HalMessage(m_type = "new shutters file",
                                                   data = {"filename" : self.parameters.get("shutters")}))

    def newShutters(self, shutters_filename):
        """
        Called when we get new parameters, which will have a shutters file,
        and also when the user loads a new shutters file for the existing
        parameters.
        """
        
        filename_to_parse = None
        path_filename = os.path.join(self.xml_directory, shutters_filename)

        # Check if the shutters file exists in the current directory.
        if os.path.exists(shutters_filename):
            filename_to_parse = shutters_filename

        # Check if the shutters exists in the current XML directory.
        elif os.path.exists(path_filename):
            filename_to_parse = path_filename
        else:
            raise halExceptions.HalException("Could not load find '" + shutters_filename + "' or '" + path_filename + "'")

        # Save possibly updated shutter file information.
        self.parameters.set("shutters", shutters_filename)
                            
        # Parse XML to get shutter information, waveforms, etc.
        [self.shutters_info, waveforms, oversampling] = xmlParser.parseShuttersXML(self.channel_name_to_id,
                                                                                   filename_to_parse)

        self.waveforms = []
        for i, channel in enumerate(self.channels):
            # Channels determine whether or not they are used for filming based on the waveform.
            channel.setUsedForFilm(waveforms[i])
            
            # Channels create DaqWaveform objects (or not) based on the waveform.
            self.waveforms.extend(channel.getDaqWaveforms(waveforms[i], oversampling))

        # Send shutters info to other modules
        self.guiMessage.emit(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : {"shutters info" : self.shutters_info}}))

    def remoteIncPower(self, channel, power_inc):
        if isinstance(channel, str):
            self.channels_by_name[channel].remoteIncPower(power_inc)
        else:
            self.channels[channel].remoteIncPower(power_inc)

    def remoteSetPower(self, channel, power):
        if isinstance(channel, str):
            self.channels_by_name[channel].remoteSetPower(power)
        else:
            self.channels[channel].remoteSetPower(power)

    def setFunctionality(self, channel_name, fn_name, functionality):
        self.channels_by_name[channel_name].setFunctionality(fn_name, functionality)

    def setTimingFunctionality(self, timing_functionality):
        self.timing_functionality = timing_functionality
        self.timing_functionality.newFrame.connect(self.handleNewFrame)
        
    def setXMLDirectory(self, xml_directory):
        self.xml_directory = xml_directory
        
    def startFilm(self, film_settings):

        # Open file to save the channel powers at each frame.
        if film_settings.isSaved():
            self.power_fp = open(film_settings.getBasename() + ".power", "w")
            self.power_fp.write("frame " + " ".join(self.getChannelNames()) + "\n")

        # Configure channels.
        if film_settings.runShutters():
            self.running_shutters = True

            # Start channels.
            for channel in self.channels:
                channel.startFilm()

            # Send waveforms to the daq.
            if (len(self.waveforms) > 0):
                self.guiMessage.emit(halMessage.HalMessage(source = None,
                                                           m_type = "daq waveforms",
                                                           data = {"waveforms" : self.waveforms}))

            # Send shutters info to other modules
#            self.guiMessage.emit(halMessage.HalMessage(m_type = "configuration",
#                                                       data = {"properties" : {"shutters info" : self.shutters_info}}))
            
    def stopFilm(self):

        # Close the channel powers file.
        if self.power_fp is not None:
            self.power_fp.close()
            self.power_fp = None

        if self.running_shutters:

            # Stop channels.
            for channel in self.channels:
                channel.stopFilm()

            self.running_shutters = False

        # Disconnect film timing functionality.
        self.timing_functionality.newFrame.disconnect(self.handleNewFrame)
        self.timing_functionality = None


class Illumination(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")

        self.view = IlluminationView(module_name = self.module_name,
                                     configuration = configuration)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " illumination control")
        self.view.guiMessage.connect(self.handleGuiMessage)

        self.ilm_functionality = IlluminationFunctionality(get_channel_names = self.view.getChannelNames,
                                                           remote_inc_power = self.view.remoteIncPower,
                                                           remote_set_power = self.view.remoteSetPower)

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleGuiMessage(self, message):
        self.sendMessage(message)
                
    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(message.getData()["extra data"],
                                       message.getData()["name"],
                                       response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("timing"):
                self.view.setTimingFunctionality(message.getData()["properties"]["functionality"])

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Illumination",
                                                           "item data" : "illumination"}))
        
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))

            self.view.getFunctionalities()

        elif message.isType("current parameters"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters().copy()}))

        elif message.isType("get functionality"):
            if (message.getData()["name"] == self.module_name):
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"functionality" : self.ilm_functionality})) 

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.setXMLDirectory(os.path.dirname(p.get("parameters_file")))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("new shutters file"):
            self.view.newShutters(message.getData()["filename"])

        elif message.isType("show"):
            if (message.getData()["show"] == "illumination"):
                self.view.show()

        elif message.isType("start"):
            # This is here because we need to have gotten the hardware functionalities
            # in order to correctly handle parameter (and shutter) initialization.
            self.view.newParameters(self.view.getParameters())
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("start film"):
            self.view.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            self.view.stopFilm()
            
            #
            # Fix shutters file information to be an absolute path as the shutters
            # file won't be saved in the same directory as the movie.
            #
            p = self.view.getParameters().copy()
            p.set("shutters", os.path.abspath(p.get("shutters")))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : p}))

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
