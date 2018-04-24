#!/usr/bin/env python
"""
Test that software starts in various configurations.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_starts_1():
    halTest(config_xml = "none_classic_config.xml",
            test_module = "storm_control.hal4000.testing.testing")


def test_hal_starts_2():
    halTest(config_xml = "none_classic_dual_config.xml",
            test_module = "storm_control.hal4000.testing.testing")    


def test_hal_starts_3():
    halTest(config_xml = "none_detached_config.xml",
            test_module = "storm_control.hal4000.testing.testing")


def test_hal_starts_4():
    halTest(config_xml = "none_detached_dual_config.xml",
            test_module = "storm_control.hal4000.testing.testing")


if (__name__ == "__main__"):
    for i in range(50):
        test_hal_starts_1()
        
