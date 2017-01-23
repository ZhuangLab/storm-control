#
# A very simple test of HAL (in emulation mode).
#

from PyQt5 import QtCore
import time

import pytestqt

import storm_control.hal4000.hal_4000 as hal4000
import storm_control.sc_library.parameters as params

def test_hal_starts(qtbot):

    # Load 'none' hardware configuration.
    none_hardware = params.hardware("../hal4000/xml/none_hardware.xml")

    # Load general parameters.
    general_parameters = params.halParameters("../hal4000/settings_default.xml")
    general_parameters.set("film.logfile", "./logfile.txt")

    # Start HAL.
    hal = hal4000.Window(none_hardware, general_parameters)
    
    params.setDefaultParameters(general_parameters)

    # Load 'none' parameters.
    none_parameters = params.halParameters("./linux_default.xml")

    hal.parameters_box.addParameters(none_parameters)
    hal.toggleSettings()
    hal.show()

    # Test
    qtbot.addWidget(hal)
    qtbot.mouseClick(hal.ui.menuFile, QtCore.Qt.LeftButton)
    qtbot.keyClick(hal.ui.menuFile, QtCore.Qt.Key_Up)
    qtbot.keyClick(hal.ui.menuFile, QtCore.Qt.Key_Enter)
    qtbot.waitSignal(hal.destroyed, 10000)
    

