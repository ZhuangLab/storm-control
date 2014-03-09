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
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(object)
    
    def __init__(self,
                 parent = None,
                 port=9500,
                 server_name = "default",
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 verbose = False):
        QtNetwork.QTcpSocket.__init__(self, parent)

        # Initialize internal variables
        self.verbose = verbose
        self.address = address # Default is local address
        self.port = port # Default is port 9500 
        self.server_name = server_name
        
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
        while (not self.waitForConnected() and (tries < 5)):
            print "Could not find " + self.server_name + " server. Attempt: " + str(tries)
            time.sleep(1)
            self.connectToHost(self.address, self.port)
            tries += 1
            
        if tries==5:
            print self.server_name + " server found"
        else:
            print "Connected to "+ self.server_name + " server"

    # ------------------------------------------------------------------------------------
    # Handle new data triggered by the readyRead signal 
    # ------------------------------------------------------------------------------------       
    def handleReadyRead(self):
        message_str = ""
        while self.canReadLine():
            # Read data line
            message_str += str(self.readLine())
        message = pickle.loads(message_str)
        if message.getType() == "Acknowledge":
            self.acknowledged.emit()
        elif message.getType() == "Busy":
            #### HANDLE BUSY
            pass
        else:
            self.complete.emit(message)

    # ------------------------------------------------------------------------------------
    # Send message 
    # ------------------------------------------------------------------------------------       
    def sendMessage(self, message):
        message_string = pickle.dumps(message)
        self.write(message_string + "\n") # Newline required to trigger canReadLine()

# ----------------------------------------------------------------------------------------
# TCP Client Class
# ----------------------------------------------------------------------------------------                                                                
class TCPClient(QtGui.QWidget):
    # Define custom command ready signal: to relay socket signals
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(object)
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
        self.unacknowledged_messages = 0
        self.command_pause_time = 0.05
        self.sent_message = None
        
        # Create instance of socket
        self.socket = Socket(port = self.port,
                             server_name = self.server_name,
                             verbose = self.verbose)
        
        # Connect socket signals
        self.socket.acknowledged.connect(self.handleAcknowledged)
        self.socket.complete.connect(self.handleComplete)
        self.socket.disconnected.connect(self.handleDisconnect)

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing client: " + self.server_name
        if self.isConnected(): self.socket.close()
        
    # ------------------------------------------------------------------------------------
    # Handle acknowledged receipt of transmitted message 
    # ------------------------------------------------------------------------------------       
    def handleAcknowledged(self):
        self.unacknowledged_messages -= 1
        if self.unacknowledged_messages == 0:
            self.acknowledged.emit() # All messages have been sent and received
        
    # ------------------------------------------------------------------------------------
    # Handle completion of signal command 
    # ------------------------------------------------------------------------------------       
    def handleComplete(self, message):
        self.complete.emit(message)

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
            self.unacknowledged_messages += 1
            self.socket.sendMessage(message)
            self.socket.flush()
            time.sleep(self.command_pause_time)
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
            self.unacknowledged_messages = 0

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create client
        self.client = TCPClient(port = 9500, server_name = "Test", verbose = True)

        # Connect PyQt signals
        self.client.acknowledged.connect(self.handleAcknowledge)
        
        # Create Test message
        self.message = TCPMessage(message_type = "Test Message")
        self.message.data = [1,2,3]

        # Start Communication and send message
        self.client.startCommunication()
        self.client.sendMessage(self.message)

    # ----------------------------------------------------------------------------------------
    # Handle ackwnoledge
    # ----------------------------------------------------------------------------------------
    def handleAcknowledge(self):
        print "Acknowledge receipt of message"

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
