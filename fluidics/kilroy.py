#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A master control class to implemented a series of automated flow protocols
# using a daisy chained valve system (and eventually syringe pumps)
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import os
import time
from PyQt4 import QtCore, QtGui
from valveChain import ValveChain
from valveProtocols import ValveProtocols
from kilroyServer import KilroyServer
import halLib.parameters as params

# ----------------------------------------------------------------------------------------
# Kilroy Class Definition
# ----------------------------------------------------------------------------------------
class Kilroy(QtGui.QMainWindow):
    def __init__(self, parameters):
        super(Kilroy, self).__init__()

        # Parse parameters into internal attributes
        self.verbose = parameters.verbose
        self.com_port = parameters.com_port
        self.tcp_port = parameters.tcp_port
        if not hasattr(parameters, "num_simulated_valves"):
            self.num_simulated_valves = 0
        else:
            self.num_simulated_valves = parameters.num_simulated_valves
        if not hasattr(parameters, "valve_protocols_file"):
            self.valve_protocols_file = "default_config.xml"
        else:
            self.valve_protocols_file = parameters.valve_protocols_file
        if not hasattr(parameters, "valve_commands_file"):
            self.valve_commands_file = "default_config.xml"
        else:
            self.valve_commands_file = parameters.valve_commands_file

        # Define additional internal attributes
        self.sent_protocol_names = []

        # Create ValveChain instance
        self.valveChain = ValveChain(com_port = self.com_port,
                                     num_simulated_valves = self.num_simulated_valves,
                                     verbose = self.verbose)

        # Create ValveProtocols instance and connect signals
        self.valveProtocols = ValveProtocols(protocol_xml_path = self.valve_protocols_file,
                                             command_xml_path = self.valve_commands_file,
                                             verbose = self.verbose)

        self.valveProtocols.command_ready_signal.connect(self.sendCommand)
        self.valveProtocols.status_change_signal.connect(self.handleProtocolStatusChange)
        self.valveProtocols.completed_protocol_signal.connect(self.handleProtocolComplete)

        # Create Kilroy TCP Server and connect signals
        self.tcpServer = KilroyServer(port = self.tcp_port,
                                      verbose = self.verbose)
        self.tcpServer.data_ready.connect(self.handleTCPData)

        # Create GUI
        self.createGUI()

    # ----------------------------------------------------------------------------------------
    # Create master GUI
    # ----------------------------------------------------------------------------------------
    def close(self):
        self.valveProtocols.close()
        self.tcpServer.close()
        self.valveChain.close()
        print "\nKilroy was here!"

    # ----------------------------------------------------------------------------------------
    # Create master GUI
    # ----------------------------------------------------------------------------------------
    def createGUI(self):
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addWidget(self.valveProtocols.mainWidget, 0, 0, 1, 3)
        self.mainLayout.addWidget(self.valveProtocols.valveCommands.mainWidget, 2, 0, 1, 3) 
        self.mainLayout.addWidget(self.valveChain.mainWidget, 0, 4, 1, 1)
        self.mainLayout.addWidget(self.tcpServer.mainWidget, 2, 4, 1, 1)

    # ----------------------------------------------------------------------------------------
    # Redirect protocol status change from valveProtocols to valveChain
    # ----------------------------------------------------------------------------------------
    def handleProtocolStatusChange(self):
        status = self.valveProtocols.getStatus()
        if status[0] >= 0: # Protocol is running
            self.valveChain.setEnabled(False)
        else:
            self.valveChain.setEnabled(True)

    # ----------------------------------------------------------------------------------------
    # Handle a protocol complete signal from the valve protocols
    # ----------------------------------------------------------------------------------------
    def handleProtocolComplete(self, protocol_name):
        # If the protocol was sent by TCP pass on the complete signal
        if protocol_name in self.sent_protocol_names:
            self.sent_protocol_names.remove(protocol_name)
            self.tcpServer.sendProtocolComplete(protocol_name)

    # ----------------------------------------------------------------------------------------
    # Handle protocol request sent via TCP server
    # ----------------------------------------------------------------------------------------
    def handleTCPData(self):
        # Get protocol from tcpServer
        protocol_name = self.tcpServer.getProtocol()
        
        if self.verbose:
            print "Running Protocol from Kilroy Client: " + protocol_name

        if self.valveProtocols.isValidProtocol(protocol_name):
            # Keep track of protocols issued via TCP 
            self.sent_protocol_names.append(protocol_name)

            # Start the protocol
            self.valveProtocols.startProtocolByName(protocol_name)
        else: # Respond with a protocol complete
            self.tcpServer.sendProtocolComplete(protocol_name)
            
    # ----------------------------------------------------------------------------------------
    # Redirect commands from valve protocol class to valve chain class
    # ----------------------------------------------------------------------------------------
    def sendCommand(self):
        command = self.valveProtocols.getCurrentCommand()
        self.valveChain.receiveCommand(command)

# ----------------------------------------------------------------------------------------
# Stand Alone Kilroy Class
# ----------------------------------------------------------------------------------------                                                                   
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parameters, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create kilroy
        self.kilroy = Kilroy(parameters)
                                          
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.kilroy.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Kilroy")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Define close menu item
        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Add menu items
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        for menu_item in self.kilroy.valveProtocols.menu_items[0]:
            file_menu.addAction(menu_item)
        file_menu.addAction(exit_action)

        valve_menu = menubar.addMenu("&Valves")
        for menu_item in self.kilroy.valveChain.menu_items[0]:
            valve_menu.addAction(menu_item)

    # ----------------------------------------------------------------------------------------
    # Handle close event
    # ----------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.kilroy.close()
        self.close()

# ----------------------------------------------------------------------------------------
# Runtime code: Kilroy is meant to be run as a stand alone
# ----------------------------------------------------------------------------------------                                
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    # Show splash screen (to allow for valve initialization)
    splash_pix = QtGui.QPixmap("kilroy_splash.jpg")
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    time.sleep(.1) # Define minimum startup time

    # Load parameters
    if len(sys.argv) == 2:
        parameters = params.Parameters(sys.argv[1])
    else:
        parameters = params.Parameters("kilroy_settings_default.xml")

    # Create instance of StandAlone class
    window = StandAlone(parameters)

    # Remove splash screen
    splash.hide()

    # Run main app
    window.show()
    sys.exit(app.exec_())
