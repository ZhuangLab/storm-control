#!/usr/bin/python
#
# Utility for running scripting files for remote
# control of the HAL-4000 data taking program.
#
# Hazen 06/13
#

import os
import sys
import traceback
from xml.dom import minidom, Node

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# General
import halLib.tcpClient
import notifications
import sequenceParser
import xml_generator

# UIs.
import qtdesigner.dave_ui as daveUi

# Misc
import halLib.parameters as params


def createTableWidget(text):
    widget = QtGui.QTableWidgetItem(text)
    widget.setFlags(QtCore.Qt.ItemIsEnabled)
    return widget

#
# Actions for taking a movie.
#
class DaveAction():

    def __init__(self):
        self.delay = 0
        self.message = ""

    def abort(self, comm):
        pass

    def getMessage(self):
        return self.message

    def handleAcknowledged(self):
        return True

    def handleComplete(self, a_string):
        return True

    def shouldPause(self):
        return False

    def start(self, comm):
        pass

    def startTimer(self, timer):
        if (self.delay > 0):
            timer.setInterval(self.delay)
            timer.start()
            return True
        else:
            return False


class DaveActionFindSum(DaveAction):

    def __init__(self, min_sum):
        DaveAction.__init__(self)
        self.min_sum = min_sum

    def handleAcknowledged(self):
        return False

    def handleComplete(self, a_string):
        if (a_string == "NA") or (float(a_string) > self.min_sum):
            return True
        else:
            self.message = "Sum signal " + a_string + " is below threshold value of " + str(self.min_sum)
            return False

    def start(self, comm):
        comm.startFindSum()


class DaveActionMovie(DaveAction):

    def __init__(self, movie):
        DaveAction.__init__(self)
        self.acquiring = False
        self.movie = movie

    def abort(self, comm):
        if self.acquiring:
            comm.stopMovie()

    def handleAcknowledged(self):
        return False

    def handleComplete(self, a_string):
        self.acquiring = False
        if (a_string == "NA") or (int(a_string) >= self.movie.min_spots):
            return True
        else:
            self.message = "Spot finder counts " + a_string + " is below threshold value of " + str(self.movie.min_spots)
            return False

    def start(self, comm):
        self.acquiring = True
        comm.startMovie(self.movie)


class DaveActionMovieParameters(DaveAction):

    def __init__(self, movie):
        DaveAction.__init__(self)
        self.delay = movie.delay
        self.movie = movie

    def shouldPause(self):
        return self.movie.pause

    def start(self, comm):
        comm.sendMovieParameters(self.movie)


class DaveActionRecenter(DaveAction):
    
    def __init__(self):
        DaveAction.__init__(self)
        self.delay = 200

    def handleAcknowledged(self):
        return False

    def start(self, comm):
        comm.startRecenterPiezo()


#
# This handles taking a movie & updating the movie details.
#
class MovieEngine(QtGui.QWidget):
    done = QtCore.pyqtSignal()
    idle = QtCore.pyqtSignal()
    problem = QtCore.pyqtSignal(str)

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
        self.comm = halLib.tcpClient.TCPClient(self)
        self.comm.acknowledged.connect(self.handleAcknowledged)
        self.comm.complete.connect(self.handleComplete)

    def abort(self):
        if self.current_action:
            self.delay_timer.stop()
            self.current_action.abort(self.comm)

    def checkPause(self):
        if (self.current_action.shouldPause()) or self.should_pause:
            self.idle.emit()
            self.should_pause = False
            self.comm.stopCommunication()
        else:
            self.nextAction()

    def handleAcknowledged(self):
        if (self.current_action.handleAcknowledged()):
            if (not self.current_action.startTimer(self.delay_timer)):
                self.checkPause()

    def handleComplete(self, a_string):
        if self.current_action.handleComplete(a_string):
            self.checkPause()
        else:
            self.comm.stopCommunication()
            self.problem.emit(self.current_action.getMessage())

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

    def nextAction(self):
        if (len(self.actions) > 0):
            self.current_action = self.actions[0]
            self.actions = self.actions[1:]
            self.current_action.start(self.comm)
        else:
            self.done.emit()

    def pause(self):
        self.should_pause = True

    def setNumberMovies(self, number):
        self.number_movies = number

    def startCommunication(self):
        self.comm.startCommunication()


#
# Main window
#
class Window(QtGui.QMainWindow):
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
                              [self.ui.smtpServerLineEdit, "smtp_server"],
                              [self.ui.toAddressLineEdit, "to_address"]]

        for [object, name] in self.noti_settings:
            object.setText(self.settings.value(name, "").toString())

    @hdebug.debug
    def cleanUp(self):
        # Save notification settings.
        for [object, name] in self.noti_settings:
            self.settings.setValue(name, object.text())

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    @hdebug.debug
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @hdebug.debug
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.newSequence(str(url.encodedPath())[1:])

    @hdebug.debug
    def handleAbortButton(self):
        if (self.running):
            self.movie_engine.abort()
            self.movie_index = 0
            self.movie_engine.newMovie(self.movies[self.movie_index], self.movie_index)
            self.running = False
            self.ui.abortButton.hide()
            self.ui.runButton.setText("Start")

    @hdebug.debug
    def handleDisconnect(self):
        if not self.comm.stopCommunication():
            self.disconnect_timer.start()

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

    @hdebug.debug
    def handleGenerate(self):
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

    @hdebug.debug
    def handleIdle(self):
        self.ui.abortButton.hide()
        self.ui.runButton.setText("Start")
        self.running = False

    @hdebug.debug
    def handleNotifierChange(self, some_text):
        self.notifier.setFields(self.ui.smtpServerLineEdit.text(),
                                self.ui.fromAddressLineEdit.text(),
                                self.ui.fromPasswordLineEdit.text(),
                                self.ui.toAddressLineEdit.text())

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

    @hdebug.debug
    def handleRunButton(self):
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

    @hdebug.debug
    def newSequenceFile(self):
        sequence_filename = str(QtGui.QFileDialog.getOpenFileName(self, "New Sequence", self.directory, "*.xml"))
        self.directory = os.path.dirname(sequence_filename)
        self.newSequence(sequence_filename)

    @hdebug.debug
    def updateEstimates(self):
        total_frames = 0
        for movie in self.movies:
            total_frames += movie.length
        est_time = float(total_frames)/(57.3 * 60.0 * 60.0) + len(self.movies) * 10.0/(60.0 * 60.0)
        est_space = float(256 * 256 * 2 * total_frames)/(1000.0 * 1000.0 * 1000.0)
        self.ui.timeLabel.setText("Run Length: {0:.1f} hours (57Hz)".format(est_time))
        self.ui.spaceLabel.setText("Run Size: {0:.1f} GB (256x256)".format(est_space))

    @hdebug.debug
    def quit(self):
        self.close()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
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
