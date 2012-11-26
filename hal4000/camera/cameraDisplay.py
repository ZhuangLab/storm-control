#!/usr/bin/python
#
# Camera control and display class.
#
# Hazen 9/09
#

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.camera_ui as cameraUi

# Camera Helper Modules
import qtWidgets.qtColorGradient as qtColorGradient
import qtWidgets.qtRangeSlider as qtRangeSlider

# Misc
import colorTables.colorTables as colorTables

class CameraDisplay(QtGui.QFrame):
    syncChange = QtCore.pyqtSignal(int)

    @hdebug.debug
    def __init__(self, parameters, show_record_button = False, show_shutter_button = False, parent = None):
        QtGui.QFrame.__init__(self, parent)

        # general (alphabetically ordered)
        self.color_gradient = 0
        self.color_table = 0
        self.color_tables = colorTables.ColorTables("./colorTables/all_tables/")
        self.debug = parameters.debug
        self.max_intensity = parameters.max_intensity
        self.parameters = parameters
        self.show_grid = 0
        self.show_info = 1
        self.show_target = 0

        # ui setup
        self.ui = cameraUi.Ui_Frame()
        self.ui.setupUi(self)
        self.ui.rangeSlider = qtRangeSlider.QVRangeSlider(parent = self.ui.rangeSliderWidget)
        layout = QtGui.QGridLayout(self.ui.rangeSliderWidget)
        layout.addWidget(self.ui.rangeSlider)
        self.ui.rangeSlider.setGeometry(0, 0, self.ui.rangeSliderWidget.width(), self.ui.rangeSliderWidget.height())
        self.ui.rangeSlider.setRange([0.0, self.max_intensity])
        self.ui.rangeSlider.setEmitWhileMoving(True)
        for color_name in self.color_tables.getColorTableNames():
            self.ui.colorComboBox.addItem(color_name[:-5])
        self.ui.gridAct = QtGui.QAction(self.tr("Show Grid"), self)
        self.ui.infoAct = QtGui.QAction(self.tr("Hide Info"), self)
        self.ui.targetAct = QtGui.QAction(self.tr("Show Target"), self)
        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()

        # show/hide shutter and record button as appropriate
        if show_record_button:
            self.ui.recordButton.show()
        else:
            self.ui.recordButton.hide()

        if show_shutter_button:
            self.ui.cameraShutterButton.show()
        else:
            self.ui.cameraShutterButton.hide()

        # Camera display widget. Load as appropriate 
        # based on the camera type.
        camera_type = parameters.camera_type.lower()
        cameraWidget = __import__('camera.' + camera_type + 'CameraWidget', globals(), locals(), [camera_type], -1)
        self.camera_widget = cameraWidget.ACameraWidget(parent = self.ui.cameraDisplayFrame)
        self.camera_widget.setGeometry(3, 3, 512, 512)
        self.camera_widget.show()

        # signals
        self.ui.rangeSlider.rangeChanged.connect(self.rangeChange)
        self.ui.rangeSlider.doubleClick.connect(self.autoScale)
        self.ui.autoScaleButton.clicked.connect(self.autoScale)
        self.ui.colorComboBox.currentIndexChanged.connect(self.colorTableChange)
        self.ui.syncSpinBox.valueChanged.connect(self.handleSync)
        self.camera_widget.intensityInfo.connect(self.handleIntensityInfo)
        self.ui.gridAct.triggered.connect(self.handleGrid)
        self.ui.infoAct.triggered.connect(self.handleInfo)
        self.ui.targetAct.triggered.connect(self.handleTarget)

    #
    # All other methods alphabetically ordered, for lack of a better system
    #

    @hdebug.debug
    def autoScale(self):
        [scalemin, scalemax] = self.camera_widget.getAutoScale()
        if scalemin < 0:
            scalemin = 0
        if scalemax > self.max_intensity:
            scalemax = self.max_intensity
        self.ui.rangeSlider.setValues([float(scalemin), float(scalemax)])

    @hdebug.debug
    def colorTableChange(self, index):
        self.parameters.colortable = self.ui.colorComboBox.currentText() + ".ctbl" 
        self.color_table = self.color_tables.getTableByName(self.parameters.colortable)
        self.camera_widget.newColorTable(self.color_table)
        self.color_gradient.newColorTable(self.color_table)

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.ui.infoAct)
        menu.addAction(self.ui.targetAct)
        menu.addAction(self.ui.gridAct)
        menu.exec_(event.globalPos())

    def displayFrame(self, frame):
        self.camera_widget.updateImageWithData(frame)

    def getShutterButton(self):
        return self.ui.cameraShutterButton

    def getRecordButton(self):
        return self.ui.recordButton

    @hdebug.debug
    def handleGrid(self):
        if self.show_grid:
            self.show_grid = 0
            self.ui.gridAct.setText("Show Grid")
        else:
            self.show_grid = 1
            self.ui.gridAct.setText("Hide Grid")
        self.camera_widget.setShowGrid(self.show_grid)

    @hdebug.debug
    def handleInfo(self):
        if self.show_info:
            self.show_info = 0
            self.ui.infoAct.setText("Show Info")
            self.ui.intensityPosLabel.hide()
            self.ui.intensityIntLabel.hide()
        else:
            self.show_info = 1
            self.ui.infoAct.setText("Hide Info")
            self.ui.intensityPosLabel.show()
            self.ui.intensityIntLabel.show()
        self.camera_widget.setShowInfo(self.show_info)

    def handleIntensityInfo(self, x, y, i):
        self.ui.intensityPosLabel.setText("({0:d},{1:d})".format(x, y, i))
        self.ui.intensityIntLabel.setText("{0:d}".format(i))

    @hdebug.debug
    def handleSync(self, frame):
        #self.emit(QtCore.SIGNAL("syncChange(int)"), frame)
        self.syncChange.emit(frame)

    @hdebug.debug
    def handleTarget(self):
        if self.show_target:
            self.show_target = 0
            self.ui.targetAct.setText("Show Target")
        else:
            self.show_target = 1
            self.ui.targetAct.setText("Hide Target")
        self.camera_widget.setShowTarget(self.show_target)

    @hdebug.debug
    def newParameters(self, parameters):
        # for conveniently accessing parameters
        p = parameters
        self.parameters = p

        #
        # setup the camera display widget
        #
        self.color_table = self.color_tables.getTableByName(p.colortable)
        display_range = [p.scalemin, p.scalemax]
        self.camera_widget.newParameters(p, self.color_table, display_range)

        # camera display
        self.updateRange()

        # color gradient
        if self.color_gradient:
            self.color_gradient.newColorTable(self.color_table)
        else:
            self.color_gradient = qtColorGradient.QColorGradient(colortable = self.color_table,
                                                                 parent = self.ui.colorFrame)
            layout = QtGui.QGridLayout(self.ui.colorFrame)
            layout.setMargin(2)
            layout.addWidget(self.color_gradient)

        self.ui.colorComboBox.setCurrentIndex(self.ui.colorComboBox.findText(p.colortable[:-5]))

        # general settings
        self.max_intensity = parameters.max_intensity
        self.ui.rangeSlider.setRange([0.0, self.max_intensity])
        self.ui.rangeSlider.setValues([float(p.scalemin), float(p.scalemax)])
        self.ui.syncSpinBox.setValue(p.sync)

    @hdebug.debug
    def rangeChange(self, scale_min, scale_max):
        if scale_max == scale_min:
            if scale_max < float(self.max_intensity):
                scale_max += 1.0
            else:
                scale_min -= 1.0
        self.parameters.scalemax = int(scale_max)
        self.parameters.scalemin = int(scale_min)
        self.updateRange()

    @hdebug.debug
    def setSyncMax(self, sync_max):
        self.ui.syncSpinBox.setMaximum(sync_max)

    @hdebug.debug
    def startFilm(self):
        self.ui.syncLabel.show()
        self.ui.syncSpinBox.show()

    @hdebug.debug
    def stopFilm(self):
        self.ui.syncLabel.hide()
        self.ui.syncSpinBox.hide()

    def updateImage(self, frame):
        if frame:
            self.camera_widget.updateImageWithData(frame.data)

    @hdebug.debug
    def updateRange(self):
        self.ui.scaleMax.setText(str(self.parameters.scalemax))
        self.ui.scaleMin.setText(str(self.parameters.scalemin))
        self.camera_widget.newRange([self.parameters.scalemin, self.parameters.scalemax])


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
