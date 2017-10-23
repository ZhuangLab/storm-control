#!/usr/bin/env python
"""
Handles remote control (via TCP/IP of the data collection program) 

Jeffrey Moffitt
3/8/14
jeffmoffitt@gmail.com

Hazen 05/14
"""

import copy
import json


class TCPMessage(object):
    """
    Contains the contents and status of a TCP message.
    """
    _COUNTER = 0 # Track number of created instances of this class.

    def __init__(self,
                 message_type = None,
                 message_data = {},
                 test_mode = False,
                 **kwds):
        super().__init__(**kwds)

        assert message_type is not None
        
        #self.complete = False
        self.error = False
        self.error_message = None
        self.message_data = copy.copy(message_data)
        self.message_type = message_type
        self.response = {}
        self.test_mode = test_mode

        self.message_id = TCPMessage._COUNTER # Record instance number.
        TCPMessage._COUNTER += 1 # Increment the instance counter.

    def addData(self, key_name, value):
        """
        Add or change the contents of fields in the message data dictionary.
        """
        self.message_data[key_name] = value

    def addResponse(self, key_name, value):
        """
        Add or change the contents of fields in the response data dictionary.
        """
        self.response[key_name] = value

    @staticmethod
    def fromJSON(json_string):
        """
        Creates a Message from a JSON string.
        """
        message = TCPMessage(message_type = True)
        message.__dict__.update(json.loads(json_string))
        return message

    def getData(self, key_name, default = None):
        """
        Access elements of the message data by name.
        """
        return self.message_data.get(key_name, default)

    def getErrorMessage(self):
        """
        Return the error message string, which is empty if no error occurred. 
        """
        return self.error_message

    def getID(self):
        """
        Return a unique ID for each message object.
        """
        return self.message_id

    def getMessageData(self):
        """
        Return the message data dictionary.
        """
        return self.message_data

    def getResponse(self, key_name):
        """
        Access elements of the response message by name. If the element is 
        not present, None is returned.
        """
        return self.response.get(key_name, None)

    def getType(self):
        """
        Return a string describing the message type.

        The use of this to check for a certain method type is deprecated! 
        Use isType() instead! i.e.:

        if message.isType("asdf"):        # correct.
        if (message.getType() == "asdf"): # wrong.
        """
        return self.message_type

    def hasError(self):
        """
        Return the error status of the message.
        """
        return self.error

    def isTest(self):
        """
        Return the test status of the message. If the message is in test 
        mode, then it will not be executed. Rather its validity and properties 
        of its execution will be returned. 
        """
        return self.test_mode

    def isType(self, string):
        """
        Use this to check if the message is a certain type.
        """
        return (self.message_type == string)

    def setError(self, error_boolean, error_message):
        """
        Set the error status of the message.
        """
        self.error = error_boolean
        self.error_message = error_message

    def setTestMode(self, test_boolean):
        """
        Set the test status of the message.
        """
        self.test_mode = test_boolean

    def toJSON(self):
        """
        Serialize using JSON.
        """
        return json.dumps(self.__dict__)

    ## markAsComplete
    #
    # Mark a message as complete. A message can be completed while still generating an error. 
    #
    #def markAsComplete(self):
    #    self.complete = True

    def __str__(self):
        """
        Generate a string representation of the message.
        """
        string_rep = "\tMessage Type: " + str(self.message_type)
        for attribute in sorted(vars(self).keys()):
            if not (attribute == "message_type"):
                string_rep += "\n\t" + attribute + ": " + str(getattr(self, attribute))
        return string_rep


# 
# Test of Class
#                         
if (__name__ == "__main__"):

    if False:
        message = TCPMessage(message_type="findSum",
                             message_data={"find_sum":200},
                             test_mode=False)

        print("-"*40)
        print(message)
        print("-"*40)
        print(message.getData("find_sum"))
        message.setError(True, "Could not find focus")
        print("-"*40)
        print(message)

        message = TCPMessage(message_type="movie",
                             message_data={"name":"Test_0_0.dax", "length":1000, "parameters":1},
                             test_mode=False)
        print("-"*40)
        print(message)

    if True:
        message = TCPMessage(message_type="findSum",
                             message_data={"find_sum":200},
                             test_mode=False)
        temp = message.toJSON()
        print(temp)
        print(type(temp))

        #print message
        #print ""
        #message = TCPMessage.fromJSON(message.toJSON())
        #print message

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
