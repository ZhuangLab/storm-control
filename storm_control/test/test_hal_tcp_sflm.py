#!/usr/bin/env python
"""
Test setting the focus lock mode.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_tcp_sflm_11():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetFocusLockMode1",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")
    

def test_hal_tcp_sflm_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetFocusLockMode2",
            test_module = "storm_control.test.hal.tcp_tests")
