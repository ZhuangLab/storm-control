#
# A very simple test of Dave.
#

from PyQt5 import QtCore
import time

import pytestqt

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.dave.dave as dave

def test_dave_starts(qtbot):

    parameters = params.parameters("./dave_xml/test_default.xml")
    hdebug.startLogging(parameters.get("directory") + "logs/", "dave")
    mainw = dave.Dave(parameters)
    mainw.show()

    qtbot.addWidget(mainw)

    # Run for about 0.5 seconds.
    qtbot.wait(500)

