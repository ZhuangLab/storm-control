#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest

def test_hal_gui():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "GUITest",
            test_module = "storm_control.test.hal.gui_test",
            show_gui = True)

if (__name__ == "__main__"):
    test_hal_gui()
