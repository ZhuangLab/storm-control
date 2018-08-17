#!/usr/bin/env python
"""
Hand run tests, not designed for CI as they will take a 
while to run.
"""

from storm_control.test.hal.standardHalTest import halTest


def dave_sequence():
    halTest(config_xml = "none_tcp_config.xml",
            class_name = "StandardDaveSequence1",
            test_module = "storm_control.test.hal.manual_tcp_tests")
    
    
def movie_single_camera(random_pause = False):
    if random_pause:
        halTest(config_xml = "none_tcp_config_random_pause.xml",
                class_name = "TakeMovie1",
                test_module = "storm_control.test.hal.manual_tcp_tests")
    else:
        halTest(config_xml = "none_tcp_config.xml",
                class_name = "TakeMovie1",
                test_module = "storm_control.test.hal.manual_tcp_tests")

        
def stage_move():
    halTest(config_xml = "none_tcp_config.xml",
            class_name = "MoveStage1",
            test_module = "storm_control.test.hal.manual_tcp_tests")

   
        
    
if (__name__ == "__main__"):
    dave_sequence()
    #movie_single_camera()
    #stage_move()

