#!/usr/bin/env python
"""
File dialog that allows for regex filtering.

Hazen 10/18
"""
import re
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.qtdesigner.qt_regex_file_dialog_ui as qtRegexFileDialogUi


def regexGetFileNames(caption = "Select File(s)", directory = None, extensions = None, regex = ""):
    fdialog = QRegexFileDialog(caption = caption,
                               directory = directory,
                               extensions = extensions,
                               regex = regex)
    fdialog.exec_()
    return fdialog.getSelectedFiles()


class RegexFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, regex_string = None, **kwds):
        super().__init__(**kwds)

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


class QRegexFileDialog(QtWidgets.QDialog):

    def __init__(self, caption = "Select File(s)", directory = None, extensions = None, regex = "", **kwds):
        super().__init__(**kwds)

        self.files_selected = None
        self.regex_str = regex

        # Create UI.
        self.ui = qtRegexFileDialogUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(caption)

        # Insert standard file dialog.
        self.fdialog = QtWidgets.QFileDialog()
        self.fdialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
        if directory is not None:
            self.fdialog.setDirectory(directory)
        self.fdialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if extensions is not None:
            self.fdialog.setNameFilters(extensions)
        self.ui.verticalLayout.addWidget(self.fdialog)

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

    def getSelectedFiles(self):
        return [self.files_selected, self.ui.frameNumSpinBox.value(), self.regex_str]

    def handleAccepted(self):
        self.close()

    def handleRegexChanged(self):
        self.regex_timer.start()

    def handleRegexTimer(self):
        new_regex_str = str(self.ui.nameLineEdit.text())
        try:
            self.fdialog.setProxyModel(RegexFilterModel(new_regex_str))
            self.ui.nameLineEdit.setStyleSheet("color: rgb(0, 0, 0);")
            self.regex_str = new_regex_str
        except:
            self.ui.nameLineEdit.setStyleSheet("color: rgb(255, 0, 0);")
            self.fdialog.setProxyModel(RegexFilterModel("")) # Display all files

    def handleRejected(self):
        self.close()

    def handleSelected(self, files_selected):
        self.files_selected = files_selected


## Stand alone test
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = QRegexFileDialog()
    dialog.show()
    app.exec_()

    
