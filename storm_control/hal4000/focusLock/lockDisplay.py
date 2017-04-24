#!/usr/bin/env python
"""
This class handles the lock display group box and it's widgets.

Hazen 04/17
"""

from PyQt5 import QtCore, QtGui, QtWidgets

# UI.
import storm_control.hal4000.qtdesigner.lockdisplay_ui as lockdisplayUi


class LockDisplay(QtWidgets.QGroupBox):
    """
    The lock display UI group box.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.ir_laser_functionality = None
        self.ir_on = False
        self.ir_power = configuration.get("ir_power", 0)

        # UI setup
        self.ui = lockdisplayUi.Ui_GroupBox()
        self.ui.setupUi(self)
        
        self.ui.irButton.hide()
        self.ui.irSlider.hide()
        self.ui.qpdXText.hide()
        self.ui.qpdYText.hide()

        # Add the widgets that will actually display the data from the
        # QPD and z stage.
        self.q_qpd_offset_display = QQPDOffsetDisplay(q_label = self.ui.offsetText,
                                                      parent = self)
        layout = QtWidgets.QGridLayout(self.ui.offsetFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.q_qpd_offset_display)

        self.q_stage_display = QStageDisplay(jump_size = configuration.get("jump_size"),
                                             q_label = self.ui.zText,
                                             parent = self)
        layout = QtWidgets.QGridLayout(self.ui.zFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.q_stage_display)

        self.q_qpd_sum_display = QQPDSumDisplay(q_label = self.ui.sumText,
                                                parent = self)
        layout = QtWidgets.QGridLayout(self.ui.sumFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.q_qpd_sum_display)

    def handleIrButton(self, boolean):
        """
        Handles the IR laser button. Turns the laser on/off and
        updates the button accordingly.
        """
        if self.ir_on:
            self.ir_laser_functionality.onOff(0.0, False)
            self.ir_on = False
            self.ui.irButton.setText("IR ON")
            self.ui.irButton.setStyleSheet("QPushButton { color: green }")
        else:
            self.ir_laser_functionality.onOff(self.ir_power, True)
            self.ir_on = True
            self.ui.irButton.setText("IR OFF")
            self.ui.irButton.setStyleSheet("QPushButton { color: red }")

    def handleIrSlider(self, value):
        """
        Handles the IR laser power slider.
        """
        self.ir_power = value
        self.ir_laser_functionality.output(self.ir_power)

    def haveAllFunctionalities(self):
        if self.ir_laser_functionality is None:
            return False
        if not self.q_stage_display.haveFunctionality():
            return False
        return True
        
    def setFunctionality(self, name, functionality):
        if (name == "ir_laser"):
            self.ir_laser_functionality = functionality
            
            self.ui.irButton.show()
            self.ui.irButton.clicked.connect(self.handleIrButton)
            if self.ir_laser_functionality.hasPowerAdjustment():
                self.ui.irSlider.show()
                self.ui.irSlider.setMaximum(self.ir_laser_functionality.getMaximum())
                self.ui.irSlider.setValue(self.ir_power)
                self.ui.irSlider.valueChanged.connect(self.handleIrSlider)
        elif (name == "qpd"):
            self.q_qpd_offset_display.setFunctionality(functionality)
            self.q_qpd_sum_display.setFunctionality(functionality)
        elif (name == "z_stage"):
            self.q_stage_display.setFunctionality(functionality)


#
# These widgets are used to provide user feedback.
#
class QStatusDisplay(QtWidgets.QWidget):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.functionality = None
        self.scale_min = None
        self.scale_max = None
        self.scale_range = None
        self.value = 0
        self.warning_high = None
        self.warning_low = None

    def convert(self, value):
        """
        Convert input value into pixels.
        """
        scaled = int((value - self.scale_min) * self.scale_range * float(self.height()))
        if scaled > self.height():
            scaled = self.height()
        if scaled < 0:
            scaled = 0
        return scaled

    def haveFunctionality(self):
        return self.functionality is not None
        
    def paintBackground(self, painter):
        """
        Paint the background of the widget.
        """
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        self.update()
                    
    def setFunctionality(self, functionality):
        self.functionality = functionality

    def updateValue(self, value):
        self.value = value
        self.update()


class QOffsetDisplay(QStatusDisplay):

    def __init__(self, **kwds):
        """
        Focus lock offset & stage position.
        """
        super().__init__(**kwds)
        self.has_center_bar = None

    def paintEvent(self, event):
        if self.functionality is None:
            return

        painter = QtGui.QPainter(self)
        self.paintBackground(painter)
        
        # Warning bars.
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        if self.warning_low is not None:
            painter.drawRect(0, self.height() - self.convert(self.warning_low), self.width(), self.height())
        if self.warning_high is not None:
            painter.drawRect(0, 0, self.width(), self.height() - self.convert(self.warning_high))

        if self.has_center_bar:
            center_bar = int(0.5 * self.height())
            color = QtGui.QColor(50, 50, 50)
            painter.setPen(color)
            painter.drawLine(0, center_bar, self.width(), center_bar)

        # Foreground.
        color = QtGui.QColor(0, 0, 0, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.height() - self.convert(self.value) - 2, self.width() - 5, 3)


class QQPDOffsetDisplay(QOffsetDisplay):
    """
    Focus lock offset display. Converts to nanometers.
    """
    def __init__(self, q_label = None, **kwds):
        super().__init__(**kwds)
        self.q_label = q_label
        
    def updateValue(self, qpd_dict):
        value = 1000.0 * qpd_dict["offset"]
        super().updateValue(value)
        self.q_label.setText("{0:.1f}".format(value))

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.has_center_bar = self.functionality.getParameter("offset_has_center_bar")
        self.scale_max = 1000.0 * self.functionality.getParameter("offset_maximum")
        self.scale_min = 1000.0 * self.functionality.getParameter("offset_minimum")
        self.warning_high = 1000.0 * self.functionality.getParameter("offset_warning_high")
        self.warning_low = 1000.0 * self.functionality.getParameter("offset_warning_low")

        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.functionality.qpdUpdate.connect(self.updateValue)


class QQPDSumDisplay(QStatusDisplay):
    """
    Focus lock sum signal display.
    """
    def __init__(self, q_label = None, **kwds):
        super().__init__(**kwds)
        self.q_label = q_label

    def paintEvent(self, event):
        if self.functionality is None:
            return
        
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)        

        # warning bars
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        if self.warning_low is not None:
            painter.drawRect(0, self.height() - self.convert(self.warning_low),
                             self.width(), self.height())
        if self.warning_high is not None:
            painter.drawRect(0, 0, self.width(), self.height() - self.convert(self.warning_high))

        # foreground
        color = QtGui.QColor(0, 255, 0, 200)
        if self.warning_low is not None:
            if (self.value < self.warning_low):
                color = QtGui.QColor(255, 0, 0, 200)
        if self.warning_high is not None:
            if (self.value >= self.warning_high):
                color = QtGui.QColor(255, 0, 0, 200)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.height() - self.convert(self.value),
                         self.width() - 5, self.convert(self.value))

    def updateValue(self, qpd_dict):
        value = qpd_dict["sum"]
        super().updateValue(value)
        self.q_label.setText("{0:.1f}".format(value))

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.has_center_bar = self.functionality.getParameter("sum_has_center_bar")
        self.scale_max = self.functionality.getParameter("sum_maximum")
        self.scale_min = self.functionality.getParameter("sum_minimum")
        if self.functionality.hasParameter("sum_warning_high"):
            self.warning_high = self.functionality.getParameter("sum_warning_high")
        if self.functionality.hasParameter("sum_warning_low"):
            self.warning_low = self.functionality.getParameter("sum_warning_low")

        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.functionality.qpdUpdate.connect(self.updateValue)        

        
class QStageDisplay(QOffsetDisplay):
    """
    Z stage position.
    """
    jump = QtCore.pyqtSignal(float)
    
    def __init__(self, q_label = None, jump_size = None, **kwds):
        super().__init__(**kwds)
        self.q_label = q_label
        self.jump_size = jump_size

        self.adjust_mode = False
        self.tooltips = ["click to adjust", "use scroll wheel to move stage"]

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setToolTip(self.tooltips[0])

    def paintBackground(self, painter):
        if self.adjust_mode:
            color = QtGui.QColor(180, 180, 180)
        else:
            color = QtGui.QColor(255, 255, 255)

        if (self.value < self.warning_low) or (self.value > self.warning_high):
            color = QtGui.QColor(255, 0, 0)

        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    def mousePressEvent(self, event):
        """
        Toggles between adjust and non-adjust mode. In adjust mode the piezo 
        stage can be moved up and down with the mouse scroll wheel.
        """
        if self.functionality is not None:
            self.adjust_mode = not self.adjust_mode
            if self.adjust_mode:
                self.setToolTip(self.tooltips[1])
            else:
                self.setToolTip(self.tooltips[0])
            self.update()

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.has_center_bar = self.functionality.getParameter("has_center_bar")
        self.scale_max = self.functionality.getParameter("maximum")
        self.scale_min = self.functionality.getParameter("minimum")
        self.warning_high = self.functionality.getParameter("warning_high")
        self.warning_low = self.functionality.getParameter("warning_low")
            
        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.updateValue(self.functionality.getCurrentPosition())
        self.functionality.zStagePosition.connect(self.updateValue)

    def updateValue(self, value):
        super().updateValue(value)
        self.q_label.setText("{0:.3f}um".format(value))
            
    def wheelEvent(self, event):
        """
        Handles mouse wheel events. Emits the adjustStage signal 
        if the widget is in adjust mode.
        """
        if self.adjust_mode and (not event.angleDelta().isNull()):
            if (event.angleDelta().y() > 0):
                self.jump.emit(self.jump_size)
            else:
                self.jump.emit(-self.jump_size)
            event.accept()

            


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
