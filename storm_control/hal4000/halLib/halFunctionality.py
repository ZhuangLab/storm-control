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
    # This signal is sent by the module that sourced the
    # functionality to let it's users know that this
    # functionality is no longer valid. This could happen
    # for example with a camera when the parameters are
    # changed.
    invalid = QtCore.pyqtSignal()

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.hf_valid = True

    def isValid(self):
        return self.hf_valid

    def setInvalid(self):
        self.hf_valid = False
        self.invalid.emit()
