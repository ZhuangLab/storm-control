#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# pumpControl: A wrapper class for the a generic pump
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffrey.moffitt@childrens.harvard.edu
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import importlib
import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets
import storm_control.sc_library.parameters as params

# ----------------------------------------------------------------------------------------
# Generic PumpControl Class Definition
# ----------------------------------------------------------------------------------------
class GenericPumpControl(QtWidgets.QWidget):
    def __init__(self,
                 parameters = False,
                 parent = None):

        #Initialize parent class
        QtWidgets.QWidget.__init__(self, parent)

        # Define internal attributes
        self.com_port = parameters.get("pump_com_port", "COM8")
        self.pump_ID = parameters.get("pump_id", 30)
        self.simulate = parameters.get("simulate_pump", True)
        self.verbose = parameters.get("verbose", True)
        self.status_repeat_time = parameters.get("status_repeat_time", 2000)
        self.units = None
        self.conv_factor = None

        # Dynamic import of pump class
        pump_module = importlib.import_module(parameters.get("pump_class", "storm_control.fluidics.pumps.hamilton_psd4"))

        # Create Instance of Pump
        self.pump = pump_module.APump(parameters = parameters)

        # Create GUI Elements
        self.createGUI()
        self.pollPumpStatus()
        
        # Define timer for periodic polling of pump status
        self.status_timer = QtCore.QTimer()        
        self.status_timer.setInterval(self.status_repeat_time)
        self.status_timer.timeout.connect(self.pollPumpStatus)
        self.status_timer.start()

    # ------------------------------------------------------------------------------------
    # Close class
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: 
            print("...closing pump")
        self.pump.close()
            
    # ----------------------------------------------------------------------------------------
    # Poll Pump Status
    # ----------------------------------------------------------------------------------------
    def pollPumpStatus(self):
        self.updateStatus(self.pump.getStatus())

    # ------------------------------------------------------------------------------------
    # Change pump based on sent command: [direction, speed]
    # ------------------------------------------------------------------------------------          
    def receiveCommand(self, command):
        pass

    # ------------------------------------------------------------------------------------
    # Determine Enabled State
    # ------------------------------------------------------------------------------------          
    def setEnabled(self, enabled):
        # This control is always enabled to allow emergency control over the flow
        pass
    
    # ------------------------------------------------------------------------------------
    # Initialize the pump
    # ------------------------------------------------------------------------------------          
    def initializePump(self):
        pass

# ----------------------------------------------------------------------------------------
# PumpControl Class Definition
# ----------------------------------------------------------------------------------------
class PeristalticPumpControl(GenericPumpControl):
    def __init__(self,
                 parameters = False,
                 parent = None):

        # Syringe pump specific values
        self.speed_units = parameters.get("speed_units", "rpm")
        #Initialize parent class
        super().__init__(parameters = parameters, parent = parent)

    # ------------------------------------------------------------------------------------
    # Coerce Speed Entry to Acceptable Range
    # ------------------------------------------------------------------------------------
    def coerceSpeed(self):
        current_speed_text = self.speed_control_entry_box.displayText()
        try:
            speed_value = float(current_speed_text)
            if speed_value < 0.01:
                self.speed_control_entry_box.setText("0.01")
            elif speed_value > 48.00:
                self.speed_control_entry_box.setText("48.00")
            else:
                self.speed_control_entry_box.setText("{0:.2f}".format(speed_value))
        except:
            self.speed_control_entry_box.setText("10.00")

    # ------------------------------------------------------------------------------------
    # Create GUI Elements
    # ------------------------------------------------------------------------------------ 
    def createGUI(self):
        # Define main widget
        self.mainWidget = QtWidgets.QGroupBox()
        self.mainWidget.setTitle("Pump Controls")
        self.mainWidgetLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        
        # Add individual widgets
        self.pump_identification_label = QtWidgets.QLabel()
        self.pump_identification_label.setText("No Pump Attached")

        self.flow_status_label= QtWidgets.QLabel()
        self.flow_status_label.setText("Flow Status:")
        self.flow_status_display = QtWidgets.QLabel()
        self.flow_status_display.setText("Unknown")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.flow_status_display.setFont(font)

        self.speed_label = QtWidgets.QLabel()
        self.speed_label.setText("Flow Rate:")
        self.speed_display = QtWidgets.QLabel()
        self.speed_display.setText("Unknown")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.speed_display.setFont(font)

        self.speed_control_label = QtWidgets.QLabel()
        self.speed_control_label.setText("Desired Speed")
        self.speed_control_entry_box = QtWidgets.QLineEdit()
        self.speed_control_entry_box.setText("10.00")
        self.speed_control_entry_box.editingFinished.connect(self.coerceSpeed)
               
        self.direction_control_label = QtWidgets.QLabel()
        self.direction_control_label.setText("Desired Direction")
        self.direction_control = QtWidgets.QComboBox()
        self.direction_control.addItem("Forward")
        self.direction_control.addItem("Reverse")

        self.start_flow_button = QtWidgets.QPushButton()
        self.start_flow_button.setText("Start Flow")
        self.start_flow_button.clicked.connect(self.handleStartFlow)

        self.stop_flow_button = QtWidgets.QPushButton()
        self.stop_flow_button.setText("Stop Flow")
        self.stop_flow_button.clicked.connect(self.handleStopFlow)
        
        self.mainWidgetLayout.addWidget(self.flow_status_display)
        self.mainWidgetLayout.addWidget(self.speed_display)
        self.mainWidgetLayout.addWidget(self.speed_control_label)
        self.mainWidgetLayout.addWidget(self.speed_control_entry_box)
        self.mainWidgetLayout.addWidget(self.direction_control_label)
        self.mainWidgetLayout.addWidget(self.direction_control)
        self.mainWidgetLayout.addWidget(self.start_flow_button)
        self.mainWidgetLayout.addWidget(self.stop_flow_button)
        self.mainWidgetLayout.addStretch(1)
        
        self.menu_names = None
        self.menu_items = None
    # ----------------------------------------------------------------------------------------
    # Display Status
    # ----------------------------------------------------------------------------------------
    def updateStatus(self, status):
        # Pump identification
        self.pump_identification_label.setText(self.pump.identification)
        
        # Flow status
        if status[0] == "Flowing":
            self.flow_status_display.setText(status[2])
            self.flow_status_display.setStyleSheet("QLabel { color: green}")
            self.stop_flow_button.setEnabled(True)
            self.start_flow_button.setText("Change Flow")
        elif status[0] == "Stopped":
            self.flow_status_display.setText(status[0])
            self.flow_status_display.setStyleSheet("QLabel { color: red}")
            self.stop_flow_button.setEnabled(False)
            self.start_flow_button.setText("Start Flow")
        else: # Unknown status
            self.flow_status_display.setText(status[0])
            self.flow_status_display.setStyleSheet("QLabel { color: red}")
            self.stop_flow_button.setEnabled(False)
            self.start_flow_button.setEnabled(False)

        # Speed
        self.speed_display.setText("%0.2f" % status[1] + " " + self.speed_units)
            
    # ----------------------------------------------------------------------------------------
    # Handle Change Flow Request
    # ----------------------------------------------------------------------------------------
    def handleStartFlow(self):
        self.pump.startFlow(float(self.speed_control_entry_box.displayText()),
                            direction = self.direction_control.currentText())
        time.sleep(0.1)
        self.pollPumpStatus()
        
    # ----------------------------------------------------------------------------------------
    # Handle Change Flow Request
    # ----------------------------------------------------------------------------------------
    def handleStopFlow(self):
        self.pump.stopFlow()
        time.sleep(0.1)
        self.pollPumpStatus()

    # ------------------------------------------------------------------------------------
    # Change pump based on sent command: [direction, speed]
    # ------------------------------------------------------------------------------------          
    def receiveCommand(self, command):
        speed = command[1]
        direction = command[0]
        if speed < 0.01:
            self.pump.stopFlow()
        else:
            self.pump.startFlow(speed, direction)

# ----------------------------------------------------------------------------------------
# Syringe PumpControl Class Definition
# ----------------------------------------------------------------------------------------
class SyringePumpControl(GenericPumpControl):
    def __init__(self,
                 parameters = False,
                 parent = None):

        # Initialize syringe specific parameters
        self.volume_units = "mL"
        self.max_speed = parameters.get("max_speed", 100) # mL/min
        self.min_speed = parameters.get("min_speed", 0.05)
        self.max_volume = parameters.get("max_volume", 12.5)
        self.min_volume = parameters.get("min_volume", 0.0)
        self.port_names = parameters.get("port_names", "Pull, Exhaust").split(',')

        #Initialize parent class
        super().__init__(parameters = parameters, parent = parent)

    # ------------------------------------------------------------------------------------
    # Close class
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: 
            print("...closing pump")
        self.pump.close()

    # ------------------------------------------------------------------------------------
    # Coerce Speed Entry to Acceptable Range
    # ------------------------------------------------------------------------------------
    def coerceSpeed(self):
        current_speed_text = self.speed_control_entry_box.displayText()
        try:
            speed_value = float(current_speed_text)
            if speed_value < self.min_speed:
                self.speed_control_entry_box.setText("{0:.2f}".format(self.min_speed))
            elif speed_value > self.max_speed:
                self.speed_control_entry_box.setText("{0:.2f}".format(self.max_speed))
            else:
                self.speed_control_entry_box.setText("{0:.2f}".format(speed_value))
        except:
            print("error in setting speed")
            assert False
    
    # ------------------------------------------------------------------------------------
    # Coerce Volume to Acceptable Range
    # ------------------------------------------------------------------------------------
    def coerceVolume(self):
        current_volume_text = self.fill_control_entry_box.displayText()
        try:
            volume_value = float(current_volume_text)
            if volume_value < self.min_volume:
                self.fill_control_entry_box.setText("{0:.3f}".format(self.min_volume))
            elif volume_value > self.max_volume:
                self.fill_control_entry_box.setText("{0:.3f}".format(self.max_volume))
            else:
                self.fill_control_entry_box.setText("{0:.3f}".format(volume_value))
        except:
            print("error in setting volume")
            assert False

    # ------------------------------------------------------------------------------------
    # Create GUI Elements
    # ------------------------------------------------------------------------------------ 
    def createGUI(self):
        # Define main widget
        self.mainWidget = QtWidgets.QGroupBox()
        self.mainWidget.setTitle("Syringe Pump Controls")
        self.mainWidgetLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        
        # Add individual widgets
        self.pump_identification_label = QtWidgets.QLabel()
        self.pump_identification_label.setText("No Pump Attached")

        # Fill status
        self.fill_status_label= QtWidgets.QLabel()
        self.fill_status_label.setText("Fill Status (" + self.volume_units + ")")
        self.fill_status_display = QtWidgets.QLabel()
        self.fill_status_display.setText("Unknown")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.fill_status_display.setFont(font)

        self.mainWidgetLayout.addWidget(self.fill_status_label)
        self.mainWidgetLayout.addWidget(self.fill_status_display)

        # Speed Status
        self.speed_label = QtWidgets.QLabel()
        self.speed_label.setText("Flow Rate (" + self.volume_units + "/min)")
        self.speed_display = QtWidgets.QLabel()
        self.speed_display.setText("Unknown")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.speed_display.setFont(font)

        self.mainWidgetLayout.addWidget(self.speed_label)
        self.mainWidgetLayout.addWidget(self.speed_display)

        # Port Status
        self.port_label = QtWidgets.QLabel()
        self.port_label.setText("Port Orientation")
        self.port_display = QtWidgets.QLabel()
        self.port_display.setText("Unknown")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.port_display.setFont(font)

        self.mainWidgetLayout.addWidget(self.port_label)
        self.mainWidgetLayout.addWidget(self.port_display)

        # Fill Control
        self.fill_control_label = QtWidgets.QLabel()
        self.fill_control_label.setText("Syringe Fill (" + self.volume_units + ")")
        self.fill_control_entry_box = QtWidgets.QLineEdit()
        self.fill_control_entry_box.setText("0.00")
        self.fill_control_entry_box.editingFinished.connect(self.coerceVolume)

        self.start_fill_button = QtWidgets.QPushButton()
        self.start_fill_button.setText("Update Fill")
        self.start_fill_button.clicked.connect(self.handleStartFill)
        
        self.mainWidgetLayout.addWidget(self.fill_control_label)
        self.mainWidgetLayout.addWidget(self.fill_control_entry_box)
        self.mainWidgetLayout.addWidget(self.start_fill_button)

        # Speed Control
        self.speed_control_label = QtWidgets.QLabel()
        self.speed_control_label.setText("Current Speed (" + self.volume_units + "/min)")
        self.speed_control_entry_box = QtWidgets.QLineEdit()
        self.speed_control_entry_box.setText("1.00")
        self.speed_control_entry_box.editingFinished.connect(self.coerceSpeed)
            
        self.set_speed_button = QtWidgets.QPushButton()
        self.set_speed_button.setText("Update Speed")
        self.set_speed_button.clicked.connect(self.handleUpdateSpeed)

        self.mainWidgetLayout.addWidget(self.speed_control_label)
        self.mainWidgetLayout.addWidget(self.speed_control_entry_box)
        self.mainWidgetLayout.addWidget(self.set_speed_button)

        # Port Control
        self.port_control_label = QtWidgets.QLabel()
        self.port_control_label.setText("Port Configuration")
        self.port_control_combobox = QtWidgets.QComboBox()
        for port_name in self.port_names:
           self.port_control_combobox.addItem(port_name)

        self.change_port_button = QtWidgets.QPushButton()
        self.change_port_button.setText("Update Port")
        self.change_port_button.clicked.connect(self.handleChangePort)
    
        self.mainWidgetLayout.addWidget(self.port_control_label)
        self.mainWidgetLayout.addWidget(self.port_control_combobox)
        self.mainWidgetLayout.addWidget(self.change_port_button)

        # Emergency Stop
        self.stop_fill_button = QtWidgets.QPushButton()
        self.stop_fill_button.setText("Stop Fill")
        self.stop_fill_button.setStyleSheet("QPushButton { color: red}")
        self.stop_fill_button.clicked.connect(self.handleStopFill)
        
        self.mainWidgetLayout.addWidget(self.stop_fill_button)
        
        self.mainWidgetLayout.addStretch(1)
        
        # Define menu items
        self.pump_reset_menu_item = QtWidgets.QAction("Syringe Pump Reset", self)
        self.pump_reset_menu_item.triggered.connect(self.initializePump)

        self.menu_names = ["Pump"]
        self.menu_items = [[self.pump_reset_menu_item]]

        # Create a dialog box for bringing errors to the users attention
        self.warning_dialog = None


    # ----------------------------------------------------------------------------------------
    # Display Status
    # ----------------------------------------------------------------------------------------
    def updateStatus(self, status):
        # Pump identification
        self.pump_identification_label.setText(self.pump.identification)
        
        # Fill volume        
        self.fill_status_display.setText("%0.3f" % status[1])
        
        if status[0]:
            self.fill_status_display.setStyleSheet(("QLabel { color: red}"))
            self.start_fill_button.setEnabled(False)
            self.change_port_button.setEnabled(False)
        else:
            self.fill_status_display.setStyleSheet(("QLabel { color: green}"))
            self.start_fill_button.setEnabled(True)
            self.change_port_button.setEnabled(True)
        
        # Port orientation
        self.port_display.setText(self.port_names[status[3]-1])
        
        # Velocity
        self.speed_display.setText("%0.3f" % status[2])
            
    # ----------------------------------------------------------------------------------------
    # Poll Pump Status
    # ----------------------------------------------------------------------------------------
    def pollPumpStatus(self):
        self.updateStatus(self.pump.getStatus())
    
    # ----------------------------------------------------------------------------------------
    # Handle Change Flow Request
    # ----------------------------------------------------------------------------------------
    def handleChangePort(self):
        # Get the value of the combo box
        port_index = self.port_control_combobox.currentIndex()
        self.pump.setPort(port_index)
        
        # Poll status
        time.sleep(0.5)
        self.pollPumpStatus()
        
    # ----------------------------------------------------------------------------------------
    # Handle Change Flow Request
    # ----------------------------------------------------------------------------------------
    def handleStartFill(self):
        fill_value = float(self.fill_control_entry_box.displayText())
        self.pump.startFill(fill_value)
        
    # ----------------------------------------------------------------------------------------
    # Handle Speed Change Request
    # ----------------------------------------------------------------------------------------
    def handleUpdateSpeed(self):
        speed_value = float(self.speed_control_entry_box.displayText())
        self.pump.setSpeed(speed_value)
        
    # ----------------------------------------------------------------------------------------
    # Handle Change Flow Request
    # ----------------------------------------------------------------------------------------
    def handleStopFill(self):
        self.pump.stopFill()
        time.sleep(0.5)
        self.pollPumpStatus()

    # ------------------------------------------------------------------------------------
    # Change pump based on sent command: [port_name, speed, volume]
    # ------------------------------------------------------------------------------------          
    def receiveCommand(self, command):

        # Confirm the pump is ready for a command
        status = self.pump.getStatus()
        self.updateStatus(status)
        time_out = 10
        elapsed_time = 0
        while status[0]:
            time.sleep(0.5)
            status = self.pump.getStatus()
            self.updateStatus(status)
            elapsed_time = elapsed_time + 0.5
            if elapsed_time >= time_out:
                # Warn the user!!
                warning_message = "Pump command timeout...." + '\n'
                warning_message += "...in executing " + str(command) + '\n'
                warning_message += "...pump was stopped mid-action to protect sample"+ '\n'
                warning_message += "...WARNING: An incorrect volume may have been pulled"

                print(warning_message)
                self.warning_dialog = QtWidgets.QMessageBox()
                self.warning_dialog.setIcon(QtWidgets.QMessageBox.Warning)
                self.warning_dialog.setText(warning_message)
                self.warning_dialog.setWindowTitle("PSD4 Error!")
                self.warning_dialog.show()
                
                # Issue a hard stop to protect sample
                self.handleStopFill()
                break

        # Set the port
        found_port = False
        for port_id, port_name in enumerate(self.port_names):
            if port_name == command[0]:
                self.pump.setPort(port_id)
                found_port=True
        if not found_port:
            print("PSD4 received a bad port request")
            assert False
        
        # Let the port adjust before proceeding
        status = self.pump.getStatus()
        self.updateStatus(status)
        while status[0]:
            time.sleep(0.5)
            status = self.pump.getStatus()
            self.updateStatus(status)
            
        # Set the speed
        if command[1]>=self.min_speed and command[1]<= self.max_speed:
            self.pump.setSpeed(command[1])
        else:
            print("PSD4 received a bad speed request")
            assert False
            
        status = self.pump.getStatus()
        self.updateStatus(status)
        while status[0]:
            time.sleep(0.5)
            status = self.pump.getStatus()
            self.updateStatus(status)
            
        # Set the fill
        if command[2]>=self.min_volume and command[2]<=self.max_volume:
            self.pump.startFill(command[2])
        else:
            print("PSD4 received a bad fill request")
            assert False

    # ------------------------------------------------------------------------------------
    # Determine Enabled State
    # ------------------------------------------------------------------------------------          
    def setEnabled(self, enabled):
        # This control is always enabled to allow emergency control over the flow
        pass

    def initializePump(self):
        self.pump.initializePump()

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.pump = SyringePumpControl()

        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.pump.mainWidget)
        
        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Pump Control")

        # set window geometry
        self.setGeometry(50, 50, 500, 300)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)

    # ------------------------------------------------------------------------------------
    # Detect close event
    # ------------------------------------------------------------------------------------    
    def closeEvent(self, event):
        self.pump.close()
        self.close()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------        
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    app.exec_()
