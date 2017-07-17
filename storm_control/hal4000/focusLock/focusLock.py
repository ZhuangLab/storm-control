#!/usr/bin/env python
"""
(single) focus lock.

Hazen 04/17
"""
import importlib

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.focusLock.lockControl as lockControl
import storm_control.hal4000.focusLock.lockDisplay as lockDisplay
import storm_control.hal4000.focusLock.lockModes as lockModes

# UI.
import storm_control.hal4000.qtdesigner.focuslock_ui as focuslockUi


class FocusLockView(halDialog.HalDialog):
    """
    Manages the focus lock GUI.

    Changes to the lock mode state are expected to go through the
    LockControl class, rather than being done by directly working
    with the lock mode.
    """
    jump = QtCore.pyqtSignal(float)
    lockStarted = QtCore.pyqtSignal(bool)
    lockTarget = QtCore.pyqtSignal(float)
    modeChanged = QtCore.pyqtSignal(object)

    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.current_mode = None
        self.modes = []
        self.parameters = params.StormXMLObject()

        self.ui = focuslockUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Add parameters
        self.parameters.add(params.ParameterFloat(description = "Z stage jump size",
                                                  name = "jump_size",
                                                  value = 0.1))
        
        # Set up lock display.
        self.lock_display = lockDisplay.LockDisplay(configuration = configuration,
                                                    jump_signal = self.jump,
                                                    parent = self)
        layout = QtWidgets.QGridLayout(self.ui.lockDisplayWidget)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.lock_display)

        # Configure modes.
        lockModes.FindSumMixin.addParameters(self.parameters)
        lockModes.LockedMixin.addParameters(self.parameters)
        lockModes.ScanMixin.addParameters(self.parameters)
        for mode_class_name in configuration.get("lock_modes").split(","):
            a_class = getattr(lockModes, mode_class_name.strip())
            a_object = a_class(parameters = self.parameters,
                               parent = self)
            self.ui.modeComboBox.addItem(a_object.getName())
            self.modes.append(a_object)

        # Set parameters values based on the config file parameters.
        c_params = configuration.get("parameters")
        for attr in params.difference(c_params, self.parameters):
            print(attr, c_params.get(attr))
            self.parameters.setv(attr, c_params.get(attr))
        self.newParameters(self.parameters)

        # Connect signals.
        self.ui.jumpNButton.clicked.connect(self.handleJumpNButton)
        self.ui.jumpPButton.clicked.connect(self.handleJumpPButton)
        self.ui.lockButton.clicked.connect(self.handleLockButton)
        self.ui.lockTargetSpinBox.valueChanged.connect(self.handleLockTarget)
        self.ui.modeComboBox.currentIndexChanged.connect(self.handleModeComboBox)

        self.setEnabled(False)

    def amLocked(self):
        return self.ui.lockButton.isChecked()
    
    def getParameters(self):
        return self.parameters

    def handleJumpNButton(self):
        self.jump.emit(-self.ui.jumpSpinBox.value())

    def handleJumpPButton(self):
        self.jump.emit(self.ui.jumpSpinBox.value())

    def handleLockButton(self):
        
        # This is called after the button's state has changed.
        if self.amLocked():
            self.ui.lockButton.setText("Unlock")
            self.lockStarted.emit(True)
        else:
            self.ui.lockButton.setText("Lock")
            self.lockStarted.emit(False)

    def handleLockTarget(self, new_target):
        # For convenience targets appear in the GUI as nanometers, but
        # the focus lock uses microns.
        self.lockTarget.emit(0.001 * new_target)
            
    def handleModeComboBox(self, index):

        # Clean up previous mode.
        if self.current_mode is not None:

            # This will turn off the lock, if it is on.
            if self.amLocked():
                self.ui.lockButton.click()

            # Disconnect signals.
            self.current_mode.lockTarget.disconnect(self.setLockTargetSpinBox)
            self.current_mode.goodLock.disconnect(self.lock_display.handleGoodLock)

        # Storing the modes in data in the combobox does not seem to work
        # as it looks like copies of the mode get stored, messing up
        # newParameters().
        self.current_mode = self.modes[index]
        self.ui.lockButton.setEnabled(self.current_mode.shouldEnableLockButton())

        # Connect signals.
        self.current_mode.lockTarget.connect(self.setLockTargetSpinBox)
        self.current_mode.goodLock.connect(self.lock_display.handleGoodLock)

        self.modeChanged.emit(self.current_mode)

    def handleTCPMessage(self, message):
        #
        # Technically you can't change the focus lock mode or locked status
        # via TCP, but this ability is necessary for unit tests..
        #
        tcp_message = message.getData()["tcp message"]
        if tcp_message.isType("Set Focus Lock Mode"):
            if tcp_message.isTest():
                return True

            mode_name = tcp_message.getData("mode_name")
            locked = tcp_message.getData("locked")

            for i in range(self.ui.modeComboBox.count()):
                if (mode_name == self.ui.modeComboBox.itemText(i)):
                    self.ui.modeComboBox.setCurrentIndex(i)
                    if locked and not self.amLocked() and self.ui.lockButton.isEnabled():
                        self.ui.lockButton.click()
                    return True

            tcp_message.setError(True, "Requested mode '" + mode_name + "' not found.")
            return True
        
        else:
            return False

    def newParameters(self, parameters):
        for attr in params.difference(parameters, self.parameters):
            self.parameters.setv(attr, parameters.get(attr))
        self.lock_display.newParameters(parameters)
        for mode in self.modes:
            mode.newParameters(self.parameters)

    def setFunctionality(self, name, functionality):
        #
        # If this is the QPD and 'minimum_sum' (to be considered locked) was
        # not specified in the config file then use the QPDs 'sum_warning_low'
        # parameter as the minimum sum.
        #
        if (name == "qpd"):
            for pname in [lockModes.LockedMixin.lm_pname, lockModes.ScanMixin.sm_pname]:
                if (self.parameters.get(pname + ".minimum_sum") == -1.0):
                    self.parameters.setv(pname + ".minimum_sum", functionality.getParameter("sum_warning_low"))

        self.lock_display.setFunctionality(name, functionality)

        # Enable UI if we have everything we need to work. Also call newParameters()
        # so that the 'minimum_sum' is set.
        if self.lock_display.haveAllFunctionalities():
            self.setEnabled(True)
            self.newParameters(self.parameters)

    def setLockTargetSpinBox(self, new_value):
        self.ui.lockTargetSpinBox.valueChanged.disconnect(self.handleLockTarget)
        self.ui.lockTargetSpinBox.setValue(int(1000.0 * new_value))
        self.ui.lockTargetSpinBox.valueChanged.connect(self.handleLockTarget)

    def show(self):
        super().show()
        self.setFixedSize(self.width(), self.height())

    def start(self):
        if (self.ui.modeComboBox.currentIndex() != 0):
            self.ui.modeComboBox.setCurrentIndex(0)
        else:
            self.handleModeComboBox(0)

        
class FocusLock(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.control = lockControl.LockControl()
        self.view = FocusLockView(module_name = self.module_name,
                                  configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " focus lock")

        # Connect signals.
        self.control.controlMessage.connect(self.handleControlMessage)
        self.view.jump.connect(self.control.handleJump)
        self.view.lockStarted.connect(self.control.handleLockStarted)
        self.view.lockTarget.connect(self.control.handleLockTarget)
        self.view.modeChanged.connect(self.control.handleModeChanged)

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleControlMessage(self, message):
        self.sendMessage(message)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.control.setFunctionality(message.getData()["extra data"],
                                          response.getData()["functionality"])
            self.view.setFunctionality(message.getData()["extra data"],
                                       response.getData()["functionality"])
            
    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("timing"):
                self.control.setTimingFunctionality(message.getData()["properties"]["functionality"])

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Focus Lock",
                                                           "item data" : "focus lock"}))

            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))

        elif message.isType("configure2"):
            
            # Get functionalities. Do this here because the modules that provide these functionalities
            # will likely need functionalities from other modules. The IR laser for example might
            # need a functionality from a DAQ module.
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("ir_laser"),
                                                           "extra data" : "ir_laser"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("qpd"),
                                                           "extra data" : "qpd"}))
            
            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("z_stage"),
                                                           "extra data" : "z_stage"}))
            
        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("show"):
            if (message.getData()["show"] == "focus lock"):
                self.view.show()

        elif message.isType("start"):
            self.view.start()
            self.control.start()
            if message.getData()["show_gui"]:
                self.view.showIfVisible()

        elif message.isType("start film"):
            self.control.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            self.control.stopFilm()
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.view.getParameters().copy()}))
            lock_good = params.ParameterSetBoolean(name = "good_lock",
                                                   value = self.control.isGoodLock())
            lock_mode = params.ParameterString(name = "lock_mode",
                                               value = self.control.getLockModeName())
            lock_sum = params.ParameterFloat(name = "lock_sum",
                                                value = self.control.getQPDSumSignal())
            lock_target = params.ParameterFloat(name = "lock_target",
                                                value = self.control.getLockTarget())
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"acquisition" : [lock_good,
                                                                                       lock_mode,
                                                                                       lock_sum,
                                                                                       lock_target]}))

        elif message.isType("tcp message"):

            # See control handles this message.
            handled = self.control.handleTCPMessage(message)

            # If not, check view.
            if not handled:
                handled = self.view.handleTCPMessage(message)

            # Mark if we handled the message.
            if handled:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"handled" : True}))

