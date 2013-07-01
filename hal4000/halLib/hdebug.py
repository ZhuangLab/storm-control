#!/usr/bin/python
#
# Debugging decorators & logging.
#
# Hazen 07/13
#

import logging
import logging.handlers
import sys
import time

want_debugging = False

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

def getDebug():
    return want_debugging

# Needs to be set at compile time?
def setDebugging(state):
    global want_debugging
    if state:
        want_debugging = True
    else:
        want_debugging = False

#
# This should only be called once in "main".
#
def startLogging(directory, program_name):

    # Initialize logger.
    a_logger = logging.getLogger(program_name)
    a_logger.setLevel(logging.DEBUG)

    # Create formatter.
    a_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    # Rotating file handle for saving output.
    rf_handler = logging.handlers.RotatingFileHandler(directory + program_name + ".out",
                                                      maxBytes = 10000,
                                                      backupCount = 5)
    rf_handler.setFormatter(a_formatter)
    a_logger.addHandler(rf_handler)

    # Stream handler for console output.
    st_handler = logging.StreamHandler()
    st_handler.setFormatter(a_formatter)
    a_logger.addHandler(st_handler)

    # Set to capture stdout.
    sys.stdout = StreamToLogger(a_logger, logging.INFO)

    # Set to capture stderr.
    sys.stderr = StreamToLogger(a_logger, logging.ERROR)

#
# This is basically a copy of the code from here:
#  http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
#    
class StreamToLogger(object):

   def __init__(self, logger, log_level):
      self.logger = logger
      self.log_level = log_level
 
   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

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
