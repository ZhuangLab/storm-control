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
from PyQt5 import QtCore, QtGui, QtWidgets
from storm_control.fluidics.valves.valveChain import ValveChain
from storm_control.fluidics.pumps.pumpControl import PeristalticPumpControl
from storm_control.fluidics.pumps.pumpControl import SyringePumpControl
from storm_control.fluidics.kilroyProtocols import KilroyProtocols
from storm_control.sc_library.tcpServer import TCPServer
import storm_control.sc_library.parameters as params

# ----------------------------------------------------------------------------------------
# Kilroy Class Definition
# ----------------------------------------------------------------------------------------
class Kilroy(QtWidgets.QMainWindow):
    def __init__(self, parameters):
        super(Kilroy, self).__init__()

        # Parse parameters into internal attributes
        self.verbose = parameters.get("verbose")
        self.valve_com_port = parameters.get("valves_com_port")
        self.tcp_port = parameters.get("tcp_port")
        self.pump_com_port = parameters.get("pump_com_port")
        self.pump_ID = parameters.get("pump_ID")

        if not parameters.has("pump_type"):
            self.pump_type = 'peristaltic'
        else:
            self.pump_type = parameters.get('pump_type')

        if not parameters.has("num_simulated_valves"):
            self.num_simulated_valves = 0
        else:
            self.num_simulated_valves = parameters.get("num_simulated_valves")

        if not parameters.has("valve_type"):
            self.valve_type = 'Hamilton'
        else:
            self.valve_type = parameters.get("valve_type")
            
        if not parameters.has("protocols_file"):
            self.protocols_file = "default_config.xml"
        else:
            self.protocols_file = parameters.get("protocols_file")
            
        if not parameters.has("commands_file"):
            self.commands_file = "default_config.xml"
        else:
            self.commands_file = parameters.get("commands_file")
            
        if not parameters.has("simulate_pump"):
            self.simulate_pump = False
        else:
            self.simulate_pump = parameters.get("simulate_pump")

        # Define additional internal attributes
        self.received_message = None
        
        # Create ValveChain instance
        self.valveChain = ValveChain(com_port = self.valve_com_port,
                                     num_simulated_valves = self.num_simulated_valves,
                                     valve_type=self.valve_type,
                                     verbose = self.verbose)

        # Create PumpControl instance
        if self.pump_type == 'peristaltic':
            self.pumpControl = PeristalticPumpControl(parameters=parameters)
        elif self.pump_type == 'syringe':
            self.pumpControl = SyringePumpControl(parameters=parameters)

        # Create KilroyProtocols instance and connect signals
        self.kilroyProtocols = KilroyProtocols(protocol_xml_path = self.protocols_file,
                                               command_xml_path = self.commands_file,
                                               verbose = self.verbose,
                                               pumpType = self.pump_type)

        self.kilroyProtocols.command_ready_signal.connect(self.sendCommand)
        self.kilroyProtocols.status_change_signal.connect(self.handleProtocolStatusChange)
        self.kilroyProtocols.completed_protocol_signal.connect(self.handleProtocolComplete)

        # Create Kilroy TCP Server and connect signals
        self.tcpServer = TCPServer(port = self.tcp_port,
                                   server_name = "Kilroy",
                                   verbose = self.verbose)
        
        self.tcpServer.messageReceived.connect(self.handleTCPData)

        # Create GUI
        self.createGUI()

    # ----------------------------------------------------------------------------------------
    # Close
    # ----------------------------------------------------------------------------------------
    def close(self):
        self.kilroyProtocols.close()
        self.tcpServer.close()
        self.valveChain.close()
        self.pumpControl.close()
        print("\nKilroy was here!")

    # ----------------------------------------------------------------------------------------
    # Create master GUI
    # ----------------------------------------------------------------------------------------
    def createGUI(self):
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.addWidget(self.kilroyProtocols.mainWidget, 0, 0, 2, 2)
        self.mainLayout.addWidget(self.kilroyProtocols.valveCommands.mainWidget, 2, 0, 1, 1)
        self.mainLayout.addWidget(self.kilroyProtocols.pumpCommands.mainWidget, 2, 1, 1, 1)
        self.mainLayout.addWidget(self.valveChain.mainWidget, 0, 2, 2, 2)
        self.mainLayout.addWidget(self.pumpControl.mainWidget, 0, 4, 2, 1)
        #self.mainLayout.addWidget(self.tcpServer.mainWidget, 2, 2, 1, 4)

    # ----------------------------------------------------------------------------------------
    # Redirect protocol status change from kilroyProtocols to valveChain
    # ----------------------------------------------------------------------------------------
    def handleProtocolStatusChange(self):
        status = self.kilroyProtocols.getStatus()
        if status[0] >= 0: # Protocol is running
            self.valveChain.setEnabled(False)
            self.pumpControl.setEnabled(False)
        else:
            self.valveChain.setEnabled(True)
            self.pumpControl.setEnabled(True)

    # ----------------------------------------------------------------------------------------
    # Handle a protocol complete signal from the valve protocols
    # ----------------------------------------------------------------------------------------
    def handleProtocolComplete(self, message):
        # If the protocol was sent by TCP pass on the complete signal
        if (self.received_message is not None) and self.received_message.getID() == message.getID():
            self.tcpServer.sendMessage(message)
            self.received_message = None # Reset the received_message

    # ----------------------------------------------------------------------------------------
    # Handle protocol request sent via TCP server
    # ----------------------------------------------------------------------------------------
    def handleTCPData(self, message):        
        # Confirm that message is a protocol message
        if not message.getType() == "Kilroy Protocol":
            message.setError(True, "Wrong message type sent to Kilroy: " + message.getType())
            self.tcpServer.sendMessage(message)
        elif not self.kilroyProtocols.isValidProtocol(message.getData("name")):
            message.setError(True, "Invalid Kilroy Protocol")
            self.tcpServer.sendMessage(message)
        elif message.isTest():
            required_time = self.kilroyProtocols.requiredTime(message.getData("name"))
            message.addResponse("duration", required_time)
            self.tcpServer.sendMessage(message)
        else: # Valid, non-test message                                    
            # Keep track of valid messages issued via TCP 
            self.received_message = message
            # Start the protocol
            self.kilroyProtocols.startProtocolRemotely(message)
            
    # ----------------------------------------------------------------------------------------
    # Redirect commands from kilroy protocol class to valves or pump
    # ----------------------------------------------------------------------------------------
    def sendCommand(self):
        command_data = self.kilroyProtocols.getCurrentCommand()
        if command_data[0] == "valve":
            self.valveChain.receiveCommand(command_data[1])
        elif command_data[0] == "pump":
            self.pumpControl.receiveCommand(command_data[1])
        else:
            print("Received command of unknown type: " + str(command_data[0]))

# ----------------------------------------------------------------------------------------
# Stand Alone Kilroy Class
# ----------------------------------------------------------------------------------------                                                                   
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parameters, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create kilroy
        self.kilroy = Kilroy(parameters)
                                          
        # central widget
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.kilroy.mainLayout)

        # This is for handling file drops.
        self.centralWidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.centralWidget.__class__.dropEvent = self.dropEvent
        self.centralWidget.setAcceptDrops(True)
        
        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Kilroy")

        # set window geometry
        self.setGeometry(50, 50, 1200, 800)

        # Define close menu item
        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Add menu items
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        for menu_item in self.kilroy.kilroyProtocols.menu_items[0]:
            file_menu.addAction(menu_item)
        file_menu.addAction(exit_action)

        valve_menu = menubar.addMenu("&Valves")
        for menu_item in self.kilroy.valveChain.menu_items[0]:
            valve_menu.addAction(menu_item)

    # ----------------------------------------------------------------------------------------
    # Handle dragEnterEvent
    # ----------------------------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # ----------------------------------------------------------------------------------------
    # Handle dragEnterEvent
    # ----------------------------------------------------------------------------------------
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.kilroy.kilroyProtocols.loadFullConfiguration(xml_file_path = str(url.path())[1:])

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
    app = QtWidgets.QApplication(sys.argv)

    # Show splash screen (to allow for valve initialization)
    splash_pix = QtGui.QPixmap("kilroy_splash.jpg")
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    time.sleep(.1) # Define minimum startup time

    # Load parameters
    if len(sys.argv) == 2:
        parameters = params.parameters(sys.argv[1])
    else:
        parameters = params.parameters("kilroy_settings_default.xml")

    # Create instance of StandAlone class
    window = StandAlone(parameters)

    # Remove splash screen
    splash.hide()

    # Run main app
    window.show()
    sys.exit(app.exec_())
