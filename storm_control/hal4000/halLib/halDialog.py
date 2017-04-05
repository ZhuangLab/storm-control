#!/usr/bin/env python
"""

The standard HAL dialog box.

All the dialog boxes in HAL are sub-classes of this dialog box.

Hazen 2/17

"""

from PyQt5 import QtWidgets

import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon


class HalDialog(QtWidgets.QDialog):

    def __init__(self, module_name = None, **kwds):
        super().__init__(**kwds)
        self.ignore_close = True
        self.module_name = module_name

    def cleanUp(self, qt_settings):
        """
        Save GUI settings & close.
        """
        qt_settings.setValue(self.module_name + ".pos", self.pos())
        qt_settings.setValue(self.module_name + ".main", self.size())
        qt_settings.setValue(self.module_name + ".visible", self.isVisible())

        self.ignore_close = False
        self.close()
        
    def closeEvent(self, event):
        if self.ignore_close:
            event.ignore()
            self.hide()

    def halDialogInit(self, qt_settings, window_title):
        """
        This is called after sub class specific initialization
        to finish configuring the GUI.
        """
        self.setWindowIcon(qtAppIcon.QAppIcon())
        self.setWindowTitle(window_title)
                
        self.am_visible = (qt_settings.value(self.module_name + ".visible", "false") == "true")
        self.move(qt_settings.value(self.module_name + ".pos", self.pos()))
        self.resize(qt_settings.value(self.module_name + ".size", self.size()))

        # Connect signals.
        self.ui.okButton.clicked.connect(self.handleOk)

    def handleOk(self, boolean):
        self.hide()

    def showIfVisible(self):
        """
        Show the dialog if visible, this is called at the "start" stage.
        """
        if self.am_visible:
            self.show()        
