#!/usr/bin/python
#
## @file
#
# Defines the core functionality for a HAL module.
#
# Hazen 02/14
#

import halLib.hdebug as hdebug

## HalModule class.
#
# Provides the default functionality for a HAL module
#
class HalModule():

    ## close
    #
    # This should always be overridden and/or provided by a different base class.
    #
    @hdebug.debug
    def close(self):
        print "close error!"

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        pass

    ## getSignals
    #
    # @return An array of signals provided by the module.
    #
    @hdebug.debug
    def getSignals(self):
        return []

    ## loadGUISettings
    #
    # @param settings A QtCore.QSettings object.
    #
    @hdebug.debug
    def loadGUISettings(self):
        pass

    ## newFrame
    #
    # @param frame A camera.Frame object
    #
    @hdebug.debug
    def newFrame(self, frame):
        pass

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        pass

    ## newShutters
    #
    # @param filename The name of a shutters file.
    #
    @hdebug.debug
    def newShutters(self, filename):
        pass

    ## saveGUISettings
    #
    # @param settings A QtCore.QSettings object.
    #
    @hdebug.debug
    def saveGUISettings(self, settings):
        pass

    ## show
    #
    # This should always be overridden and/or provided by a different base class.
    #
    @hdebug.debug
    def show(self):
        print "show error!"

    ## startFilm
    #
    # @param filename The name of the film without any extensions.
    #
    @hdebug.debug
    def startFilm(self, filename):
        pass

    ## stopFilm
    #
    @hdebug.debug
    def stopFilm(self):
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
