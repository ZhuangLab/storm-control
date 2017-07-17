#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest

def test_hal_lock_config1():
    halTest(config_xml = "none_config_lock_check.xml",
            class_name = "LockConfigTest1",
            test_module = "storm_control.test.hal.config_tests")

if (__name__ == "__main__"):
    test_hal_lock_config1()
