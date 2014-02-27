#!/usr/bin/python
#
## @file
#
# Control a Edmunds high speed filter wheel.
#
# Hazen 02/14
#

import os
import socket
import subprocess
import time
import win32com.client

class HSFW():
    
    def __init__(self):
        #self.excel = win32com.client.Dispatch("Excel.Application")
        #self.excel.Visible = 1
        fw_com = win32com.client.Dispatch("OptecHID_FilterWheelAPI.FilterWheels")
        fw_wheels = fw_com.FilterWheelList
        self.fw = fw_wheels(0)
        self.fw.ClearErrorState
        self.fw.HomeDevice

    def getPosition(self):
        return self.fw.CurrentPosition

    def getStatus(self):
        return True

    def setPosition(self, position):
        if (position > 0) and (position <= self.fw.NumberOfFilters):
            self.fw.CurrentPosition = position
        else:
            print "HSFW: position out of range:", position

    def shutDown(self):
        pass


class HSFW64Bit():
    
    def __init__(self):
        self.cur_position = 1
        self.hsfw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hsfw_socket.bind(("127.0.0.1", 9002))

        dir = os.path.dirname(__file__)
        if (len(dir) > 0):
            hsfw_cmd = dir + "\hsFilterWheel32Bit.py"
        else:
            hsfw_cmd = "hsFilterWheel32Bit.py"

        self.hsfw_proc = subprocess.Popen(["c:\python27_32bit\python", hsfw_cmd], close_fds = True)

        self.hsfw_socket.listen(1)
        [self.hsfw_conn, self.hsfw_addr] = self.hsfw_socket.accept()

    def getStatus(self):
        return True

    def setPosition(self, position):
        if (position != self.cur_position):
            self.hsfw_conn.sendall(str(position))
            self.cur_position = position
        
    def shutDown(self):
        self.hsfw_conn.sendall("shutdown")
        self.hsfw_conn.close()


#
# Testing
#

if __name__ == "__main__":
    hsfw = HSFW64Bit()
    time.sleep(1.0)
#    print hsfw.fw.IsMoving
    for i in range(10):
        print i
        hsfw.setPosition(i+1)
        time.sleep(1.0)
    hsfw.shutDown()
        
#        print hsfw.fw.IsMoving

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

