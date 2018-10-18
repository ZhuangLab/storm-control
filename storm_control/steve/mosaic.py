#!/usr/bin/env python
"""
The handles all the UI elements in the Mosaic tab.

Hazen 10/18
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.hdebug as hdebug

import storm_control.steve.comm as comm
import storm_control.steve.mosaicView as mosaicView
import storm_control.steve.objectives as objectives
import storm_control.steve.qtdesigner.mosaic_ui as mosaicUi
import storm_control.steve.steveModule as steveModule


class Mosaic(steveModule.SteveModule):

    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.ui = mosaicUi.Ui_Form()
        self.ui.setupUi(self)

        # Set up view.
        self.mosaic_view = mosaicView.MosaicView()
        layout = QtWidgets.QGridLayout(self.ui.mosaicFrame)
        layout.addWidget(self.mosaic_view)
        self.ui.mosaicFrame.setLayout(layout)
        self.mosaic_view.show()
        self.mosaic_view.setScene(self.item_store.getScene())

        # Send message to request mosaic settings.
        msg = comm.CommMessageMosaicSettings(finalizer_fn = self.handleMosaicSettingsMessage)
        self.comm.sendMessage(msg)

    @hdebug.debug
    def getObjective(self):
        msg = comm.CommMessageObjective(finalizer_fn = self.handleGetObjectiveMessage)
        self.comm.sendMessage(msg)

    @hdebug.debug
    def handleGetObjectiveMessage(self, tcp_message, tcp_message_response):
        self.ui.objectivesGroupBox.changeObjective(tcp_message_response.getResponse("objective"))
        #[magnification, x_offset, y_offset] = self.ui.objectivesGroupBox.getData(objective)
        #self.current_offset = coord.Point(x_offset, y_offset, "um")

    @hdebug.debug
    def handleMosaicSettingsMessage(self, tcp_message, tcp_message_response):
        i = 1
        while tcp_message_response.getResponse("obj" + str(i)) is not None:
            data = tcp_message_response.getResponse("obj" + str(i)).split(",")
            self.ui.objectivesGroupBox.addObjective(data)
            i += 1

        # Send message to get current objective.
        if (i > 1):
            self.getObjective()

