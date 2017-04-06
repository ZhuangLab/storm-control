#
# A very simple test of Kilroy.
#

from PyQt5 import QtCore
import time

import pytestqt

import storm_control.sc_library.parameters as params
import storm_control.test as test

import storm_control.fluidics.kilroy as kilroy

def test_kilroy_starts(qtbot):

    parameters = params.parameters(test.kilroyXmlFilePathAndName("test_default.xml"))

    mainw = kilroy.StandAlone(parameters)
    mainw.show()

    qtbot.addWidget(mainw)

    # Run for about 0.5 seconds.
    qtbot.wait(500)

