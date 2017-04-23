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
        self.display_widgets = []
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
        z_stage_widget = QStageDisplay(functionality_name = "z_stage",
                                       qlabel = self.ui.zText,
                                       parent = self)
        layout = QtWidgets.QGridLayout(self.ui.zFrame)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(z_stage_widget)
        self.display_widgets.append(z_stage_widget)

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
        for widget in self.display_widgets:
            if not widget.haveFunctionality():
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
        else:
            for widget in self.display_widgets:
                widget.setFunctionality(name, functionality)


#
# These widgets are used to provide user feedback.
#
class QStatusDisplay(QtWidgets.QWidget):

    def __init__(self, functionality_name = None, qlabel = None, **kwds):
        super().__init__(**kwds)
        self.functionality = None
        self.functionality_name = functionality_name
        self.qlabel = qlabel
        self.scale_min = None
        self.scale_max = None
        self.scale_range = None
        self.value = 0

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

    def getValue(self, normalized = True):
        """
        Returns the current value.
        
        FIXME: Do we use this?
        """
        if normalized:
            return float(self.value)/float(self.height())
        else:
            return float(self.value)

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
        
    def setFunctionality(self, name, functionality):
        if (name == self.functionality_name):
            self.functionality = functionality
            self.scale_max = self.functionality.getMaximum()
            self.scale_min = self.functionality.getMinimum()
            self.scale_range = 1.0/(self.scale_max - self.scale_min)
        
    def updateValue(self, value):
        self.value = value
        self.update()


class QOffsetDisplay(QStatusDisplay):

    def __init__(self, has_center_bar = False, **kwds):
        """
        Focus lock offset & stage position.
        """
        super().__init__(**kwds)
        self.has_center_bar = has_center_bar

    def paintEvent(self, event):
        if self.functionality is None:
            return

        painter = QtGui.QPainter(self)
        self.paintBackground(painter)
        
        # Warning bars.
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, self.height() - self.convert(self.warning_low), self.width(), self.height())
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

    def setFunctionality(self, name, functionality):
        super().setFunctionality(name, functionality)
        if self.functionality is not None:
            self.has_center_bar = self.functionality.hasCenterBar()
            self.warning_high = self.functionality.getWarningHigh()
            self.warning_low = self.functionality.getWarningLow()


class QStageDisplay(QOffsetDisplay):
    """
    Z stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

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
            
    def setFunctionality(self, name, functionality):
        super().setFunctionality(name, functionality)
        if self.functionality is not None:
            self.updateValue(self.functionality.getCurrentPosition())
            self.functionality.zStagePosition.connect(self.updateValue)

    def updateValue(self, value):
        super().updateValue(value)
        self.qlabel.setText("{0:.3f}um".format(value))
         
    def wheelEvent(self, event):
        """
        Handles mouse wheel events. Emits the adjustStage signal 
        if the widget is in adjust mode.
        """
        if self.adjust_mode and (not event.angleDelta().isNull()):
            if (event.angleDelta().y() > 0):
                self.functionality.jump(1.0)
            else:
                self.functionality.jump(-1.0)
            event.accept()

            
class QSumDisplay(QStatusDisplay):

    def __init__(self, warning_low = None, warning_high = None, **kwds):
        """
        Focus lock sum signal display.
        """
        super().__init__(**kwds)
        self.warning_low = None
        self.warning_high = None
        
#        self.warning_low = self.convert(float(warning_low))
#        if warning_high:
#            self.warning_high = self.convert(float(warning_high))
#        else:
#            self.warning_high = False

    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QtGui.QPainter(self)

        # warning bar
        if self.warning_low is not None:
            color = QtGui.QColor(255, 150, 150)
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(0, self.y_size - self.warning_low, self.x_size, self.y_size)

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
        painter.drawRect(2, self.height() - self.value, self.width() - 5, self.value)            


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
