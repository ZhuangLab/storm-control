#!/usr/bin/env python
"""
sCMOS calibration UI.

Hazen Babcock 06/17
"""

import numpy
import os
from PyQt5 import QtCore, QtWidgets

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.halModule as halModule


# UI.
import storm_control.hal4000.qtdesigner.scmos_calibration_ui as scmosCalibrationUi


class Calibrator(QtCore.QObject):
    """
    Handles accumulating data from the camera, doing the calibration
    calculations and saving the results.
    """
    done = QtCore.pyqtSignal(int)
    newFrame = QtCore.pyqtSignal(int, float)

    def __init__(self, camera_fn = None, id_number = None, **kwds):
        super().__init__(**kwds)
        self.accumulated = 0
        self.camera_fn = camera_fn
        self.filename = None
        self.frame_mean = None
        self.id_number = id_number
        self.mean = None
        self.n_frames = 0
        self.running = False
        self.var = None

    def clearStats(self):
        self.mean = None
        self.var = None
        
    def getFileName(self, basename):
        if (len(self.camera_fn.getParameter("extension")) != 0):
            basename += "_" + self.camera_fn.getParameter("extension")
        basename += ".npy"
        return basename

    def getStats(self):
        if self.mean is not None and (self.accumulated == self.n_frames):
            mean_mean = numpy.mean(self.mean)/float(self.n_frames)
            mean_var = numpy.mean(self.var)/float(self.n_frames) - mean_mean*mean_mean
            return [mean_mean, mean_var]
        else:
            return [None, None]
        
    def handleNewFrame(self, frame):
        frame_32 = frame.getData().astype(numpy.int32)
        frame_32 = numpy.reshape(frame_32, self.mean.shape)
        self.frame_mean[self.accumulated] = numpy.mean(frame_32)
        self.mean += frame_32
        self.var += frame_32 * frame_32

        self.accumulated += 1
        self.newFrame.emit(self.id_number, float(self.accumulated/self.n_frames))

        if (self.accumulated == self.n_frames):
            self.camera_fn.newFrame.disconnect(self.handleNewFrame)
            numpy.save(self.filename, [self.frame_mean, self.mean, self.var])
            self.running = False
            self.done.emit(self.id_number)

    def start(self, basename, n_frames):
        self.filename = self.getFileName(basename)
        self.n_frames = n_frames

        self.accumulated = 0
        cam_x = self.camera_fn.getParameter("x_pixels")
        cam_y = self.camera_fn.getParameter("y_pixels")
        self.frame_mean = numpy.zeros(self.n_frames)
        self.mean = numpy.zeros((cam_x, cam_y), dtype = numpy.int64)
        self.var = numpy.zeros((cam_x, cam_y), dtype = numpy.int64)

        self.camera_fn.newFrame.connect(self.handleNewFrame)

        self.running = True

    def stop(self):
        if self.running:
            self.camera_fn.newFrame.disconnect(self.handleNewFrame)
            self.running = False
            self.done.emit(self.id_number)
    
    
class SCMOSCalibrationView(halDialog.HalDialog):
    """
    Manages the sCMOS calibration GUI.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.calibrators = []
        self.cgb_layout = None
        self.directory = ""
        self.n_running = 0
        self.will_overwrite = False
        self.ui_elements = []

        self.ui = scmosCalibrationUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.calibrationFileLineEdit.textChanged.connect(self.handleFileLineEdit)
        self.ui.startButton.clicked.connect(self.handleStartButton)
        
        self.ui.startButton.setEnabled(False)
        
    def checkExists(self):
        if (len(self.calibrators)>0):
            fname = self.calibrators[0].getFileName(os.path.join(self.directory, self.ui.calibrationFileLineEdit.text()))
            if os.path.exists(fname):
                self.will_overwrite = True
                self.ui.calibrationFileLineEdit.setStyleSheet("QLineEdit { color: red}")
            else:
                self.will_overwrite = False
                self.ui.calibrationFileLineEdit.setStyleSheet("QLineEdit { color: black}")

    def gotAllCameras(self):
        self.adjustSize()
        #self.setFixedSize(self.width(), self.height())
        self.checkExists()
        
    def handleDone(self, cal_id):
        self.n_running -= 1

        # Update stats.
        [mean, var] = self.calibrators[cal_id].getStats()
        self.calibrators[cal_id].clearStats()
        if mean is not None:
            self.ui_elements[cal_id][2].setText("{0:.2f} +- {1:.2f}".format(mean, var))
            
        # Reset GUI if all the calibrators have finished.
        if (self.n_running == 0):
            self.checkExists()
            for elt in self.ui_elements:
                elt[1].reset()
            self.ui.startButton.setStyleSheet("QPushButton { color: black }")
            self.ui.startButton.setText("Start")            

    def handleFileLineEdit(self, text):
        self.checkExists()
        
    def handleNewFrame(self, calibrator_number, progress):
        self.ui_elements[calibrator_number][1].setValue(round(100.0*progress))
                       
    def handleStartButton(self, boolean):
        if (self.n_running == 0):

            # Check if we'll overwrite an existing calibration.
            if self.will_overwrite:
                reply = halMessageBox.halMessageBoxResponse(self,
                                                            "Warning!",
                                                            "Overwrite Existing Calibration(s)?")
                if (reply == QtWidgets.QMessageBox.No):
                    return

            fname = os.path.join(self.directory, self.ui.calibrationFileLineEdit.text())
            for cal in self.calibrators:
                cal.start(fname, self.ui.framesSpinBox.value())
                self.n_running += 1
            self.ui.startButton.setStyleSheet("QPushButton { color: red }")
            self.ui.startButton.setText("Stop")
            
        else:
            for i, cal in enumerate(self.calibrators):
                cal.stop()
                self.ui_elements[i][1].reset()
            self.ui.startButton.setStyleSheet("QPushButton { color: black }")
            self.ui.startButton.setText("Start")
        
    def newCameraFn(self, camera_fn):
        if not camera_fn.isCamera():
            return
        
        calibrator = Calibrator(camera_fn = camera_fn,
                                id_number = len(self.calibrators))
        calibrator.done.connect(self.handleDone)
        calibrator.newFrame.connect(self.handleNewFrame)
        self.calibrators.append(calibrator)
        
        self.ui.startButton.setEnabled(True)
            
        # Add a new row to the layout.
        ui_row = []

        # Add camera name label.
        cam_label = QtWidgets.QLabel(camera_fn.getCameraName(), self)
        ui_row.append(cam_label)
        self.cgb_layout.addWidget(cam_label, len(self.ui_elements), 0)

        # Progress bar.
        prog_bar = QtWidgets.QProgressBar(self)
        prog_bar.setMinimumWidth(120)
        prog_bar.setMinimum(0)
        prog_bar.setMaximum(100)
        ui_row.append(prog_bar)
        self.cgb_layout.addWidget(prog_bar, len(self.ui_elements), 1)

        # Add stats label.
        stats_label = QtWidgets.QLabel("NA", self)
        stats_label.setMinimumWidth(150)
        stats_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        ui_row.append(stats_label)
        self.cgb_layout.addWidget(stats_label, len(self.ui_elements), 2)
        
        self.ui_elements.append(ui_row)
            
    def resetCalibrators(self):
        if (len(self.calibrators) > 0):
            for cal in self.calibrators:
                cal.stop()
                cal.done.disconnect(self.handleDone)
                cal.newFrame.disconnect(self.handleNewFrame)

        # Delete old layout, if any.
        layout = self.ui.cameraGroupBox.layout()
        if layout:
            QtWidgets.QWidget().setLayout(layout)

        # Create new layout.
        self.cgb_layout = QtWidgets.QGridLayout(self.ui.cameraGroupBox)
        self.cgb_layout.setContentsMargins(1,1,1,1)
        self.cgb_layout.setSpacing(1)
        
        self.calibrators = []
        self.ui_elements = []
        self.ui.startButton.setEnabled(False)

    def setDirectory(self, directory):
        self.directory = directory
        self.checkExists()


class SCMOSCalibration(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.number_fn_requested = 0

        self.view = SCMOSCalibrationView(module_name = self.module_name)
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " sCMOS calibration")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.newCameraFn(response.getData()["functionality"])
            self.number_fn_requested -= 1
            if (self.number_fn_requested == 0):
                self.view.gotAllCameras()

    def processMessage(self, message):

        if message.isType("change directory"):
            self.view.setDirectory(message.getData()["directory"])

        elif message.isType("configuration"):
            if message.sourceIs("feeds"):
                self.view.resetCalibrators()
                for name in message.getData()["properties"]["feed names"]:
                    self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                           data = {"name" : name}))
                    self.number_fn_requested += 1
                    
        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "sCMOS Calibration",
                                                           "item data" : "scmos calibration"}))

        elif message.isType("show"):
            if (message.getData()["show"] == "scmos calibration"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()
