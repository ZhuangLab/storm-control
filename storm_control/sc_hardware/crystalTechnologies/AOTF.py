#!/usr/bin/env python
"""
Communicates with the Crystal Technologies AOTF (via USB).

To work around the lack of a 64 bit version of the
AotfLibrary.dll file we handle a aotf communication
using the AOTF32Bit.py script which needs to be
run in 32 bit Python. Then we communicate with it
using basic IPC.

Hazen 12/13
"""

import ctypes
import os
import socket
import subprocess
import telnetlib
import time

aotf = None
response_time = 0.05
instantiated = False


class AOTF(object):
    """
    This class handles communication with a Crystal Technologies AOTF.
    
    FIXME: I'd like for this class to make sure that the AOTF is closed
    For now, you have to make sure shutdown is called or the process will
    lock (or at least it will lock the DOS prompt).
    """
    def __init__(self, **kwds):
        """
        Create a AOTF object, load the DLL that is used to control the AOTF
        and verify that we can talk to the AOTF.
        
        FIXME: Is the instantiated stuff necessary? It doesn't seem likely
               that we'd ever make the mistake of trying to create two of
               these classes in a single process.
        """
        self.encoding = 'utf-8'
        self.live = True

        global instantiated
        if instantiated:
            print("Attempt to instantiate two AOTF communication classes.")
            self.live = False
        else:
            # Load the AOTF driver library library.
            global aotf
            if os.path.exists('C:\Program Files\Crystal Technology\AOTF Utilities\AotfLibrary\LegacyAotfLibrary\DLL\AotfLibrary.dll'):
                aotf = ctypes.cdll.LoadLibrary('C:\Program Files\Crystal Technology\AOTF Utilities\AotfLibrary\LegacyAotfLibrary\DLL\AotfLibrary')
            elif os.path.exists('C:\Program Files\Crystal Technology\Developer\AotfLibrary\DLL\AotfLibrary.dll'):
                aotf = ctypes.cdll.LoadLibrary('C:\Program Files\Crystal Technology\Developer\AotfLibrary\DLL\AotfLibrary')
            else:
                print("Failed to load AotfLibrary.dll")

            if self._aotfOpen():
                self.live = True
                instantiated = True
            else:
                print("Failed to connect to the AOTF, perhaps it is turned off?")
                self.live = False

    def _aotfGetResp(self):
        """
        This gets a response from the AOTF. If the AOTF does not respond with any data
        in response_time (50ms) then it assumes that there is no more data to get
        from the AOTF.
        """
        if self.live:
            response = ""
            b_size = 100
            time.sleep(response_time)
            have_data = aotf.AotfIsReadDataAvailable(self.aotf_handle)
            while have_data:
                c_resp = ctypes.create_string_buffer(b_size)
                c_read = ctypes.c_uint(0)
                assert(aotf.AotfRead(self.aotf_handle, ctypes.c_uint(b_size), c_resp, ctypes.byref(c_read)))
                temp = c_resp.value
                response += temp[:c_read.value].decode(self.encoding)
                time.sleep(response_time)
                have_data = aotf.AotfIsReadDataAvailable(self.aotf_handle)
            return response
        else:
            return "Invalid"

    def _aotfOpen(self):
        """
        The checks whether the AOTF is "open", i.e. that we can talk to it.
        """
        try:
            self.aotf_handle = aotf.AotfOpen(0)
            self._aotfSendCmd("dau en")
            self._sendCmd("dau gain * 255")
            return True
        except OSError:
            return False

    def _aotfSendCmd(self, cmd):
        """
        Sends a command to the AOTF.
        """
        if self.live:
            cmd += "\n"
            cmd = cmd.encode(self.encoding)
            assert(aotf.AotfWrite(self.aotf_handle, ctypes.c_uint(len(cmd)), ctypes.c_char_p(cmd)) == 1)

    def _sendCmd(self, cmd):
        """
        Sends a command to the AOTF and waits for a response.
        """
        self._aotfSendCmd(cmd)
        response = self._aotfGetResp()
        bad_response = "Invalid"
        if (response[0:len(bad_response)] == bad_response):
            print("AOTF Warning:", response)
        else:
            return response

    def _shutDown(self):
        """
        If you don't call this then the program will lock on shutdown. The only
        way to unlock it is to run the Crystal Technologies labview AOTF control
        program.
        """
        if self.live:
            self._aotfSendCmd("dds Reset")
            self._aotfGetResp()
            aotf.AotfClose(self.aotf_handle)

    def analogModulationOn(self):
        """
        Turn on analog modulation of the AOTF.
        """
        self._sendCmd("dau dis")

    def analogModulationOff(self):
        """
        Turn off analog modulation of the AOTF.
        """
        self._sendCmd("dau en")

    def fskOff(self, channel):
        """
        Turn frequency shift key off for the specified channel.
        """
        cmd = "dds fsk " + str(channel) + " 0"
        self._sendCmd(cmd)

    def fskOn(self, channel, mode = 1):
        """
        Turn frequency shift key on for the specified channel.
        """
        cmd = "dds fsk " + str(channel) + " " + str(mode)
        self._sendCmd(cmd)

    def getStatus(self):
        return self.live

    def reset(self):
        """
        Resets the AOTF.
        """
        self._sendCmd("dds Reset")

    def setAmplitude(self, channel, amplitude):
        """
        Sets amplitude of the specified channel.
        """
        assert(channel >= 0)
        assert(channel < 8)
        assert(amplitude >= 0)
        assert(amplitude <= 16383)
        cmd = "dds a " + str(channel) + " " + str(amplitude)
        self._sendCmd(cmd)

    def setChannel(self, channel, frequency, amplitude):
        """
        Sets the frequency and the amplitude of the specified channel.
        """
        self.setFrequency(channel, frequency)
        self.setAmplitude(channel, amplitude)

    def setFrequencies(self, channel, frequencies):
        """
        Sets the frequencies of the specified channel.
        """
        assert(channel >= 0)
        assert(channel < 8)
        frequency_string = ""
        for frequency in frequencies:
            assert(frequency >= 0)
            assert(frequency < 160.0)
            frequency_string += " " + str(frequency)
        cmd = "dds f " + str(channel) + frequency_string
        self._sendCmd(cmd)

    def setFrequency(self, channel, frequency):
        """
        Set the frequency of the specified channel. 
        """
        self.setFrequencies(channel, [frequency])

    def shutDown(self):
        """
        Reset the AOTF and shutdown communication.
        """
        global instantiated
        instantiated = False
        self._shutDown()
        self.aotf_handle = False


class AOTF64Bit(AOTF):
    """
    This class is for communication with a AOTF when running
    64 bit Python. Since the provided driver only works with
    32 bit processes we start a 32 bit Python process to
    control the AOTF, then we talk to it via IPC (port #9001).

    FIXME: Should there be time-outs on the connection?
    """
    def __init__(self, python32_exe = None):
        """
        Create a 32 bit process for communication with the AOTF and
        verify that it can talk to the AOTF.
        """
        self.encoding = 'utf-8'

        # Create socket.
        self.aotf_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.aotf_socket.settimeout(1.0)
        self.aotf_socket.bind(("127.0.0.1", 9001))

        # Create sub-process to control the AOTF.
        ctech_dir = os.path.dirname(__file__)
        if (len(ctech_dir) > 0):
            aotf_cmd = os.path.join(ctech_dir, "AOTF32Bit.py")
        else:
            aotf_cmd = "AOTF32Bit.py"

        self.live = True
        self.aotf_proc = subprocess.Popen([python32_exe, aotf_cmd], close_fds = True)

        # Wait for connection from the sub-process.
        self.aotf_socket.listen(1)
        [self.aotf_conn, self.aotf_addr] = self.aotf_socket.accept()

        # Verify that we can talk to the AOTF (through the sub-process).
        if not self._aotfOpen():
            self.live = False

    def _aotfOpen(self):
        response = self._sendCmd("dau en")
        if ("Invalid" in response):
            return False
        else:
            self._sendCmd("dau gain * 255")
            return True

    def _sendCmd(self, cmd):
        """
        Send a command to the AOTF using IPC.
        """
        if self.live:
            self.aotf_conn.sendall(cmd.encode(self.encoding))
            resp = self.aotf_conn.recv(1024)
            return resp.decode(self.encoding)
        else:
            return "Invalid"

    def shutDown(self):
        """
        Reset the AOTF and shutdown IPC.
        """
        if self.live:
            self._sendCmd("shutdown")
            self.aotf_conn.close()
            self.aotf_proc.terminate()


class AOTFTelnet(AOTF):
    """
    This class communicates with the AOTF over the ethernet using telnet.
    """
    def __init__(self, ip_address, timeout = 1.0):
        """
        Open telnet connection and verify that it works.
        """
        self.encoding = 'utf-8'
        self.live = True
        
        # Open connection.
        try:
            self.aotf_conn = telnetlib.Telnet(ip_address, timeout = 0.1)
        except socket.timeout:
            print("AOTF not found")
            self.live = False
            return
        
        self.timeout = timeout

        # Login.
        self.aotf_conn.read_until("login: ".encode(self.encoding), self.timeout)
        self.aotf_conn.write("root\n".encode(self.encoding))
        self.aotf_conn.read_until("Password: ".encode(self.encoding), self.timeout)

        dirname = os.path.dirname(__file__)
        if (len(dirname) == 0):
            dirname = "."
        #print(dirname)
        with open(dirname + '/aotf_pass.txt', 'r') as fp:
            password = fp.readline()
        msg = password + "\n"
        self.aotf_conn.write(msg.encode(self.encoding))
        self.aotf_conn.read_until("root:~> ".encode(self.encoding), self.timeout)

        # Start Aotf control program.
        self.aotf_conn.write("/bin/Aotf\n".encode(self.encoding))
        self.aotf_conn.read_until("* ".encode(self.encoding), self.timeout)

        # Verify that we can talk to the Aotf.
        if not self._aotfOpen():
            self.live = False
        
    def _aotfOpen(self):
        response = self._sendCmd("dau en")
        if ("Invalid" in response):
            return False
        else:
            self._sendCmd("dau gain * 255")
            return True

    def _sendCmd(self, cmd):
        """
        Send a command to the AOTF using IPC.
        """
        if self.live:
            msg = cmd + "\n"
            self.aotf_conn.write(msg.encode(self.encoding))
            resp = self.aotf_conn.read_until("* ".encode(self.encoding), self.timeout)
            return resp.decode(self.encoding)
        else:
            return "Invalid"

    def shutDown(self):
        """
        Reset the AOTF and shutdown IPC.
        """
        if self.live:
            self._sendCmd("shutdown")
            self.aotf_conn.close()


#
# Testing.
#
if (__name__ == "__main__"):
    #my_aotf = AOTF()
    #my_aotf = AOTF64Bit(python32_exe = "C:/Users/hazen/AppData/Local/Programs/Python/Python36-32/python")
    my_aotf = AOTFTelnet("192.168.10.3")

    if not my_aotf.getStatus():
        exit()

    print(my_aotf._sendCmd("BoardID ID"))
    print(my_aotf._sendCmd("dds f 0 88.6"))

#    start_time = time.time()
#    for i in range(100):
#        for j in range(8):
#            my_aotf._sendCmd("dds a " + str(j) + " 6100")
#            my_aotf._sendCmd("dds a " + str(j) + " 0")
#            #print my_aotf._sendCmd("dds a " + str(j) + " 6100")
#            #print my_aotf._sendCmd("dds a " + str(j) + " 0")
#    print("elapsed time ", time.time() - start_time)
#    time.sleep(1.0)
    my_aotf.shutDown()

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
 
