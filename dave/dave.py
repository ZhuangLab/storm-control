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

# XML parsing
from xml.dom import minidom, Node 

# PyQt
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# General
import notifications
import sequenceParser
from xml_generators import xml_generator, recipeParser

# Communication
import fluidics.kilroyClient
import halLib.tcpClient

# UI
import qtdesigner.dave_ui as daveUi

# Dave actions
import daveActions

# Parameter loading
import halLib.parameters as params

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
    idle = QtCore.pyqtSignal()
    problem = QtCore.pyqtSignal(str)

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
        
        # Setup delay timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.checkPause)

        # HAL Client
        self.HALClient = halLib.tcpClient.TCPClient(self)
        self.HALClient.acknowledged.connect(self.handleAcknowledged)
        self.HALClient.complete.connect(self.handleComplete)

        self.HALClient.startCommunication()
        self.has_HAL = self.HALClient.isConnected()
        if self.has_HAL: self.HALClient.stopCommunication()
        
        # Kilroy Client
        self.kilroyClient = fluidics.kilroyClient.KilroyClient(verbose = True)
        self.kilroyClient.acknowledged.connect(self.handleAcknowledged)
        self.kilroyClient.complete.connect(self.handleComplete)

        self.kilroyClient.startCommunication()
        self.has_kilroy = self.kilroyClient.isConnected()
        if self.has_kilroy: self.kilroyClient.stopCommunication()
    
    ## abort
    #
    # Aborts the current action (if any).
    #
    @hdebug.debug
    def abort(self):
        if self.current_action:
            self.delay_timer.stop()
            self.current_action.abort(self.getClient(self.current_action))
                
    ## checkPause
    #
    # Checks if we should stop acquisition because either the current action
    # of the user requested a pause.
    #
    @hdebug.debug
    def checkPause(self):
        if (self.current_action.shouldPause()) or self.should_pause:
            self.idle.emit()
            self.should_pause = False
            self.stopCommunication()
        else:
            print "Next action in checkPause"
            self.nextAction()

    ## execute Command
    #
    # Decompose a dave command into the necessary actions and run them
    #
    # @param command A XML command object from sequenceParser
    #
    @hdebug.debug
    def executeCommand(self, command):
        self.actions = []
        command_type = command.getType()
        if command_type == "movie":
            self.actions.append(daveActions.DaveActionMovieParameters(command))
            if command.recenter:            self.actions.append(daveActions.DaveActionRecenter())
            if (command.find_sum > 0.0):    self.actions.append(daveActions.DaveActionFindSum(command.find_sum))
            if (command.length > 0):        self.actions.append(daveActions.DaveActionMovie(command))
        elif command_type == "fluidics":
            self.actions.append(daveActions.DaveActionValveProtocol(command))

    ## getClient
    #
    # Returns the appropriate comm port for the action
    #
    # @current_action An action class for which the appropriate TCP/IP client will be determined
    #
    @hdebug.debug
    def getClient(self, current_action):
        if current_action.getCommType() == "HAL":
            return self.HALClient
        elif current_action.getCommType() == "Kilroy":
            return self.kilroyClient
        else:
            print "Unknown action type: " + current_action.getCommType()
            return None

    ## getClientStatus
    #
    # Returns the status of the TCP Clients
    #
    # @return (have HAL Client, have Kilroy Client)
    #
    @hdebug.debug
    def getClientStatus(self):
        return [self.has_HAL, self.has_kilroy]

    ## handleAcknowledged
    #
    # Handles the acknowledged signal from the tcpClient object.
    #
    @hdebug.debug
    def handleAcknowledged(self):
        if (self.current_action.handleAcknowledged()):
            if (not self.current_action.startTimer(self.delay_timer)):
                self.checkPause()

    ## handleComplete
    #
    # Handles the complete signal from the tcpClient object.
    #
    # @param a_string The message from HAL.
    #
    @hdebug.debug
    def handleComplete(self, a_string):
        if self.current_action.handleComplete(a_string):
            self.checkPause()
        else:
            self.stopCommunication()
            self.problem.emit(self.current_action.getMessage())

    ## nextAction
    #
    # Performs the next action for the movie. If there are no actions remaining then the done signal is emitted.
    #
    @hdebug.debug
    def nextAction(self):
        if (len(self.actions) > 0):
            self.current_action = self.actions[0]
            self.actions = self.actions[1:]
            self.current_action.start(self.getClient(self.current_action))
        else:
            self.done.emit()

    ## pause
    #
    # Sets the pause flag so that we will pause as soon as the current action is finished.
    #
    @hdebug.debug
    def pause(self):
        self.should_pause = True

    ## startCommunication
    #
    # Starts communication with HAL and kilroy
    #
    @hdebug.debug
    def startCommunication(self):
        if self.has_HAL: self.HALClient.startCommunication()
        if self.has_kilroy: self.kilroyClient.startCommunication()

    ## stopCommunication
    #
    # Stops communication with HAL.
    #
    @hdebug.debug
    def stopCommunication(self):
        if self.has_HAL: self.HALClient.stopCommunication()
        if self.has_kilroy: self.kilroyClient.stopCommunication()

## Window
#
# The main window
#
class Window(QtGui.QMainWindow):

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
        self.notifier = notifications.Notifier("", "", "", "")
        self.running = False
        self.settings = QtCore.QSettings("Zhuang Lab", "dave")
        self.sequence_filename = ""

        self.createGUI()

        # Movie engine.
        self.command_engine = CommandEngine()
        self.command_engine.done.connect(self.handleDone)
        self.command_engine.idle.connect(self.handleIdle)
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
        self.ui.abortButton.hide()
        self.ui.frequencyLabel.hide()
        self.ui.frequencySpinBox.hide()
        self.ui.runButton.hide()
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
        self.ui.actionGenerate.triggered.connect(self.handleGenerate)
        self.ui.actionGenerate_from_Recipe.triggered.connect(self.handleGenerateFromRecipe)
        self.ui.fromAddressLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.fromPasswordLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.runButton.clicked.connect(self.handleRunButton)
        self.ui.smtpServerLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.toAddressLineEdit.textChanged.connect(self.handleNotifierChange)
                                                        
        # Load saved notifications settings.
        self.noti_settings = [[self.ui.fromAddressLineEdit, "from_address"],
                              [self.ui.fromPasswordLineEdit, "from_password"],
                              [self.ui.smtpServerLineEdit, "smtp_server"]]
#                              [self.ui.toAddressLineEdit, "to_address"]]

        for [object, name] in self.noti_settings:
            object.setText(self.settings.value(name, "").toString())

        # Initialize command descriptor table
        self.command_details_table_size = [12, 2]
        self.ui.commandDetailsTable.setRowCount(self.command_details_table_size[0])
        self.ui.commandDetailsTable.setColumnCount(self.command_details_table_size[1])

        # Set active status
##        self.ui.commandSequenceList.setEnabled(False)
##        self.ui.commandDetailsTable.setEnabled(False)
        self.command_widgets = []

        # Enable mouse over updates of command descriptor
        self.ui.commandSequenceList.setMouseTracking(True)
        self.ui.commandSequenceList.itemEntered.connect(self.updateCommandDescriptorTable)
        self.ui.commandSequenceList.clicked.connect(self.handleCommandListClick)

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
            self.newSequence(str(url.encodedPath())[1:])

    ## handleAbortButton
    #
    # Tells the movie engine to abort the current movie. Resets everything to the initial movie.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleAbortButton(self, boolean):
        if (self.running):
            self.command_engine.abort()
            self.command_index = 0
            self.issueCommand()
            
            self.running = False
            self.ui.abortButton.setEnabled(False)
            self.ui.runButton.setText("Start")

    ## handleCommandListClick
    #
    # Reset command sequence list to the current command
    #
    #
    def handleCommandListClick(self):
        self.ui.commandSequenceList.setCurrentRow(self.command_index)

#    ## handleDisconnect
#    #
#    # Disconnects from HAL.
#    #
#    @hdebug.debug
#    def handleDisconnect(self):
#        if not self.comm.stopCommunication():
#            self.disconnect_timer.start()

    ## handleDone
    #
    # Handles starting the next movie (if we are done with the current movie).
    #
    @hdebug.debug
    def handleDone(self):
        if (self.command_index < (self.sequence_length-1)):
            self.command_index += 1
            self.issueCommand()
            self.command_engine.nextAction()
        else:
            self.command_index = 0
            self.ui.runButton.setText("Run")
            self.running = False
            self.issueCommand()
            self.command_engine.stopCommunication()

    ## handleGenerate
    #
    # Handles generating the XML that Dave uses from a positions text file and a experiment XML file.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleGenerate(self, boolean):
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self, "Positions File", self.directory, "*.txt"))
        self.directory = os.path.dirname(positions_filename)
        experiment_filename = str(QtGui.QFileDialog.getOpenFileName(self, "Experiment File", self.directory, "*.xml"))
        self.directory = os.path.dirname(experiment_filename)
        output_filename = str(QtGui.QFileDialog.getSaveFileName(self, "Generated File", self.directory, "*.xml"))
        tb = "No Error"
        try:
            xml_generator.generateXML(experiment_filename, positions_filename, output_filename, self.directory, self)
        except:
            QtGui.QMessageBox.information(self,
                                          "XML Generation Error",
                                          traceback.format_exc())
                                          #str(sys.exc_info()[0]))
        else:
            self.newSequence(output_filename)

    ## handleGenerateFromRecipe
    #
    # Handles Generate from Recipe XML
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleGenerateFromRecipe(self, boolean):
        recipe_parser = recipeParser.XMLRecipeParser(verbose = True)
        output_filename = recipe_parser.parseXML()
        if os.path.isfile(output_filename):
            self.newSequence(output_filename)

    ## handleIdle
    #
    # Handles the idle signal from the movie engine. Hides the abort button, changes the text of the run button
    # from "Pause" to "Start".
    #
    @hdebug.debug
    def handleIdle(self):
        self.ui.abortButton.hide()
        self.ui.runButton.setText("Start")
        self.running = False

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
        self.ui.runButton.setText("Start")
        self.running = False
        if (self.ui.errorMsgCheckBox.isChecked()):
            self.notifier.sendMessage("Acquisition Problem",
                                      message)
        QtGui.QMessageBox.information(self,
                                      "Acquisition Problem",
                                      message)

    ## handleRunButton
    #
    # Handles the run button. If we are running then the text is set to "Pausing.." and the movie engine is told to pause.
    # Otherwise the text is set to "Pause" and the movie engine is told to start.
    #
    # @param boolean Dummy parameter.
    #
    @hdebug.debug
    def handleRunButton(self, boolean):
        if (self.running):
            self.command_engine.pause()
            self.ui.runButton.setText("Pausing..")
            self.ui.runButton.setDown(True)
            self.running = False
        else:
            self.command_engine.startCommunication()
            self.command_engine.nextAction()
            self.ui.abortButton.show()
            self.ui.runButton.setText("Pause")
            self.running = True

    ## issueCommand
    #
    #  Send current command to command engine and update GUI
    #
    def issueCommand(self):
        # disable selectability of all other elements
        for widget in self.command_widgets:
            widget.setFlags(QtCore.Qt.ItemIsEnabled)

        self.command_widgets[self.command_index].setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.ui.commandSequenceList.setCurrentRow(self.command_index)
        self.updateCommandDescriptorTable(self.command_widgets[self.command_index])
        self.command_engine.executeCommand(self.commands[self.command_index])
        
    ## newSequence
    #
    # Parses a XML file describing the list of movies to take.
    #
    # @param sequence_filename The name of the XML file.
    #
    @hdebug.debug
    def newSequence(self, sequence_filename):
        if (not self.running):
            commands = []
            try:
                commands = sequenceParser.parseMovieXml(sequence_filename)
            except:
                QtGui.QMessageBox.information(self,
                                              "XML Generation Error",
                                              traceback.format_exc())
            else:
                self.commands = commands
                self.command_index = 0
                self.sequence_length = len(self.commands)
                self.sequence_filename = sequence_filename
                self.updateGUI()
                
                self.ui.abortButton.show()
                self.ui.runButton.setText("Run")
                self.ui.runButton.show()
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
        sequence_filename = str(QtGui.QFileDialog.getOpenFileName(self, "New Sequence", self.directory, "*.xml"))
        if sequence_filename:
            self.directory = os.path.dirname(sequence_filename)
            self.newSequence(sequence_filename)

    ## updateEstimates
    #
    # Updates the (displayed) estimates of the run time and the run size.
    #
    @hdebug.debug
    def updateEstimates(self):
        total_frames = 0
        for command in self.commands:
            if command.getType() == "movie":
                total_frames += command.length
        est_time = float(total_frames)/(57.3 * 60.0 * 60.0) + len(self.commands) * 10.0/(60.0 * 60.0)
        est_space = float(256 * 256 * 2 * total_frames)/(1000.0 * 1000.0 * 1000.0)
        self.ui.timeLabel.setText("Run Length: {0:.1f} hours (57Hz)".format(est_time))
        self.ui.spaceLabel.setText("Run Size: {0:.1f} GB (256x256)".format(est_space))

    ## updateGUI
    #
    # Update the GUI elements
    #
    @hdebug.debug
    def updateGUI(self):
        # Current sequence xml file
        self.ui.sequenceLabel.setText(self.sequence_filename)
        print self.sequence_filename
        # Update TCP/IP client status
        client_status = self.command_engine.getClientStatus()
        if client_status[0]: # HAL status
            self.ui.HALConnectionLabel.setText("HAL Client: Connected")
        else:
            self.ui.HALConnectionLabel.setText("HAL Client: Not connected")

        if client_status[1]: # Kilroy status
            self.ui.kilroyConnectionLabel.setText("Kilroy Client: Connected")
        else:
            self.ui.kilroyConnectionLabel.setText("Kilroy Client: Not connected")

        # Update time estimates 
        self.updateEstimates()

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
            
    ## createCommandList
    #
    # create the command list
    #
    @hdebug.debug
    def createCommandList(self):
        self.ui.commandSequenceList.clear()
        self.command_widgets = []
        
        for command in self.commands:
            widget = QtGui.QListWidgetItem(command.getDescriptor())
            widget.setFlags(QtCore.Qt.ItemIsEnabled)
            self.ui.commandSequenceList.addItem(widget)
            self.command_widgets.append(widget)
        
        if len(self.commands) > 0:
            self.command_widgets[0].setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.ui.commandSequenceList.setCurrentRow(0)

        self.updateCommandDescriptorTable(self.command_widgets[0])
        
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
    window = Window(parameters)
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
