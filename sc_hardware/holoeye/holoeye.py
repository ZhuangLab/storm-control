#!/usr/bin/env python
#
## @file
#
# GUI for control of Holoeye SLM.
#
# Hazen 07/14
#

import sys

from PyQt4 import QtCore, QtGui

import sc_hardware.holoeye.holoeye_ui as holoeyeUi

## HoloeyeDialog
#
# The GUI for controlling what is displayed on the Holoeye.
#
class HoloeyeDialog(QtGui.QDialog):

    ## __init__
    #
    # @param parent (Optional) default is none.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        # UI setup.
        self.ui = holoeyeUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Connect signals.
        if parent is not None:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.hide)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.close)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dialog = HoloeyeDialog()
    dialog.show()
    sys.exit(app.exec_())
