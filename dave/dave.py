#!/usr/bin/python
#
# Utility for running scripting files for remote
# control of the HAL-4000 data taking program.
#
# Hazen 12/10
#

import os
import sys
from PyQt4 import QtCore, QtGui
from xml.dom import minidom, Node

# Debugging
import halLib.hdebug as hdebug

# General
import sequenceParser
import xml_generator
import halLib.tcpClient

# UIs.
import qtdesigner.dave_ui as daveUi

#
# Main window
#
class Window(QtGui.QMainWindow):
    @hdebug.debug
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        
        # general
        self.action = "none"
        self.comm_queue = [None, None, None]
        self.current_comm = None
        self.directory = ""
        self.mode = "idle"
        self.movies = 0
        self.skip_pause = False

        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)

        # This is for disconnecting. We wait for all the commands
        # to get processed before we break the connection.
        self.disconnect_timer = QtCore.QTimer(self)
        self.disconnect_timer.setInterval(100)
        self.disconnect_timer.setSingleShot(True)

        # ui setup
        self.ui = daveUi.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.detailsFrame.setStyleSheet("QFrame { background: white }")
        self.ui.detailsLabel.setStyleSheet("QLabel { background: white }")
        self.ui.detailsLabel.setText("No sequence loaded")
        self.ui.spaceLabel.setText("")
        self.ui.timeLabel.setText("")
        self.ui.startButton.hide()
        self.ui.skipButton.hide()

        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # signals
        self.connect(self.ui.actionNew_Sequence, QtCore.SIGNAL("triggered()"), self.newSequenceFile)
        self.connect(self.ui.actionQuit, QtCore.SIGNAL("triggered()"), self.quit)
        self.connect(self.ui.actionGenerate, QtCore.SIGNAL("triggered()"), self.handleGenerate)
        self.connect(self.ui.runButton, QtCore.SIGNAL("clicked()"), self.handleRunButton)
        self.connect(self.ui.abortButton, QtCore.SIGNAL("clicked()"), self.handleAbortButton)
        self.connect(self.ui.skipButton, QtCore.SIGNAL("clicked()"), self.handleSkipButton)
        self.connect(self.ui.startButton, QtCore.SIGNAL("clicked()"), self.handleStartButton)
        self.connect(self.delay_timer, QtCore.SIGNAL("timeout()"), self.handleDelay)
        self.connect(self.disconnect_timer, QtCore.SIGNAL("timeout()"), self.handleDisconnect)

        # tcp communications
        self.comm = halLib.tcpClient.TCPClient(self.ui.centralwidget)
        self.connect(self.comm, QtCore.SIGNAL("complete()"), self.handleComplete)

    @hdebug.debug
    def cleanUp(self):
        pass

    @hdebug.debug
    def closeEvent(self, event):
        self.cleanUp()

    @hdebug.debug
    def handleComplete(self):
        self.action = "complete"
        self.updateState()

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
    def goToIdle(self):
        self.ui.skipButton.hide()
        self.ui.startButton.hide()
        self.handleDisconnect()
        self.ui.runButton.setText("Run")
        self.ui.runButton.setDown(False)
        self.ui.abortButton.setText("Abort")
        self.ui.abortButton.setDown(False)

    @hdebug.debug
    def handleAbortButton(self):
        self.action = "abortButton"
        self.updateState()

    @hdebug.debug
    def handleDelay(self):
        self.action = "delayTimeOver"
        self.updateState()

    @hdebug.debug
    def handleDisconnect(self):
        if not self.comm.stopCommunication():
            self.disconnect_timer.start()
            
    @hdebug.debug
    def handleGenerate(self):
        positions_filename = str(QtGui.QFileDialog.getOpenFileName(self, "Positions File", self.directory, "*.txt"))
        self.directory = os.path.dirname(positions_filename)
        experiment_filename = str(QtGui.QFileDialog.getOpenFileName(self, "Experiment File", self.directory, "*.xml"))
        self.directory = os.path.dirname(experiment_filename)
        output_filename = str(QtGui.QFileDialog.getSaveFileName(self, "Generated File", self.directory, "*.xml"))
        try:
            xml_generator.generateXML(experiment_filename, positions_filename, output_filename, self.directory, self)
        except:
            QtGui.QMessageBox.information(self,
                                          "XML Generation Error",
                                          str(sys.exc_info()[0]))
        else:
            self.newSequence(output_filename)

    @hdebug.debug
    def handleRunButton(self):
        if self.movies:
            if self.mode == "idle":
                self.action = "runButton"
            else:
                self.action = "idleButton"
            self.updateState()

    @hdebug.debug
    def handleSkipButton(self):
        self.action = "skipButton"
        self.updateState()

    @hdebug.debug
    def handleStartButton(self):
        self.action = "startButton"
        self.updateState()

    @hdebug.debug
    def newSequence(self, sequence_filename):
        if self.mode == "idle":
            new_movies = 0
            try:
                new_movies = sequenceParser.parseMovieXml(sequence_filename)
            except:
                QtGui.QMessageBox.information(self,
                                              "XML Generation Error",
                                              str(sys.exc_info()[0]))
            else:
                self.movies = new_movies
                self.movie_index = 0
                self.number_movies = len(self.movies)
                self.updateEstimates()
                self.updateDetails()
                self.ui.sequenceLabel.setText(sequence_filename)

    @hdebug.debug
    def newSequenceFile(self):
        sequence_filename = str(QtGui.QFileDialog.getOpenFileName(self, "New Sequence", self.directory, "*.xml"))
        self.directory = os.path.dirname(sequence_filename)
        self.newSequence(sequence_filename)

    @hdebug.debug
    def nextMovieSetup(self):
        movie = self.movies[self.movie_index]
        self.comm.sendMovieParameters(movie)
        self.comm_queue = []
        delay = movie.delay
        if movie.recenter:
            self.comm_queue.append(["recenter", delay])
            delay = 200
        if movie.find_sum:
            self.comm_queue.append(["find_sum", delay])
            delay = 200
        if (movie.length > 0):
            self.comm_queue.append(["movie", delay])
        print self.comm_queue
        self.handleComplete()

    @hdebug.debug
    def updateDetails(self):
        spacing = "    "
        movie = self.movies[self.movie_index]
        details = "Movie {0:d} of {1:d}\n\n".format(self.movie_index+1, self.number_movies)
        details += "Parameters:\n"
        if movie.pause:
            details += spacing + "Pause: True\n"
        else:
            details += spacing + "Pause: False\n"
        if hasattr(movie, "stage_x") and hasattr(movie, "stage_y"):
            details += spacing + "Stage X,Y: {0:.2f}, {1:.2f}\n".format(movie.stage_x, movie.stage_y)
        if hasattr(movie, "parameters"):
            details += spacing + "Parameters: {0:d}\n".format(movie.parameters)
        if hasattr(movie, "lock_target"):
            details += spacing + "Lock Target: {0:.1f}\n".format(movie.lock_target)
        if movie.recenter:
            details += spacing + "Recenter Piezo: True\n"
        else:
            details += spacing + "Recenter Piezo: False\n"
        if movie.find_sum:
            details += spacing + "Find Sum: True\n"
        else:
            details += spacing + "Find Sum: False\n"
        details += spacing + "Name: {0:s}\n".format(movie.name)
        details += spacing + "Length: {0:d}\n".format(movie.length)
        details += spacing + "Progression: " + movie.progression.type + "\n"
        details += spacing + "Start Delay in ms: {0:d}\n".format(movie.delay)
        self.ui.detailsLabel.setText(details)

    @hdebug.debug
    def updateEstimates(self):
        total_frames = 0
        for movie in self.movies:
            total_frames += movie.length
        est_time = float(total_frames)/(57.3 * 60.0 * 60.0) + len(self.movies) * 10.0/(60.0 * 60.0)
        est_space = float(256 * 256 * 2 * total_frames)/(1000.0 * 1000.0 * 1000.0)
        self.ui.timeLabel.setText("Run Length: {0:.1f} hours (57Hz)".format(est_time))
        self.ui.spaceLabel.setText("Run Size: {0:.1f} GB (256x256)".format(est_space))

    #
    # This is where everything happens. The idea is that having it all in 
    # one function will make it little easier to achieve the correct 
    # behavior then having stuff scattered across multiple functions.
    # It still seems quite messy however.
    #
    # mode = "run", we are connected & running.
    # mode = "pause", we are not connected.
    #
    @hdebug.debug
    def updateState(self):
        update = True
        print self.action

        # abort button.
        if (self.action == "abortButton"):
            self.movie_index = 0
            self.mode = "idle"
            if self.current_comm:
                if (self.current_comm == "movie"):
                    self.comm.stopMovie()
                self.ui.abortButton.setText("Aborting...")
                self.ui.abortButton.setDown(True)
            else:
                self.goToIdle()

        # complete event.
        elif (self.action == "complete"):
            if (self.mode == "running"):
                self.current_comm = False
                if (len(self.comm_queue) > 0):
                    next = self.comm_queue[0]
                    self.delay_timer.setInterval(next[1])
                    self.delay_timer.start()
                else:
                    self.movie_index += 1
                    if (self.movie_index == self.number_movies):
                        self.mode = "idle"
                        self.movie_index = 0
                        self.comm.sendMovieParameters(self.movies[0])
                        self.goToIdle()
                    else:
                        self.nextMovieSetup()
            else:
                self.goToIdle()

        # delay time over event.
        elif (self.action == "delayTimeOver"):
            if (self.mode == "running"):
                    next = self.comm_queue[0]
                    self.current_comm = next[0]
                    if (next[0] == "recenter"):
                        self.comm.startRecenterPiezo()
                    elif (next[0] == "find_sum"):
                        self.comm.startFindSum()
                    elif (next[0] == "movie"):
                        movie = self.movies[self.movie_index]
                        if movie.pause:
#                            self.ui.skipButton.show()
                            self.ui.startButton.show()
                        else:
                            self.comm.startMovie(movie)
                    else:
                        print "???", next[0]
                    self.comm_queue = self.comm_queue[1:]
            else:
                self.goToIdle()

        # idle button.
        elif (self.action == "idleButton"):
            self.mode = "idle"
            if self.current_comm:
                self.ui.runButton.setText("Pausing...")
                self.ui.runButton.setDown(True)
                self.movie_index += 1
                update = False
            else:
                self.goToIdle()

        # run button.
        elif (self.action == "runButton"):
            self.mode = "running"
            self.ui.runButton.setText("Pause")
            self.comm.startCommunication()
            self.nextMovieSetup()

        # skip button.
        elif (self.action == "skipButton"):
            if self.filming:
                self.comm.stopMovie()
            self.movie_index += 1
            if (self.movie_index == self.number_movies):
                self.mode = "idle"
                self.movie_index = 0
                self.comm.sendMovieParameters(self.movies[0])
                self.goToIdle()
            else:
                self.ui.skipButton.hide()
                self.ui.startButton.hide()
                self.nextMovieSetup()

        # start button.
        elif (self.action == "startButton"):
            self.ui.skipButton.hide()
            self.ui.startButton.hide()
            self.comm.startMovie(self.movies[self.movie_index])

#        # find sum TCP event.
#        elif (self.action == "sumComplete"):
#            self.finding_sum = False
#            if (self.mode == "running"):
#                movie = self.movies[self.movie_index]
#                if movie.pause:
##                    self.ui.skipButton.show()
#                    self.ui.startButton.show()
#                else:
#                    self.filming = True
#                    self.comm.startMovie(movie)
#            else:
#                self.goToIdle()

        # unknown.
        else:
            print "unexpected action:", self.action

        if update:
            self.updateDetails()

    @hdebug.debug
    def quit(self):
        self.close()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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
