#!/usr/bin/python
#
## @file
#
# Handles objectives manipulation.
#
# Hazen 07/15
#

from PyQt4 import QtCore, QtGui


## Objective
#
# Handles controls for a single objective.
#
class Objective(object):

    def __init__(self, data, fixed, parent):
        
        self.data = data
        self.fixed = fixed
        self.objective_name = data[0]
        self.qt_widgets = []

        # Add objective name.
        self.qt_widgets.append(ObjLabel(self.objective_name, parent))
        
        # Add fixed elements.
        if fixed:
            for j, datum in enumerate(data):
                self.qt_widgets.append(ObjLabel(datum, parent))

        # Or add adjustable elements.
        else:
            
            # Magnification.
            sbox = ObjDoubleSpinBox(float(data[1]), 1.0, 200.0, parent)
            sbox.setDecimals(2)
            sbox.setSingleStep(0.01)
            self.qt_widgets.append(sbox)

            # X offset.
            sbox = ObjDoubleSpinBox(float(data[2]), -10000.0, 10000.0, parent)
            self.qt_widgets.append(sbox)

            # Y offset.
            sbox = ObjDoubleSpinBox(float(data[3]), -10000.0, 10000.0, parent)
            self.qt_widgets.append(sbox)

    ## getData
    #
    # @return The data for the currently selected objective.
    #
    def getData(self):
        if self.fixed:
            return map(float, self.data[1:])
        else:
            return map(lambda(x): x.value(), self.qt_widgets[1:])

    ## getQtWidgets
    #
    # @return A list of QtWidgets associated with this objective.
    #
    def getQtWidgets(self):
        return self.qt_widgets
    
    ## select
    #
    # Indicate that this is the current objective.
    #
    def select(self, on_off):
        for widget in self.qt_widgets:
            widget.select(on_off)

        
## ObjectivesGroupBox
#
# Handle display and interaction with all the objectives.
#
class ObjectivesGroupBox(QtGui.QGroupBox):
    
    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, parent)

        self.last_objective = None
        self.layout = QtGui.QGridLayout(self)
        self.objectives = {}

        self.layout.setMargin(4)
        self.layout.setSpacing(0)

    def addObjective(self, data):
        
        # Add headers if necessary.
        if (len(self.objectives) == 0):
            for i, label_text in enumerate(["Objective", "Magnification", "X Offset", "Y Offset"]):
                text_item = QtGui.QLabel(label_text, self)
                self.layout.addWidget(text_item, 0, i)

        # Create objective managing object.
        if data[0] in self.objectives:
            return
        
        obj = Objective(data, False, self)
        self.objectives[data[0]] = obj
        
        # Add objective to layout.
        row_index = self.layout.rowCount()
        for i, item in enumerate(obj.getQtWidgets()):
            self.layout.addWidget(item, row_index, i)

        # Update selected objective
        self.updateSelected(data[0])

    def changeObjective(self, new_objective):
        self.updateSelected(new_objective)
        
    def getData(self, objective_name):
        self.updateSelected(objective_name)
        return self.objectives[objective_name].getData()
        
    def updateSelected(self, cur_objective):
        if self.last_objective is not None:
            self.last_objective.select(False)
        self.objectives[cur_objective].select(True)
        self.last_objective = self.objectives[cur_objective]


## ObjDoubleSpinBox
#
# This is just a QDoubleSpinBox with a border around it that we can
# paint to indicate that it is selected.
#
class ObjDoubleSpinBox(QtGui.QWidget):

    def __init__(self, val, minimum, maximum, parent):
        QtGui.QWidget.__init__(self, parent)
        self.selected = False
        self.spin_box = QtGui.QDoubleSpinBox(self)
        
        self.spin_box.setMaximum(maximum)
        self.spin_box.setMinimum(minimum)
        self.spin_box.setValue(val)

        layout = QtGui.QHBoxLayout(self)
        layout.setMargin(2)
        layout.addWidget(self.spin_box)

    ## paintEvent
    #
    # Paints the control UI depending on whether it is selected or not.
    #
    # @param event A PyQy paint event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.selected:
            color = QtGui.QColor(200,255,200)
        else:
            color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    ## select
    #
    # Indicate that this is the current objective.
    #
    def select(self, on_off):
        self.selected = on_off
        self.update()

    def setDecimals(self, decimals):
        self.spin_box.setDecimals(decimals)

    def setSingleStep(self, step):
        self.spin_box.setSingleStep(step)

    def value(self):
        return self.spin_box.value()


## ObjLabel
#
# This is just a QLabel that we can paint to indicate that it is selected.
#
class ObjLabel(QtGui.QLabel):

    def __init__(self, text, parent):
        QtGui.QLabel.__init__(self, text, parent)
        self.selected = False

    ## paintEvent
    #
    # Paints the control UI depending on whether it is selected or not.
    #
    # @param event A PyQy paint event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.selected:
            color = QtGui.QColor(200,255,200)
        else:
            color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())
        QtGui.QLabel.paintEvent(self, event)

    ## select
    #
    # Indicate that this is the current objective.
    #
    def select(self, on_off):
        self.selected = on_off
        self.update()


        
