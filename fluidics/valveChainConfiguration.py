#!/usr/bin/python
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui

class ValveChainConfiguration(QtGui.QMainWindow):
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
        self.default_num_valves = 0
        self.default_config = []

        # Initialize file path
        self.setConfigXML(xml_file_path)

        # Parse XML
        self.parseConfigXML()

        # Display configurations
        if self.verbose:
            self.printConfigurations()

    def setConfigXML(self, xml_file_path):
        if xml_file_path == "":
            xml_file_name = QtGui.QFileDialog.getOpenFileName(self, "Open File", path)
        else:
            self.file_name = xml_file_path
            
    def setConfigXML(self, xml_file_path):
        self.file_name = xml_file_path

    def getConfigNames(self):
        return self.config_names

    def getNumConfigs(self):
        return self.num_configs

    def getConfigByName(self, config_name):
        try:
            if config_name == "Default":
                return self.default_config
            else:
                config_ID = self.config_names.index(config_name)
                return self.configs[config_ID]
        except:
            print "Did not find " + config_name
            return []

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

        #
        # Load default settings
        #

        # Confirm 1 and only 1 <default_configurations>
        num_default = len(list(self.config_data.findall("default_configuration")))

        if not num_default == 1:
            print "Incorrect number of <default_configuration> elements"
            return

        # Load default setting
        for settings in self.config_data.findall("default_configuration"):
            self.default_num_valves = len(list(settings.findall("valve_pos")))
            self.default_config = [-1]*self.default_num_valves # initialize port positions
                                                               # for each valve 
            for valve_pos in settings.findall("valve_pos"):
                valve_ID = int(valve_pos.get("valve_ID")) - 1
                port_ID = int(valve_pos.get("port_ID")) - 1
                self.default_config[valve_ID] = port_ID                 

        # Confirm and display default settings
        for valve_ID in range(len(self.default_config)):
            port_ID = self.default_config[valve_ID]
            if port_ID == -1:
                print "Warning missing valve_ID in default configuration"

        # Load different configurations
        self.num_configs = len(list(self.config_data.findall("configuration")))
        if self.verbose:
            print "Loading " + str(self.num_configs) + " configurations"
        
        for config in self.config_data.findall("configuration"):
            self.config_names.append(config.get("name"))
            new_config = self.default_config[:] # make copy to initialize config with default
            for valve_pos in config.findall("valve_pos"):
                valve_ID = int(valve_pos.get("valve_ID")) - 1
                port_ID = int(valve_pos.get("port_ID")) - 1
                if valve_ID < self.default_num_valves:
                    new_config[valve_ID] = port_ID
                else:
                    print "Valve out of range on configuration: " + self.config_names[-1]
            
            self.configs.append(new_config)
        
    def printConfigurations(self):
        print "Default configuration: "
        for valve_ID in range(self.default_num_valves):
            port_ID = self.default_config[valve_ID]
            print ("   " + "Valve " + str(valve_ID+1)
                        + " configured to port " + str(port_ID+1) ) 

        print "General configurations:"
        for config_ID in range(self.num_configs):
            print self.config_names[config_ID]
            for valve_ID in range(self.default_num_valves):
                port_ID = self.configs[config_ID][valve_ID]
                print ("   " + "Valve " + str(valve_ID+1)
                        + " configured to port " + str(port_ID+1) )
    
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    stand_alone = ValveChainConfiguration(verbose = True)
    stand_alone.show()
    sys.exit(app.exec_())
