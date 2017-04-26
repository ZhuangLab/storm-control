#!/usr/bin/env python
"""
Debugging decorators & logging.

Hazen 01/14
"""

import functools
import logging
import logging.handlers

from PyQt5 import QtCore

a_logger = False
logging_mutex = QtCore.QMutex()

def objectToString(a_object, a_name, a_attrs):
    a_string = "<" + a_name
    for a_attr in a_attrs:
        if (hasattr(a_object, a_attr)):
            a_string = a_string + "," + a_attr + "=" + str(getattr(a_object, a_attr))
        else:
            a_string = a_string + "," + a_attr + "=?"
    a_string = a_string + ">"
    return a_string

def debug(fn):
    """
    Function decorator. This logs all the arguments to a function that it decorates
    if logging has been started.
    """
    global a_logger, logging_mutex
    @functools.wraps(fn)
    def __wrapper(*args, **kw):
        if a_logger:
            logging_mutex.lock()
            if fn.__module__ == "__main__":
                a_logger.info(fn.__module__ + "." + fn.__name__ + " started")
                for i, arg in enumerate(args):
                    a_logger.info("    " + str(i) + " " + str(arg))
            else:
                a_logger.info("  " + fn.__module__ + "." + fn.__name__ + " started")
                for i, arg in enumerate(args):
                    a_logger.info("      " + str(i) + " " + str(arg))
            logging_mutex.unlock()
        temp = fn(*args, **kw)
        if a_logger:
            logging_mutex.lock()
            if fn.__module__ == "__main__":
                a_logger.info(fn.__module__ + "." + fn.__name__ + " ended")
            else:
                a_logger.info("  " + fn.__module__ + "." + fn.__name__ + " ended")
            logging_mutex.unlock()
        return temp
    return __wrapper

def getDebug():
    """
    Return True/False if debugging information desired.
    """
    global a_logger
    if a_logger:
        return True
    else:
        return False

def logText(a_string, to_console = False):
    """
    Note: Calling this with to_console = True from a thread that is not
          the main thread seemed to occasionally lock the computer.
    """
    global a_logger, logging_mutex
    if a_logger:
        logging_mutex.lock()
        a_logger.info("message:")
        a_logger.info("  " + a_string)
        if to_console:
            print(a_string)
        logging_mutex.unlock()
    else:
        print(a_string)

def startLogging(directory, program_name):
    """
    This should only be called once in "main". It uses QSettings() to generate
    a new index (1-10) each time that it is called so that (hopefully) we can
    log from multiple programs with the same name.

    FIXME? As this seems to just append to existing log files, it would probably
           be better to delete the existing files first.
    """
    global a_logger

    # Get logger index (to allow logging from several programs with the same name).
    settings = QtCore.QSettings("Zhuang Lab", "hdebug logger")
    index = int(settings.value("current index", 1))
    new_index = index + 1
    if (new_index > 100):
        new_index = 1
    settings.setValue("current index", new_index)

    # Initialize logger.
    a_logger = logging.getLogger(program_name)
    a_logger.setLevel(logging.DEBUG)

    # Create formatter.
    rt_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

    # Rotating file handle for saving output.
    log_filename = directory + program_name + "_" + str(index) + ".out"
    try:
        rf_handler = logging.handlers.RotatingFileHandler(log_filename,
                                                          maxBytes = 200000,
                                                          backupCount = 5)
    except IOError:
        print("Logging Error! Could not open", log_filename)
        print("  Logging is disabled.")
        a_logger = False

    if a_logger:
        rf_handler.setFormatter(rt_formatter)
        a_logger.addHandler(rf_handler)
        

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
