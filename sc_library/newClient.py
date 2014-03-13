#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A TCP communication class that acts as the client side for generic communications
# between programs in the storm-control project
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 3/8/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time
import pickle
from PyQt4 import QtCore, QtGui, QtNetwork
from sc_library.tcpMessage import TCPMessage

# ----------------------------------------------------------------------------------------
# Basic Socket
# ----------------------------------------------------------------------------------------
class Socket(QtNetwork.QTcpSocket):
    # Define custom command ready signal
    message_ready = QtCore.pyqtSignal(object)
    
    def __init__(self,
                 parent = None,
                 port=9500,
                 server_name = "default",
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 verbose = False):
        QtNetwork.QTcpSocket.__init__(self, parent)

        # Initialize internal variables
        self.verbose = verbose
        self.address = address 
        self.port = port 
        self.server_name = server_name
        self.num_conn_tries = 5
        
        # Connect data ready signal
        self.readyRead.connect(self.handleReadyRead)

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing socket"

    # ------------------------------------------------------------------------------------
    # Connect to Server 
    # ------------------------------------------------------------------------------------       
    def connectToServer(self):
        if self.verbose:
            string = "Looking for " + self.server_name + " server at: \n"
            string += "    Address: " + self.address.toString() + "\n"
            string += "    Port: " + str(self.port)
            print string

        self.connectToHost(self.address, self.port)
        tries = 0
        while (not self.waitForConnected() and (tries < self.num_conn_tries)):
            print "Could not find " + self.server_name + " server. Attempt: " + str(tries)
            time.sleep(1)
            self.connectToHost(self.address, self.port)
            tries += 1
            
        if tries==self.num_conn_tries:
            print self.server_name + " server not found"
        else:
            print "Connected to "+ self.server_name + " server"

    # ------------------------------------------------------------------------------------
    # Handle multiple client connections 
    # ------------------------------------------------------------------------------------       
    def handleBusy(self): 
        pass
    
    # ------------------------------------------------------------------------------------
    # Handle new data triggered by the readyRead signal 
    # ------------------------------------------------------------------------------------       
    def handleReadyRead(self):
        message_str = ""
        while self.canReadLine():
            # Read data line
            message_str += str(self.readLine())
            
        message = pickle.loads(message_str)
        if self.verbose: print "Received: \n" + str(message)

        if message.getType() == "Busy":
            self.handleBusy()
        else:
            self.message_ready.emit(message)

    # ------------------------------------------------------------------------------------
    # Send message 
    # ------------------------------------------------------------------------------------       
    def sendMessage(self, message):
        message_string = pickle.dumps(message)
        self.write(message_string + "\n") # Newline required to trigger canReadLine()
        self.flush()
        if self.verbose: print "Sent: \n" + str(message)

# ----------------------------------------------------------------------------------------
# TCP Client Class
# ----------------------------------------------------------------------------------------                                                                
class TCPClient(QtGui.QWidget):
    # Define custom command ready signal: to relay socket signals
    message_ready = QtCore.pyqtSignal(object)
    disconnect = QtCore.pyqtSignal()

    def __init__(self,
                 parent = None,
                 port=9500,
                 server_name = "default",
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 verbose = False):
        QtGui.QWidget.__init__(self, parent)

        # Define attributes
        self.address = address # Default is local machine
        self.port = port # Default is 9500
        self.server_name = server_name
        self.verbose = verbose
        
        # Create instance of socket
        self.socket = Socket(port = self.port,
                             server_name = self.server_name,
                             address = self.address,
                             verbose = self.verbose)
        
        # Connect socket signals
        self.socket.message_ready.connect(self.handleMessageReady)
        self.socket.disconnected.connect(self.handleDisconnect)

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing client: " + self.server_name
        if self.isConnected(): self.socket.close()
        
    # ------------------------------------------------------------------------------------
    # Relay message ready signal with message 
    # ------------------------------------------------------------------------------------       
    def handleMessageReady(self, message):
        self.message_ready.emit(message)

    # ------------------------------------------------------------------------------------
    # Pass server disconnect signal 
    # ------------------------------------------------------------------------------------       
    def handleDisconnect(self):
        self.disconnect.emit()

    # ------------------------------------------------------------------------------------
    # Return true if socket exists and is connected 
    # ------------------------------------------------------------------------------------       
    def isConnected(self):
        if (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False   

    # ------------------------------------------------------------------------------------
    # Send a message via the socket 
    # ------------------------------------------------------------------------------------       
    def sendMessage(self, message):
        if self.isConnected():
            self.socket.sendMessage(message)
            return True
        else:
            print self.server_name + " socket not connected. Did not send: " + str(command)
            return False      

    # ------------------------------------------------------------------------------------
    # Disconnect the socket from the host
    # ------------------------------------------------------------------------------------       
    def stopCommunication(self):
        if self.isConnected():
            self.socket.disconnectFromHost()

    # ------------------------------------------------------------------------------------
    # Attempt to connect socket
    # ------------------------------------------------------------------------------------       
    def startCommunication(self):
        if not self.isConnected():
            self.socket.connectToServer()

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create client
        self.client = TCPClient(port = 9500, server_name = "Test", verbose = True)
        self.client.message_ready.connect(self.handleMessageReady)            
        self.client.startCommunication()

        self.message_ID = 1
        self.sendTestMessage()
        
    # ----------------------------------------------------------------------------------------
    # Send Test Messages
    # ----------------------------------------------------------------------------------------
    def sendTestMessage(self):
        if self.message_ID == 1:
            # Create Test message
            message = TCPMessage(message_type = "Stage Position",
                                  data = {"Stage_X": 100.00, "Stage_Y": 0.00})
        elif self.message_ID ==2:
            message = TCPMessage(message_type = "Movie",
                                  data = {"Name": "Test_Movie_01", "Parameters": 1})

        else:
            message = TCPMessage(message_type = "Done")
    
        self.message_ID += 1
        self.sent_message = message
        self.client.sendMessage(message)
        
    # ----------------------------------------------------------------------------------------
    # Handle New Message
    # ----------------------------------------------------------------------------------------
    def handleMessageReady(self, message):
        # Handle responses to messages
        if self.sent_message.getID() == message.getID():
            if message.isComplete():
                print "Completed message: "
                print message
        else:
            print "Received an unexpected message"

        self.sendTestMessage()
        
    # ----------------------------------------------------------------------------------------
    # Handle close event
    # ----------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.client.close()
        self.close()
       
# ----------------------------------------------------------------------------------------
# Test/Demo of Class
# ----------------------------------------------------------------------------------------                        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())
    
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
