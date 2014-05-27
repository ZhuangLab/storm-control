#!/usr/bin/python
#
## @file 
#
# Handles remote control (via TCP/IP of the data collection program) 
# 
# Jeffrey Moffitt
# 3/8/14
# jeffmoffitt@gmail.com
# 
# Hazen 05/14
#

import json


## TCPMessage
#
# Contains the contents and status of a TCP message.
#
class TCPMessage(object):
    _COUNTER = 0 # Track number of created instances of this class.

    ## __init__
    #
    # The constructor for a TCP message object
    #
    # @param message_type A string specifying the type of the command.
    # @param message_data A dictionary containing the message data.
    # @param test_mode A boolean specifying whether the command is a test command
    #
    def __init__(self,
                 message_type = False,
                 message_data = {},
                 test_mode = False):

        assert message_type, "Message type must be defined!"
        #self.complete = False
        self.error = False
        self.error_message = None
        self.message_data = message_data
        self.message_type = message_type
        self.response = {}
        self.test_mode = test_mode

        self.message_id = TCPMessage._COUNTER # Record instance number.
        TCPMessage._COUNTER += 1 # Increment the instance counter.

    ## addData
    #
    # Add or change the contents of fields in the message data dictionary
    #
    # @param key_name A string specifying the name/type of the data to be added to the message data.
    # @param value The data.
    #
    def addData(self, key_name, value):
        self.message_data[key_name] = value

    ## addResponse
    #
    # Add or change the contents of fields in the response data dictionary
    #
    # @param key_name A string specifying the name/type of the data to be added to the response data.
    # @param value The data.
    #
    def addResponse(self, key_name, value):
        self.response[key_name] = value

    ## fromJSON
    #
    # Creates a Message from a JSON string.
    #
    # @param json_string A JSON string containing the serialized object data.
    #
    @staticmethod
    def fromJSON(json_string):
        message = TCPMessage(message_type = True)
        message.__dict__.update(json.loads(json_string))
        return message

    ## getData
    #
    # Access elements of the message data by name
    #
    # @param key_name A string specifying the name/type of the data to be accessed from the message data.
    #
    # @return The value of the requested entry.
    #
    def getData(self, key_name):
        return self.message_data.get(key_name, None)

    ## getErrorMessage
    #
    # Return the error message string, which is empty if no error occurred. 
    #
    # @return A string describing any errors if present.
    #
    def getErrorMessage(self):
        return self.error_message

    ## getID
    #
    # Return a unique ID for each message object
    #
    # @return An unique ID for the message.
    #
    def getID(self):
        return self.message_id

    ## getResponse
    #
    # Access elements of the response message by name. If the element is not present, None is returned.
    #
    # @param key_name A string specifying the name/type of the data to be accessed from the response data.
    # @return The value of the requested entry.
    #
    def getResponse(self, key_name):
        return self.response.get(key_name, None)

    ## getType
    #
    # Return a string describing the message type
    #
    # @return A string describing the type of the message.
    #    
    def getType(self):
        return self.message_type

    ## hasError
    #
    # Return the error status of the message
    #
    # @return A boolean which indicates whether an error has occurred or not.
    #    
    def hasError(self):
        return self.error

    ## isTest
    #
    # Return the test status of the message. If the message is in test mode, then it will not be
    # executed. Rather its validity and properties of its execution will be returned. 
    #
    # @return A boolean which indicates whether the message is in test mode.
    #  
    def isTest(self):
        return self.test_mode

    ## setError
    #
    # Set the error status of the message
    #
    # @param error_boolean A boolean that indicates whether an error has occurred
    # @param error_message A string describing the error
    #  
    def setError(self, error_boolean, error_message):
        self.error = error_boolean
        self.error_message = error_message

    ## setTestMode
    #
    # Set the test status of the message
    #
    # @param test_boolean A boolean that indicates whether the message should be considered a test
    #
    def setTestMode(self, test_boolean):
        self.test_mode = test_boolean

    ## toJSON
    #
    # Serialize using JSON.
    #
    # @return A string containing the JSON serialization.
    #
    def toJSON(self):
        return json.dumps(self.__dict__)

    ## markAsComplete
    #
    # Mark a message as complete. A message can be completed while still generating an error. 
    #
    #def markAsComplete(self):
    #    self.complete = True

    ## __str__
    #
    # Generate a string representation of the message
    #
    # @return string_rep A string representation of the contents of the message and its properties
    #
    def __str__(self):
        string_rep = "\tMessage Type: " + str(self.message_type)
        for attribute in sorted(vars(self).keys()):
            if not (attribute == "message_type"):
                string_rep += "\n\t" + attribute + ": " + str(getattr(self, attribute))
        return string_rep


# 
# Test of Class
#                         
if __name__ == "__main__":

    if 0:
        message = TCPMessage(message_type="findSum",
                             message_data={"find_sum":200},
                             test_mode=False)

        print "-"*40
        print message
        print "-"*40
        print message.getData("find_sum")
        message.setError(True, "Could not find focus")
        print "-"*40
        print message

        message = TCPMessage(message_type="movie",
                             message_data={"name":"Test_0_0.dax", "length":1000, "parameters":1},
                             test_mode=False)
        print "-"*40
        print message

    if 1:
        message = TCPMessage(message_type="findSum",
                             message_data={"find_sum":200},
                             test_mode=False)
        temp = message.toJSON()
        print temp
        print type(temp)

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
