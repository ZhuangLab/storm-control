#!/usr/bin/env python

import sys
from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.tcpClient as tcpClient
import storm_control.sc_library.tcpMessage as tcpMessage
import storm_control.sc_library.tcpServer as tcpServer


class Client(QtCore.QObject):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Create client
        self.client = tcpClient.TCPClient(port = 9500, server_name = "Test")

        self.client.messageReceived.connect(self.handleMessageReceived)
        self.client.startCommunication()

        self.message_ID = 1
        self.sendTestMessage()

    def sendTestMessage(self):
        """
        Send test messages.
        """
        if (self.message_ID == 1):
            # Create Test message
            message = tcpMessage.TCPMessage(message_type = "Stage Position",
                                            message_data = {"Stage_X": 100.00, "Stage_Y": 0.00})
        elif (self.message_ID ==2):
            message = tcpMessage.TCPMessage(message_type = "Movie",
                                            message_data = {"Name": "Test_Movie_01", "Parameters": 1})

        else:
            message = tcpMessage.TCPMessage(message_type = "Done")
    
        self.message_ID += 1
        self.sent_message = message
        self.client.sendMessage(message)
        
    def handleMessageReceived(self, message):
        """
        Handle new message.
        """
        # Handle responses to messages
        if (self.sent_message.getID() != message.getID()):
            print("Received an unexpected message")
        print("")

        if (self.message_ID < 4):
            self.sendTestMessage()
        else:
            self.client.close()


class Server(QtCore.QObject):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Create server
        self.server = tcpServer.TCPServer(port = 9500, verbose = True)

        # Connect PyQt signals
        self.server.comGotConnection.connect(self.handleNewConnection)
        self.server.comLostConnection.connect(self.handleLostConnection)
        self.server.messageReceived.connect(self.handleMessageReceived)

    def handleNewConnection(self):
        """
        Handle new connection.
        """
        print("Established connection")

    def handleLostConnection(self):
        """
        Handle lost connection.
        """
        print("Lost connection")
        self.server.close()
        QtWidgets.QApplication.quit()

    def handleMessageReceived(self, message):
        """
        Handle new message.
        """
        # Parse Based on Message Type
        if message.isType("Stage Position"):
            self.server.sendMessage(message)
            
        elif message.isType("Movie"):
            self.server.sendMessage(message)

        elif message.isType("Done"):
            self.server.sendMessage(message)


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)    
    server = Server()
    client = Client()
    app.exec_()
