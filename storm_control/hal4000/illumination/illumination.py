#!/usr/bin/env python
"""
Illumination control.

Hazen 04/17
"""

import importlib
import os

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.illumination.illuminationChannel as illuminationChannel
import storm_control.hal4000.illumination.illuminationParameters as illuminationParameters
import storm_control.hal4000.illumination.xmlParser as xmlParser

# UI.
import storm_control.hal4000.qtdesigner.illumination_ui as illuminationUi


#
# FIXME: The parameters object is shared with all of the channels. It
#        would probably be better to only have one copy here.
#
class IlluminationView(halDialog.HalDialog):
    """
    Manages the illumination GUI.
    """
    guiMessage = QtCore.pyqtSignal(object)
    
    def __init__(self, module_name = None, hardware = None, **kwds):
        super().__init__(**kwds)

        self.camera1_fps = None
        self.channels = []
        self.channels_by_name = {}
        self.hardware_modules = {}
        self.module_name = module_name
        self.oversampling = None
        self.parameters = params.StormXMLObject()
        self.running_shutters = False
        self.shutters_info = False
        self.waveforms = None
        self.xml_directory = os.path.dirname(os.path.dirname(__file__))

        # UI setup.
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Default power setting.
        default_power = []
        for i in range(len(hardware.channels)):
            default_power.append(1.0)
        self.parameters.add(illuminationParameters.ParameterDefaultPowers(description = "Power",
                                                                          name = "default_power",
                                                                          value = default_power,
                                                                          is_mutable = False))

        # Default on/off state.
        on_off_state = []
        for i in range(len(hardware.channels)):
            on_off_state.append(False)
        self.parameters.add(illuminationParameters.ParameterOnOffStates(description = "On/Off",
                                                                        name = "on_off_state",
                                                                        value = on_off_state,
                                                                        is_mutable = False))


        # Default buttons.
        buttons = []
        for i in range(len(hardware.channels)):
            buttons.append([["Max", 1.0], ["Low", 0.1]])
        self.parameters.add(illuminationParameters.ParameterPowerButtons(description = "Buttons",
                                                                         name = "power_buttons",
                                                                         value = buttons))

        # Default shutters file.
        self.parameters.add(params.ParameterStringFilename(description = "Shutters file name",
                                                           name= "shutters",
                                                           value = "shutters_default.xml",
                                                           use_save_dialog = False))

        # Hardware modules setup.
        for module in hardware.modules:
            m_name = module.module_name
            a_module =  importlib.import_module(m_name)
            a_class = getattr(a_module, module.class_name)
            a_instance = a_class(module.parameters, self)
            if a_instance.isBuffered():
                a_instance.start(QtCore.QThread.NormalPriority)
            self.hardware_modules[module.name] = a_instance            

        # Illumination channels setup.
        layout = QtWidgets.QHBoxLayout(self.ui.powerControlBox)
        layout.setContentsMargins(1,1,1,1)
        layout.setSpacing(1)
        for i, channel in enumerate(hardware.channels):
            a_instance = illuminationChannel.Channel(channel_id = i,
                                                     channel = channel,
                                                     hardware_modules = self.hardware_modules,
                                                     parent = self.ui.powerControlBox)
            self.channels.append(a_instance)
            self.channels_by_name[a_instance.getName()] = a_instance
            layout.addWidget(a_instance.channel_ui)

        self.newParameters(self.parameters)

    def cleanUp(self, qt_settings):
        for channel in self.channels:
            channel.cleanup()

        for name, instance in self.hardware_modules.items():
            instance.cleanup()

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
    
    def getParameters(self):
        return self.parameters

    def getShuttersInfo(self):
        return self.shutters_info
        
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

        self.newShutters(self.parameters.get("shutters"))

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
        [self.shutters_info, self.waveforms, self.oversampling] = xmlParser.parseShuttersXML(len(self.channels),
                                                                                             filename_to_parse)
        for i, channel in enumerate(self.channels):
            self.waveforms[i] = channel.newShutters(self.waveforms[i])

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

    def setCamera1FPS(self, fps):
        self.camera1_fps = fps
        
    def setXMLDirectory(self, xml_directory):
        self.xml_directory = xml_directory
        
    def startFilm(self, run_shutters):
        if run_shutters:
            self.running_shutters = True

            # Setup channels.
            for i, channel in enumerate(self.channels):
                channel.setupFilm(self.waveforms[i])

            # Start hardware.
            for name, instance in self.hardware_modules.items():
                if (instance.getStatus() == True):
                    instance.startFilm(self.camera1_fps, self.oversampling)

            # Start channels.
            for channel in self.channels:
                channel.startFilm()

    def stopFilm(self):
        if self.running_shutters:

            # Stop hardware.
            for name, instance in self.hardware_modules.items():
                if (instance.getStatus() == True):
                    instance.stopFilm()

            # Stop channels.
            for channel in self.channels:
                channel.stopFilm()

            self.running_shutters = False


class Illumination(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.power_fp = None

        ilm_params = module_params.get("parameters")
        ilm_xml_file = os.path.join(os.path.dirname(__file__), ilm_params.get("settings_xml"))
        channel_config = xmlParser.parseHardwareXML(os.path.join(os.path.dirname(__file__),
                                                                 ilm_xml_file))

        self.view = IlluminationView(module_name = self.module_name,
                                     hardware = channel_config)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " illumination control")

        # The names of the illumination channels that are available.
        halMessage.addMessage("illumination channels",
                              validator = {"data" : {"names" : [True, list]},
                                           "resp" : None})

        # Increment the power of an illumination channel.
        halMessage.addMessage("remote inc power",
                              validator = {"data" : {"channel" : [True, (str, int)],
                                                     "power" : [True, float]},
                                           "resp" : None})

        # Set the power of an illumination channel.
        halMessage.addMessage("remote set power",
                              validator = {"data" : {"channel" : [True, (str, int)],
                                                     "power" : [True, float]},
                                           "resp" : None})        

        # Shutters sequence.
        halMessage.addMessage("shutters sequence",
                              validator = {"data" : {"sequence" : [True, xmlParser.ShuttersInfo]},
                                           "resp" : None})
                              
        # Unhide illumination control.
        halMessage.addMessage("show illumination",
                              validator = {"data" : None, "resp" : None})

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):

        if message.isType("get camera configuration"):
            if (response.getData()["camera"] == "camera1"):
                fps = response.getData()["config"].getParameter("fps")
                self.view.setCamera1FPS(fps)
            
    def processL1Message(self, message):

        if message.isType("configure1"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "add to menu",
                                                       data = {"item name" : "Illumination",
                                                               "item msg" : "show illumination"}))
            
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "initial parameters",
                                                       data = {"parameters" : self.view.getParameters()}))

            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "illumination channels",
                                                       data = {"names" : self.view.getChannelNames()}))

            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "shutters sequence",
                                                       data = {"sequence" : self.view.getShuttersInfo()}))

            # Query camera1 for timing information.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "get camera configuration",
                                                       data = {"display_name" : "NA",
                                                               "camera" : "camera1"}))

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.setXMLDirectory(os.path.dirname(p.get("parameters_file")))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("remote inc power"):
            self.view.remoteIncPower(message.getData()["channel"],
                                     message.getData()["power"])

        elif message.isType("remote set power"):
            self.view.remoteSetPower(message.getData()["channel"],
                                     message.getData()["power"])            

        elif message.isType("show illumination"):
            self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("start film"):
            film_settings = message.getData()["film settings"]
            self.view.startFilm(film_settings.runShutters())
            if film_settings.isSaved():
                self.power_fp = open(film_settings.getBasename() + ".power", "w")
                self.power_fp.write("frame " + " ".join(self.view.getChannelNames()) + "\n")

        elif message.isType("stop film"):
            self.view.stopFilm()
            if self.power_fp is not None:
                self.power_fp.close()
                self.power_fp = None

            #
            # Fix shutters file information to be an absolute path as the shutters
            # file won't be saved in the same directory as the movie.
            #
            p = self.view.getParameters().copy()
            p.set("shutters", os.path.abspath(p.get("shutters")))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : p}))

        elif message.isType("updated parameters"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "shutters sequence",
                                                       data = {"sequence" : self.view.getShuttersSequence()}))

            # Query camera1 for timing information.
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "get camera configuration",
                                                       data = {"display_name" : "NA",
                                                               "camera" : "camera1"}))
            #self.view.updatedParameters()

    def processL2Message(self, message):
        if self.power_fp is not None:
            frame_number = str(message.getData()["frame"].frame_number + 1)
            self.power_fp.write(frame_number + " " + " ".join(self.view.getChannelPowers()) + "\n")


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
