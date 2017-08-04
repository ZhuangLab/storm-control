#!/usr/bin/env python
#
# Handles the destination dialog interface.
#
# Hazen 08/16
#

import paramiko
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import qtdesigner.destination_ui as destinationUi


class DestinationDialog(QtWidgets.QDialog):

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.destination_directory = ""
        self.transfer_mode = "sftp"

        # Configure UI.
        self.ui = destinationUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.handleSFTPButton()
        
        # Connect signals.
        self.ui.directoryButton.pressed.connect(self.handleDirectoryButton)
        self.ui.sftpButton.pressed.connect(self.handleSFTPButton)
        self.ui.shareButton.pressed.connect(self.handleShareButton)

    def getDestination(self):
        if (self.transfer_mode == "file"):
            return [self.transfer_mode,
                    self.ui.directoryButton.text()]
        if (self.transfer_mode == "sftp"):
            return [self.transfer_mode,
                    self.ui.addressLineEdit.text(),
                    self.ui.usernameLineEdit.text(),
                    self.ui.directoryLineEdit.text()]

    def handleDirectoryButton(self):
        new_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       "Destination Directory",
                                                                       self.destination_directory,
                                                                       QtWidgets.QFileDialog.ShowDirsOnly))
        if new_directory:
            self.destination_directory = new_directory
            self.ui.directoryButton.setText(self.destination_directory)
        
    def handleSFTPButton(self):
        self.transfer_mode = "sftp"
        self.toggleEnabled(True)

    def handleShareButton(self):
        self.transfer_mode = "file"
        self.toggleEnabled(False)
        
    def toggleEnabled(self, enabled):
        self.ui.directoryButton.setEnabled(not enabled)
        self.ui.addressLineEdit.setEnabled(enabled)
        self.ui.usernameLineEdit.setEnabled(enabled)


class DestinationDialogHandler(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.accepted = True
        
        self.dest_dialog = DestinationDialog()

    def authHandler(self, title, instructions, prompt_list):
        responses = []
        for prompt in prompt_list:
            [resp, is_ok] = QtWidgets.QInputDialog.getText(self, title, prompt[0])
            print(resp)
            response.append(resp)
        return responses

    def getDestination(self):
        if self.dest_dialog.exec_():
            destination = self.dest_dialog.getDestination()
            
            # Special handling of SFTP.
            if (destination[0] == "sftp"):
                transport = paramiko.Transport((destination[1], 22))
                transport.start_client()
                try:
                    #
                    # FIXME: This does work not in PyQt, not sure why. This means
                    #        that user will have to use the command line.
                    #
                    #transport.auth_interactive(destination[2], self.authHandler)
                    transport.auth_interactive_dumb(destination[2])
                except paramiko.AuthenticationException as e:
                    print(e)
                    QtWidgets.QMessageBox.about(self, "Hazelnut", "SFTP authentication failed.")
                    return None
                return ["sftp", transport, destination[3]]
            else:
                return destination


if (__name__ == '__main__'):

    app = QtWidgets.QApplication(sys.argv)
    dest_dialog_handler = DestinationDialogHandler()
    dest_dialog_handler.show()
    sys.exit(app.exec_())
