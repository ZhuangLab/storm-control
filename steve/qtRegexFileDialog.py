#!/usr/bin/env python
#
# File dialog that allows for regex filtering.
#

from PyQt4 import QtCore, QtGui

import re
import sys

import qtdesigner.qt_regex_file_dialog_ui as qtRegexFileDialogUi


def regexGetOpenFileNames():
    fdialog = QRegexFileDialog()
    fdialog.exec_()
    return fdialog.getSelectedFiles()


class RegexFilterModel(QtGui.QSortFilterProxyModel):

    def __init__(self, regex_string, parent = None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.regex = re.compile(regex_string)

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

        
class QRegexFileDialog(QtGui.QDialog):

    def __init__(self, caption = "Select File(s)", directory = None, extensions = None, regex = "", parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.files_selected = None

        # Create UI.
        self.ui = qtRegexFileDialogUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(caption)

        # Insert standard file dialog.
        self.fdialog = QtGui.QFileDialog()
        if directory is not None:
            self.fdialog.setDirectory(directory)
        self.fdialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        if extensions is not None:
            self.fdialog.setFilter(extensions)
        self.ui.verticalLayout.addWidget(self.fdialog)
        self.setMinimumSize(self.fdialog.width() + 20, self.fdialog.height() + 40)

        # Set filter
        self.fdialog.setProxyModel(RegexFilterModel(""))

        # Connect file dialog signals.
        self.fdialog.accepted.connect(self.handleAccepted)
        self.fdialog.filesSelected.connect(self.handleSelected)        
        self.fdialog.rejected.connect(self.handleRejected)

        # Configure timer for regex updates.
        self.regex_timer = QtCore.QTimer()
        self.regex_timer.setInterval(200)
        self.regex_timer.setSingleShot(True)
        self.regex_timer.timeout.connect(self.handleRegexTimer)

        # Connect regex line edit.
        self.ui.nameLineEdit.textChanged.connect(self.handleRegexChanged)
        
    def getSelectedFiles(self):
        return self.files_selected
    
    def handleAccepted(self):
        self.close()

    def handleRegexChanged(self):
        self.regex_timer.start()
        
    def handleRegexTimer(self): 
        self.fdialog.setProxyModel(RegexFilterModel(str(self.ui.nameLineEdit.text())))
        
    def handleRejected(self):
        self.close()
        
    def handleSelected(self, files_selected):
        self.files_selected = map(str, files_selected)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    dialog = QRegexFileDialog()
    dialog.show()
    app.exec_()

    
