#!/usr/bin/python
#
## @file
#
# Defines the core functionality for a HAL module.
#
# Hazen 02/14
#

from PyQt4 import QtCore

import sc_library.hdebug as hdebug

## HalModule class.
#
# Provides the default functionality for a HAL module
#
class HalModule(object):

    ## cleanup
    #
    # This will be called when HAL closes to perform any module specific clean-up.
    #
    @hdebug.debug
    def cleanup(self):
        pass

    ## connectSignals
    #
    # The signals is an array of arrays in this form:
    #  [[A string containing the module type,
    #   [A string containing the name of the signal,
    #   [The signal object],
    #  ...]
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        pass

    ## getSignals
    #
    # This returns the (PyQt) signals that this module provides
    # as part of it's interface.
    #
    # @return An array of signals provided by the module.
    #
    @hdebug.debug
    def getSignals(self):
        return []

    ## loadGUISettings
    #
    # Called after initialization so that module can
    # access any settings (such as visible, position, etc..)
    # that it wanted to maintain across sessions.
    #
    # @param settings A QtCore.QSettings object.
    #
    @hdebug.debug
    def loadGUISettings(self, settings):
        if self.hal_gui:
            self.move(settings.value(self.hal_type + "_pos", QtCore.QPoint(200, 200)).toPoint())
            if settings.value(self.hal_type + "_visible", False).toBool():
                self.show()

    ## moduleInit
    #
    # Called only once after all the modules are instantiated and 
    # have had a chance to connect signals. This exists so that 
    # modules can exchange information that other modules might need
    # to configure themselves properly.
    #
    @hdebug.debug
    def moduleInit(self):
        pass

    ## newFrame
    #
    # Called whenever a new frame of data is available
    # from the camera.
    #
    # @param frame A camera.Frame object
    # @param filming True/False if we are currently filming.
    #
    def newFrame(self, frame, filming):
        pass

    ## newParameters
    #
    # Called when a new set of parameters is chosen.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        pass

    ## newShutters
    #
    # Called when a new shutters file is selected.
    #
    # @param shutters_filename The name of a shutters XML file.
    #
    @hdebug.debug
    def newShutters(self, shutters_filename):
        pass

    ## saveGUISettings
    #
    # Called when HAL closes so that the module can save any
    # settings that it wants to maintain across multiple
    # sessions.
    #
    # @param settings A QtCore.QSettings object.
    #
    @hdebug.debug
    def saveGUISettings(self, settings):
        if self.hal_gui:
            settings.setValue(self.hal_type + "_pos", self.pos())
            settings.setValue(self.hal_type + "_visible", self.isVisible())

    ## show
    #
    # This should always be overridden and/or provided by a different base class.
    #
    @hdebug.debug
    def show(self):
        print "show error!"

    ## startFilm
    #
    # Called at the start of film acquisition.
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        pass

    ## stopFilm
    #
    # Called at when filming is complete. The writer is passed to the modules
    # so that they can (optionally) add any module specific data to the film's
    # meta-data (the .inf file).
    #
    # @param film_writer The film writer object, or False if the film was not saved.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        pass


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
