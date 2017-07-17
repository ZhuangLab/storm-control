#!/usr/bin/env python

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test

#
# Check the default parameters.
#
class LockConfigTest1Action(testActions.GetParameters):

    def checkParameters(self):
        p = self.parameters
        
        assert(p.get("focuslock.locked.buffer_length") == 10)
        assert(p.get("focuslock.locked.offset_threshold") == 40.0)

class LockConfigTest1(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [LockConfigTest1Action(p_name = "default")]

