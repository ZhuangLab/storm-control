#
# A very simple test of zee-calibrator.
#

from PyQt5 import QtCore
import time

import pytestqt

import storm_control.zee_calibrator.main as zcal

def _test_zeecal_starts(qtbot):

    mainw = zcal.Window()
    mainw.show()

    qtbot.addWidget(mainw)

    # Run for about 0.5 seconds.
    qtbot.wait(500)
