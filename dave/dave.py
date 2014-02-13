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

import os
import sys
import traceback
from xml.dom import minidom, Node

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# General
import sc_library.tcpClient as tcpClient
import notifications
import sequenceParser
import xml_generator

# UIs.
import qtdesigner.dave_ui as daveUi

# Misc
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

## DaveAction
#
# The base class for actions that can be performed as part of taking a movie.
#
class DaveAction():

    ## __init__
    #
    # Default initialization.
    #
    def __init__(self):
        self.delay = 0
        self.message = ""

    ## abort
    #
    # The default behaviour is not to do anything.
    #
    # @param comm A tcpClient object.
    #
    def abort(self, comm):
        pass

    ## getMessage
    #
    # @return The error message if there a problem occured during this action.
    #
    def getMessage(self):
        return self.message

    ## handleAcknowledged
    #
    # This is called when we get command acknowledgement from HAL. If this
    # returns true and the delay time is greater than zero then the delay
    # timer is started.
    #
    # @return True.
    #
    def handleAcknowledged(self):
        return True

    ## handleComplete
    #
    # This is called when we get a complete message from HAL with a_string
    # containing the contents of the complete message. If it returns true
    # then we continue to the next action, otherwise we stop taking movies.
    #
    # @param a_string The complete message from HAL (as a string).
    #
    # @return True
    #
    def handleComplete(self, a_string):
        return True

    ## shouldPause
    #
    # @return True/False if movie acquisition should pause after taking this movie, the default is False.
    #
    def shouldPause(self):
        return False

    ## start
    #
    # The default behaviour is not do anything.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        pass

    ## startTimer
    #
    # If there is a delay time for this action then set the interval of the provided timer, start it
    # and return True, otherwise return False.
    #
    # @param timer A PyQt timer.
    #
    # @return True/False if we started timer.
    #
    def startTimer(self, timer):
        if (self.delay > 0):
            timer.setInterval(self.delay)
            timer.start()
            return True
        else:
            return False


## DaveActionFindSum
#
# The find sum action.
#
class DaveActionFindSum(DaveAction):

    ## __init__
    #
    # @param min_sum The minimum sum that we should get from HAL upon completion of this action.
    #
    def __init__(self, min_sum):
        DaveAction.__init__(self)
        self.min_sum = min_sum

    ## handleAcknowledged
    #
    # @return False.
    #
    def handleAcknowledged(self):
        return False

    ## handleComplete
    #
    # @param a_string The sum signal message from HAL.
    #
    # @return True/False if float(a_string) is greater than min_sum.
    #
    def handleComplete(self, a_string):
        if (a_string == "NA") or (float(a_string) > self.min_sum):
            return True
        else:
            self.message = "Sum signal " + a_string + " is below threshold value of " + str(self.min_sum)
            return False

    ## start
    #
    # Send the startFindSum message to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.startFindSum()


## DaveActionMovie
#
# The movie acquisition action.
#
class DaveActionMovie(DaveAction):

    ## __init__
    #
    # @param movie A movie XML object.
    #
    def __init__(self, movie):
        DaveAction.__init__(self)
        self.acquiring = False
        self.movie = movie

    ## abort
    #
    # Aborts the movie (if we are current acquiring).
    #
    # @param comm A tcpClient object.
    #
    def abort(self, comm):
        if self.acquiring:
            comm.stopMovie()

    ## handleAcknowledged
    #
    # @return True.
    #
    def handleAcknowledged(self):
        return False

    ## handleComplete
    #
    # Returns false if a_string is "NA" or int(a_string) is greater than the
    # minimum number of spots that the movie should have (as specified by
    # the movie XML object).
    #
    # @param a_string The response from HAL.
    #
    # @return True/False if the movie was good.
    #
    def handleComplete(self, a_string):
        self.acquiring = False
        if (a_string == "NA") or (int(a_string) >= self.movie.min_spots):
            return True
        else:
            self.message = "Spot finder counts " + a_string + " is below threshold value of " + str(self.movie.min_spots)
            return False

    ## start
    #
    # Send the startMovie command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        self.acquiring = True
        comm.startMovie(self.movie)


## DaveActionMovieParameters
#
# The movie parameters action.
#
class DaveActionMovieParameters(DaveAction):

    ## __init__
    #
    # @param movie A XML movie object.
    #
    def __init__(self, movie):
        DaveAction.__init__(self)
        self.delay = movie.delay
        self.movie = movie

    ## shouldPause
    #
    # @return The pause time specified by the movie object.
    #
    def shouldPause(self):
        return self.movie.pause

    ## start
    #
    # Send  the movie parameters command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.sendMovieParameters(self.movie)


## DaveActionRecenter
#
# The piezo recentering action. Note that this is only useful if the microscope
# has a motorized Z.
#
class DaveActionRecenter(DaveAction):

    ## __init__
    #
    # Create the object, set the delay time to 200 milliseconds.
    #
    def __init__(self):
        DaveAction.__init__(self)
        self.delay = 200

    ## handleAcknowledged
    #
    # @return False
    #
    def handleAcknowledged(self):
        return False

    ## start
    #
    # Send the recenter piezo command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.startRecenterPiezo()


## MovieEngine
#
# This handles taking a movie & updating the movie details.
#
class MovieEngine(QtGui.QWidget):
    done = QtCore.pyqtSignal()
    idle = QtCore.pyqtSignal()
    problem = QtCore.pyqtSignal(str)

    ## __init__
    #
    # This sets the size of the QTableWidget (in rows and columns) that will be used to
    # to display the movie details. It fills in the fields of the table that do not change.
    # It creates the timer that we will use as needed for actions that specify a delay time.
    #
    # @param details_table The PyQt QTableWidget that will be used for display of the movie details.
    # @param parent The PyQy parent of this widget.
    #
    @hdebug.debug
    def __init__(self, details_table, parent):
        QtGui.QWidget.__init__(self, parent)
        self.actions = []
        self.current_action = False
        self.details_table = details_table
        self.movie = False
        self.number_movies = 0
        self.should_pause = False

        # Setup Info Table.
        fields = ["Delay",
                  "Find Sum",
                  "Length",
                  "Lock Target",
                  "Minimum Spots",
                  "Name",
                  "Parameters",
                  "Pause",
                  "Progression",
                  "Recenter Piezo",
                  "Stage Position"]

        self.details_table.setRowCount(len(fields)+1)
        self.details_table.setColumnCount(3)
        for i, field in enumerate(fields):
            self.details_table.setItem(i+1,0,createTableWidget(" "))
            self.details_table.setItem(i+1,1,createTableWidget(field))
        self.details_table.resizeColumnToContents(0)
        self.details_table.setSpan(0,0,1,3)

        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.checkPause)

        # TCP communications.
        self.comm = tcpClient.TCPClient(self)
        self.comm.acknowledged.connect(self.handleAcknowledged)
        self.comm.complete.connect(self.handleComplete)

    ## abort
    #
    # Aborts the current action (if any).
    #
    @hdebug.debug
    def abort(self):
        if self.current_action:
            self.delay_timer.stop()
            self.current_action.abort(self.comm)

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
            self.nextAction()

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

    ## newMovie
    #
    # Fills in the appropriate fields of the details table and creates the actions necessary to take a movie.
    #
    # @param movie A XML movie object.
    # @param index The index of the current movie. Confusingly this is also used a variable in this method for a different purpose..
    #
    @hdebug.debug
    def newMovie(self, movie, index):
        self.details_table.setItem(0,0,createTableWidget("Movie {0:d} of {1:d}\n\n".format(index+1, self.number_movies)))

        # Update movie details display.
        # delay
        index = 1
        self.details_table.setItem(index,2,createTableWidget("{0:d}".format(movie.delay)))

        # find sum
        index += 1
        if (movie.find_sum > 0.0):
            self.details_table.setItem(index,2,createTableWidget("{0:.1f}".format(movie.find_sum)))
        else:
            self.details_table.setItem(index,2,createTableWidget("No"))

        # length
        index += 1
        self.details_table.setItem(index,2,createTableWidget("{0:d}".format(movie.length)))

        # lock target
        index += 1
        if hasattr(movie, "lock_target"):
            self.details_table.setItem(index,2,createTableWidget("{0:.1f}".format(movie.lock_target)))
        else:
            self.details_table.setItem(index,2,createTableWidget("None"))

        # minimum spots
        index += 1
        self.details_table.setItem(index,2,createTableWidget("{0:d}".format(movie.min_spots)))

        # name
        index += 1
        self.details_table.setItem(index,2,createTableWidget("{0:s}".format(movie.name)))

        # parameters
        index += 1
        if hasattr(movie, "parameters"):
            self.details_table.setItem(index,2,createTableWidget("{0:d}".format(movie.parameters)))
        else:
            self.details_table.setItem(index,2,createTableWidget("None"))

        # pause
        index += 1
        if movie.pause:
            self.details_table.setItem(index,2,createTableWidget("Yes"))
        else:
            self.details_table.setItem(index,2,createTableWidget("No"))

        # progression
        index += 1
        self.details_table.setItem(index,2,createTableWidget(movie.progression.type))

        # recenter
        index += 1
        if movie.recenter:
            self.details_table.setItem(index,2,createTableWidget("Yes"))
        else:
            self.details_table.setItem(index,2,createTableWidget("No"))

        # stage position
        index += 1
        if hasattr(movie, "stage_x") and hasattr(movie, "stage_y"):
            self.details_table.setItem(index,2,createTableWidget("{0:.2f}, {1:.2f}".format(movie.stage_x, movie.stage_y)))
        else:
            self.details_table.setItem(index,2,createTableWidget("NA,NA"))

        # Generate actions for taking the movie.
        self.actions = []
        self.actions.append(DaveActionMovieParameters(movie))
        if movie.recenter:
            self.actions.append(DaveActionRecenter())
        if (movie.find_sum > 0.0):
            self.actions.append(DaveActionFindSum(movie.find_sum))
        if (movie.length > 0):
            self.actions.append(DaveActionMovie(movie))

    ## nextAction
    #
    # Performs the next action for the movie. If there are no actions remaining then the done signal is emitted.
    #
    @hdebug.debug
    def nextAction(self):
        if (len(self.actions) > 0):
            self.current_action = self.actions[0]
            self.actions = self.actions[1:]
            self.current_action.start(self.comm)
        else:
            self.done.emit()

    ## pause
    #
    # Sets the pause flag so that we will pause as soon as the current action is finished.
    #
    @hdebug.debug
    def pause(self):
        self.should_pause = True

    ## setNumberMovies
    #
    # Sets the total number of movies. This value is also included in the details table.
    #
    # @param number An integer specifying the total number of movies.
    #
    @hdebug.debug
    def setNumberMovies(self, number):
        self.number_movies = number

    ## startCommunication
    #
    # Starts communication with HAL.
    #
    @hdebug.debug
    def startCommunication(self):
        self.comm.startCommunication()

    ## stopCommunication
    #
    # Stops communication with HAL.
    #
    @hdebug.debug
    def stopCommunication(self):
        self.comm.stopCommunication()


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
        self.movie_index = 0
        self.movies = []
        self.notifier = notifications.Notifier("", "", "", "")
        self.running = False
        self.settings = QtCore.QSettings("Zhuang Lab", "dave")

        # UI setup.
        self.ui = daveUi.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.spaceLabel.setText("")
        self.ui.timeLabel.setText("")

        self.ui.abortButton.hide()
        #self.ui.backButton.hide()
        #self.ui.forwardButton.hide()
        self.ui.frequencyLabel.hide()
        self.ui.frequencySpinBox.hide()
        self.ui.movieTableWidget.hide()
        self.ui.runButton.hide()
        self.ui.statusMsgCheckBox.hide()

        self.setWindowIcon(QtGui.QIcon("dave.ico"))

        # This is for handling file drops.
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # Connect UI signals.
        self.ui.abortButton.clicked.connect(self.handleAbortButton)
        self.ui.actionNew_Sequence.triggered.connect(self.newSequenceFile)
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionGenerate.triggered.connect(self.handleGenerate)
        self.ui.fromAddressLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.fromPasswordLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.runButton.clicked.connect(self.handleRunButton)
        self.ui.smtpServerLineEdit.textChanged.connect(self.handleNotifierChange)
        self.ui.toAddressLineEdit.textChanged.connect(self.handleNotifierChange)

        # Movie engine.
        self.movie_engine = MovieEngine(self.ui.movieTableWidget, self.ui.movieGroupBox)
        self.movie_engine.done.connect(self.handleDone)
        self.movie_engine.idle.connect(self.handleIdle)
        self.movie_engine.problem.connect(self.handleProblem)

        # Load saved notifications settings.
        self.noti_settings = [[self.ui.fromAddressLineEdit, "from_address"],
                              [self.ui.fromPasswordLineEdit, "from_password"],
                              [self.ui.smtpServerLineEdit, "smtp_server"]]
#                              [self.ui.toAddressLineEdit, "to_address"]]

        for [object, name] in self.noti_settings:
            object.setText(self.settings.value(name, "").toString())

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
            self.movie_engine.abort()
            self.movie_index = 0
            self.movie_engine.newMovie(self.movies[self.movie_index], self.movie_index)
            self.running = False
            self.ui.abortButton.hide()
            self.ui.runButton.setText("Start")

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
        if (self.movie_index < (self.number_movies-1)):
            self.movie_index += 1
            self.movie_engine.newMovie(self.movies[self.movie_index], self.movie_index)
            self.movie_engine.nextAction()
        else:
            self.movie_index = 0
            #self.movies[self.movie_index].pause = True # This keeps us from looping forever.
            self.ui.runButton.setText("Run")
            self.running = False
            self.movie_engine.newMovie(self.movies[self.movie_index], self.movie_index)
            self.movie_engine.stopCommunication()

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
            self.movie_engine.pause()
            self.ui.runButton.setText("Pausing..")
            self.ui.runButton.setDown(True)
            self.running = False
        else:
            self.movie_engine.startCommunication()
            self.movie_engine.nextAction()
            self.ui.abortButton.show()
            self.ui.runButton.setText("Pause")
            self.running = True

    ## newSequence
    #
    # Parses a XML file describing the list of movies to take.
    #
    # @param sequence_filename The name of the XML file.
    #
    @hdebug.debug
    def newSequence(self, sequence_filename):
        if (not self.running):
            new_movies = []
            try:
                new_movies = sequenceParser.parseMovieXml(sequence_filename)
            except:
                QtGui.QMessageBox.information(self,
                                              "XML Generation Error",
                                              traceback.format_exc())
                #str(sys.exc_info()[0]))
            else:
                self.movies = new_movies
                self.movie_index = 0
                self.number_movies = len(self.movies)
                self.updateEstimates()
                self.ui.abortButton.show()
                self.ui.movieTableWidget.show()
                self.ui.runButton.setText("Run")
                self.ui.runButton.show()
                self.ui.sequenceLabel.setText(sequence_filename)
                self.movie_engine.setNumberMovies(self.number_movies)
                self.movie_engine.newMovie(self.movies[self.movie_index], self.movie_index)

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
        for movie in self.movies:
            total_frames += movie.length
        est_time = float(total_frames)/(57.3 * 60.0 * 60.0) + len(self.movies) * 10.0/(60.0 * 60.0)
        est_space = float(256 * 256 * 2 * total_frames)/(1000.0 * 1000.0 * 1000.0)
        self.ui.timeLabel.setText("Run Length: {0:.1f} hours (57Hz)".format(est_time))
        self.ui.spaceLabel.setText("Run Size: {0:.1f} GB (256x256)".format(est_space))

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
    hdebug.startLogging(parameters.directory + "logs/", "dave")

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
