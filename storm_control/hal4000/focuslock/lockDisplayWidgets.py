#!/usr/bin/python
#
## @file
#
# These widgets are used by the focusLockZ 
# class to provide user feedback.
#
# Hazen 03/12
#

from PyQt4 import QtCore, QtGui


## QStatusDisplay
#
# Base class class for the status display widgets.
#
class QStatusDisplay(QtGui.QWidget):

    ## __init__
    #
    # Create a QStatusDisplay
    #
    # @param x_size The size of the widget in x in pixels.
    # @param y_size The size of the widget in y in pixels.
    # @param scale_min The minimum value of the display bar.
    # @param scale_max The maximum value of the display bar.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, scale_min, scale_max, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.x_size = x_size
        self.y_size = y_size
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.range = scale_max - scale_min
        self.value = 0
        self.warning = False

    ## convert
    #
    # Convert input value into pixels.
    #
    # @param value The input value.
    #
    # @return Value scaled to pixels.
    #
    def convert(self, value):
        scaled = int((value - self.scale_min)/self.range * float(self.y_size))
        if scaled > self.y_size:
            scaled = self.y_size
        if scaled < 0:
            scaled = 0
        return scaled

    ## getValue
    #
    # Returns the current value
    #
    # @param normalized The value should be normalized to the range 0.0 - 1.0
    #
    # @return The current value as a floating point number.
    #
    def getValue(self, normalized = True):
        if normalized:
            return float(self.value)/float(self.y_size)
        else:
            return float(self.value)

    ## paintBackground
    #
    # Paint the background of the widget.
    #
    # @param painter A PyQt painter object.
    #
    def paintBackground(self, painter):
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

    ## updateValue
    #
    # Updates the widget display based on value.
    #
    # @param value The input value.
    #
    def updateValue(self, value, warning = False):
        self.value = self.convert(value)
        self.warning = warning
        self.update()

## QSumDisplay
#
# Focus lock sum signal display.
#
class QSumDisplay(QStatusDisplay):
    
    ## __init__
    #
    # @param x_size The size of the widget in x in pixels.
    # @param y_size The size of the widget in y in pixels.
    # @param scale_min The minimum value of the display bar.
    # @param scale_max The maximum value of the display bar.
    # @param warning_low This specifies where to draw the red bar that indicate proximity to the end of the usable range on the low side.
    # @param warning_high This specifies where to draw the red bar that indicate proximity to the end of the usable range on the high side.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, warning_high, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, scale_min, scale_max, parent = parent)
        self.warning_low = self.convert(float(warning_low))
        if warning_high:
            self.warning_high = self.convert(float(warning_high))
        else:
            self.warning_high = False

    ## paintEvent
    #
    # Handles redrawing the widget.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)

        # warning bar
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, self.y_size - self.warning_low, self.x_size, self.y_size)

        # foreground
        color = QtGui.QColor(0, 255, 0, 200)
        if self.value < self.warning_low:
            color = QtGui.QColor(255, 0, 0, 200)
        if self.warning_high:
            if self.value >= self.warning_high:
                color = QtGui.QColor(255, 0, 0, 200)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.y_size - self.value, self.x_size - 5, self.value)

## QOffsetDisplay
#
# Focus lock offset & stage position.
#
class QOffsetDisplay(QStatusDisplay):

    ## __init__
    #
    # @param x_size The size of the widget in x in pixels.
    # @param y_size The size of the widget in y in pixels.
    # @param scale_min The minimum value of the display bar.
    # @param scale_max The maximum value of the display bar.
    # @param warning_low This specifies where to draw the red bar that indicate proximity to the end of the usable range on the low side.
    # @param warning_high This specifies where to draw the red bar that indicate proximity to the end of the usable range on the high side.
    # @param has_center_bar This specifies whether or not to draw a line in the center to indicate the middle of the range.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, warning_high, has_center_bar = False, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, scale_min, scale_max, parent = parent)
        self.center_bar = 0
        if has_center_bar:
            self.center_bar = int(0.5 * self.y_size)
        self.warning_low = self.convert(float(warning_low))
        self.warning_high = self.convert(float(warning_high))
        
    ## paintEvent
    #
    # Handles redrawing the widget.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)

        # warning bars
        color = QtGui.QColor(255, 150, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, self.y_size - self.warning_low, self.x_size, self.y_size)
        painter.drawRect(0, 0, self.x_size, self.y_size - self.warning_high)

        if self.center_bar:
            color = QtGui.QColor(50, 50, 50)
            painter.setPen(color)
            painter.drawLine(0, self.center_bar, self.x_size, self.center_bar)

        # foreground
        color = QtGui.QColor(0, 0, 0, 150)
        if self.warning:
            color = QtGui.QColor(0, 255, 0, 200)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(2, self.y_size - self.value - 2, self.x_size - 5, 3)

# Stage position.
class QStageDisplay(QOffsetDisplay):
    adjustStage = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param x_size The size of the widget in x in pixels.
    # @param y_size The size of the widget in y in pixels.
    # @param scale_min The minimum value of the display bar.
    # @param scale_max The maximum value of the display bar.
    # @param warning_low This specifies where to draw the red bar that indicate proximity to the end of the usable range on the low side.
    # @param warning_high This specifies where to draw the red bar that indicate proximity to the end of the usable range on the high side.
    # @param has_center_bar This specifies whether or not to draw a line in the center to indicate the middle of the range.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, scale_min, scale_max, warning_low, warning_high, has_center_bar = 0, parent = None):
        QOffsetDisplay.__init__(self,
                                x_size,
                                y_size,
                                scale_min,
                                scale_max,
                                warning_low,
                                warning_high,
                                has_center_bar = has_center_bar,
                                parent = parent)

        self.adjust_mode = False
        self.tooltips = ["click to adjust", "use scroll wheel to move stage"]

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setToolTip(self.tooltips[0])

    ## paintBackground
    #
    # Paint the background of the widget.
    #
    # @param painter A PyQt painter object.
    #
    def paintBackground(self, painter):
        if self.adjust_mode:
            color = QtGui.QColor(180, 180, 180)
        else:
            color = QtGui.QColor(255, 255, 255)

        if (self.value < self.warning_low) or (self.value > self.warning_high):
            color = QtGui.QColor(255, 0, 0)

        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

    ## mousePressEvent
    #
    # Toggles between adjust and non-adjust mode. In adjust mode the piezo stage
    # can be moved up and down with the mouse scroll wheel.
    #
    # @param event A PyQt event.
    #
    def mousePressEvent(self, event):
        self.adjust_mode = not self.adjust_mode
        if self.adjust_mode:
            self.setToolTip(self.tooltips[1])
        else:
            self.setToolTip(self.tooltips[0])
        self.update()

    ## wheelEvent
    #
    # Handles mouse wheel events. Emits the adjustStage signal if the
    # widget is in adjust mode.
    #
    # @param wheel_event A PyQt event.
    #
    def wheelEvent(self, wheel_event):
        if self.adjust_mode:
            if (wheel_event.delta() > 0):
                self.adjustStage.emit(1)
            else:
                self.adjustStage.emit(-1)
        else:
            wheel_event.ignore()

# QPD XY position.
class QQPDDisplay(QStatusDisplay):

    ## __init__
    #
    # @param x_size The size of the widget in x in pixels.
    # @param y_size The size of the widget in y in pixels.
    # @param scale The 1/2 the size of the display in QPD units.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, scale, parent = None):
        QStatusDisplay.__init__(self, x_size, y_size, (-1 * scale), scale, parent = parent)
        self.center = self.convert(0.0) - 4
        self.x_value = 0
        self.y_value = 0

    ## paintEvent
    #
    # Handles redrawing the widget.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.paintBackground(painter)
        
        # cross hairs
        color = QtGui.QColor(50, 50, 50)
        painter.setPen(color)
        painter.drawLine(0, self.center, self.x_size, self.center)
        painter.drawLine(self.center, 0, self.center, self.y_size)

        # spot
        color = QtGui.QColor(0, 0, 0, 150)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawEllipse(self.x_value - 7, self.y_value - 7, 6, 6)

    ## updateValue
    #
    # Updates where the ellipse is drawn that indicates the current position of the QPD.
    #
    # @param x The x value from the QPD.
    # @param y The y value from the QPD.
    #
    def updateValue(self, x, y):
        self.x_value = self.convert(x)
        self.y_value = self.convert(y)
        self.update()

## QCamDisplay
#
# USB camera image display.
#
class QCamDisplay(QtGui.QWidget):    
    adjustCamera = QtCore.pyqtSignal(int, int)
    adjustOffset = QtCore.pyqtSignal(float)
    changeFitMode = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.adjust_mode = False
        self.background = QtGui.QColor(0,0,0)
        self.camera_image = None
        self.display_pixmap = None
        self.draw_e1 = True
        self.draw_e2 = True
        self.e_size = 8
        self.fit_mode = True
        self.foreground = QtGui.QColor(0,255,0)
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

    ## getImage
    #
    # @return A image from the focus lock camera.
    #
    def getImage(self):
        return self.display_pixmap

    ## keyPressEvent
    #
    # Handles key press events.
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        if self.adjust_mode:
            which_key = event.key()
            # The minimun increment (at least for the
            # Thorlabs USB camera) is two pixels.
            if (which_key == QtCore.Qt.Key_Left): 
                self.adjustCamera.emit(2,0)
            elif (which_key == QtCore.Qt.Key_Right):
                self.adjustCamera.emit(-2,0)
            elif (which_key == QtCore.Qt.Key_Up):
                self.adjustCamera.emit(0,2)
            elif (which_key == QtCore.Qt.Key_Down):
                self.adjustCamera.emit(0,-2)

            # Adjust the distance between the spots which
            # is considered to be zero.
            elif (which_key == QtCore.Qt.Key_Comma):
                self.adjustOffset.emit(-0.1)
            elif (which_key == QtCore.Qt.Key_Period):
                self.adjustOffset.emit(+0.1)

            # Adjust how to the offset is determined,
            # i.e. by fitting or by a moment calculation
            elif (which_key == QtCore.Qt.Key_M):
                self.fit_mode = not self.fit_mode
                self.changeFitMode.emit(int(self.fit_mode))

    ## mouseMoveEvent
    #
    # Handles mouse movement events.
    #
    # @param event A PyQt event.
    #
    def mouseMoveEvent(self, event):
        self.zoom_im_x = -1
        if self.display_pixmap and self.adjust_mode:
            half_size = self.zoom_size / 2
            x_bound = half_size * self.width()/self.display_pixmap.width() + 1
            y_bound = half_size * self.height()/self.display_pixmap.height() + 1
            if ((event.x() >= x_bound) and (event.x() < (self.width() - x_bound)) and (event.y() >= y_bound) and (event.y() < (self.height() - y_bound))):
                self.zoom_im_x = event.x() * self.display_pixmap.width()/self.width() - half_size
                self.zoom_im_y = event.y() * self.display_pixmap.height()/self.height() - half_size
                self.zoom_x = event.x() - half_size
                self.zoom_y = event.y() - half_size

    ## mousePressEvent
    #
    # Handles mouse press events.
    #
    # @param event A PyQt event.
    #
    def mousePressEvent(self, event):
        self.adjust_mode = not self.adjust_mode
        if self.adjust_mode:
            self.setToolTip(self.tooltips[1])
        else:
            self.setToolTip(self.tooltips[0])
        self.update()

    ## newImage
    #
    # Updates the image that will be shown in the widget given a new image from the focus lock camera.
    #
    # @param data A Python array containing the latest image from the camera and the calculated offset and sum signal.
    # @param show_dot True/False draw the flashing red dot in the corner of the display that indicates if the camera is still live.
    #    
    def newImage(self, data, show_dot):
        # Update image if data is good..
        if (type(data) == type([])):

            # Update the camera image.
            np_data = data[0]
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

            self.e_size = round(1.5 * data[5] * float(self.width())/float(w))

            # Update offsets
            if (data[1] == 0.0):
                self.draw_e1 = False
            else:
                self.draw_e1 = True
                self.x_off1 = ((data[2]+w/2)/float(w))*float(self.width())
                self.y_off1 = ((data[1]+w/2)/float(w))*float(self.height())
            
            if (data[3] == 0.0):
                self.draw_e2 = False
            else:
                self.draw_e2 = True
                self.x_off2 = ((data[4]+w/2)/float(w))*float(self.width())
                self.y_off2 = ((data[3]+w/2)/float(w))*float(self.height())

            # Red dot in camera display
            self.show_dot = show_dot

            self.update()

    ## paintEvent
    #
    # Handles redrawing the widget.
    #
    # @param event A PyQt event.
    #
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

    ## toggleCircles
    #
    # Show/hide the circles that are drawn to indicate where the fitting code
    # thinks the two laser spots are in the camera field.
    #
    def toggleCircles(self):
        self.display_circles = not self.display_circles

    ## toggleLine
    #
    # Show/hide the alignment lines.
    #
    def toggleLine(self):
        self.display_lines = not self.display_lines


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
