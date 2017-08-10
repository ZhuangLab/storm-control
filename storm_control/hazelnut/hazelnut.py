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
import shutil
import sys
import time
import watchdog
import watchdog.events
import watchdog.observers

from PyQt5 import QtCore, QtGui, QtWidgets

import destination
import qtdesigner.hazelnut_ui as hazelnutUi


class DirObject(object):
    movie_extensions = (".dax", ".inf", ".off", ".png", ".power", ".spe", ".tif", ".xml")
    """
    A class for doing several things.
    1. Source directory:
       a. Get list of files in directory on startup.
       b. Get new files that are added.
       c. Get creation / modification time of the files.

    2. Transfer directory.
       a. Check if the file needs to be transferred.
       b. Transfer a file.
       
    """
    def __init__(self):
        self.directory = ""
        self.files = []
        
    def getDirectory(self):
        return self.directory

    def getFiles(self):
        temp = self.files
        self.files = []
        return temp
    
    
class DirObjectFileSystem(DirObject):
    """
    Specialized for the file system protocol.
    """
    def __init__(self, directory, local = True):
        DirObject.__init__(self)
        self.directory = directory
        self.watcher = None

        # Don't watchdog remote directories.
        if not local:
            return

        self.watchDirectory(True)
                
    def addFile(self, fullpath_name):

        # Check to see that this is an xml file.
        [basename, ext] = os.path.splitext(fullpath_name)
        ext = ext.lower()
        if not (ext == ".xml"):
            return

        # If it is, add it and any related files to the current list of files.
        for ext in DirObject.movie_extensions:
            fullpath_name = basename + ext
            if os.path.exists(fullpath_name):
                partialpath_name = fullpath_name[(len(self.directory)+1):]
                f_object = FileObject(fullpath_name,
                                      partialpath_name,
                                      datetime.datetime.fromtimestamp(os.path.getmtime(fullpath_name)))
                self.files.append(f_object)

    def getCurrentFiles(self):
        """
        Get all the current files in the directory (and it's sub-directories).
        """
        for (path_original, dirs, files) in os.walk(self.directory):
            for filename in files:
                self.addFile(os.path.join(path_original, filename))
                
    def shouldTransfer(self, file_object):
        dest_file = os.path.join(self.directory, file_object.getPartialPathName())
        if os.path.exists(dest_file):
            dest_file_time = datetime.datetime.fromtimestamp(os.path.getmtime(dest_file))
            if file_object.isNewerThan(dest_file_time):
                return True
            else:
                return False
        return True
        
    def transferFile(self, file_object, callback):
        """
        The callback function expects an integer in the range 0-100 that
        indicates the current progress of the transfer.
        """
        dest_file = os.path.join(self.directory, file_object.getPartialPathName())

        # For GUI testing.
        if True:
            for i in range(10):
                callback(10 * i)
                time.sleep(0.1)
            return

        # Make a directory if necessary first.
        #
        # FIXME: Limited to a single level?
        #
        dest_dir = os.path.dirname(dest_file)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Copy the file.
        shutil.copyfile(file_object.getFullPathName(), dest_file)
        
    def watchDirectory(self, start):

        # Start directory watchdog.
        if start:
            self.watcher = watchdog.observers.Observer()
            self.watcher.schedule(FileSystemWatcher(self),
                                  self.directory,
                                  recursive = True)
            self.watcher.start()

        # Stop directory watchdog.            
        else:
            self.watcher.stop()


class DirObjectSFTP(DirObject):
    """
    Specialized for a SFTP protocol.
    """
    def __init__(self, sftp_transport, destination_directory):
        DirObject.__init__(self)
        self.sftp_transport = sftp_transport
        self.sftp_client = self.sftp_transport.open_sftp_client()

        # Check that the destination directory exists.
        try:
            sftp_attr = self.sftp_client.chdir(destination_directory)
        except IOError as e:
            print(e)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText(destination_directory + " does not exist?")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.exec_()
            self.sftp_client = None
            
    def shouldTransfer(self, file_object):
        try:
            sftp_attr = self.sftp_client.stat(file_object.getPartialPathName())
        except IOError:
            return True

        print(sftp_attr)
        dest_file_time = datetime.datetime.fromtimestamp(sftp_attr.st_mtime)
        if file_object.isNewerThan(dest_file_time):
            return True
        else:
            return False
        
    def transferFile(self, file_object, callback):
        assert (self.sftp_client is not None)
        
        sftp_callback = lambda bytes_trans, bytes_total : callback(int(100.0 * bytes_trans/bytes_total))
        self.sftp_client.put(file_object.getFullPathName(),
                             file_object.getPartialPathName(),
                             callback = sftp_callback)

        
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


class FileSystemWatcher(watchdog.events.FileSystemEventHandler):

    def __init__(self, dir_object):
        watchdog.events.FileSystemEventHandler.__init__(self)
        self.dir_object = dir_object
        
    def on_created(self, event):
        self.dir_object.addFile(event.src_path)


class Window(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.destination_dir_obj = None
        self.dhandler = destination.DestinationDialogHandler()
        self.source_dir_obj = None
        self.update_timer = QtCore.QTimer(self)

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

        # Configure update timer.
        self.update_timer.setInterval(500)
        self.update_timer.timeout.connect(self.handleUpdateTimer)
        
    def closeEvent(self, event):
        if self.source_dir_obj is not None:
            self.source_dir_obj.watchDirectory(False)
            
        self.settings.setValue("MainWindow/Size", self.size())
        self.settings.setValue("MainWindow/Position", self.pos())

    def handleDestination(self, boolean):
        dest = self.dhandler.getDestination()
        if dest is not None:
            if (dest[0] == "file"):
                self.destination_dir_obj = DirObjectFileSystem(dest[1], local = False)
                self.ui.destinationLabel.setText(dest[1])
            if (dest[0] == "sftp"):
                self.destination_dir_obj = DirObjectSFTP(dest[1], dest[2])
                self.ui.destinationLabel.setText(str(dest[2]))
            self.ui.transferQueueMVC.addDestination(self.destination_dir_obj)
            if self.source_dir_obj is not None:
                self.ui.startPushButton.setEnabled(True)

    def handleQuit(self, boolean):
        self.close()

    def handleStartButton(self):
        self.ui.startPushButton.setEnabled(False)
        if self.ui.transferQueueMVC.amTransferring():
            self.ui.startPushButton.setText("Pausing")
            self.ui.transferQueueMVC.stopTransfer()
        else:
            self.ui.transferQueueMVC.startTransfer()
            self.ui.actionDestination.setEnabled(False)
            self.ui.actionSource.setEnabled(False)

    def handleSource(self, boolean):
        current_directory = ""
        if self.source_dir_obj is not None:
            current_directory = self.source_dir_obj.getDirectory()
            
        new_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       "Source Directory",
                                                                       current_directory,
                                                                       QtWidgets.QFileDialog.ShowDirsOnly))
        if new_directory:

            # Stop old directory watcher.
            if self.source_dir_obj is not None:
                self.source_dir_obj.watchDirectory(False)
            
            self.source_dir_obj = DirObjectFileSystem(new_directory)
            self.source_dir_obj.getCurrentFiles()
            self.ui.sourceLabel.setText(new_directory)
            self.ui.transferQueueMVC.clearFileObjects()
            self.handleUpdateTimer()
            self.update_timer.start()

    def handleStarted(self):
        self.ui.startPushButton.setText("Stop")
        self.ui.startPushButton.setEnabled(True)
        
    def handleStopped(self):
        self.ui.startPushButton.setText("Start")
        self.ui.startPushButton.setEnabled(True)
        self.ui.actionDestination.setEnabled(True)
        self.ui.actionSource.setEnabled(True)

    def handleUpdateTimer(self):
        for src_file in self.source_dir_obj.getFiles():
            self.ui.transferQueueMVC.addFileObject(src_file)        

        
if (__name__ == '__main__'):

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
