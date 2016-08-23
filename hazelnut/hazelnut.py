#!/usr/bin/env python
#
# A file transfer utility specialized for storm-control. It's
# primary difference is that it waits until HAL has finished
# acquiring a movie before transferring. The finished state
# is indicated by the presence of the corresponding XML file
# for the movie.
#
# Hazen 08/16
#

import datetime
import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import qtdesigner.hazelnut_ui as hazelnutUi


class DirObject(object):
    """
    A class for doing several things.
    1. Source directory:
       a. List existing files in the directory.
       b. Keep track of new files / folders that appear in the directory.
       c. Get creation / modification time of the files.

    2. Transfer directory.
       a. Check if the file needs to be transferred.
       b. Transfer a file.
       
    """
    def __init__(self):
        self.directory = ""
        self.new_files = []
        self.old_files = []
        
    def getAllFiles(self):
        return self.old_files + self.new_files

    def getDirectory(self):
        return self.directory

    def getNewFiles(self):
        return self.new_files

    def updateNewFiles(self):
        self.old_files += self.new_files
        self.new_files = []


class DirObjectFileSystem(DirObject):
    """
    Specialized for the file system protocol.
    """
    def __init__(self, directory, local = True):
        DirObject.__init__(self)
        self.directory = directory
        self.watcher = None

        # Don't get an initial list of files for the remote directory.
        if not local:
            return
        
        # Get all the current files in the directory (and it's sub-directories).
        for (path_original, dirs, files) in os.walk(directory):
            for filename in files:

                fullpath_name = os.path.join(path_original, filename)
                partialpath_name = fullpath_name[(len(directory)+1):]

                # If this is a movie file, check for it's xml file
                # before adding it to the list of files.
                basename, ext = os.path.splitext(fullpath_name)
                ext = ext.lower()
                if ext in [".dax", ".spe", ".tif"]:
                    if not os.path.exists(basename + ".xml"):
                        continue

                f_object = FileObject(fullpath_name,
                                      partialpath_name,
                                      datetime.datetime.fromtimestamp(os.path.getmtime(fullpath_name)))
                self.old_files.append(f_object)

                
    def __del__(self):
        # Stop watchdog handler.
        pass                

    def shouldTransfer(self, file_object):
        dest_file = os.path.join(self.directory, file_object.getPartialPathName())
        if os.path.exists(dest_file):
            dest_file_time = datetime.datetime.fromtimestamp(os.path.getmtime(dest_file))
            if file_object.isNewerThan(dest_file_time):
                return True
            else:
                return False
        return True
        
    def transferFile(self, file_object):
        print "transferring", file_object
        
    def watchDirectory(self):
        # Register watchdog handler for new file/directory events & start.
        pass


class DirObjectSFTP(DirObject):
    """
    Specialized for a SFTP protocol.
    """
    def __init__(self, sftp_client):
        DirObject.__init__(self)
        self.sftp_client = sftp_client


class FileObject(object):
    """
    A class for keeping track of the relevant details of a single file.
    """
    def __init__(self, fullpath_name, partialpath_name, mtime):
        self.fullpath_name = fullpath_name
        self.mtime = mtime
        self.partialpath_name = partialpath_name

    def __eq__(self, other):
        return (self.partialpath_name == other.partialpath_name)
        
    def __str__(self):
        return self.partialpath_name + " " + self.mtime.strftime("%c")

    def getFullPathName(self):
        return self.fullpath_name
    
    def getPartialPathName(self):
        return self.partialpath_name
                                 
    def getMTime(self):
        return self.mtime
    
    def isNewerThan(self, a_time):
        return (self.mtime > a_time)


class Window(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.destination_dir_obj = None
        self.transfer_object = None
        self.source_dir_obj = None

        self.settings = QtCore.QSettings("Zhuang Lab", "hazelnut")
        
        # Configure UI.
        self.ui = hazelnutUi.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.startPushButton.setEnabled(False)
        
        # Load settings
        self.resize(self.settings.value("MainWindow/Size", self.size()))
        self.move(self.settings.value("MainWindow/Position", self.pos()))

        # Connect signals.
        self.ui.actionDestination.triggered.connect(self.handleDestination)
        self.ui.actionQuit.triggered.connect(self.handleQuit)
        self.ui.actionSource.triggered.connect(self.handleSource)

        self.ui.startPushButton.pressed.connect(self.handleStartButton)

        self.ui.transferQueueMVC.transferStarted.connect(self.handleStarted)
        self.ui.transferQueueMVC.transferStopped.connect(self.handleStopped)
        
    def closeEvent(self, event):
        self.settings.setValue("MainWindow/Size", self.size())
        self.settings.setValue("MainWindow/Position", self.pos())

    def doUpdate(self):
        if self.source_dir_obj is not None:
            self.ui.transferQueueMVC.clearFileObjects()
            for src_file in self.source_dir_obj.getAllFiles():
                self.ui.transferQueueMVC.addFileObject(src_file)

            if self.destination_dir_obj is not None:
                self.ui.transferQueueMVC.addDestination(self.destination_dir_obj)
                self.ui.startPushButton.setEnabled(True)

    def handleDestination(self, boolean):
        current_directory = ""
        if self.destination_dir_obj is not None:
            current_directory = self.destination_dir_obj.getDirectory()

        new_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       "Destination Directory",
                                                                       current_directory,
                                                                       QtWidgets.QFileDialog.ShowDirsOnly))
        if new_directory:
            self.destination_dir_obj = DirObjectFileSystem(new_directory, local = False)
            self.ui.destinationLabel.setText(new_directory)
            self.doUpdate()
    
    def handleQuit(self, boolean):
        self.close()

    def handleStartButton(self):
        self.ui.startPushButton.setEnabled(False)
        if self.ui.transferQueueMVC.amTransferring():
            self.ui.startPushButton.setText("Pausing")
            self.ui.transferQueueMVC.stopTransfer()
        else:
            self.ui.transferQueueMVC.startTransfer()

    def handleSource(self, boolean):
        current_directory = ""
        if self.source_dir_obj is not None:
            current_directory = self.source_dir_obj.getDirectory()
            
        new_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       "Source Directory",
                                                                       current_directory,
                                                                       QtWidgets.QFileDialog.ShowDirsOnly))
        if new_directory:
            self.source_dir_obj = DirObjectFileSystem(new_directory)
            self.ui.sourceLabel.setText(new_directory)
            self.doUpdate()

    def handleStarted(self):
        self.ui.startPushButton.setText("Stop")
        self.ui.startPushButton.setEnabled(True)
        
    def handleStopped(self):
        self.ui.startPushButton.setText("Start")
        self.ui.startPushButton.setEnabled(True)
        
        
if (__name__ == '__main__'):

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
