#!/usr/bin/env python
"""

Heuristically programmed ALgorithmic STORM setup control.

This module handles setup, clean up and message passing
between the various sub-modules that define the 
behavior. Each of these modules must be a sub-class of
the HalModule class in halLib.halModule. Setup specific
configuration is provided by a 'XX_config.xml' file
examples of which can be found in the xml folder.

In addition this module handles drag/drops and
the film notes QTextEdit.

Jeff 03/14
Hazen 01/17

"""

from collections import deque
import importlib
import os
import time

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.hgit as hgit
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon


app = None

#
# Main window controller.
#
class HalController(halModule.HalModule):
    """
    HAL main window controller.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        if (module_params.get("ui_type") == "classic"):
            self.view = ClassicView(module_params = module_params,
                                    qt_settings = qt_settings,
                                    **kwds)
        else:
            self.view = DetachedView(module_params = module_params,
                                     qt_settings = qt_settings,
                                     **kwds)

        self.view.guiMessage.connect(self.handleGuiMessage)

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleGuiMessage(self, message):
        """
        This just passes through the messages from the GUI after 
        correcting the source.
        """
        self.sendMessage(message)

    def processMessage(self, message):

        if message.isType("add to menu"):
            self.view.addMenuItem(message.getData()["item name"],
                                  message.getData()["item data"])

        elif message.isType("add to ui"):
            [module, parent_widget] = message.getData()["ui_parent"].split(".")
            if (module == self.module_name):
                self.view.addUiWidget(parent_widget,
                                      message.getData()["ui_widget"],
                                      message.getData().get("ui_order"))

        elif message.isType("change directory"):
            self.view.setFilmDirectory(message.getData()["directory"])
                        
        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.addMenuItems()
                self.view.addWidgets()
                self.view.show()
                
            self.sendMessage(halMessage.HalMessage(m_type = "change directory",
                                                   data = {"directory" : self.view.getFilmDirectory()}))

        elif message.isType("start film"):
            self.view.startFilm(message.getData()["film settings"])

        elif message.isType("stop film"):
            self.view.stopFilm()
            notes_param = params.ParameterString(name = "notes",
                                                 value = self.view.getNotesEditText())
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"acquisition" : [notes_param]}))
            
        elif message.isType("tests done"):
            self.view.close()

#
# Main window View.
#
class HalView(QtWidgets.QMainWindow):
    """
    HAL main window view.
    """
    guiMessage = QtCore.pyqtSignal(object)

    def __init__(self, module_name = None, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
                
        self.close_now = False
        self.close_timer = QtCore.QTimer(self)
        self.film_directory = module_params.get("directory")
        self.menu_items_to_add = []
        self.module_name = module_name
        self.widgets_to_add = []

        # Configure UI.
        if self.classic_view:
            import storm_control.hal4000.qtdesigner.hal4000_ui as hal4000Ui            
        else:
            import storm_control.hal4000.qtdesigner.hal4000_detached_ui as hal4000Ui
            
        self.ui = hal4000Ui.Ui_MainWindow()
        self.ui.setupUi(self)

        # Create layout for the cameraFrame.
        if self.classic_view:
            vbox_layout = QtWidgets.QVBoxLayout(self.ui.cameraFrame)
            vbox_layout.setContentsMargins(0,0,0,0)
            vbox_layout.setSpacing(0)
            self.ui.cameraFrame.setLayout(vbox_layout)

        # Create layout for settings, film, etc..
        vbox_layout = QtWidgets.QVBoxLayout(self.ui.containerWidget)
        vbox_layout.setContentsMargins(0,0,0,0)
        vbox_layout.setSpacing(0)
        self.ui.containerWidget.setLayout(vbox_layout)
                
        # Set icon.
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Set title
        title = module_params.get("setup_name")
        if (hgit.getBranch().lower() != "master"):
            title += " (" + hgit.getBranch() + ")"
        self.setWindowTitle(title)

        # Configure based on saved settings.
        self.move(qt_settings.value(self.module_name + ".pos", self.pos()))
        self.resize(qt_settings.value(self.module_name + ".size", self.size()))
        self.xml_directory = str(qt_settings.value(self.module_name + ".xml_directory",
                                                   self.film_directory))
        
        # ui signals
        self.ui.actionDirectory.triggered.connect(self.handleDirectory)
        self.ui.actionSettings.triggered.connect(self.handleSettings)
        self.ui.actionShutter.triggered.connect(self.handleShutters)
        self.ui.actionQuit.triggered.connect(self.handleQuit)

        # Configure close timer.
        self.close_timer.setInterval(5)
        self.close_timer.timeout.connect(self.handleCloseTimer)
        self.close_timer.setSingleShot(True)

    def addMenuItem(self, item_name, item_data):
        """
        A menu item (from another module) that should be added to the file menu.
        """
        self.menu_items_to_add.append([item_name, item_data])

    def addMenuItems(self):
        """
        This actually adds the items to the file menu.
        """
        if (len(self.menu_items_to_add) > 0):
            for item in sorted(self.menu_items_to_add, key = lambda x : x[0]):
                a_action = QtWidgets.QAction(self.tr(item[0]), self)
                self.ui.menuFile.insertAction(self.ui.actionQuit, a_action)
                a_action.triggered.connect(lambda x, item_data = item[1] : self.handleMenuMessage(item_data))
            self.ui.menuFile.insertSeparator(self.ui.actionQuit)
        
    def addUiWidget(self, parent_widget_name, ui_widget, ui_order):
        """
        A UI widget (from another module) to the list of widgets to add.
        """
        if ui_order is None:
            ui_order = 0
        self.widgets_to_add.append([parent_widget_name, ui_widget, ui_order])

    def addWidgets(self):
        """
        This actually adds the widgets to UI.
        """
        for to_add in sorted(self.widgets_to_add, key = lambda x: x[2]):
            [parent_widget_name, ui_widget] = to_add[:2]
            hal_widget = getattr(self.ui, parent_widget_name)
            ui_widget.setParent(hal_widget)
            layout = hal_widget.layout()
            layout.addWidget(ui_widget)
    
    def cleanUp(self, qt_settings):
        """
        Save GUI settings and close.
        """
        qt_settings.setValue(self.module_name + ".pos", self.pos())
        qt_settings.setValue(self.module_name + ".size", self.size())
        qt_settings.setValue(self.module_name + ".xml_directory", self.xml_directory)
        self.close_now = True
        self.close()

    def closeEvent(self, event):
        #
        # This is a little fiddly. Basically the problem is that we'll get event
        # if the user clicks on the X in the upper right corner of the window.
        # In that case we don't want to close right away as core needs some
        # time to clean up the modules. However we also get this event when
        # we call close() and at that point we do want to close.
        #
        # We use a timer with a small delay because without it it appeared
        # that this method was getting called twice with same event object when
        # we clicked on the X, and this meant that you had to click the X
        # twice.
        #
        if not self.close_now:
            event.ignore()
            self.close_timer.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):

        # Get filename(s)
        filenames = []
        for url in event.mimeData().urls():
            filenames.append(str(url.toLocalFile()))

        # Send message(s) with filenames.
        for filename in sorted(filenames):
            [file_type, error_text] = params.fileType(filename)
            if (file_type == "parameters"):
                self.xml_directory = os.path.dirname(filename)
                self.guiMessage.emit(halMessage.HalMessage(m_type = "new parameters file",
                                                           data = {"filename" : filename}))
            elif (file_type == "shutters"):
                self.xml_directory = os.path.dirname(filename)
                self.guiMessage.emit(halMessage.HalMessage(m_type = "new shutters file",
                                                           data = {"filename" : filename}))
            else:
                if error_text:
                    halMessageBox.halMessageBoxInfo("XML file parsing error " + error_text + ".")
                else:
                    halMessageBox.halMessageBoxInfo("File type not recognized.")

    def getFilmDirectory(self):
        return self.film_directory

    def getNotesEditText(self):
        return self.ui.notesEdit.toPlainText()
        
    def handleCloseTimer(self):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "close event",
                                                   sync = True))
            
    def handleDirectory(self, boolean):
        new_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                                   "New Directory",
                                                                   self.film_directory,
                                                                   QtWidgets.QFileDialog.ShowDirsOnly)
        if new_directory and os.path.exists(new_directory):
            self.film_directory = new_directory
            self.guiMessage.emit(halMessage.HalMessage(m_type = "change directory",
                                                       data = {"directory" : self.film_directory}))

    def handleMenuMessage(self, item_data):
        self.guiMessage.emit(halMessage.HalMessage(m_type = "show",
                                                   data = {"show" : item_data}))
        
    def handleSettings(self, boolean):
        parameters_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                    "New Settings",
                                                                    self.xml_directory, 
                                                                    "*.xml")[0]
        if parameters_filename:
            self.xml_directory = os.path.dirname(parameters_filename)
            self.guiMessage.emit(halMessage.HalMessage(m_type = "new parameters file",
                                                       data = {"filename" : parameters_filename}))

    def handleShutters(self, boolean):
        shutters_filename = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                                  "New Shutter Sequence", 
                                                                  self.xml_directory, 
                                                                  "*.xml")[0]
        if shutters_filename:
            self.xml_directory = os.path.dirname(shutters_filename)
            self.guiMessage.emit(halMessage.HalMessage(m_type = "new shutters file",
                                                       data = {"filename" : shutters_filename}))

    def handleQuit(self, boolean):
        self.close_now = True
        self.guiMessage.emit(halMessage.HalMessage(m_type = "close event",
                                                   sync = True))

    def setFilmDirectory(self, film_directory):
        self.film_directory = film_directory

    def startFilm(self, film_settings):
        pass

    def stopFilm(self):
        pass

        
class ClassicView(HalView):
    """
    The 'classic' main window view. The record button is handled
    by the camera view.
    """
    def __init__(self, **kwds):
        self.classic_view = True
        super().__init__(**kwds)

class DetachedView(HalView):
    """
    The 'detached' main window view. This includes a record
    button that this view has to handle.
    """
    def __init__(self, **kwds):
        self.classic_view = False
        super().__init__(**kwds)

        self.ui.recordButton.clicked.connect(self.handleRecordButton)

    def handleRecordButton(self, boolean):
        self.guiMessage.emit(self.ui.recordButton.getHalMessage())

    def startFilm(self, film_settings):
        self.ui.recordButton.startFilm(film_settings)

    def stopFilm(self):
        self.ui.recordButton.stopFilm()
        

#
# The core..
#
class HalCore(QtCore.QObject):
    """
    The core of it all. It sets everything else up, handles 
    the message passing and tears everything down.
    """
    def __init__(self, config = None,
                 parameters_file_name = None,
                 testing_mode = False,
                 show_gui = True,
                 **kwds):
        super().__init__(**kwds)

        self.modules = []
        self.module_name = "core"
        self.qt_settings = QtCore.QSettings("storm-control", "hal4000" + config.get("setup_name").lower())
        self.queued_messages = deque()
        self.queued_messages_timer = QtCore.QTimer(self)
        self.running = True # This is solely for the benefit of unit tests.
        self.sent_messages = []
        self.strict = config.get("strict", False)

        self.queued_messages_timer.setInterval(0)
        self.queued_messages_timer.timeout.connect(self.handleSendMessage)
        self.queued_messages_timer.setSingleShot(True)

        # Initialize messages.
        halMessage.initializeMessages()
        
        # Load all the modules.
        print("Loading modules")

        #
        # For HAL it is easier to just use a list of modules, but at initialization
        # we also send a dictionary with the module names as keys to all of the
        # modules
        #
        # In testing mode the testing.testing module may use the other modules to
        # spoof the message sources.
        #
        # During normal operation most inter-module communication is done using
        # messages. Modules may also request functionalities from other modules
        # that they can use to do specific tasks, such as daq output or displaying
        # the images from a camera.
        #
        all_modules = {}
        if testing_mode:
            all_modules["core"] = self
        else:
            all_modules["core"] = True

        #
        # Need to load HAL's main window first so that other GUI windows will
        # have the correct Qt parent.
        #
        module_names = sorted(config.get("modules").getAttrs())
        module_names.insert(0, module_names.pop(module_names.index("hal")))        
        for module_name in module_names:
            print("  " + module_name)

            # Get module specific parameters.
            module_params = config.get("modules").get(module_name)

            # Add the 'root' parameters to this module parameters
            # so that they are visible to the module.
            for root_param in config.getAttrs():
                if (root_param != "modules"):
                    module_params.add(root_param, config.getp(root_param))

            # Load the module.
            a_module = importlib.import_module(module_params.get("module_name"))
            a_class = getattr(a_module, module_params.get("class_name"))
            a_object = a_class(module_name = module_name,
                               module_params = module_params,
                               qt_settings = self.qt_settings)

            # If this is HAL's main window set the HalDialog qt_parent class
            # attribute so that any GUI QDialogs will have the correct Qt parent.
            if (module_name == "hal"):
                halDialog.HalDialog.qt_parent = a_object.view
                
            self.modules.append(a_object)
            if testing_mode:
                all_modules[module_name] = a_object
            else:
                all_modules[module_name] = True

        print("")

        # Connect signals.
        for module in self.modules:
            module.newMessage.connect(self.handleMessage)

        # Create messages.
        #
        # We do it this way with finalizers because otherwise all of these messages
        # would get queued first and the modules would not have a chance to insert
        # messages in between these messages.
        #
        # The actual sequence of sent messages is:
        #
        # 1. "configure1", tell modules to finish configuration.
        #    The message includes a dictionary of the names of
        #    all modules that were loaded.
        #
        # 2. "configure2", gives the modules a chance to 'react'
        #    based on what happened during configure1.
        #
        # 3. "configure3", gives the modules a chance to 'react'
        #    based on what happened during configure1.
        #
        # 4. "new parameters file", initial parameters (if any).
        #
        # 5. "start", tell the modules to start.
        #    This is the point where any GUI modules that are
        #    visible should call show().
        #
        message_chain = []

        # configure1.
        message_chain.append(halMessage.HalMessage(source = self,
                                                   m_type = "configure1",
                                                   data = {"all_modules" : all_modules}))

        # configure2.
        message_chain.append(halMessage.HalMessage(source = self,
                                                   m_type = "configure2"))

        # configure3.
        message_chain.append(halMessage.HalMessage(source = self,
                                                   m_type = "configure3"))
        
        # update default parameters.
        if parameters_file_name is not None:
            message_chain.append(halMessage.HalMessage(source = self,
                                                       m_type = "new parameters file",
                                                       data = {"parameters filename" : parameters_file_name,
                                                               "is_default" : True}))

        # start.
        #
        # It is safe to stop blocking Qt's last window closed behavior after
        # this message as HAL's main window will be open.
        #
        # If we run HAL from another module, in testing for example, app might
        # be none.
        #
        if app is not None:
            message_chain.append(halMessage.HalMessage(source = self,
                                                       m_type = "start",
                                                       data = {"show_gui" : show_gui},
                                                       sync = True,
                                                       finalizer = lambda : app.setQuitOnLastWindowClosed(True)))

        else:
           message_chain.append(halMessage.HalMessage(source = self,
                                                      m_type = "start",
                                                      data = {"show_gui" : show_gui},
                                                      sync = True))
           message_chain.append(halMessage.SyncMessage(source = self))

        self.handleMessage(halMessage.chainMessages(self.handleMessage,
                                                    message_chain))

    def close(self):
        """
        This is called by qtbot at the end of a test.
        """
        self.cleanUp()
        
    def cleanUp(self):
        for module in self.modules:
            module.cleanUp(self.qt_settings)
        print("Waiting for QThreadPool to finish.")
        halModule.threadpool.waitForDone()
        self.running = False
        print(" Dave? What are you doing Dave?")
        print("  ...")

    def findChild(self, qt_type, name, options = QtCore.Qt.FindChildrenRecursively):
        """
        Overwrite the QT version as the 'child' will be (hopefully) be in one of
        the modules.
        """
        for module in self.modules:
            print(module)
            m_child = module.findChild(qt_type, name, options)
            if m_child is not None:
                return m_child
        assert False, "UI element " + name + " not found."

    def handleErrors(self, message):
        """
        Handle errors in messages from 'core'
        """
        for m_error in message.getErrors():
            msg = "from '" + m_error.source + "' of type '" + m_error.message + "'!"

            # Just print the error and crash on exceptions.
            if m_error.hasException():
                m_error.printException()
                self.cleanUp()

            # Use a informational box for warnings.
            else:
                msg = "Got a warning" + msg
                halMessageBox.halMessageBoxInfo(msg)

    def handleMessage(self, message):
        """
        Adds a message to the queue of images to send.
        """
        # Check the message and it to the queue.
        if self.strict:
            if not message.m_type in halMessage.valid_messages:
                msg = "Invalid message type '" + message.m_type
                msg += "' received from " + message.getSourceName()
                raise halExceptions.HalException(msg)

            validator = halMessage.valid_messages[message.m_type].get("data")
            halMessage.validateData(validator, message)
            
        message.logEvent("queued")

        self.queued_messages.append(message)

        # Start the message timer, if it is not already running.
        self.startMessageTimer()

    def handleProcessed(self, message):
        """
        Removes a processed message from the queue of sent messages
        and performs message finalization.
        """

        # Remove message from list of sent messages.
        self.sent_messages.remove(message)

        # Disconnect messages processed signal.
        message.processed.disconnect(self.handleProcessed)
        
        # Call message finalizer.
        message.finalize()

        # Always exit on exceptions in strict mode.
        if self.strict and message.hasErrors():
            for m_error in message.getErrors():
                if m_error.hasException():
                    m_error.printException()
                    self.cleanUp()
                    return

        # Notify the sender if errors occured while processing the
        # message and exit if the sender doesn't handle the error.
        if message.hasErrors():
            if not message.getSource().handleErrors(sent_message):
                self.cleanUp()
                return

        # Check the responses if we are in strict mode.
        if self.strict:
            validator = halMessage.valid_messages[message.m_type].get("resp")
            for response in message.getResponses():
                halMessage.validateResponse(validator, message, response)

        # Notify the sender of any responses to the message.
        message.getSource().handleResponses(message)

        # Print a warning if the message was 'get functionality'
        # and there were no responses.
        if message.isType("get functionality") and not message.hasResponses():
            print(">> Warning functionality '" + message.getData()["name"] + "' not found!")
            hdebug.logText("no functionality " + message.getData()["name"])

        # Start message processing timer in case there are other messages
        # waiting for this message to get finalized.
        self.startMessageTimer()

    def handleResponses(self, message):
        """
        This is just a place holder. There should not be any responses
        to message from HalCore.
        """
        assert not message.hasResponses()

    def handleSendMessage(self):
        """
        Handle sending the current message to all the modules.
        """
        # Process the next message.
        if (len(self.queued_messages) > 0):
            cur_message = self.queued_messages.popleft()
            
            #
            # If this message requested synchronization and there are
            # pending messages then push it back into the queue.
            #
            if cur_message.sync and (len(self.sent_messages) > 0):
                print("> waiting for the following to be processed:")
                for message in self.sent_messages:
                    text = "  '" + message.m_type + "' from " + message.getSourceName() + ", "
                    text += str(message.getRefCount()) + " module(s) have not responded yet."
                    print(text)
                print("")
                self.queued_messages.appendleft(cur_message)
            
            #
            # Otherwise process the message.
            #
            else:
                print(cur_message.source.module_name + " '" + cur_message.m_type + "'")

                # Check for "closeEvent" message from the main window.
                if cur_message.isType("close event") and (cur_message.getSourceName() == "hal"):
                    self.cleanUp()
                    return

                else:
                    # Check for "sync" message, these don't actually get sent.
                    if cur_message.isType("sync"):
                        pass

                    # Otherwise send the message.
                    else:
                        cur_message.logEvent("sent")

                        cur_message.processed.connect(self.handleProcessed)
                        self.sent_messages.append(cur_message)
                        for module in self.modules:
                            cur_message.ref_count += 1
                            module.handleMessage(cur_message)

                    # Process any remaining messages with immediate timeout.
                    if (len(self.queued_messages) > 0):
                        self.startMessageTimer()

    def startMessageTimer(self, interval = 0):
        if not self.queued_messages_timer.isActive():
            self.queued_messages_timer.setInterval(interval)
            self.queued_messages_timer.start()


if (__name__ == "__main__"):

    # Use both so that we can pass sys.argv to QApplication.
    import argparse
    import sys

    # Get command line arguments..
    parser = argparse.ArgumentParser(description = 'STORM microscope control software')
    parser.add_argument('config', type = str, help = "The name of the configuration file to use.")
    parser.add_argument('--xml', dest = 'default_xml', type = str, required = False, default = None,
                        help = "The name of a settings xml file to use as the default.")

    args = parser.parse_args()
    
    # Start..
    app = QtWidgets.QApplication(sys.argv)

    # This keeps Qt from closing everything if a message box is displayed
    # before HAL's main window is shown.
    app.setQuitOnLastWindowClosed(False)

    # Splash Screen.
    pixmap = QtGui.QPixmap("splash.png")
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Load configuration.
    config = params.config(args.config)

    # Start logger.
    hdebug.startLogging(config.get("directory") + "logs/", "hal4000")
    
    # Setup HAL and all of the modules.
    hal = HalCore(config = config,
                  parameters_file_name = args.default_xml)

    # Hide splash screen and start.
    splash.hide()

    app.exec_()


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
