#!/usr/bin/python
#
## @file
#
# Qt Widget Range slider widget. This is a slider with two bars, one of
# which is used to set the maximum and the other of which is used to
# set the minimum.
#
# Qt Double Spin Box slider widget. This is the range slider grouped
# with two spin boxes to make the range editable.
#
# Hazen 07/14
#

import decimal
from PyQt4 import QtCore, QtGui
import sys

## QRangeSlider
#
# Range Slider super class.
#
class QRangeSlider(QtGui.QWidget):
    doubleClick = QtCore.pyqtSignal(bool)
    rangeChanged = QtCore.pyqtSignal(float, float)

    ## __init__
    #
    # @param slider_range [min, max, step size].
    # @param values [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range, values, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.bar_width = 10
        self.emit_while_moving = False
        self.moving = "none"
        self.old_scale_min = 0.0
        self.old_scale_max = 0.0
        self.scale = 0
        self.setMouseTracking(False)
        self.single_step = 0.0

        if slider_range:
            self.setRange(slider_range)
        else:
            self.setRange([0.0, 1.0, 0.01])
        if values:
            self.setValues(values)
        else:
            self.setValues([0.3, 0.6])

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    ## emitRange
    #
    # Emits the rangeChanged signal, if the range has actually changed.
    #
    def emitRange(self):
        if (self.old_scale_min != self.scale_min) or (self.old_scale_max != self.scale_max):
            self.rangeChanged.emit(self.scale_min, self.scale_max)
            self.old_scale_min = self.scale_min
            self.old_scale_max = self.scale_max
            if 0:
                print "Range change:", self.scale_min, self.scale_max

    ## getValues
    #
    # @return [current minimum, current maximum].
    #
    def getValues(self):
        return [self.scale_min, self.scale_max]

    ## keyPressEvent
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        key = event.key()

        # move bars based on arrow keys
        moving_max = False
        if key == QtCore.Qt.Key_Up:
            self.scale_max += self.single_step
            moving_max = True
        elif key == QtCore.Qt.Key_Down:
            self.scale_max -= self.single_step
            moving_max = True
        elif key == QtCore.Qt.Key_Left:
            self.scale_min -= self.single_step
        elif key == QtCore.Qt.Key_Right:
            self.scale_min += self.single_step

        # update (if necessary) based on allowed range
        if moving_max:
            if (self.scale_max < self.scale_min):
                self.scale_min = self.scale_max
        else:
            if (self.scale_min > self.scale_max):
                self.scale_max = self.scale_min

        if (self.scale_min < self.start):
            self.scale_min = self.start
        if (self.scale_max < self.start):
            self.scale_max = self.start

        slider_max = self.start + self.scale
        if (self.scale_min > slider_max):
            self.scale_min = slider_max
        if (self.scale_max > slider_max):
            self.scale_max = slider_max

        self.emitRange()
        self.updateDisplayValues()
        self.update()

    ## mouseDoubleClickEvent
    #
    # Emits a doubleClick signal when the user double clicks on the slider.
    #
    # @param event A PyQt double click event.
    #
    def mouseDoubleClickEvent(self, event):
        self.doubleClick.emit(True)

    ## mouseMoveEvent
    #
    # Handles moving the slider bars if necessary.
    #
    # @param event A PyQt mouse motion event.
    #
    def mouseMoveEvent(self, event):
        size = self.rangeSliderSize()
        diff = self.start_pos - self.getPos(event)
        if self.moving == "min":
            temp = self.start_display_min - diff
            if (temp >= self.bar_width) and (temp < size - self.bar_width):
                self.display_min = temp
                if self.display_max < self.display_min:
                    self.display_max = self.display_min
                self.updateScaleValues()
                if self.emit_while_moving:
                    self.emitRange()
        elif self.moving == "max":
            temp = self.start_display_max - diff
            if (temp >= self.bar_width) and (temp < size - self.bar_width):
                self.display_max = temp
                if self.display_max < self.display_min:
                    self.display_min = self.display_max
                self.updateScaleValues()
                if self.emit_while_moving:
                    self.emitRange()
        elif self.moving == "bar":
            temp = self.start_display_min - diff
            if (temp >= self.bar_width) and (temp < size - self.bar_width - (self.start_display_max - self.start_display_min)):
                self.display_min = temp
                self.display_max = self.start_display_max - diff
                self.updateScaleValues()
                if self.emit_while_moving:
                    self.emitRange()

    ## mousePressEvent
    #
    # If the mouse is pressed down when the cursor is over one of the slider bars
    # then we need to move the slider bar as the mouse moves.
    #
    # @param event A PyQt event.
    #
    def mousePressEvent(self, event):
        pos = self.getPos(event)
        if abs(self.display_min - 0.5 * self.bar_width - pos) < (0.5 * self.bar_width):
            self.moving = "min"
        elif abs(self.display_max + 0.5 * self.bar_width - pos) < (0.5 * self.bar_width):
            self.moving = "max"
        elif (pos > self.display_min) and (pos < self.display_max):
            self.moving = "bar"
        self.start_display_min = self.display_min
        self.start_display_max = self.display_max
        self.start_pos = pos

    ## mouseReleaseEvent
    #
    # Stop moving the slider bar when the mouse is released.
    #
    # @param event A PyQt event.
    #
    def mouseReleaseEvent(self, event):
        if not (self.moving == "none"):
            self.emitRange()
        self.moving = "none"

    ## resiveEvent
    #
    # Handles adusting the (displayed) scroll bars positions when the slider is resized.
    #
    # @param event A PyQt event.
    #
    def resizeEvent(self, event):
        self.updateDisplayValues()

    ## setEmitWhileMoving
    #
    # Set whether or not to emit rangeChanged signal while the slider is being moved with the mouse.
    #
    # @param flag True/False emit while moving.
    #
    def setEmitWhileMoving(self, flag):
        if flag:
            self.emit_while_moving = True
        else:
            self.emit_while_moving = False

    ## setRange
    #
    # @param slider_range [min, max, step size].
    #
    def setRange(self, slider_range):
        self.start = slider_range[0]
        self.scale = slider_range[1] - slider_range[0]
        self.single_step = slider_range[2]

        # Check that the range is a multiple of the step size.
        steps = self.scale / self.single_step
        if (abs(steps - round(steps)) > 0.01 * self.single_step):
            raise Exception("Slider range is not a multiple of the step size!")

    ## setValues
    #
    # @param values [position of minimum slider, position of maximum slider].
    #
    def setValues(self, values):
        self.scale_min = values[0]
        self.scale_max = values[1]
        self.emitRange()
        self.updateDisplayValues()
        self.update()

    ## updateDisplayValues
    #
    # This updates the display value, i.e. the real location in the widgets where the bars are drawn.
    #
    def updateDisplayValues(self):
        size = float(self.rangeSliderSize() - 2 * self.bar_width - 1)
        self.display_min = int(size * (self.scale_min - self.start)/self.scale) + self.bar_width
        self.display_max = int(size * (self.scale_max - self.start)/self.scale) + self.bar_width

    ## updateScaleValues
    #
    # This updates the internal / real values that correspond to the current slider positions.
    #
    def updateScaleValues(self):
        size = float(self.rangeSliderSize() - 2 * self.bar_width - 1)
        if (self.moving == "min") or (self.moving == "bar"):
            self.scale_min = self.start + (self.display_min - self.bar_width)/float(size) * self.scale
            self.scale_min = float(round(self.scale_min/self.single_step))*self.single_step
        if (self.moving == "max") or (self.moving == "bar"):
            self.scale_max = self.start + (self.display_max - self.bar_width)/float(size) * self.scale
            self.scale_max = float(round(self.scale_max/self.single_step))*self.single_step
        self.updateDisplayValues()
        self.update()


## QHRangeSlider
#
# Horizontal Range Slider.
#
class QHRangeSlider(QRangeSlider):

    ## __init__
    #
    # @param slider_range (Optional) [min, max, step size].
    # @param values (Optional) [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range = None, values = None, parent = None):
        QRangeSlider.__init__(self, slider_range, values, parent)
        if (not parent):
            self.setGeometry(200, 200, 200, 100)

    ## getPos
    #
    # @param event A PyQt event.
    #
    # @return The location in x of the event.
    #
    def getPos(self, event):
        return event.x()

    ## paintEvent
    #
    # Draw the horizontal slider.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        w = self.width()
        h = self.height()

        # background
        painter.setPen(QtCore.Qt.gray)
        painter.setBrush(QtCore.Qt.lightGray)
        painter.drawRect(2, 2, w-4, h-4)

        # range bar
        painter.setPen(QtCore.Qt.darkGray)
        painter.setBrush(QtCore.Qt.darkGray)
        painter.drawRect(self.display_min-1, 5, self.display_max-self.display_min+2, h-10)

        # min & max tabs
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(self.display_min-self.bar_width, 1, self.bar_width, h-2)

        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(self.display_max, 1, self.bar_width, h-2)

    ## rangeSliderSize
    #
    # @return The current width of the slider widget.
    #
    def rangeSliderSize(self):
        return self.width()


## QVRangeSlider
#
# Vertical Range Slider.
#
class QVRangeSlider(QRangeSlider):

    ## __init__
    #
    # @param slider_range (Optional) [min, max, step size].
    # @param values (Optional) [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range = None, values = None, parent = None):
        QRangeSlider.__init__(self, slider_range, values, parent)
        if (not parent):
            self.setGeometry(200, 200, 100, 200)

    ## getPos
    #
    # @param event A PyQt event.
    #
    # @return The location in x of the event.
    #
    def getPos(self, event):
        return self.height() - event.y()

    ## paintEvent
    #
    # Draw the vertical slider.
    #
    # @param event A PyQt event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        w = self.width()
        h = self.height()

        # background
        painter.setPen(QtCore.Qt.gray)
        painter.setBrush(QtCore.Qt.lightGray)
        painter.drawRect(2, 2, w-4, h-4)

        # range bar
        painter.setPen(QtCore.Qt.darkGray)
        painter.setBrush(QtCore.Qt.darkGray)
        painter.drawRect(5, h-self.display_max-1, w-10, self.display_max-self.display_min+1)

        # min & max tabs
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(1, h-self.display_max-self.bar_width-1, w-2, self.bar_width)

        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.gray)
        painter.drawRect(1, h-self.display_min-1, w-2, self.bar_width)

    ## rangeSliderSize
    #
    # @return The current height of the slider widget.
    #
    def rangeSliderSize(self):
        return self.height()


## QSpinBoxRangeSlider
#
# Range slider with two double spin boxes super class.
#
class QSpinBoxRangeSlider(QtGui.QWidget):
    doubleClick = QtCore.pyqtSignal(bool)
    rangeChanged = QtCore.pyqtSignal(float, float)

    ## __init__
    #
    # @param slider_range [min, max, step size].
    # @param values [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range, values, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.max_val = values[1]
        self.min_val = values[0]
        self.range_slider = False

        # Attempt to calculate the appropriate number of decimal points.
        dec_pnts = abs(decimal.Decimal(slider_range[2]).as_tuple().exponent)

        self.min_spin_box = QtGui.QDoubleSpinBox()
        self.min_spin_box.setDecimals(dec_pnts)
        self.min_spin_box.setMinimum(slider_range[0])
        self.min_spin_box.setMaximum(slider_range[1])
        self.min_spin_box.setSingleStep(slider_range[2])
        self.min_spin_box.setValue(values[0])
        self.min_spin_box.valueChanged.connect(self.handleMinSpinBox)

        self.max_spin_box = QtGui.QDoubleSpinBox()
        self.max_spin_box.setDecimals(dec_pnts)
        self.max_spin_box.setMinimum(slider_range[0])
        self.max_spin_box.setMaximum(slider_range[1])
        self.max_spin_box.setSingleStep(slider_range[2])
        self.max_spin_box.setValue(values[1])
        self.max_spin_box.valueChanged.connect(self.handleMaxSpinBox)

    ## addRangeSlider
    #
    # Adds the range slider element and connects it's signals.
    #
    # @param range_slider
    #
    def addRangeSlider(self, range_slider):
        self.range_slider = range_slider

        # Make range slider take as much of the space as possible.
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        self.range_slider.setSizePolicy(size_policy)

        # Connect signals/
        self.range_slider.doubleClick.connect(self.handleDoubleClick)
        self.range_slider.rangeChanged.connect(self.handleRangeChange)

    ## adjustValue
    #
    # Checks that the value is a multiple of the step size, rounds to the
    # nearest step if it is not.
    #
    # @param a_value.
    #
    # @return [The adjusted value, True / False if it was adjusted].
    #
    def adjustValue(self, new_value):
        adj = round(new_value / self.range_slider.single_step)
        adj = adj * self.range_slider.single_step
        return adj

    ## emitRangeChange
    #
    # Emit range changed signal, but only if it actually changed.
    # This also updates the range slider.
    #
    def emitRangeChange(self):
        should_emit = False
        if (self.min_val != self.min_spin_box.value()):
            self.min_val = self.min_spin_box.value()
            should_emit = True
        if (self.max_val != self.max_spin_box.value()):
            self.max_val = self.max_spin_box.value()
            should_emit = True
        if should_emit:
            if 0:
                print self.min_val, self.max_val
            self.range_slider.setValues([self.min_val, self.max_val])
            self.rangeChanged.emit(self.min_val, self.max_val)

    ## getValues
    #
    # @return [current minimum, current maximum].
    #
    def getValues(self):
        return [self.min_spin_box.value(),
                self.max_spin_box.value()]

    ## handleDoubleClick
    #
    # This just passes on the double click signal from the range slider.
    #
    # @param boolean A dummy parameter.
    #
    def handleDoubleClick(self, boolean):
        self.doubleClick.emit(boolean)
    
    ## handleMaxSpinBox
    #
    # @param new_value The new value of the spin box.
    #
    def handleMaxSpinBox(self, new_value):
        cur_value = self.max_spin_box.value()
        self.max_spin_box.setValue(self.adjustValue(new_value))
        if (new_value < self.min_spin_box.value()):
            self.min_spin_box.setValue(new_value)

        self.emitRangeChange()

    ## handleMinSpinBox
    #
    # @param new_value The new value of the spin box.
    #
    def handleMinSpinBox(self, new_value):
        self.min_spin_box.setValue(self.adjustValue(new_value))
        if (new_value > self.max_spin_box.value()):
            self.max_spin_box.setValue(new_value)

        self.emitRangeChange()

    ## handleRangeChange
    #
    # Handles the range changed signal from the range slider.]
    #
    # @param min_val, max_val
    #
    def handleRangeChange(self, min_val, max_val):
        self.min_spin_box.setValue(min_val)
        self.max_spin_box.setValue(max_val)

    ## setEmitWhileMoving
    #
    # Set whether or not to emit rangeChanged signal while the slider is being moved with the mouse.
    #
    # @param flag True/False emit while moving.
    #
    def setEmitWhileMoving(self, flag):
        self.range_slider.setEmitWhileMoving(flag)
        

## QHSpinBoxRangeSlider
#
# Horizontal range slider with two double spin boxes.
#
class QHSpinBoxRangeSlider(QSpinBoxRangeSlider):

    ## __init__
    #
    # @param slider_range [min, max, step size].
    # @param values [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range, values, parent = None):
        QSpinBoxRangeSlider.__init__(self, slider_range, values, parent)
        self.addRangeSlider(QHRangeSlider(slider_range, values, self))

        if (not parent):
            self.setGeometry(200, 200, 300, 100)

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.min_spin_box)
        self.layout.addWidget(self.range_slider)
        self.layout.addWidget(self.max_spin_box)


## QVSpinBoxRangeSlider
#
# Vertical range slider with two double spin boxes.
#
class QVSpinBoxRangeSlider(QSpinBoxRangeSlider):

    ## __init__
    #
    # @param slider_range [min, max, step size].
    # @param values [initial minimum setting, initial maximum setting].
    # @param parent (Optional) The PyQt parent of this widget.
    #
    def __init__(self, slider_range, values, parent = None):
        QSpinBoxRangeSlider.__init__(self, slider_range, values, parent)
        self.addRangeSlider(QVRangeSlider(slider_range, values, self))

        if (not parent):
            self.setGeometry(200, 200, 100, 300)

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.max_spin_box)
        self.layout.addWidget(self.range_slider)
        self.layout.addWidget(self.min_spin_box)

## QRangeSliderDialog
#
# A dialog wrapper around a QRangeSlider
#
class QRangeSliderDialog(QtGui.QDialog):
    ## __init__
    #
    # @param title_text The title of the dialog
    # @param slider_range The range and increment of the slider [min, max, step size].
    # @param values The initial [min, max] of the slider
    # @param Slider type
    #
    def __init__(self, parent=None,
                 title_text = "Range Selection",
                 slider_range = [0, 10, 1],
                 values = [0, 10],
                 slider_type = "horizontal"):
        QtGui.QDialog.__init__(self, parent)

        # Update window title
        self.setWindowTitle(title_text)

        # Create and add QRange Widget
        if slider_type == "horizontal":
            self.range_widget = QHSpinBoxRangeSlider(slider_range, values)
        else:
            self.range_widget = QVSpinBoxRangeSlider(slider_range, values)

        # Create layout, add widget, and add buttons    
        layout = QtGui.QGridLayout()
        layout.addWidget(self.range_widget, 0,0)
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)

        layout.addWidget(self.button_box, 1, 0)
        self.setLayout(layout)
        
        # Connect buttons
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
    # getValues
    #
    # Return the current range values
    #
    def getValues(self):
        return self.range_widget.getValues()
   
#
# Testing
#

if __name__ == "__main__":
    class Parameters:
        def __init__(self):
            self.x_pixels = 200
            self.y_pixels = 200

    app = QtGui.QApplication(sys.argv)
    if 0:
        hslider = QHRangeSlider(slider_range = [-5.0, 5.0, 0.5], values = [-2.5, 2.5])
        hslider.setEmitWhileMoving(True)
        hslider.show()
    if 0:
        vslider = QVRangeSlider(slider_range = [-5.0, 5.0, 0.5], values = [-2.5, 2.5])
        vslider.setEmitWhileMoving(True)
        vslider.show()
    if 0:
        dhslider = QHSpinBoxRangeSlider(slider_range = [-5.0, 5.0, 0.5], values = [-2.5, 2.5])
        dhslider.setEmitWhileMoving(True)
        dhslider.show()
    if 0:
        dhslider = QVSpinBoxRangeSlider(slider_range = [-10, 10, 0.5], values = [-2, 2])
        dhslider.setEmitWhileMoving(True)
        dhslider.show()        
    if 1:
        dialog = QRangeSliderDialog(title_text = "Range Slider",
                                    slider_range = [-10,10,0.5],
                                    values = [-5, 5])
        if dialog.exec_():
            print dialog.getValues()

    sys.exit(app.exec_())


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

