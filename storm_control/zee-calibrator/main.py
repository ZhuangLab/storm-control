#!/usr/bin/python
#
# Utility for calculating z calibration curves.
#
# Hazen 02/13
#

import os, sys
from PyQt4 import QtCore, QtGui

# UIs.
import mainwindow_ui

# Plotting
import plot

# Calibration fitting
import zcal

#
# Main window
#
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        self.binned_points = []
        self.directory = ""
        self.filename = None
        self.fit_values = []
        self.minimum_intensity = 10
        self.points = []
        self.settings = QtCore.QSettings("Zhuang Lab", "zee-calibrator")
        self.stage_fit = []
        self.stage_qpd = []
        self.wx_wy_cat = []
        self.z_calib = None

        # ui setup
        self.ui = mainwindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowIcon(QtGui.QIcon("leifeng.ico"))

        # set ui defaults
        self.ui.powerComboBox.addItems(["0","1","2","3","4"])
        self.ui.powerComboBox.setCurrentIndex(2)

        # handling file drops
        self.ui.centralwidget.__class__.dragEnterEvent = self.dragEnterEvent
        self.ui.centralwidget.__class__.dropEvent = self.dropEvent

        # signals
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionLoad_Molecule_List.triggered.connect(self.handleLoad)
        self.ui.actionRedo_Fit.triggered.connect(self.handleRedo)
        self.ui.actionSave_Calibration.triggered.connect(self.handleSaveCalibration)
        self.ui.actionLoad_Calibration.triggered.connect(self.handleLoadCalibration)
        self.ui.actionLoad_Data.triggered.connect(self.handleLoadData)

        # plots
        self.wxwyvz_plot = plot.PlotWindow("Z (nm)", [-500.0, 500.0, 100.0], "Wx, Wy (pixels)", [0.0, 6.0, 1.0], self.ui.wxwyvzTab)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.wxwyvz_plot)
        self.ui.wxwyvzTab.setLayout(layout)

        #policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #policy.setHeightForWidth(True)
        #self.ui.wxvwyPlotWidget.setSizePolicy(policy)
        #self.ui.wxvwyPlotWidget.heightForWidth = lambda(x): x

        self.wxvwy_plot = plot.SquarePlotWindow("Wx (pixels)", [0.0, 6.0, 1.0], "Wy (pixels)", [0.0, 6.0, 1.0], self.ui.wxvwyPlotWidget)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.wxvwy_plot)
        self.ui.wxvwyPlotWidget.setLayout(layout)

        self.stage_plot = plot.PlotWindow("Stage Position (um)", [-1.0, 1.0, 0.2], "QPD offset (au)", [-0.5, 0.5, 0.1], self.ui.stageTab)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.stage_plot)
        self.ui.stageTab.setLayout(layout)

        #self.ui.plotTabWidget.currentChanged.connect(self.handleTabChanges)
        #self.handleTabChanges(0)

        # load settings.
        self.directory = str(self.settings.value("directory", "").toString())
        self.move(self.settings.value("position", QtCore.QPoint(100, 100)).toPoint())
        self.resize(self.settings.value("size", self.size()).toSize())
        self.ui.pixelSpinBox.setValue(self.settings.value("pix_per_nm", 160.0).toFloat()[0])


    def analyzeData(self, filename):
        self.ui.plotTabWidget.setCurrentIndex(0)
        self.filename = filename
        self.ui.filenameLabel.setText(self.filename)
        self.z_calib = zcal.ZCalibration(filename,
                                         self.ui.powerComboBox.currentIndex(),
                                         self.minimum_intensity,
                                         self.ui.pixelSpinBox.value())

        good = True
        # calibrate the stage
        if good:
            good = self.z_calib.stageCalibration(filename)
            if (not good):
                self.errorMessageBox("A problem occurred with the .off file.")

        # first pass on the defocusing curve
        if good:
            good = self.z_calib.fitDefocusing()
            if (not good):
                self.errorMessageBox("A problem occurred in the 1st pass of defocus fitting.")

        # determine stage tilt
        if good:
            good = self.z_calib.fitTilt()
            if (not good):
                self.errorMessageBox("A problem occurred fitting for stage tilt.")

        for i in range(2):

            # determine z offset of the point where wx = wy
            if good:
                good = self.z_calib.findZOffset()
                if (not good):
                    self.errorMessageBox("A problem occurred finding the z offset.")
 
            # second pass on the defocusing curve
            if good:
                good = self.z_calib.fitDefocusing()
                if (not good):
                    self.errorMessageBox("A problem occurred in a later pass of defocus fitting.")

        # plot results
        if good:

            # clear plots
            self.wxwyvz_plot.clear()
            self.wxvwy_plot.clear()
            self.stage_plot.clear()

            # get stage calibration info
            self.stage_fit = self.z_calib.getStageFit()
            self.stage_qpd = self.z_calib.getStageQPD()

            # get data for wx vs. wy plot
            [wx, wy] = self.z_calib.getWxWyData()
            cat = self.z_calib.getCategory()
            self.wx_wy_cat = [wx, wy, cat]

            # plot data
            self.points = self.z_calib.getPoints()
            self.wxwyvz_plot.plotData(*self.points)

            # plot smoothed data
            self.binned_points = self.z_calib.getBinnedPoints()
            self.wxwyvz_plot.plotBinnedData(*self.binned_points)

            # plot fit
            self.fit_values = self.z_calib.getFitValues()
            self.wxwyvz_plot.plotFit(*self.fit_values)

            # plot wx vs wy data
            self.wxvwy_plot.plotWxWyData(*self.wx_wy_cat)

            # plot wx vs wy fit
            self.wxvwy_plot.plotWxWyFit(self.fit_values[1], self.fit_values[2])

            # plot stage / qpd data
            self.stage_plot.plotStageQPD(self.stage_qpd[0],
                                         self.stage_qpd[1],
                                         self.stage_fit[0],
                                         self.stage_fit[1])

            # update calibration expression
            self.ui.calLineEdit.setText(self.z_calib.getWxString() + self.z_calib.getWyString())

        # print & save coefficients
        #z_calib.printWxWyCoeff()
        #z_calib.saveZCal()

    def closeEvent(self, event):
        self.settings.setValue("directory", self.directory)
        self.settings.setValue("position", self.pos())
        self.settings.setValue("size", self.size())
        self.settings.setValue("pix_per_nm", self.ui.pixelSpinBox.value())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        filename = str(url.encodedPath())[1:]
        self.analyzeData(filename)

    def errorMessageBox(self, info):
        QtGui.QMessageBox.critical(self,
                                   "Calibrator",
                                   info,
                                   QtGui.QMessageBox.Ok)

    def handleLoad(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self, "New Molecule List", self.directory, "*.bin"))
        if filename:
            self.directory = os.path.dirname(filename)
            self.analyzeData(filename)

    def handleLoadCalibration(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self, "Load Calibration", self.directory, "Files (*.txt *.ini)"))
        if filename:
            self.ui.plotTabWidget.setCurrentIndex(0)
            self.directory = os.path.dirname(filename)
            self.z_calib = zcal.ZCalibration(filename,
                                             self.ui.powerComboBox.currentIndex(),
                                             self.minimum_intensity,
                                             self.ui.pixelSpinBox.value())
            self.fit_values = self.z_calib.getFitValues()

            self.wxwyvz_plot.clear()
            self.wxvwy_plot.clear()
            self.stage_plot.clear()
            self.wxwyvz_plot.plotFit(*self.fit_values)
            self.wxvwy_plot.plotWxWyFit(self.fit_values[1], self.fit_values[2])

    def handleLoadData(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self, "Load Data", self.directory, "*.bin"))
        if filename:
            self.directory = os.path.dirname(filename)
            if self.z_calib:
                self.ui.plotTabWidget.setCurrentIndex(1)
                #self.plot.clear()
                #self.plot.plotInit("wx_vs_wy")
                self.z_calib.loadMolecules(filename, self.minimum_intensity)
                [wx, wy] = self.z_calib.getWxWyData()
                cat = self.z_calib.getCategory()
                self.wx_wy_cat = [wx, wy, cat]
                self.fit_values = self.z_calib.getFitValues()
                self.wxvwy_plot.plotWxWyData(*self.wx_wy_cat)
                self.wxvwy_plot.plotWxWyFit(self.fit_values[1], self.fit_values[2])
            else:
                print "You need to load a calibration curve first."

    def handleRedo(self):
        if self.filename:
            self.analyzeData(str(self.filename))

    def handleSaveCalibration(self):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, "Save Calibration", self.directory, "*.txt"))
        if filename:
            self.directory = os.path.dirname(filename)
            self.z_calib.saveCalibration(filename)

#    def handleTabChanges(self, index):
#        if (index == 0):
#            self.ui.wxwyvzTab.setLayout(self.plot_layout)
#            self.plot_widget.plotInit("z_graph")
#            if(len(self.points)>0):
#                self.plot_widget.plotData(*self.points)
#            if(len(self.binned_points)>0):
#                self.plot_widget.plotBinnedData(*self.binned_points)
#            if(len(self.fit_values)>0):
#                self.plot_widget.plotFit(*self.fit_values)
#            self.plot_widget.update()
#        elif (index == 1):
#            self.ui.wxvwyTab.setLayout(self.plot_layout)
#            self.plot_widget.plotInit("wx_vs_wy")
#            if(len(self.wx_wy_cat)>0):
#                self.plot_widget.plotWxWyData(*self.wx_wy_cat)
#            if(len(self.fit_values)>0):
#                self.plot_widget.plotWxWyFit(self.fit_values[1], self.fit_values[2])
#            self.plot_widget.update()
#        elif (index == 2):
#            self.ui.stageTab.setLayout(self.plot_layout)
#            self.plot_widget.plotInit("stage")
#            if(len(self.stage_qpd)>0):
#                self.plot_widget.plotStageQPD(self.stage_qpd[0],
#                                              self.stage_qpd[1],
#                                              self.stage_fit[0],
#                                              self.stage_fit[1])
#            self.plot_widget.update()

    def quit(self):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
