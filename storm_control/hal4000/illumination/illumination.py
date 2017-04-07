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


class IlluminationView(halDialog.HalDialog):
    """
    Manages the illumination GUI.
    """
    guiMessage = QtCore.pyqtSignal(object)
    
    def __init__(self, module_name = None, hardware = None, **kwds):
        super().__init__(**kwds)
        
        self.channels = []
        self.hardware_modules = {}
        self.fp = False
        self.module_name = module_name
        self.parameters = params.StormXMLObject()
        self.running_shutters = False

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
            if((i%2)==0):
                buttons.append([["Max", 1.0], ["Low", 0.1]])
            else:
                buttons.append([["Max", 1.0]])
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
            layout.addWidget(a_instance.channel_ui)

        self.newParameters(self.parameters)

    def cleanUp(self, qt_settings):
        for channel in self.channels:
            channel.cleanup()

        for name, instance in self.hardware_modules.items():
            instance.cleanup()

        super().cleanUp(qt_settings)


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

#    def moduleInit(self):
#        names = []
#        for channel in self.channels:
#            names.append(channel.getName())
#        self.channelNames.emit(names)

    ## newFrame
    #
    # Handles new frames. If there is a open file and the frame
    # is a master frame then this calls QIlluminationControl's
    # savePowers method.
    #
    # @param frame A camera.Frame object
    # @param filming True/False if we are currently filming.
    #
    def newFrame(self, frame, filming):
        if self.fp and frame.master:
            str = "{0:d}".format(frame.number)
            for channel in self.channels:
                str = str + " " + channel.getAmplitude()
            self.fp.write(str + "\n")

    def newParameters(self, parameters):
        """
        Calls channels newParameters method, then updates the size of 
        the dialog as appropriate to fit all of the channels.
        """

        # A sanity check that settings.settings is not giving us bad parameters.
        for attr in parameters.getAttrs():
            assert(type(self.parameters.getp(attr)) == type(parameters.getp(attr)))
        
        self.parameters = parameters
                
        for channel in self.channels:
            channel.newParameters(self.parameters)
            
        self.updateSize()


    ## newShutters
    #
    # @param shutters_filename The name of a shutters XML file.
    #
    def newShutters(self, shutters_filename):
        [waveforms, colors, frames, oversampling] = xmlParser.parseShuttersXML(len(self.channels), 
                                                                               shutters_filename)

        p = self.parameters.get("illumination")
        p.set("shutter_data", [])
        for i, channel in enumerate(self.channels):
            p.get("shutter_data").append(channel.newShutters(waveforms[i]))
        p.set("shutter_colors", colors)
        p.set("shutter_frames", frames)
        p.set("shutter_oversampling", oversampling)
        self.newColors.emit(colors)
        self.newCycleLength.emit(frames)

    # FIXME: Allow setting power by name as well as by index.
    def remoteIncPower(self, channel, power_inc):
        self.channels[channel].remoteIncPower(power_inc)

    def remoteSetPower(self, channel, power):
        self.channels[channel].remoteSetPower(power)

    def startFilm(self, film_name, run_shutters):

        # Recording the power.
        if film_name:
            self.fp = open(film_name + ".power", "w")
            frame_base = "frame"
            for channel in self.channels:
                frame_base = frame_base + " " + channel.getName()
            self.fp.write(frame_base + "\n")

        # Running the shutters.
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


    def startLiveView(self, live_view):
        pass

    def stopLiveView(self, live_view):
        pass

    def stopFilm(self, film_writer):
        if self.fp:
            self.fp.close()
            self.fp = False

        if self.running_shutters:

            # Stop hardware.
            for name, instance in self.hardware_modules.items():
                if (instance.getStatus() == True):
                    instance.stopFilm()

            # Stop channels.
            for channel in self.channels:
                channel.stopFilm()

            self.running_shutters = False

#    def updatedParameters(self, parameters):
#        # The parameters are hopefully good, so keep a copy.
#        self.parameters = parameters
        
    def updateSize(self):
        """
        This resizes the channels so that they are all the height even if
        they have a different number of buttons. Then it resizes the dialog
        box to fit everything & fixes the dialog box size.
        """

        # Determine max channel height.
        new_height = 0
        for channel in self.channels:
            if (new_height < channel.getHeight()):
                new_height = channel.getHeight()
        print(">us", new_height)

#        # Resize all the channels to be the same height.
#        for channel in self.channels:
#            if (channel.getHeight() != new_height):
#                channel.setFixedHeight(new_height)

        self.adjustSize()
#        self.setFixedSize(self.width(), self.height())


#    channelNames = QtCore.pyqtSignal(object)
#    newColors = QtCore.pyqtSignal(object)
#    newCycleLength = QtCore.pyqtSignal(int)
#    tcpComplete = QtCore.pyqtSignal(object)


class Illumination(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        ilm_params = module_params.get("parameters")
        ilm_xml_file = os.path.join(os.path.dirname(__file__), ilm_params.get("settings_xml"))
        channel_config = xmlParser.parseHardwareXML(os.path.join(os.path.dirname(__file__),
                                                                 ilm_xml_file))

        self.view = IlluminationView(module_name = self.module_name,
                                     hardware = channel_config)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " illumination control")

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

        elif message.isType("show illumination"):
            self.view.show()

        elif message.isType("start"):
            self.view.showIfVisible()
        
    
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
