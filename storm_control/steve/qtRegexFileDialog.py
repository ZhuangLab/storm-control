#!/usr/bin/env python
#
# File dialog that allows for regex filtering.
#

from PyQt5 import QtCore, QtGui, QtWidgets

import re
import sys

import storm_control.steve.qtdesigner.qt_regex_file_dialog_ui as qtRegexFileDialogUi

def regexGetFileNames(caption = "Select File(s)", directory = None, extensions = None, regex = ""):
    fdialog = QRegexFileDialog(caption, directory, extensions, regex)
    fdialog.exec_()
    return fdialog.getSelectedFiles()

class RegexFilterModel(QtCore.QSortFilterProxyModel):
    ## __init__
    #
    # @param regex_string The default regular expression
    # @param parent (Optional) The PyQt parent of this object, default is None.
    #
    def __init__(self, regex_string, parent = None):
        QtCore.QSortFilterProxyModel.__init__(self, parent)
        self.regex = re.compile(regex_string)

    ## filterAcceptsRow
    #
    # @param source_row
    # @param source_parent
    #
    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        index0 = source_model.index(source_row, 0, source_parent)

        # Alway show directories
        if source_model.isDir(index0):
            return True

        # Filter files.
        filename = source_model.fileName(index0)
        if self.regex.match(filename) is not None:
            return True
        else:
            return False
        
class QRegexFileDialog(QtWidgets.QDialog):
    ## __init__
    #
    # @param caption The title of the dialog
    # @param directory The starting directory.
    # @param extensions The required file extensions
    # @param regex The default regular expression string
    # @param parent (Optional) The PyQt parent of this object, default is None.
    #
    def __init__(self, caption = "Select File(s)", directory = None, extensions = None, regex = "", parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.files_selected = None
        self.regex_str = regex

        # Create UI.
        self.ui = qtRegexFileDialogUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(caption)

        # Insert standard file dialog.
        self.fdialog = QtWidgets.QFileDialog()
        if directory is not None:
            self.fdialog.setDirectory(directory)
        self.fdialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if extensions is not None:
            self.fdialog.setNameFilters(extensions)
        self.ui.verticalLayout.addWidget(self.fdialog)
        self.setMinimumSize(self.fdialog.width() + 20, self.fdialog.height() + 40)

        # Set filter
        self.fdialog.setProxyModel(RegexFilterModel(regex))
        self.ui.nameLineEdit.setText(regex)
        
        # Connect file dialog signals.
        self.fdialog.accepted.connect(self.handleAccepted)
        self.fdialog.filesSelected.connect(self.handleSelected)        
        self.fdialog.rejected.connect(self.handleRejected)

        # Configure timer for regex updates.
        self.regex_timer = QtCore.QTimer()
        self.regex_timer.setInterval(200) # Delay between regexp changes and application of filter
        self.regex_timer.setSingleShot(True)
        self.regex_timer.timeout.connect(self.handleRegexTimer)

        # Connect regex line edit.
        self.ui.nameLineEdit.textChanged.connect(self.handleRegexChanged)

    ## getSelectedFiles
    #
    # @return The list of selected files, the frame number, the previous regex
    #
    def getSelectedFiles(self):
        return [self.files_selected, self.ui.frameNumSpinBox.value(), self.regex_str]

    ## handleAccepted
    #    
    def handleAccepted(self):
        self.close()

    ## handleRegexChanged
    #    
    def handleRegexChanged(self):
        self.regex_timer.start()

    ## handleRegexTimer
    #  
    def handleRegexTimer(self):
        new_regex_str = str(self.ui.nameLineEdit.text())
        try:
            self.fdialog.setProxyModel(RegexFilterModel(new_regex_str))
            self.ui.nameLineEdit.setStyleSheet("color: rgb(0, 0, 0);")
            self.regex_str = new_regex_str
        except:
            self.ui.nameLineEdit.setStyleSheet("color: rgb(255, 0, 0);")
            self.fdialog.setProxyModel(RegexFilterModel("")) # Display all files

    ## handleRejected
    #       
    def handleRejected(self):
        self.close()

    ## handleSelected
    #     
    def handleSelected(self, files_selected):
        self.files_selected = files_selected


## Stand alone test
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    dialog = QRegexFileDialog()
    dialog.show()
    app.exec_()

    
