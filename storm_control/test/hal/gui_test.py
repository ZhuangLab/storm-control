#!/usr/bin/env python

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testing as testing

class GUITest(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.Timer(timeout = 1000)]
