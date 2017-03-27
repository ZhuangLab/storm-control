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

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon


#
# Main window controller.
#
class HalController(halModule.HalModule):
    """
    HAL main window controller.

    This sends the following messages:
     'close event'
     'new directory'
     'new parameters file'
     'new shutters file'
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
        This just passes through the messages from the GUI.
        """
        self.newMessage.emit(message)

    def processL1Message(self, message):
        
        if (message.getType() == "add to ui"):
            [module, parent_widget] = message.data["ui_parent"].split(".")
            if (module == self.module_name):
                self.view.addUiWidget(parent_widget,
                                      message.data["ui_widget"],
                                      message.data.get("ui_order"))
                
        elif (message.getType() == "start"):
            self.view.addWidgets()
            self.view.show()


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
                self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "new parameters file",
                                                           data = {"filename" : filename}))
            elif (file_type == "shutters"):
                self.xml_directory = os.path.dirname(filename)
                self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "new shutters file",
                                                           data = {"filename" : filename}))
            else:
                if error_text:
                    halMessageBox.halMessageBoxInfo("XML file parsing error " + error_text + ".")
                else:
                    halMessageBox.halMessageBoxInfo("File type not recognized.")

    def handleCloseTimer(self):
        self.close_now = True
        self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "close event",
                                                   sync = True))
            
    def handleDirectory(self, boolean):
        new_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 
                                                                   "New Directory",
                                                                   self.film_directory,
                                                                   QtWidgets.QFileDialog.ShowDirsOnly)
        #
        # FIXME: Why do we have the existence check? Is it possible to get a directory that does not exist?
        #
        if new_directory and os.path.exists(new_directory):
            self.film_directory = new_directory
            self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "new directory",
                                                       data = {"directory" : self.film_directory}))

    def handleSettings(self, boolean):
        parameters_filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                    "New Settings",
                                                                    self.xml_directory, 
                                                                    "*.xml")[0]
        if parameters_filename:
            self.xml_directory = os.path.dirname(parameters_filename)
            self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "new parameters file",
                                                       data = {"filename" : parameters_filename}))

    def handleShutters(self, boolean):
        shutters_filename = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                                  "New Shutter Sequence", 
                                                                  self.xml_directory, 
                                                                  "*.xml")[0]
        if shutters_filename:
            self.xml_directory = os.path.dirname(shutters_filename)
            self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "new shutters file",
                                                       data = {"filename" : shutters_filename}))

    def handleQuit(self, boolean):
        self.close_now = True
        self.guiMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "close event",
                                                   sync = True))

#    def setFilmDirectory(self, film_directory):
#        self.film_directory = film_directory

        
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


#
# The core..
#
class HalCore(QtCore.QObject):
    """
    The core of it all. It sets everything else up, handles 
    the message passing and tears everything down.

    This sends the following messages:
     'configure1'
     'configure2'
     'new parameters file'
     'start'
    """
    def __init__(self, config = None, parameters_file_name = None, **kwds):
        super().__init__(**kwds)

        self.modules = []
        self.module_name = "core"
        self.qt_settings = QtCore.QSettings("storm-control", "hal4000" + config.get("setup_name").lower())
        self.queued_messages = deque()
        self.queued_messages_timer = QtCore.QTimer(self)
        self.sent_messages = []

        self.queued_messages_timer.setInterval(0)
        self.queued_messages_timer.timeout.connect(self.handleSendMessage)
        self.queued_messages_timer.setSingleShot(True)

        # Load all the modules.
        module_names = []
        print("Loading modules")
        for module_name in config.get("modules").getAttrs():
            print("  " + module_name)
            module_names.append(module_name)

            # Get module specific parameters.
            module_params = config.get("modules").get(module_name)

            # Add the 'root' parameters to this module parameters
            # so that they are visible to the module.
            for root_param in config.getAttrs():
                if (root_param != "modules"):
                    module_params.add(root_param, config.getp(root_param))

            # Load the module.
            a_module = importlib.import_module("storm_control.hal4000." + module_params.get("module_name"))
            a_class = getattr(a_module, module_params.get("class_name"))
            self.modules.append(a_class(module_name = module_name,
                                        module_params = module_params,
                                        qt_settings = self.qt_settings))
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
        # 3. "start", tell the modules to start.
        #    This is the point where any GUI modules that are
        #    visible should call show().
        #
        # 4. "new parameters file", initial parameters (if any).
        #
        if parameters_file_name is not None:
            newp_message = halMessage.HalMessage(source = self,
                                                 m_type = "new parameters file",
                                                 data = {"filename" : parameters_file_name})
            start_message = halMessage.HalMessage(source = self,
                                                  m_type = "start",
                                                  sync = True,
                                                  finalizer = lambda: self.handleMessage(newp_message))
        else:
            start_message = halMessage.HalMessage(source = self,
                                                  m_type = "start",
                                                  sync = True)

        config2_message = halMessage.HalMessage(source = self,
                                                m_type = "configure2",
                                                finalizer = lambda: self.handleMessage(start_message))
        
        config1_message = halMessage.HalMessage(source = self,
                                                m_type = "configure1",
                                                data = {"module_names" : module_names},
                                                finalizer = lambda: self.handleMessage(config2_message))
        
        self.handleMessage(config1_message)

    def cleanup(self):
        print(" Dave? What are you doing Dave?")
        print("  ...")
        for module in self.modules:
            module.cleanUp(self.qt_settings)
            
    def handleMessage(self, message):
        """
        Adds a message to the queue of images to send.
        """
        # Check the message and it to the queue.
        if not message.m_type in halMessage.valid_messages:
            msg = "Invalid message type '" + message.m_type
            msg += "' received from " + message.getSourceName()
            raise halExceptions.HalException(msg)
        self.queued_messages.append(message)

        # Start the message timer, if it is not already running.
        self.startMessageTimer()

    def handleSendMessage(self):
        """
        Handle sending the current message to all the modules.
        """
        interval = -1
        #
        # Remove all the messages that have already been
        # handled from the list of sent messages.
        #
        unhandled = []
        for sent_message in self.sent_messages:
            if sent_message.refCountIsZero():

                # Call message finalizer.
                sent_message.finalize()

                # Notify the sender if errors occured while processing the message.
                if sent_message.hasErrors():
                    sent_message.getSource().handleErrors(sent_message)

                # Notify the sender of any responses to the message.
                if sent_message.hasResponses():
                    sent_message.getSource().handleResponses(sent_message)

            else:
                unhandled.append(sent_message)
        self.sent_messages = unhandled

        # Process the next message.
        if (len(self.queued_messages) > 0):
            cur_message = self.queued_messages.popleft()
            
            #
            # If this message requested synchronization and there are
            # pending messages then push it back into the queue and
            # wait ~50 milliseconds.
            #
            if cur_message.sync and (len(self.sent_messages) > 0):
                self.queued_messages.appendleft(cur_message)
                interval = 50
            
            #
            # Otherwise process the message.
            #
            else:
                if (cur_message.level == 1):
                    print(cur_message.source.module_name + " '" + cur_message.m_type + "'")

                # Check for "closeEvent" message from the main window.
                if (cur_message.getSourceName() == "hal") and (cur_message.getType() == "close event"):
                    self.cleanup()

                else:
                    # Check for "sync" message, these don't actually get sent.
                    if (cur_message.getType() == "sync"):
                        pass

                    # Otherwise send the message.
                    else:
                        if (cur_message.level == 1):
                            cur_message.logEvent("sent")
                            
                        self.sent_messages.append(cur_message)
                        for module in self.modules:
                            cur_message.ref_count += 1
                            module.handleMessage(cur_message)

                    # Process any remaining messages with immediate timeout.
                    if (len(self.queued_messages) > 0):
                        interval = 0

                    #
                    # Otherwise wait ~50 milliseconds, then check if the message
                    # that was just sent has been processed.
                    #
                    # See note below about sent messages and finalizers.
                    #
                    else:
                        interval = 50

        #
        # If have unprocesses messages wait ~50 milliseconds and check again.
        #
        # We do this even if we don't have queued messages because one or of
        # the sent messages might have a finalizer specified.
        #
        elif (len(self.sent_messages) > 0):
            interval = 50

        if (interval > -1):
            self.startMessageTimer(interval = interval)

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
    parser.add_argument('config', type=str, help = "The name of the configuration file to use.")

    args = parser.parse_args()

    # FIXME: Should allow an (optional) initial setup file name.
    
    # Start..
    app = QtWidgets.QApplication(sys.argv)

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
    hal = HalCore(config)

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
