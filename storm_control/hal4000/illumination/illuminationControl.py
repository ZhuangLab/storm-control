#!/usr/bin/python
#
## @file
#
# Illumination control master class.
#
# Hazen 04/14
#

import ast
import importlib
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.illumination.buttonEditor as buttonEditor
import storm_control.hal4000.illumination.illuminationChannel as illuminationChannel
import storm_control.hal4000.illumination.xmlParser as xmlParser

# UI.
import storm_control.hal4000.qtdesigner.illumination_ui as illuminationUi

## IlluminationControl
#
# Illumination power control.
#
class IlluminationControl(QtWidgets.QDialog, halModule.HalModule):
    channelNames = QtCore.pyqtSignal(object)
    newColors = QtCore.pyqtSignal(object)
    newCycleLength = QtCore.pyqtSignal(int)
    tcpComplete = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this dialog box.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        halModule.HalModule.__init__(self)
        
        self.channels = []
        self.hardware_modules = {}
        self.fp = False
        self.parameters = parameters
        self.running_shutters = False
        self.spacing = 3

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup.
        self.ui = illuminationUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Illumination Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Parse XML that describes the hardware.
        hardware = xmlParser.parseHardwareXML("illumination/" + hardware.get("settings_xml"))

        # Add illumination specific settings.
        #
        # FIXME: These used to be customizable.
        #
        default_power = []
        on_off_state = []
        for i in range(len(hardware.channels)):
            default_power.append(1.0)
            on_off_state.append(False)
        self.parameters.set("illumination.default_power", default_power)
        self.parameters.set("illumination.on_off_state", on_off_state)

        # Check for button settings, use defaults if they do not exist.
        #
        buttons = []
        for i in range(len(hardware.channels)):
            buttons.append([["Max", 1.0], ["Low", 0.1]])
        power_buttons = params.ParameterCustom("Illumination power buttons",
                                               "power_buttons",
                                               buttons,
                                               1,
                                               is_mutable = True,
                                               is_saved = True)
        power_buttons.editor = buttonEditor.ParametersTablePowerButtonEditor
        self.parameters.add("illumination.power_buttons", power_buttons)

        # This parameter is used to be able to tell when the shutters file
        # has been changed for a given set of parameters.
        self.parameters.add("illumination.last_shutters", params.ParameterString("Last shutters file name",
                                                                                "last_shutters",
                                                                                "",
                                                                                is_mutable = False,
                                                                                is_saved = False))

        # Default camera parameters.
        self.parameters.add("illumination.shutters", params.ParameterStringFilename("Shutters file name",
                                                                                    "shutters",
                                                                                    "shutters_default.xml",
                                                                                    False))

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
        x = 7
        names = []
        for i, channel in enumerate(hardware.channels):
            a_instance = illuminationChannel.Channel(i,
                                                     channel,
                                                     parameters.get("illumination"),
                                                     self.hardware_modules,
                                                     self.ui.powerControlBox)
            x += a_instance.setPosition(x, 14) + self.spacing
            self.channels.append(a_instance)
            names.append(a_instance.getName())
            
        power_buttons.channel_names = names

        # Connect signals.
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        for channel in self.channels:
            channel.cleanup()

        for name, instance in self.hardware_modules.items():
            instance.cleanup()

    ## closeEvent
    #
    # Close the dialog if it has no parent, otherwise just hide it.
    #
    # @param event A PyQt event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "setPower"):
                signal[2].connect(self.remoteSetPower)
            elif (signal[1] == "incPower"):
                signal[2].connect(self.remoteIncPower)
            elif (signal[1] == "commMessage"):
                signal[2].connect(self.handleCommMessage)

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "channelNames", self.channelNames],
                [self.hal_type, "newColors", self.newColors],
                [self.hal_type, "newCycleLength", self.newCycleLength],
                [self.hal_type, "tcpComplete", self.tcpComplete]]

    ## handleCommMessage
    #
    # Handles all the message from tcpControl.
    #
    # @param message A tcpControl.TCPMessage object.
    #
    @hdebug.debug
    def handleCommMessage(self, message):
        if (message.getType() == "Set Power"):
            if not message.isTest():
                self.remoteSetPower(message.getData("channel"),
                                    message.getData("power"))
            self.tcpMessage.emit(message)
        elif (message.getType() == "Increment Power"):
            if not message.isTest():
                self.remoteIncPower(message.getData("channel"),
                                    message.getData("increment"))
            self.tcpMessage.emit(message)

    ## handleOk
    #
    # Hide the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleQuit
    #
    # Close the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## moduleInit
    #
    @hdebug.debug
    def moduleInit(self):
        names = []
        for channel in self.channels:
            names.append(channel.getName())
        self.channelNames.emit(names)

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

    ## newParameters
    #
    # Calls channels newParameters method, then updates the size of 
    # the dialog as appropriate to fit all of the channels.
    #
    # Note that the camera updates the kinetic value (time per frame).
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        p = parameters.get("illumination")

        #
        # Convert string representation of a power buttons list to an actual list
        # if necessary. This would happen for example the first time that a
        # settings file is loaded that contains save power button information.
        #
        if isinstance(p.get("power_buttons"), str):
            buttons = ast.literal_eval(p.get("power_buttons"))
            p.setv("power_buttons", buttons)
            
        for channel in self.channels:
            channel.newParameters(p)

        if (p.get("shutter_frames", 0) > 0):
            self.newColors.emit(p.get("shutter_colors"))
            self.newCycleLength.emit(p.get("shutter_frames"))

        self.parameters = parameters

        self.updateSize()

    ## newShutters
    #
    # @param shutters_filename The name of a shutters XML file.
    #
    @hdebug.debug
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

    ## remoteIncPower
    #
    # Calls QIlluminationControl's remoteIncPower method.
    #
    # @param channel The channel index.
    # @param power_inc The amount increment the power by.
    #
    @hdebug.debug
    def remoteIncPower(self, channel, power_inc):
        self.channels[channel].remoteIncPower(power_inc)

    ## remoteSetPower
    #
    # Calls QIlluminationControl's remoteSetPower method.
    #
    # @param channel The channel index.
    # @param power The desired power (0.0 - 1.0).
    #
    @hdebug.debug
    def remoteSetPower(self, channel, power):
        self.channels[channel].remoteSetPower(power)

    ## startFilm
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    @hdebug.debug
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
                for name, instance in self.hardware_modules.iteritems():
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

    ## startLiveView
    #
    # Setup the illumination for live view
    # @param live_view A boolean describing whether or not the live view is running
    #
    @hdebug.debug
    def startLiveView(self, live_view):
        pass
##        for channel in self.channels:
##            channel.startLiveView(live_view)

    ## stopLiveView
    #
    # Cleanup the illumination when live view mode is toggled off
    #
    # @param live_view A boolean describing whether or not the live view is running
    #
    @hdebug.debug
    def stopLiveView(self, live_view):
        pass
##        for channel in self.channels:
##            channel.stopLiveView(live_view)

    ## stopFilm
    #
    # Called at the end of filming.
    #
    # @param film_writer The film writer object.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        if self.fp:
            self.fp.close()
            self.fp = False

        if self.running_shutters:

            # Stop hardware.
            for name, instance in self.hardware_modules.iteritems():
                if (instance.getStatus() == True):
                    instance.stopFilm()

            # Stop channels.
            for channel in self.channels:
                channel.stopFilm()

            self.running_shutters = False

    ## updateSize
    #
    # Resize the dialog based on the size of the channels.
    # (i.e. the sliders, buttons, etc.).
    #
    @hdebug.debug
    def updateSize(self):

        # Determine max channel height.
        new_height = 0
        for channel in self.channels:
            if (new_height < channel.getHeight()):
                new_height = channel.getHeight()

        # Resize all the channels to be the same height.
        for channel in self.channels:
            if (channel.getHeight() != new_height):
                channel.setHeight(new_height)
        
        # Resize the group box and the dialog box.
        if (len(self.channels) > 1):
            new_width = self.channels[-1].getX() + self.channels[1].getWidth() + 7
        else:
            new_width = self.channels[0].getWidth() + 7
        self.ui.powerControlBox.setGeometry(10, 0, new_width, new_height + 19)

        lb_width = self.ui.powerControlBox.width()
        lb_height = self.ui.powerControlBox.height()
        self.ui.okButton.setGeometry(lb_width - 65, lb_height + 4, 75, 24)
        self.setFixedSize(lb_width + 18, lb_height + 36)


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
