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
        
        self.channels = []
        self.channels_by_name = {}
        self.hardware_modules = {}
        self.module_name = module_name
        self.parameters = params.StormXMLObject()
        self.running_shutters = False
        self.shutters_sequence = False
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

#        # This parameter is used to be able to tell when the shutters file
#        # has been changed for a given set of parameters.
#        self.parameters.add(params.ParameterString(name = "last_shutters",
#                                                   value = "",
#                                                   is_mutable = False,
#                                                   is_saved = False))

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

    def getShuttersSequence(self):
        return self.shutters_sequence
        
#    def handleCommMessage(self, message):
#        if (message.getType() == "Set Power"):
#            if not message.isTest():
#                self.remoteSetPower(message.getData("channel"),
#                                    message.getData("power"))
#            self.tcpMessage.emit(message)
#        elif (message.getType() == "Increment Power"):
#            if not message.isTest():
#                self.remoteIncPower(message.getData("channel"),
#                                    message.getData("increment"))
#            self.tcpMessage.emit(message)

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
        if os.path.exists(shutters_filename):
            self.shutters_sequence = xmlParser.parseShuttersXML(len(self.channels), 
                                                                shutters_filename)
            self.parameters.set("shutters", os.path.abspath(shutters_filename))
            return
            
        path_filename = os.path.join(self.xml_directory, shutters_filename)
        if os.path.exists(path_filename):
            self.shutters_sequence = xmlParser.parseShuttersXML(len(self.channels), 
                                                                path_filename)
            return
        
        raise halExceptions.HalException("Could not load find '" + shutters_filename + "' or '" + path_filename + "'")

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

    def setXMLDirectory(self, xml_directory):
        self.xml_directory = xml_directory
        
    def startFilm(self, film_name, run_shutters):
        if run_shutters:
            self.running_shutters = True

            # Setup channels.
            for channel in self.channels:
                channel.setupFilm()

            try:
                # Start hardware.
                for name, instance in self.hardware_modules.items():
                    if (instance.getStatus() == True):
                        instance.startFilm(self.parameters.get("seconds_per_frame"),
                                           self.parameters.get("illumination.shutter_oversampling"))

                # Start channels.
                for channel in self.channels:
                    channel.startFilm()
                    
            except halExceptions.HardwareException as error:
                error_message = "startFilm in illumination control encountered an error: \n" + str(error)
                hdebug.logText(error_message)
                raise halModule.StartFilmException(error_message)

    def startFilm(self, film_settings):
        pass

    def stopFilm(self, film_writer):
        if self.running_shutters:

            # Stop hardware.
            for name, instance in self.hardware_modules.items():
                if (instance.getStatus() == True):
                    instance.stopFilm()

            # Stop channels.
            for channel in self.channels:
                channel.stopFilm()

            self.running_shutters = False

    def stopFilm(self):
        pass
    
    def updatedParameters(self):
        # Update shutters here.
        pass


#    channelNames = QtCore.pyqtSignal(object)
#    newColors = QtCore.pyqtSignal(object)
#    newCycleLength = QtCore.pyqtSignal(int)
#    tcpComplete = QtCore.pyqtSignal(object)


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
                              validator = {"data" : {"sequence" : [True, xmlParser.ShuttersSequence]},
                                           "resp" : None})
                              
        # Unhide illumination control.
        halMessage.addMessage("show illumination",
                              validator = {"data" : None, "resp" : None})

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)
            
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
                                                       m_type = "shutters sequence",
                                                       data = {"sequence" : self.view.getShuttersSequence()}))

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
            self.view.startFilm(film_settings)
            if film_settings.isSaved():
                self.power_fp = open(film_settings.getBasename() + ".power", "w")
                self.power_fp.write("frame " + " ".join(self.view.getChannelNames()) + "\n")

        elif message.isType("stop film"):
            self.view.stopFilm()
            if self.power_fp is not None:
                self.power_fp.close()
                self.power_fp = None
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters()}))

        elif message.isType("updated parameters"):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "shutters sequence",
                                                       data = {"sequence" : self.view.getShuttersSequence()}))
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
