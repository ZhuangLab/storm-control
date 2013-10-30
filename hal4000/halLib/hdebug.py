#!/usr/bin/python
#
## @file
#
# Debugging decorators & logging. This is still a work in progress
# as my original concept for decorators has been broken by changes in
# PyQt and my logging concept is also somewhat of a failure.
#
# Hazen 07/13
#

import logging
import logging.handlers
import sys
import time

from PyQt4 import QtCore

want_debugging = False

## debug
#
# Function decorator. This prints all the arguments to a function that it decorates.
#
def debug(fn):
    def debug_f(*args, **kw):
        if fn.__module__ == "__main__":
            print fn.__module__ + "." + fn.__name__ + ": " + str(time.time())
            for i, arg in enumerate(args):
                print "    " + str(i) + ".", arg
        else:
            print "  " + fn.__module__ + "." + fn.__name__ + ": " + str(time.time())
            for i, arg in enumerate(args):
                print "      " + str(i) + ".", arg
        return fn(*args, **kw)
    global want_debugging
    if want_debugging:
        return debug_f
    else:
        return fn

## debugSlot
#
# Slot decorator. This prints all the signal arguments to a slot.
#
def debugSlot(fn):
    def debug_f(*args):
        if fn.__module__ == "__main__":
            print fn.__module__ + "." + fn.__name__ + ": " + str(time.time())
            for i, arg in enumerate(args):
                print "    " + str(i) + ".", arg
        else:
            print "  " + fn.__module__ + "." + fn.__name__ + ": " + str(time.time())
            for i, arg in enumerate(args):
                print "      " + str(i) + ".", arg
        return fn(*args[:-1])
    global want_debugging
    if want_debugging:
        return debug_f
    else:
        return fn

## getDebug
#
# @return True/False is debugging information desired.
#
def getDebug():
    return want_debugging

## setDebugging
#
# Sets the debugging flag.
# 
# FIXME: This doesn't actually work as you
# need to set the debugging flag at compile time, run time is
# too late as all the decorators have already been created.
#
# @param state True/False the desired debugging state.
#
def setDebugging(state):
    global want_debugging
    if state:
        want_debugging = True
    else:
        want_debugging = False

## startLogging
#
# This should only be called once in "main".
#
# @param directory The directory to save the log files in.
# @param program_name The name of the program that is doing the logging.
#
def startLogging(directory, program_name):

    # Initialize logger.
    a_logger = logging.getLogger(program_name)
    a_logger.setLevel(logging.DEBUG)

    # Create formatters.
    rt_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    st_formatter = logging.Formatter('%(message)s')

    # Rotating file handle for saving output.
    rf_handler = logging.handlers.RotatingFileHandler(directory + program_name + ".out",
                                                      maxBytes = 10000,
                                                      backupCount = 5)
    rf_handler.setFormatter(rt_formatter)
    a_logger.addHandler(rf_handler)

    # Stream handler for console output.
    st_handler = logging.StreamHandler()
    st_handler.setFormatter(st_formatter)
    a_logger.addHandler(st_handler)

    # Set to capture stdout.
    sys.stdout = StreamToLogger(a_logger, logging.INFO)

    # Set to capture stderr.
    sys.stderr = StreamToLogger(a_logger, logging.ERROR)

## StreamToLogger
#
# This is basically a copy of the code from here:
#  http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
#    
# FIXME: The print command is thread safe, but this is not, so capturing print
#   statements from a program with multiple threads like HAL will cause it to freeze.
#
class StreamToLogger(object):

    ## __init__
    #
    # Create the stream logging object.
    #
    # @param logger A logging object.
    # @param log_level What level logging to use (info, error, etc.).
    #
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.write_mutex = QtCore.QMutex()

    ## write
    #
    # Called when new text is sent to the stream.
    #
    # @param buf The text string.
    #
    def write(self, buf):
        self.write_mutex.lock()
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
        self.write_mutex.unlock()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
