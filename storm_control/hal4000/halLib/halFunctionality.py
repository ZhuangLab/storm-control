#!/usr/bin/env python
"""
This is the base class for a HAL functionality. Typically these
are provided by a module to other modules that want to use some
of the hardware that the module controls.

Hazen 04/17
"""

from PyQt5 import QtCore

class HalFunctionality(QtCore.QObject):
    """
    Base class for a functionality that a module can provide.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
