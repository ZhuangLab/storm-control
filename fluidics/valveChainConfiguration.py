#!/usr/bin/python
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui

class ValveChainConfiguration(QtGui.QMainWindow):

    change_configuration_signal = QtCore.pyqtSignal(int)
    
    def __init__(self,
                 xml_file_path="configuration_default.xml",
                 verbose = False):
        super(ValveChainConfiguration, self).__init__()

        # Initialize internal attributes
        self.num_configurations = 0
        self.verbose = verbose
        self.file_name = xml_file_path
        self.config_names = []
        self.configs = []
        self.num_configs = 0
        self.num_valves = 0

        # Create GUI
        self.createGUI()

        # Load Configurations
        self.loadConfigurations(xml_file_path = self.file_name)

    def loadConfigurations(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        print "Provided file path: " + str(xml_file_path)
        if not xml_file_path:
            xml_file_path = QtGui.QFileDialog.getOpenFileName(self, "Open File", "\home")
        self.file_name = xml_file_path
        
        # Parse XML
        self.parseConfigXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printConfigurations()

        
    def setConfigXML(self, xml_file_path):
        self.file_name = xml_file_path

    def getConfigNames(self):
        return self.config_names

    def getNumberOfValves(self):
        return self.default_num_valves

    def getNumConfigs(self):
        return self.num_configs

    def getConfigByName(self, config_name):
        try:
            config_ID = self.config_names.index(config_name)
            return self.configs[config_ID]
        except:
            print "Did not find " + config_name
            return []

    def getConfigByIndex(self, config_ID):
        try:
            return self.configs[config_ID]
        except:
            print "Invalvid config index: " + config_ID
            return self.configs[0] # return default

    def parseConfigXML(self):
        try:
            self.config_data = elementTree.parse(self.file_name)
            self.config_data.getroot()
            self.valve_configs = self.config_data.getroot()
        except:
            print "Valid xml file not loaded"
            return
        else:
            print "Loaded: " + self.file_name

        # Clear previous configurations
        self.config_names = []
        self.configs = []
        self.num_configs = 0
        self.num_valves = 0

        # Confirm 1 and only 1 <default_configurations>
        num_default = len(list(self.config_data.findall("default_configuration")))

        if not num_default == 1:
            print "Incorrect number of <default_configuration> elements"
            return

        # Load default setting
        for settings in self.config_data.findall("default_configuration"):
            self.num_valves = len(list(settings.findall("valve_pos")))
            temp_config = [-1]*self.num_valves              # initialize port positions
            for valve_pos in settings.findall("valve_pos"):
                valve_ID = int(valve_pos.get("valve_ID")) - 1
                port_ID = int(valve_pos.get("port_ID")) - 1
                temp_config[valve_ID] = port_ID
        # Confirm and display default settings
        for valve_ID in range(len(temp_config)):
            port_ID = temp_config[valve_ID]
            if port_ID == -1:
                print "Warning missing valve_ID in default configuration"

        # Add Default Configuration (the first)
        self.configs.append(temp_config)
        self.config_names.append("Default")
        
        # Load different configurations
        num_custom_configs = len(list(self.config_data.findall("configuration")))
        if self.verbose:
            print "Loading " + str(num_custom_configs) + " configurations"
        
        for config in self.config_data.findall("configuration"):
            new_config = self.configs[0][:] # make copy to initialize config with default
            print new_config
            for valve_pos in config.findall("valve_pos"):
                valve_ID = int(valve_pos.get("valve_ID")) - 1
                port_ID = int(valve_pos.get("port_ID")) - 1
                print config.get("name"), valve_ID, port_ID
                if valve_ID < self.num_valves:
                    new_config[valve_ID] = port_ID
                else:
                    print "Valve out of range on configuration: " + config.get("name")
            # Add custom config
            self.configs.append(new_config)
            self.config_names.append(config.get("name"))

        # Record number of configs
        self.num_configs = len(self.config_names)
        
    def printConfigurations(self):
        print "Current  configurations:"
        for config_ID in range(self.num_configs):
            print self.config_names[config_ID]
            for valve_ID in range(self.num_valves):
                port_ID = self.configs[config_ID][valve_ID]
                print ("   " + "Valve " + str(valve_ID+1)
                       + " configured to port " + str(port_ID+1) )

    def createGUI(self):
        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setTitle("Valve Configurations")
        self.groupBoxLayout = QtGui.QVBoxLayout(self.groupBox)

        self.fileLabel = QtGui.QLabel()
        self.fileLabel.setText("")

        self.configListWidget = QtGui.QListWidget()
        self.configListWidget.currentItemChanged.connect(self.updateConfigurationDisplay)
        
        self.sendConfigurationButton = QtGui.QPushButton("Set Configuration")
        self.sendConfigurationButton.clicked.connect(self.transmitConfigIndex)

        self.currentConfigGroupBox = QtGui.QGroupBox()
        self.currentConfigGroupBox.setTitle("Current Configuration")
        self.currentConfigGroupBoxLayout = QtGui.QVBoxLayout(self.currentConfigGroupBox)

        self.currentConfigLabel = QtGui.QLabel()
        self.currentConfigLabel.setText("")
        self.currentConfigGroupBoxLayout.addWidget(self.currentConfigLabel)

        self.groupBoxLayout.addWidget(self.fileLabel)
        self.groupBoxLayout.addWidget(self.configListWidget)
        self.groupBoxLayout.addWidget(self.sendConfigurationButton)
        self.groupBoxLayout.addWidget(self.currentConfigGroupBox)

        self.groupBoxLayout.addStretch(1)

        # Menu items (may not be used)
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)

        self.load_config_action = QtGui.QAction("Load configuration", self)
        self.load_config_action.setShortcut("Ctrl+O")
        self.load_config_action.triggered.connect(self.loadConfigurations)
        self.load_config_action_menu_name = "File"
        
    def updateGUI(self):
        self.configListWidget.clear() # Remove previous items
        for name in self.config_names:
            self.configListWidget.addItem(name)

        if len(self.config_names) > 0:
            self.configListWidget.setCurrentRow(0) # Set to default
        self.fileLabel.setText(self.file_name)

    def updateConfigurationDisplay(self):
        current_ID = self.configListWidget.currentRow()
        current_config_name = self.config_names[current_ID]
        current_config = self.configs[current_ID]

        text_string = current_config_name + "\n"
        for valve_ID, port_ID in enumerate(current_config):
            text_string += "Valve " + str(valve_ID+1)
            text_string += ": Port " + str(port_ID+1)
            text_string += "\n"

        self.currentConfigLabel.setText(text_string)

    def transmitConfigIndex(self):
        current_ID = self.configListWidget.currentRow()
        self.change_configuration_signal.emit(current_ID)
        if self.verbose:
            print "Emit: " + str(current_ID) + " " + self.config_names[current_ID]

class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valve_chain_config = ValveChainConfiguration(verbose = True)
        
        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.valve_chain_config.groupBox)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Chain Configuration")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)
        file_menu.addAction(self.valve_chain_config.load_config_action)

    def closeEvent(self, event):
        self.valve_chain_config.close()
        self.close()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())
