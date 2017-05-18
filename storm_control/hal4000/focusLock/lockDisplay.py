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
    def __init__(self, configuration = None, jump_signal = None, **kwds):
        super().__init__(**kwds)
        self.ir_laser_functionality = None
        self.ir_on = False
        self.ir_power = configuration.get("ir_power", 0)
        self.q_qpd_display = None

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

        self.q_stage_display = QStageDisplay(jump_signal = jump_signal,
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

    def handleGoodLock(self, good_lock):
        self.q_qpd_offset_display.handleGoodLock(good_lock)
    
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
        if not self.q_qpd_offset_display.haveFunctionality():
            return False
        return True

    def newParameters(self, parameters):
        self.q_stage_display.setJumpSize(parameters.get("jump_size"))
        
    def setFunctionality(self, name, functionality):
        if (name == "ir_laser"):
            self.ir_laser_functionality = functionality
            
            self.ui.irButton.show()
            self.ui.irButton.clicked.connect(self.handleIrButton)
            if self.ir_laser_functionality.hasPowerAdjustment():
                self.ui.irSlider.setMaximum(self.ir_laser_functionality.getMaximum())
                self.ui.irSlider.setMinimum(self.ir_laser_functionality.getMinimum())
                self.ui.irSlider.setValue(self.ir_power)
                self.ui.irSlider.show()
                self.ui.irSlider.valueChanged.connect(self.handleIrSlider)
        elif (name == "qpd"):
            self.q_qpd_offset_display.setFunctionality(functionality)
            self.q_qpd_sum_display.setFunctionality(functionality)

            # Display the output of a QPD.
            if (functionality.getType() == "qpd"):
                self.q_qpd_display = QQPDDisplay(q_xlabel = self.ui.qpdXText,
                                                 q_ylabel = self.ui.qpdYText,
                                                 parent = self)
                layout = QtWidgets.QGridLayout(self.ui.qpdFrame)
                layout.setContentsMargins(0,0,0,0)
                layout.addWidget(self.q_qpd_display)
                self.ui.qpdXText.show()
                self.ui.qpdYText.show()
                self.q_qpd_display.setFunctionality(functionality)

            # Display camera output.
            elif (functionality.getType() == "camera"):
                self.q_qpd_display = QCamDisplay(parent = self)
                layout = QtWidgets.QGridLayout(self.ui.qpdFrame)
                layout.setContentsMargins(0,0,0,0)
                layout.addWidget(self.q_qpd_display)
                self.q_qpd_display.setFunctionality(functionality)
                
            else:
                raise Exception("Unknown QPD type.")

        elif (name == "z_stage"):
            self.q_stage_display.setFunctionality(functionality)


class QCamDisplay(QtWidgets.QWidget):
    """
    USB camera image display.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.adjust_mode = False
        self.background = QtGui.QColor(0,0,0)
        self.camera_image = None
        self.display_pixmap = None
        self.draw_e1 = True
        self.draw_e2 = True
        self.e_size = 8
        self.fit_mode = True
        self.foreground = QtGui.QColor(0,255,0)
        self.functionality = None
        self.show_dot = False
        self.static_text = [QtGui.QStaticText("Fit"), QtGui.QStaticText("Moment")]
        self.tooltips = ["click to adjust", "<m> key to change mode\n<arrow> keys to move spots\n<,.> keys to change zero point"]
        self.zoom_image = False
        self.zoom_size = 40
        self.zoom_im_x = -1
        self.zoom_im_y = -1
        self.zoom_x = 0
        self.zoom_y = 0

        self.x_off1 = 0
        self.y_off1 = 0
        self.x_off2 = 0
        self.y_off2 = 0

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)
        self.setToolTip(self.tooltips[0])

    def getImage(self):
        """
        Return the current (displayed) image. Not used?
        """
        return self.display_pixmap

    def handleQPDUpdate(self, qpd_data):
        """
        Updates the image that will be shown in the widget given a new image 
        from the focus lock camera, as well as the fit spot locations.
        """
        
        # Update the camera image.
        np_data = qpd_data["image"]
        h, w = np_data.shape
        self.camera_image = QtGui.QImage(np_data.data, w, h, QtGui.QImage.Format_Indexed8)
        self.camera_image.ndarray = np_data
        for i in range(256):
            self.camera_image.setColor(i, QtGui.QColor(i,i,i).rgb())

        # Update display image. This is a square version of the camera image.
        self.display_pixmap = QtGui.QPixmap(w, w)
        painter = QtGui.QPainter(self.display_pixmap)

        # Draw background.
        painter.setPen(QtGui.QColor(0,0,0))
        painter.setBrush(QtGui.QColor(0,0,0))
        painter.drawRect(0, 0, w, w)

        # Draw image.
        y_start = self.display_pixmap.height()/2 - self.camera_image.height()/2
        destination_rect = QtCore.QRect(0, y_start, self.camera_image.width(), self.camera_image.height())
        painter.drawImage(destination_rect, self.camera_image)

        # Draw bounding rectangle.
        if (w != h):
            pen = QtGui.QPen(QtGui.QColor(255,0,0))
            pen.setWidth(self.display_pixmap.width()/self.width())
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(0,0,0,0))
            painter.drawRect(destination_rect)

        # Update zoomed image (if necessary).
        if (self.zoom_im_x >= 0):
            self.zoom_image = QtGui.QImage(self.zoom_size, self.zoom_size, QtGui.QImage.Format_RGB32)
            painter = QtGui.QPainter(self.zoom_image)
            painter.drawPixmap(0, 0, self.display_pixmap, self.zoom_im_x, self.zoom_im_y, self.zoom_size, self.zoom_size)
        else:
            self.zoom_image = False

        self.e_size = round(1.5 * qpd_data["sigma"] * float(self.width())/float(w))

        # Update offsets.
        if (qpd_data["x_off1"] == 0.0):
            self.draw_e1 = False
        else:
            self.draw_e1 = True
            self.x_off1 = ((qpd_data["y_off1"]+w/2)/float(w))*float(self.width())
            self.y_off1 = ((qpd_data["x_off1"]+w/2)/float(w))*float(self.height())
            
        if (qpd_data["x_off2"] == 0.0):
            self.draw_e2 = False
        else:
            self.draw_e2 = True
            self.x_off2 = ((qpd_data["y_off2"]+w/2)/float(w))*float(self.width())
            self.y_off2 = ((qpd_data["x_off2"]+w/2)/float(w))*float(self.height())

        # Red dot in camera display
        self.show_dot = not self.show_dot
        
        self.update()
    
    def haveFunctionality(self):
        return self.functionality is not None
        
    def keyPressEvent(self, event):
        if not self.haveFunctionality():
            return
        
        if self.adjust_mode:
            which_key = event.key()
            
            # The minimun increment (at least for the
            # Thorlabs USB camera) is two pixels.
            if (which_key == QtCore.Qt.Key_Left): 
                self.functionality.adjustAOI(2,0)
            elif (which_key == QtCore.Qt.Key_Right):
                self.functionality.adjustAOI(-2,0)
            elif (which_key == QtCore.Qt.Key_Up):
                self.functionality.adjustAOI(0,2)
            elif (which_key == QtCore.Qt.Key_Down):
                self.functionality.adjustAOI(0,-2)

            # Adjust the distance between the spots which
            # is considered to be zero.
            elif (which_key == QtCore.Qt.Key_Comma):
                self.functionality.adjustZeroDist(-0.1)
            elif (which_key == QtCore.Qt.Key_Period):
                self.functionality.adjustZeroDist(+0.1)

            # Adjust how to the offset is determined,
            # i.e. by fitting or by a moment calculation
            elif (which_key == QtCore.Qt.Key_M):
                self.fit_mode = not self.fit_mode
                self.functionality.changeFitMode(int(self.fit_mode))

    def mouseMoveEvent(self, event):
        if not self.haveFunctionality():
            return

        self.zoom_im_x = -1
        if self.display_pixmap and self.adjust_mode:
            half_size = self.zoom_size / 2
            x_bound = half_size * self.width()/self.display_pixmap.width() + 1
            y_bound = half_size * self.height()/self.display_pixmap.height() + 1
            if (event.x() >= x_bound) and (event.x() < (self.width() - x_bound)):
                if (event.y() >= y_bound) and (event.y() < (self.height() - y_bound)):
                    self.zoom_im_x = event.x() * self.display_pixmap.width()/self.width() - half_size
                    self.zoom_im_y = event.y() * self.display_pixmap.height()/self.height() - half_size
                    self.zoom_x = event.x() - half_size
                    self.zoom_y = event.y() - half_size

    def mousePressEvent(self, event):
        if not self.haveFunctionality():
            return

        self.adjust_mode = not self.adjust_mode
        if self.adjust_mode:
            self.setToolTip(self.tooltips[1])
        else:
            self.setToolTip(self.tooltips[0])
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.display_pixmap:

            # Draw image.
            destination_rect = QtCore.QRect(0, 0, self.width(), self.height())
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            painter.drawPixmap(destination_rect, self.display_pixmap)

            # Draw alignment lines & zoomed image.
            if self.adjust_mode:

                painter.setPen(QtGui.QColor(100,100,100))
                painter.drawLine(0.0, 0.5*self.height(), self.width(), 0.5*self.height())
                for mult in [0.25, 0.5, 0.75]:
                    painter.drawLine(mult*self.width(), 0.0, mult*self.width(), self.height())

                if self.zoom_image:
                    destination_rect = QtCore.QRect(self.zoom_x, self.zoom_y, self.zoom_size, self.zoom_size)
                    painter.drawImage(destination_rect, self.zoom_image)
                    painter.setPen(QtGui.QColor(200,200,200))
                    painter.setBrush(QtGui.QColor(0,0,0,0))
                    painter.drawRect(destination_rect)

                painter.setPen(QtGui.QColor(255,255,255))
                if self.fit_mode:
                    painter.drawStaticText(2, 102, self.static_text[0])
                else:
                    painter.drawStaticText(2, 102, self.static_text[1])

            # Draw focus lock feedback.
            else:
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                painter.setBrush(QtGui.QColor(0,0,0,0))

                # Round green circles for fitting mode.
                if self.fit_mode:
                    painter.setPen(QtGui.QColor(0,255,0))
                    if self.draw_e1:
                        painter.drawEllipse(QtCore.QPointF(self.x_off1, self.y_off1), 
                                            self.e_size, self.e_size)
                    if self.draw_e2:
                        painter.drawEllipse(QtCore.QPointF(self.x_off2, self.y_off2), 
                                            self.e_size, self.e_size)

                # Square blue boxes for moment mode.
                else:
                    painter.setPen(QtGui.QColor(0,0,255))
                    if self.draw_e1:
                        painter.drawRect(self.x_off1, self.y_off1, 2*self.e_size, 2*self.e_size)
                    if self.draw_e2:
                        painter.drawRect(self.x_off2, self.y_off2, 2*self.e_size, 2*self.e_size)

            # display red dot (or not)
            if self.show_dot:
                painter.setPen(QtGui.QColor(255,0,0))
                painter.drawRect(2,2,2,2)

        else:
            painter.setPen(self.background)
            painter.setBrush(self.background)
            painter.drawRect(0, 0, self.width(), self.height())

    def setFunctionality(self, functionality):
        self.functionality = functionality
        self.functionality.qpdUpdate.connect(self.handleQPDUpdate)


class QStatusDisplay(QtWidgets.QWidget):
    """
    Base class for (most) of the display widgets.
    """
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
        self.bar_color = QtGui.QColor(0, 0, 0, 150)
        self.has_center_bar = None

    def paintEvent(self, event):
        if self.functionality is None:
            return
        
        if not self.isEnabled():
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
        painter.setPen(self.bar_color)
        painter.setBrush(self.bar_color)
        painter.drawRect(2, self.height() - self.convert(self.value) - 2, self.width() - 5, 3)


class QQPDDisplay(QStatusDisplay):
    """
    QPD XY position. This widget is assumed to be square.
    """
    def __init__(self, q_xlabel = None, q_ylabel = None, **kwds):
        super().__init__(**kwds)
        self.q_xlabel = q_xlabel
        self.q_ylabel = q_ylabel
        self.x_value = 0
        self.y_value = 0

    def paintEvent(self, event):
        if self.functionality is None:
            return
        
        if not self.isEnabled():
            return
        
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)
        
        # cross hairs
        color = QtGui.QColor(50, 50, 50)
        center = self.convert(0.0) - 4
        painter.setPen(color)
        painter.drawLine(0, center, self.width(), center)
        painter.drawLine(center, 0, center, self.height())

        # spot
        color = QtGui.QColor(0, 0, 0, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(self.convert(self.x_value) - 7, self.convert(self.y_value) - 7, 6, 6)

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.scale_max = self.functionality.getParameter("max_voltage")
        self.scale_min = self.functionality.getParameter("min_voltage")
        
        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.functionality.qpdUpdate.connect(self.updateValue)        

    def updateValue(self, qpd_dict):
        if self.isEnabled():
            self.x_value = qpd_dict["x"]
            self.y_value = qpd_dict["y"]
            self.q_xlabel.setText("x: {0:.1f}".format(self.x_value))
            self.q_ylabel.setText("y: {0:.1f}".format(self.y_value))
            self.update()
        

class QQPDOffsetDisplay(QOffsetDisplay):
    """
    Focus lock offset display. Converts to nanometers.
    """
    def __init__(self, q_label = None, **kwds):
        super().__init__(**kwds)
        self.q_label = q_label

    def handleGoodLock(self, good_lock):
        if good_lock:
            self.bar_color = QtGui.QColor(0, 255, 0, 150)
        else:
            self.bar_color = QtGui.QColor(0, 0, 0, 150)

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.has_center_bar = self.functionality.getParameter("offset_has_center_bar")
        self.scale_max = 1000.0 * self.functionality.getParameter("offset_maximum")
        self.scale_min = 1000.0 * self.functionality.getParameter("offset_minimum")
        self.warning_high = 1000.0 * self.functionality.getParameter("offset_warning_high")
        self.warning_low = 1000.0 * self.functionality.getParameter("offset_warning_low")

        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.functionality.qpdUpdate.connect(self.updateValue)

    def updateValue(self, qpd_dict):
        if self.isEnabled():
            value = 1000.0 * qpd_dict["offset"]
            super().updateValue(value)
            self.q_label.setText("{0:.1f}".format(value))

        
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
        
        if not self.isEnabled():
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

    def setFunctionality(self, functionality):
        super().setFunctionality(functionality)
        self.scale_max = self.functionality.getParameter("sum_maximum")
        self.scale_min = self.functionality.getParameter("sum_minimum")
        if self.functionality.hasParameter("sum_warning_high"):
            self.warning_high = self.functionality.getParameter("sum_warning_high")
        if self.functionality.hasParameter("sum_warning_low"):
            self.warning_low = self.functionality.getParameter("sum_warning_low")

        self.scale_range = 1.0/(self.scale_max - self.scale_min)
        self.functionality.qpdUpdate.connect(self.updateValue)        

    def updateValue(self, qpd_dict):
        if self.isEnabled():
            value = qpd_dict["sum"]
            super().updateValue(value)
            self.q_label.setText("{0:.1f}".format(value))

        
class QStageDisplay(QOffsetDisplay):
    """
    Z stage position.
    """
    def __init__(self, jump_signal = None, q_label = None, **kwds):
        super().__init__(**kwds)
        self.jump_signal = jump_signal
        self.jump_size = None
        self.q_label = q_label
        
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

    def setJumpSize(self, jump_size):
        self.jump_size = jump_size

    def updateValue(self, value):
        if self.isEnabled():
            super().updateValue(value)
            self.q_label.setText("{0:.3f}".format(value))

    def wheelEvent(self, event):
        """
        Handles mouse wheel events. Emits the adjustStage signal 
        if the widget is in adjust mode.
        """
        if self.adjust_mode and (not event.angleDelta().isNull()):
            if (event.angleDelta().y() > 0):
                self.jump_signal.emit(self.jump_size)
            else:
                self.jump_signal.emit(-self.jump_size)
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
