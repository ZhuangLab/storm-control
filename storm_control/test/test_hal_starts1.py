#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest

def test_hal_starts():
    halTest(config_xml = "none_classic_config.xml",
            test_module = "storm_control.hal4000.testing.testing")
    
if (__name__ == "__main__"):
    test_hal_starts()
