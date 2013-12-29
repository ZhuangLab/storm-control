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

# ----------------------------------------------------------------------------------------
# Kilroy Class Definition
# ----------------------------------------------------------------------------------------
class Kilroy(QtGui.QMainWindow):
    def __init__(self, verbose = False):
        super(Kilroy, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose

        # Create ValveChain instance
        self.valveChain = ValveChain(COM_port = 2,
                                     num_simulated_valves = 2,
                                     verbose = self.verbose)

        # Create ValveChain instance
        self.valveProtocols = ValveProtocols(verbose = self.verbose)

        # Connect command ready signal
        self.valveProtocols.command_ready_signal.connect(self.sendCommand)

        # Connect protocol status change signal
        self.valveProtocols.status_change_signal.connect(self.handleProtocolStatus)

        # Create GUI
        self.createGUI()

    # ----------------------------------------------------------------------------------------
    # Create master GUI
    # ----------------------------------------------------------------------------------------
    def createGUI(self):
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addWidget(self.valveProtocols.mainWidget, 0, 0, 1, 3)
        self.mainLayout.addWidget(self.valveProtocols.valveCommands.mainWidget, 2, 0, 1, 3) 
        self.mainLayout.addWidget(self.valveChain.mainWidget, 0, 4, 1, 1)

    # ----------------------------------------------------------------------------------------
    # Redirect protocol status change from valveProtocols to valveChain
    # ----------------------------------------------------------------------------------------
    def handleProtocolStatus(self):
        status = self.valveProtocols.getStatus()
        if status[0] > 0: # Protocol is running
            self.valveChain.setEnabled(False)
        else:
            self.valveChain.setEnabled(True)
        print "Protocol Status Change: " + str(status)
        
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
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.kilroy = Kilroy(verbose = True)
                                          
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
    time.sleep(2) # Define minimum startup time

    # Create instance of StandAlone class
    window = StandAlone()

    # Remove splash screen
    splash.hide()

    # Run main app
    window.show()
    sys.exit(app.exec_())
