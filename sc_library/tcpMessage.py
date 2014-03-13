#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A message class for TCP/IP communication
# ----------------------------------------------------------------------------------------
# Jeffrey Moffitt
# 3/8/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import uuid 

# ----------------------------------------------------------------------------------------
# TCP Message Class
# ----------------------------------------------------------------------------------------
class TCPMessage():
    def __init__(self,
                 message_type = "Default",
                 data = None,
                 test = False):
        self.message_type = message_type
        self.id = str(uuid.uuid1())
        self.data = data
        self.response = None
        self.error = False
        self.error_message = None
        self.test = False
        self.complete = False
        
    def getType(self):
        return self.message_type

    def getID(self):
        return self.id

    def getData(self, key_value):
        return self.data.get(key_value, None)

    def getResponse(self, key_value):
        return self.response.get(key_value, None)

    def isTest(self):
        return self.test

    def isComplete(self):
        return self.complete

    def hasError(self):
        return self.error

    def getErrorMessage(self):
        return self.error_message
    
    def markAsComplete(self):
        self.complete = True
    
    def __str__(self):
        string_rep = "Message Type: " + str(self.message_type) + "\n"
        for attribute in vars(self).keys():
            if not attribute == "message_type":
                string_rep += "\t" + attribute + ": " + str(getattr(self, attribute)) + "\n"
        return string_rep

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
