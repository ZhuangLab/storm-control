#!/usr/bin/env python
"""
The messages that are passed between modules.

Hazen 01/17
"""

import traceback
import types

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

#
# This dictionary contains all of the valid message types. Modules
# may dynamically add to this dictionary using addMessage().
#
# "data" - These are the required fields & types in the message data dictionary.
# "resp" - These are the required fields & types in the response data dictionary.
#
# The format of each entry is "field" : [Required, Expected type].
#
valid_messages = {
    
    # HAL/core/general messages.
    'add to ui' : {"data" : {"ui_order" : [False, int],
                             "ui_parent" : [True, str],
                             "ui_widget" : [True, QtCore.QObject]},
                   "resp" : None},
    'add to menu' : {"data" : {"item name" : [True, str],
                               "item msg" : [True, str]},
                     "resp" : None},
    'close event' : {"data" : None, "resp" : None},
    'configure1' : {"data" : {"all_modules" : [True, dict]},
                    "resp" : {}},
    'configure2' : {"data" : None, "resp" : None},
    'configure3' :  {"data" : None, "resp" : None},
    'initial parameters' :  {"data" : {"parameters" : [True, params.StormXMLObject]},
                             "resp" : None},
    'new directory' : {"data" : {"directory" : [True, str]},
                       "resp" : None},
    'new parameters file' : {"data" : {"filename" : [True, str],
                                       "is_default" : [False, bool]},
                             "resp" : None},
    'new shutters file' : {"data" : {"filename" : [True, str]},
                           "resp" : None},
    'start' :  {"data" : {"show_gui" : [True, bool]},
                "resp" : None},
    'sync' :  {"data" : None, "resp" : None},
    'test' :  {"data" : None, "resp" : None},
    }


def addMessage(name, validator = {}, check_exists = True):
    """
    Modules should call this function at initialization to add additional messages.
    """
    global valid_messages
    if check_exists and name in valid_messages:
        raise halExceptions.HalException("Message " + name + " already exists!")
    valid_messages[name] = validator


def chainMessages(send_fn, messages):
    """
    Constructs a chain of messages each of which will be sent when
    the previous message in the chain is finalized.
    """
    for i in range(len(messages)-1):
        #
        # Need the x = i bit to capture the current value of i,
        # otherwise all the messages have the same finalizer.
        #
        messages[i].finalizer = lambda x = i: send_fn(messages[x+1])
    return messages[0]


def validate(validator, data, base_string):
    """
    Checks that data (or response) field of a message is correct.
    """
    # Check that their is no data if the validator is None.
    if validator is None:
        if data is not None:
            msg = base_string + "' should not have data."
            raise HalMessageException(msg)
        else:
            return
    
    # Check that their is data if validator is not None.
    if data is None:
        msg = base_string + "' should have data."
        raise HalMessageException(msg)

    # Check that every item in data exists in validator.
    for item in data:
        if not item in validator:
            msg = base_string + "' has an unexpected field '" + item + "'."
            raise HalMessageException(msg)

    # Check that every item that should be in data is, and that
    # all items are of the correct type.
    for item in validator:

        # Existence check.
        if (not item in data) and validator[item][0]:
            msg = base_string + "' does not have required item '" + item + "'."
            raise HalMessageException(msg)
        
        # Type check.
        if item in data:
            if not isinstance(data[item], validator[item][1]):
                msg = base_string + "' is not the expected type, got '"
                msg += str(type(data[item])) + "' expected '" + str(validator[item][1])
                msg += " for item '" + item + "'."
                raise HalMessageException(msg)
            
    
def validateData(validator, message):
    """
    Checks that data field of a message is correct.
    """
    base_string = "Data in message '" + message.m_type + "' from '" 
    base_string += message.getSourceName()
    validate(validator, message.getData(), base_string)

    
def validateResponse(validator, message, response):
    """
    Checks that response field of a message is correct.
    """
    base_string = "Response from '" + response.source + "' in message '" 
    base_string += message.m_type + "' from '" + message.getSourceName()
    validate(validator, response.getData(), base_string)


class HalMessageException(halExceptions.HalException):
    pass


# FIXME: This is only the base class for HalMessage, do we need it separate?
class HalMessageBase(object):
    """
    Base class for the HalMessage as well as for various response
    such as errors, warnings or data.
    """
    def __init__(self, m_type = "", source = None, **kwds):
        """
        m_type - String that defines the message type. This should be a space 
                 separated lower case string.

        source - HalModule object that sent the message.
        """
        super().__init__(**kwds)

        if not isinstance(m_type, str):
            raise HalMessageException("m_type is not of type 'str'")

        self.m_type = m_type
        self.source = source
        
    def getSource(self):
        return self.source

    def getSourceName(self):
        return self.source.module_name

    def getType(self):
        return self.m_type


class HalMessage(HalMessageBase):
    istype_warned = {}

    def __init__(self, data = None, sync = False, level = 1, finalizer = None, **kwds):
        """
        data - Python object containing the message data. This must be a dictionary.

        sync - Boolean that indicates whether or not all the messages before
               this message should be processed before continuing to this message.

        level - Integer that for the message 'level'. Most messages are level 1
                but if the message is one that there will be a lot of, and that
                is only relevant to one or two other modules (such as commands
                from a USB joystick) then it should be some other level so that
                modules that are not interested can more quickly ignore it.

                Convention:
                 1. General messages
                 2. New frame messages
                 3. Joystick / mouse drag messages

        finalizer - A function with no arguments to call when the message has been 
                    completely processed by all of the modules.
        """
        super().__init__(**kwds)

        if data is not None:
            if not isinstance(data, dict):
                raise HalMessageException("data is not of type 'dict'")
        
        if not isinstance(sync, bool):
            raise HalMessageException("sync is not of type 'bool'")
        
        if not isinstance(level, int):
            raise HalMessageException("level is not of type 'int'")

        if finalizer is not None:
            if not callable(finalizer):
                raise HalMessageException("function is not of type 'function'")

        self.data = data
        self.finalizing = False
        self.finalizer = finalizer
        self.level = level
        self.m_errors = []
        self.responses = []
        self.sync = sync

        # We use a mutex for the ref_count because threaded
        # modules could change this inside the thread.
        self.ref_count = 0

    def addError(self, hal_message_error):
        self.m_errors.append(hal_message_error)

    def addResponse(self, hal_message_response):
        self.responses.append(hal_message_response)

    def decRefCount(self):
        self.ref_count -= 1
        
    def finalize(self):

        if self.finalizer is not None:
            self.finalizer()

        # Log when message was processed
        if (self.level == 1):
            self.logEvent("processed")

    def getData(self):
        return self.data

    def getErrors(self):
        return self.m_errors

    def getResponses(self):
        return self.responses

    def hasErrors(self):
        return (len(self.m_errors) > 0)

    def hasResponses(self):
        return (len(self.responses) > 0)

    def incRefCount(self):
        self.ref_count += 1
        
    def isType(self, m_type):
        if (not m_type in valid_messages) and (not m_type in self.istype_warned):
            #raise HalMessageException("'" + m_type + "' is not a valid message type.")
            print(">> Warning '" + m_type + "' is not a valid message type. <<")
            self.istype_warned[m_type] = True
        return (self.m_type == m_type)

    def logEvent(self, event_name):
        hdebug.logText(",".join([event_name, str(id(self)), self.source.module_name, self.m_type]))

    def refCountIsZero(self):
        return (self.ref_count == 0)


class HalMessageError(object):
    """
    If a module has a problem with a message that it can't handle then
    it should call the message's addError() method with one of these objects.
    """
    def __init__(self, source = "", message = "", m_exception = None, stack_trace = "NA", **kwds):
        """
        source - The halmodule that created the error/warning as a string.
        message - The warning / error message as a string.
        m_exception - The exception for the source to raise if can't handle
                      this error. If this is not set then we'll just get a
                      warning.
        """
        super().__init__(**kwds)

        if not isinstance(source, str):
            raise HalMessageException("source is not of type 'str'")
        
        if not isinstance(message, str):
            raise HalMessageException("message is not of type 'str'")
        
        if not isinstance(m_exception, Exception):
            raise HalMessageException("m_exception is not of type 'Exception'")

        self.message = message
        self.m_exception = m_exception
        self.source = source
        if (stack_trace == "NA"):
            self.stack_trace = traceback.format_exc()
        else:
            self.stack_trace = stack_trace

    def getException(self):
        return self.m_exception
    
    def hasException(self):
        return self.m_exception is not None

    def printExceptionAndDie(self):
        print("")
        print("Got an exception from '" + self.source + "' of type '" + self.message + "'!")
        print("")        
        print("Traceback when the exception occurred:")
        print(self.stack_trace)
        print("")
        raise self.m_exception


class HalMessageResponse(object):
    """
    If a module wants to send some information back to the message sender then
    it should call the message's addResponse() method with one of the objects.
    """
    def __init__(self, source = "", data = None, **kwds):
        """
        source - The halmodule that added the response as a string.
        data - Python object containing the response. This must be a
               dictionary.
        """
        super().__init__(**kwds)

        if not isinstance(source, str):
            raise HalMessageException("Source is not of type 'str'")
            
        self.data = data
        self.source = source

    def getData(self):
        return self.data


class SyncMessage(HalMessage):
    """
    A message whose sole purpose is to jam up the queue until 
    everything before it is processed. Use sparingly..
    """
    def __init__(self, source):
        kwds = {"m_type" : "sync",
                "source" : source,
                "sync" : True}
        super().__init__(**kwds)
        
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
