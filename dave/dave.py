#!/usr/bin/python
#
## @file
#
# Utility for running scripting files for remote control of the HAL-4000 data taking program.
# The concept is that for each movie that we want to take we create a list of actions that
# we iterate through. Actions are things like finding sum, recentering the z piezo and taking
# a movie. Actions can have a delay time associated with them as well as a requirement that
# a response is recieved from the acquisition software.
#
# Hazen 06/13
#

# Common
import os
import sys
import traceback
import datetime
import time

# XML parsing
from xml.dom import minidom, Node 

# PyQt
from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# General
import notifications
import sequenceParser
from xml_generators import xml_generator, recipeParser

# Communication
import sc_library.tcpClient as tcpClient

# UI
import qtdesigner.dave_ui as daveUi

# Dave actions
import daveActions

# Parameter loading
import sc_library.parameters as params

## createTableWidget
#
# Creates a PyQt table widget item with our default flags.
#
# @param text The text to use for the item.
#
# @return A QTableWidgetItem.
#
def createTableWidget(text):
    widget = QtGui.QTableWidgetItem(text)
    widget.setFlags(QtCore.Qt.ItemIsEnabled)
    return widget

## CommandEngine
#
# This class handles the execution of commands that can be given to Dave
#
class CommandEngine(QtGui.QWidget):
    done = QtCore.pyqtSignal()
    idle = QtCore.pyqtSignal(bool)
    problem = QtCore.pyqtSignal(object)
    
    ## __init__
    #
    #
    @hdebug.debug
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        # Set defaults
        self.actions = []
        self.current_action = None
        self.command = None
        self.should_pause = False
        self.command_duration = []
        self.command_disk_usage = []
        
        self.test_mode = False
        
        # HAL Client
        self.HALClient = tcpClient.TCPClient(port = 9000, server_name = "HAL")
        
        # Kilroy Client
        self.kilroyClient = tcpClient.TCPClient(port = 9500, server_name = "Kilroy")
    
    ## abort
    #
    # Aborts the current action (if any).
    #
    @hdebug.debug
    def abort(self):
        self.actions = []
        if self.current_action:
            self.current_action.abort()

    ## loadCommand
    #
    # Decompose a dave command into the necessary actions and run them
    #
    # @param command A XML command object from sequenceParser
    #
    @hdebug.debug
    def loadCommand(self, command):
        # Re-Initialize state of command_engine
        self.actions = []
        self.current_action = None
        self.command = command
        self.should_pause = False

        # Load and parse command 
        command_type = command.getType()
        if command_type == "movie":
            if hasattr(command, "stage_x") and hasattr(command, "stage_y"):
                self.actions.append(daveActions.MoveStage(self.HALClient, command))
            if hasattr(command, "lock_target"):
                self.actions.append(daveActions.SetFocusLockTarget(self.HALClient, command.lock_target))
            if command.find_sum > 0.0:
                self.actions.append(daveActions.FindSum(self.HALClient, command.find_sum))
            if command.recenter:
                self.actions.append(daveActions.RecenterPiezo(self.HALClient))
            if hasattr(command,"progression"):
                if command.progression:
                    self.actions.append(daveActions.SetProgression(self.HALClient, command.progression))
            if hasattr(command, "parameters"):
                self.actions.append(daveActions.SetParameters(self.HALClient, command))
            if hasattr(command, "delay") and (command.delay > 0):
                self.actions.append(daveActions.DaveDelay(command.delay))
            if hasattr(command, "directory"):
                self.actions.append(daveActions.SetDirectory(self.HALClient, command.directory))
            if command.length > 0:
                self.actions.append(daveActions.TakeMovie(self.HALClient, command))
        elif command_type == "fluidics":
            self.actions.append(daveActions.DaveActionValveProtocol(self.kilroyClient, command))

        # If in test mode, configure actions as test
        if self.test_mode:
            for action in self.actions:
                action.message.setTestMode(True)  

    ## getPause
    #
    # Returns the current pause request state of the command engine
    #
    def getPause(self):
        if self.test_mode: return False
        else: return self.should_pause
    
    ## startCommand
    #
    # Start a command or command sequence
    # 
    def startCommand(self):
        if not self.should_pause and len(self.actions) > 0:
            # Extract next action from list
            self.current_action = self.actions.pop(0)

            # Disconnect previous signals and connect new ones
            self.current_action.complete_signal.connect(self.handleActionComplete)
            self.current_action.error_signal.connect(self.handleErrorSignal)

            # Reset command duration and disk usage
            self.command_duration = 0.0
            self.command_disk_usage = 0.0
            # Start current action
            self.current_action.start()

    ## enableTestMode
    #
    # Toggle the command engine test mode
    # 
    def enableTestMode(self, mode_boolean):
        self.test_mode = mode_boolean

    ## handleActionComplete
    #
    # Handle the completion of the previous action
    #
    def handleActionComplete(self, message):
        self.current_action.cleanUp()
        self.current_action.complete_signal.disconnect()
        self.current_action.error_signal.disconnect()
        
        if self.test_mode:
            time = message.getResponse("duration")
            if time is not None: self.command_duration += time
            space = message.getResponse("disk_usage")
            if space is not None: self.command_disk_usage += space

        # Configure the command engine to pause after completion of the command sequence
        if self.current_action.shouldPause() and not self.test_mode:
            self.should_pause = True
        
        if len(self.actions) > 0:
            self.startCommand()
        else:
            self.done.emit()
        
    ## handleErrorSignal
    #
    # Handle an error signal
    #
    def handleErrorSignal(self, message):
        self.problem.emit(message)
        self.handleActionComplete(message)

## Dave Main Window Function
#
# The main window
#
class Dave(QtGui.QMainWindow):

    ## __init__
    #
    # Creates the window and the UI. Connects the signals. Creates the movie engine.
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        
        # General.
        self.directory = ""
        self.parameters = parameters
        self.command_index = 0
        self.commands = []
        self.disk_usages = []
        self.command_durations = []
        self.is_command_valid = []
        self.notifier = notifications.Notifier("", "", "", "")
        self.running = False
        self.settings = QtCore.QSettings("Zhuang Lab", "dave")
        self.sequence_filename = ""
        self.sequence_validated = False
        self.test_mode = False
        self.skip_warning = False
        self.needs_hal = False
        self.needs_kilroy = False
        
        self.createGUI()

        # Movie engine.
        self.command_engine = CommandEngine()
        self.command_engine.done.connect(self.handleDone)
        self.command_engine.problem.connect(self.handleProblem)

        self.updateGUI()

    ## cleanUp
    #
    # Saves (most of) the notification settings at program exit.
    #
    @hdebug.debug
    def cleanUp(self):
        # Save notification settings.
        for [object, name] in self.noti_settings:
            self.settings.setValue(name, object.text())

    ## closeEvent
    #
    # Handles the PyQt close event.
    #
    # @param event A PyQt close event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    ## createCommandList
    #
    # create the command list
    #
    @hdebug.debug
    def createCommandList(self):
        self.ui.commandSequenceList.clear()
        self.command_widgets = []
        
        for [command_ID, command] in enumerate(self.commands):
            widget = QtGui.QListWidgetItem(command.getDescriptor())
            
            widget.setFlags(QtCore.Qt.ItemIsEnabled)
            if self.is_command_valid[command_ID]:
                widget.setBackground(QtGui.QBrush(QtCore.Qt.white))
            else:
                widget.setBackground(QtGui.QBrush(QtCore.Qt.red))
            self.ui.commandSequenceList.addItem(widget)
            self.command_widgets.append(widget)
        
        if len(self.commands) > 0:
            self.command_widgets[0].setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.commandSequenceList.setCurrentRow(0)

        self.updateCommandDescriptorTable(self.command_widgets[0])

        self.ui.progressBar.setMaximum(len(self.commands))

    ## createGUI
    #
    # Creates the GUI elements
    #
    @hdebug.debug
    def createGUI(self):
        # UI setup.
        self.ui = daveUi.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.spaceLabel.setText("")
        self.ui.timeLabel.setText("")

        # Hide widgets
        self.ui.frequencyLabel.hide()
        self.ui.frequencySpinBox.hide()
        self.ui.statusMsgCheckBox.hide()

        # Set icon.
        self.setWindowIcon(QtGui.QIcon("dave.ico"))

        # This is for handling file drops.
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # Connect UI signals.
        self.ui.abortButton.clicked.connect(self.handleAbortButton)
        self.ui.actionNew_Sequence.triggered.connect(self.newSequenceFile)
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionGenerateXML.triggered.connect(self.handleGenerateXML)
        self.ui.actionSendTestEmail.triggered.connect(self.handleSendTestEmail)
        self.ui.fromAddressLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.fromPasswordLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.runButton.clicked.connect(self.handleRunButton)
        self.ui.selectCommandButton.clicked.connect(self.handleSelectButton)
        self.ui.smtpServerLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.toAddressLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.validateSequenceButton.clicked.connect(self.validateCommandSequence)
                                              
        # Load saved notifications settings.
        self.noti_settings = [[self.ui.fromAddressLineEdit, "from_address"],
                              [self.ui.fromPasswordLineEdit, "from_password"],
                              [self.ui.smtpServerLineEdit, "smtp_server"]]

        for [object, name] in self.noti_settings:
            object.setText(self.settings.value(name, "").toString())

        # Initialize command descriptor table
        self.command_details_table_size = [12, 2]
        self.ui.commandDetailsTable.setRowCount(self.command_details_table_size[0])
        self.ui.commandDetailsTable.setColumnCount(self.command_details_table_size[1])

        # Initialize command widgets
        self.command_widgets = []

        # Set enabled/disabled status
        self.ui.runButton.setEnabled(False)
        self.ui.abortButton.setEnabled(False)
        self.ui.selectCommandButton.setEnabled(False)
        self.ui.validateSequenceButton.setEnabled(False)
        
        # Enable mouse over updates of command descriptor
        self.ui.commandSequenceList.clicked.connect(self.handleCommandListClick)

        # Initialize progress bar
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(1)

    ## dragEnterEvent
    #
    # Handles a PyQt (file) drag enter event.
    #
    # @param event A PyQt drag enter event.
    #
    @hdebug.debug
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    ## dropEvent
    #
    # Handles a PyQt (file) drop event.
    #
    # @param event A PyQt drop event.
    #
    @hdebug.debug
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.handleDragDropFile(str(url.encodedPath())[1:])

    ## handleAbortButton
    #
    # Tells the movie engine to abort the current movie. Resets everything to the initial movie.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleAbortButton(self, boolean):
        if not self.test_mode:
            # Force manual conformation of abort
            messageBox = QtGui.QMessageBox(parent = self)
            messageBox.setWindowTitle("Abort?")
            messageBox.setText("Are you sure you want to abort the current run?")
            messageBox.setStandardButtons(QtGui.QMessageBox.Cancel |
                                          QtGui.QMessageBox.Ok)
            messageBox.setDefaultButton(QtGui.QMessageBox.Cancel)
            button_ID = messageBox.exec_()

            # Handle response
            if button_ID == QtGui.QMessageBox.Ok:
                abort_text =  "Aborted current run at command " + str(self.command_index)
                abort_text += ": " + str(self.commands[self.command_index].getDetails()[1][1])
                print abort_text
                if (self.running):
                    #Set flag to signal reset to handleDone when called
                    self.command_index = len(self.commands) + 1
                    self.command_engine.abort()
                else: # Paused
                    self.command_index = len(self.commands) + 1
                    self.handleDone()
            else: # Cancel button or window closed event
                pass
        else:
            self.command_index = len(self.commands) + 1
            self.sequence_validated = False
    
    ## handleCommandListClick
    #
    # Reset command sequence list to the current command
    #
    #
    def handleCommandListClick(self):
        self.updateCommandSequenceDisplay(self.ui.commandSequenceList.currentRow())

    ## 
    #
    # Handles completion of the current command engine.  
    #
    @hdebug.debug
    def handleDone(self):
        if self.test_mode and (self.command_index <= (len(self.commands)-1)) and self.is_command_valid[self.command_index]:
            self.disk_usages[self.command_index] = self.command_engine.command_disk_usage
            self.command_durations[self.command_index] = self.command_engine.command_duration

        # Increment command to the next valid command
        self.command_index += 1
        while (self.command_index <= (len(self.commands)-1)) and (not self.is_command_valid[self.command_index]):
            self.command_index += 1
            
        # Handle last command in list
        if self.command_index >= len(self.commands):
            self.command_index = 0
            self.ui.runButton.setText("Start")
            self.ui.runButton.setEnabled(True)
            self.ui.abortButton.setEnabled(False)
            self.ui.selectCommandButton.setEnabled(True)
            self.ui.validateSequenceButton.setEnabled(True)
            
            self.running = False
            self.command_engine.enableTestMode(False) # To complete a validation run
            if self.test_mode:
                self.sequence_validated = True
                self.updateEstimates()
                self.createCommandList() # Redraw list to color invalid commands
                self.test_mode = False

            # Stop TCP communication
            if self.needs_hal:
                self.command_engine.HALClient.stopCommunication()
            if self.needs_kilroy:
                self.command_engine.kilroyClient.stopCommunication()
        
        # Issue the command
        self.issueCommand()

        # Check whether to proceed with the next command or pause
        if self.command_engine.getPause():
            self.running = False
        if self.running: #Proceed to next command
            self.command_engine.startCommand()
        else: # Handle pause state (not running with an intermediate command_index)
            if self.command_index > 0 and self.command_index < len(self.commands):
                self.ui.runButton.setText("Restart")
                self.ui.runButton.setEnabled(True)
                self.ui.selectCommandButton.setEnabled(True)
                print "\7\7" # Provide audible acknowledgement of pause

    ## handleDropXML
    #
    # Handles a drop event containing a url to an xml file
    #
    # @param file_path Path to file dragged into Dave.
    #
    def handleDragDropFile(self, file_path):
        if self.running:
            QtGui.QMessageBox.information(self,
                                          "New Sequence Request",
                                          "Please pause or abort current")
        else:
            recipe_parser = recipeParser.XMLRecipeParser(verbose = True)
            (xml, xml_file_path) = recipe_parser.loadXML(file_path)
            root = xml.getroot()
            if root.tag == "recipe" or root.tag == "experiment":
                output_filename = recipe_parser.parseXML(xml_file_path)
                if os.path.isfile(output_filename):
                    self.newSequence(output_filename)
            elif root.tag == "sequence":
                self.newSequence(xml_file_path)
        
    ## handleGenerateXML
    #
    # Handles Generate from Recipe XML
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleGenerateXML(self, boolean):
        if self.running:
            QtGui.QMessageBox.information(self,
                                          "New Sequence Request",
                                          "Please pause or abort current")
        else:
            recipe_parser = recipeParser.XMLRecipeParser(verbose = True)
            output_filename = recipe_parser.parseXML()
            if os.path.isfile(output_filename):
                self.newSequence(output_filename)
            
    ## handleNotifierChange
    #
    # Handles changes to any of the notification fields of the UI.
    #
    # @param some_text This is a dummy variable that gets the text from the PyQt textChanged signal.
    #
    @hdebug.debug
    def handleNotifierChange(self, some_text):
        self.notifier.setFields(self.ui.smtpServerLineEdit.text(),
                                self.ui.fromAddressLineEdit.text(),
                                self.ui.fromPasswordLineEdit.text(),
                                self.ui.toAddressLineEdit.text())

    ## handleProblem
    #
    # Handles the problem signal from the movie engine. Notifies the operator by e-mail if requested.
    # Displays a dialog box describing the problem.
    #
    # @param message The problem message from the movie engine.
    #
    @hdebug.debug
    def handleProblem(self, message):
        current_command_name = str(self.commands[self.command_index].getDetails()[1][1])
        message_str = current_command_name + "\n" + message.getErrorMessage()
        if not self.test_mode:
            self.ui.runButton.setText("Restart")
            self.running = False
            if (self.ui.errorMsgCheckBox.isChecked()):
                self.notifier.sendMessage("Acquisition Problem",
                                          message_str)
            QtGui.QMessageBox.information(self,
                                          "Acquisition Problem",
                                          message_str)

            # Stop TCP communication
            if self.needs_hal:
                self.command_engine.HALClient.stopCommunication()
            if self.needs_kilroy:
                self.command_engine.kilroyClient.stopCommunication()
            
        else: # Test mode
            self.is_command_valid[self.command_index] = False
            message_str += "\nSuppress remaining warnings?"
            if not self.skip_warning:
                messageBox = QtGui.QMessageBox(parent = self)
                messageBox.setWindowTitle("Invalid Command")
                messageBox.setText(message_str)
                messageBox.setStandardButtons(QtGui.QMessageBox.No |
                                              QtGui.QMessageBox.YesToAll)
                messageBox.setIcon(QtGui.QMessageBox.Warning)
                messageBox.setDefaultButton(QtGui.QMessageBox.YesToAll)
                button_ID = messageBox.exec_()
                if button_ID == QtGui.QMessageBox.YesToAll:
                    self.skip_warning = True # Skip additional warnings

            print "Invalid command: " + current_command_name

    ## handleRunButton
    #
    # Handles the run button. If we are running then the text is set to "Pausing.." and the movie engine is told to pause.
    # Otherwise the text is set to "Pause" and the movie engine is told to start.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleRunButton(self, boolean):
        if (self.running): # Pause
            self.ui.runButton.setText("Pausing..")
            self.ui.runButton.setEnabled(False) #Inactivate button until current action is complete
            self.running = False
        else: # Start
            if not all(self.is_command_valid): # Confirm run in the presence of invalid commands
                messageBox = QtGui.QMessageBox(parent = self)
                messageBox.setWindowTitle("Invalid Commands")
                box_text = "There are invalid commands. Are you sure you want to start?\n"
                box_text += "Invalid commands will be skipped."
                messageBox.setText(box_text)
                messageBox.setStandardButtons(QtGui.QMessageBox.No |
                                              QtGui.QMessageBox.Yes)
                messageBox.setDefaultButton(QtGui.QMessageBox.No)
                button_ID = messageBox.exec_()
                if not (button_ID == QtGui.QMessageBox.Yes):
                    return
            if not self.sequence_validated:
                messageBox = QtGui.QMessageBox(parent = self)
                messageBox.setWindowTitle("Unvalidated Sequence")
                box_text = "The current sequence has not been validated. Are you sure you want to start?\n"
                messageBox.setText(box_text)
                messageBox.setStandardButtons(QtGui.QMessageBox.No |
                                              QtGui.QMessageBox.Yes)
                messageBox.setDefaultButton(QtGui.QMessageBox.No)
                button_ID = messageBox.exec_()
                if not (button_ID == QtGui.QMessageBox.Yes):
                    return

            # Start TCP communication
            if self.needs_hal:
                self.command_engine.HALClient.startCommunication()
            if self.needs_kilroy:
                self.command_engine.kilroyClient.startCommunication()
            
            self.ui.runButton.setText("Pause")
            self.ui.abortButton.setEnabled(True)
            self.ui.selectCommandButton.setEnabled(False)
            self.ui.validateSequenceButton.setEnabled(False)
            self.running = True
            self.issueCommand()
            self.command_engine.startCommand()

    ## handleSelectButton
    #
    # Handles the select command button. Used to set the current command to the selected command. 
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSelectButton(self, boolean):
        # Force manual conformation of abort
        messageBox = QtGui.QMessageBox(parent = self)
        messageBox.setWindowTitle("Change Command?")
        messageBox.setText("Are you sure you want to change to the current command?")
        messageBox.setStandardButtons(QtGui.QMessageBox.Cancel |
                                      QtGui.QMessageBox.Ok)
        messageBox.setDefaultButton(QtGui.QMessageBox.Cancel)
        button_ID = messageBox.exec_()

        old_command_index = self.command_index
        new_command_index = self.ui.commandSequenceList.currentRow()

        # Handle response
        if button_ID == QtGui.QMessageBox.Ok:
            # Generate display text
            display_text =  "Changed command\n"
            display_text += "   From command " + str(old_command_index) + ": "
            display_text += str(self.commands[old_command_index].getDetails()[1][1])
            display_text += "   To command " + str(new_command_index) + ": "
            display_text += str(self.commands[new_command_index].getDetails()[1][1])
            print display_text
            
            self.command_index = new_command_index

            self.issueCommand()

        else: # Cancel button or window closed event
            print "Canceled change command request"

    ## handleSendTestEmail
    #
    # Sends a test email based on the current notifier settings. 
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleSendTestEmail(self, boolean):
        self.notifier.sendMessage("Notifier Test", "Open the pod bay doors, HAL")

    ## issueCommand
    #
    #  Send current command to command engine and update GUI
    #
    def issueCommand(self):
        self.updateCommandSequenceDisplay(self.command_index)
        self.updateCurrentCommandDisplay(self.command_index)
        self.ui.progressBar.setValue(self.command_index)
        self.command_engine.loadCommand(self.commands[self.command_index])
        
    ## newSequence
    #
    # Parses a XML file describing the list of movies to take.
    #
    # @param sequence_filename The name of the XML file.
    #
    @hdebug.debug
    def newSequence(self, sequence_filename):
        if self.running:
            QtGui.QMessageBox.information(self,
                                          "New Sequence Request",
                                          "Please pause or abort current run")
        if not self.running:
            commands = []
            try:
                commands = sequenceParser.parseMovieXml(sequence_filename)
            except:
                QtGui.QMessageBox.information(self,
                                              "XML Generation Error",
                                              traceback.format_exc())
            else:
                self.skip_warning = False #Enable warnings for invalid commands
                self.sequence_validated = False #Mark sequence as unvalidated
                self.commands = commands
                self.command_index = 0
                self.sequence_length = len(self.commands)
                self.sequence_filename = sequence_filename
                self.updateGUI()
                self.disk_usages = [0.0] * len(self.commands)
                self.command_durations = [0.0] * len(self.commands)
                self.is_command_valid = [True] * len(self.commands)
                
                # Set enabled/disabled status
                self.ui.runButton.setEnabled(True)
                self.ui.runButton.setText("Start")
                self.ui.abortButton.setEnabled(False)
                self.ui.selectCommandButton.setEnabled(False)
                self.ui.validateSequenceButton.setEnabled(True)
                
                self.createCommandList()
                self.issueCommand()
                
    ## newSequenceFile
    #
    # Opens the dialog box that lets the user specify a sequence file.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def newSequenceFile(self, boolean):
        if self.running:
            QtGui.QMessageBox.information(self,
                                          "New Sequence Request",
                                          "Please pause or abort current")
        else:
            sequence_filename = str(QtGui.QFileDialog.getOpenFileName(self, "New Sequence", self.directory, "*.xml"))
            if sequence_filename:
                self.directory = os.path.dirname(sequence_filename)
                self.newSequence(sequence_filename)

    ## updateCommandSequenceDisplay
    #
    #  Update the GUI display of the current command deails
    #
    def updateCommandSequenceDisplay(self, command_index):
        # disable selectability of all other elements
        for widget in self.command_widgets:
            widget.setFlags(QtCore.Qt.ItemIsEnabled)
            
        self.command_widgets[command_index].setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.ui.commandSequenceList.setCurrentRow(command_index)
        self.updateCommandDescriptorTable(self.command_widgets[command_index])

    ## updateCurrentCommandDisplay
    #
    #  Update the GUI display of the current command details
    #
    def updateCurrentCommandDisplay(self, command_index):
        command_details = self.commands[command_index].getDetails()
        display_text = str(command_index + 1) + ": "
        display_text += str(command_details[1][1])
        self.ui.currentCommand.setText(display_text)

    ## updateGUI
    #
    # Update the GUI elements
    #
    @hdebug.debug
    def updateGUI(self):
        # Current sequence xml file
        self.ui.sequenceLabel.setText(self.sequence_filename)

    ## updateEstimates
    #
    # Update disk and duration estimates
    #
    @hdebug.debug
    def updateEstimates(self):
        est_time = 0.0
        est_space = 0.0
        for i in range(len(self.commands)):
            est_time += self.command_durations[i]
            est_space += self.disk_usages[i]
            
        self.ui.timeLabel.setText("Run Duration: " + str(datetime.timedelta(seconds=est_time))[0:8])
        if est_space/2**10 < 1.0: # Less than GB
            self.ui.spaceLabel.setText("Run Size: {0:.2f} MB ".format(est_space))
        elif est_space/2**20 < 1.0: # Less than TB
            self.ui.spaceLabel.setText("Run Size: {0:.2f} GB ".format(est_space/2**10))
        else: # Bigger than 1 TB
            self.ui.spaceLabel.setText("Run Size: {0:.2f} TB ".format(est_space/2**20))
        
    ## updateCommandDescriptorTable
    #
    # Display the details of the current command
    #
    @hdebug.debug
    def updateCommandDescriptorTable(self, list_widget):
        # Find widget
        command_index = self.command_widgets.index(list_widget)
        current_command = self.commands[command_index]

        command_details = current_command.getDetails()

        self.ui.commandDetailsTable.clear()
        
        for [line_num, line] in enumerate(command_details):
            for [entry_pos, entry] in enumerate(line):
                self.ui.commandDetailsTable.setItem(line_num, entry_pos, createTableWidget(entry))

    ## validateTCP
    #
    # Determine that the required TCP communications are ready
    #
    # @return tcp_ready A boolean describing the state of TCP communications
    def validateTCP(self):
        self.needs_hal = False
        self.needs_kilroy = False
        for command in self.commands:
            if command.getType() == "movie":
                self.needs_hal = True
            elif command.getType() == "fluidics":
                self.needs_kilroy = True

        tcp_ready = True
        # Poll tcp status
        if self.needs_hal:
            if not self.command_engine.HALClient.startCommunication():
                tcp_ready = False
                err_message = "This sequence requires communication with Hal.\n"
                err_message += "Please start Hal!"
                QtGui.QMessageBox.information(self,
                                              "TCP Communication Error",
                                              err_message)
        if self.needs_kilroy:
            if not self.command_engine.kilroyClient.startCommunication():
                tcp_ready = False
                err_message = "This sequence requires communication with Kilroy.\n"
                err_message += "Please start Kilroy!"
                QtGui.QMessageBox.information(self,
                                              "TCP Communication Error",
                                             err_message)
        return tcp_ready

    ## validateCommandSequence
    #
    # Start the validation process for a command sequence
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def validateCommandSequence(self, boolean):
        tcp_ready = self.validateTCP()   
        if tcp_ready: # Start Test Run
            # Configure UI
            self.running = True
            self.test_mode = True
            self.ui.runButton.setEnabled(False)
            self.ui.abortButton.setEnabled(True)
            self.ui.selectCommandButton.setEnabled(False)
            self.ui.validateSequenceButton.setEnabled(False)
            self.skip_warning = False
            
            # Reset command properties
            self.disk_usages = [0.0] * len(self.commands)
            self.command_durations = [0.0] * len(self.commands)
            self.is_command_valid = [True] * len(self.commands)
            
            # Configure command engine
            self.command_engine.enableTestMode(True)
            self.command_index = 0
            self.issueCommand()
            self.command_engine.startCommand()

        else: # Mark all commands as invalid
            self.disk_usages = [0.0] * len(self.commands)
            self.command_durations = [0.0] * len(self.commands)
            self.is_command_valid = [False] * len(self.commands)
            self.createCommandList()
            self.updateEstimates()
   
    ## quit
    #
    # Handles the quit file action.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def quit(self, boolean):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    
    # Start logger.
    #hdebug.startLogging(parameters.directory + "logs/", "dave")

    # Load app.
    window = Dave(parameters)
    window.show()
    app.exec_()

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
