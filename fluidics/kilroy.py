#!/usr/bin/python
import sys
import os
import time
from PyQt4 import QtCore, QtGui
from valveChain import ValveChain
from valveProtocols import ValveProtocols

class Kilroy(QtGui.QMainWindow):
    
    def __init__(self, verbose = False):
        super(Kilroy, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose

        # Create Valve Chain
        self.valveChain = ValveChain(COM_port = 2,
                                         verbose = self.verbose,
                                         num_simulated_valves = 2)

        self.valveProtocols = ValveProtocols(verbose = self.verbose)

        # Connect command ready signal
        self.valveProtocols.command_ready_signal.connect(self.sendCommand)

        # Create GUI
        self.createGUI()

    def createGUI(self):
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addWidget(self.valveProtocols.mainWidget, 0, 0, 1, 3)
        self.mainLayout.addWidget(self.valveProtocols.valveCommands.mainWidget, 2, 0, 1, 3) 
        self.mainLayout.addWidget(self.valveChain.mainWidget, 0, 4, 1, 1)

    def sendCommand(self):
        command = self.valveProtocols.getCurrentCommand()
        self.valveChain.receiveCommand(command)
    
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

        # Create file menu
##        menubar = self.menuBar()
##        file_menu = menubar.addMenu("File")
##
##        exit_action = QtGui.QAction("Exit", self)
##        exit_action.setShortcut("Ctrl+Q")
##        exit_action.triggered.connect(self.closeEvent)
##
##        file_menu.addAction(exit_action)
##        file_menu.addAction(self.valve_chain_commands.load_commands_action)

##    def closeEvent(self, event):
##        self.valve_chain_commands.close()
##        self.close()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

     # Splash Screen.

    splash_pix = QtGui.QPixmap("kilroy_splash.jpg")
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    
    time.sleep(2)
    
    app.setWindowIcon(QtGui.QIcon('kilroy.jpg'))
    window = StandAlone()
    window.setWindowIcon(QtGui.QIcon('kilroy.jpg'))

    splash.hide()
    window.show()
    sys.exit(app.exec_())
