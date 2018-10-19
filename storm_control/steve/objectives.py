#!/usr/bin/env python
"""
Handles objectives manipulation.

X/Y offsets are in units of microns.

Hazen 10/18
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class Objective(QtCore.QObject):
    """
    Handles controls for a single objective.
    """
    valueChanged = QtCore.pyqtSignal(str, str, float)

    def __init__(self, data, fixed, parent):
        super().__init__(parent)
        
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
            
            # Microns per pixel.
            sbox = ObjDoubleSpinBox(float(data[1]), 0.01, 100.0, parent)
            sbox.setDecimals(2)
            sbox.setSingleStep(0.01)
            sbox.valueChanged.connect(self.handleMagChanged)
            self.qt_widgets.append(sbox)

            # X offset in microns.
            sbox = ObjDoubleSpinBox(float(data[2]), -10000.0, 10000.0, parent)
            sbox.valueChanged.connect(self.handleXOffsetChanged)
            self.qt_widgets.append(sbox)

            # Y offset in microns.
            sbox = ObjDoubleSpinBox(float(data[3]), -10000.0, 10000.0, parent)
            sbox.valueChanged.connect(self.handleYOffsetChanged)
            self.qt_widgets.append(sbox)

    def getData(self):
        """
        Return the data for the currently selected objective.
        """
        if self.fixed:
            return map(float, self.data[1:])
        else:
            return map(lambda x: x.value(), self.qt_widgets[1:])
    def getQtWidgets(self):
        """
        Return a list of QtWidgets associated with this objective.
        """
        return self.qt_widgets

    def handleMagChanged(self, value):
        self.valueChanged.emit(self.objective_name, "micron_per_pixel", value)

    def handleXOffsetChanged(self, value):
        self.valueChanged.emit(self.objective_name, "xoffset", value)

    def handleYOffsetChanged(self, value):
        self.valueChanged.emit(self.objective_name, "yoffset", value)

    def select(self, on_off):
        """
        Indicate that this is the current objective.
        """
        for widget in self.qt_widgets:
            widget.select(on_off)


class ObjectivesGroupBox(QtWidgets.QGroupBox):
    """
    Handle display and interaction with all the objectives.
    """
    valueChanged = QtCore.pyqtSignal(str, str, float)
    
    def __init__(self, parent):
        super().__init__(parent)

        self.last_objective = None
        self.layout = QtWidgets.QGridLayout(self)
        self.objectives = {}

        self.layout.setContentsMargins(4,4,4,4)
        self.layout.setSpacing(0)

    def addObjective(self, data):
        
        # Add headers if necessary.
        if (len(self.objectives) == 0):
            for i, label_text in enumerate(["Objective", "Um / Pixel", "X Offset", "Y Offset"]):
                text_item = QtWidgets.QLabel(label_text, self)
                self.layout.addWidget(text_item, 0, i)

        # Create objective managing object.
        if data[0] in self.objectives:
            return
        
        obj = Objective(data, False, self)
        obj.valueChanged.connect(self.handleValueChanged)
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

    def handleValueChanged(self, objective, pname, value):
        self.valueChanged.emit(objective, pname, value)

    def hasObjective(self, objective_name):
        return (objective_name in self.objectives)
    
    def updateSelected(self, cur_objective):
        if self.last_objective is not None:
            self.last_objective.select(False)
        self.objectives[cur_objective].select(True)
        self.last_objective = self.objectives[cur_objective]


class ObjDoubleSpinBox(QtWidgets.QWidget):
    """
    This is just a QDoubleSpinBox with a border around it 
    that we can paint to indicate that it is selected.
    """
    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, val, minimum, maximum, parent):
        super().__init__(parent)
        self.selected = False
        self.spin_box = QtWidgets.QDoubleSpinBox(self)
        
        self.spin_box.setMaximum(maximum)
        self.spin_box.setMinimum(minimum)
        self.spin_box.setValue(val)
        self.spin_box.valueChanged.connect(self.handleValueChanged)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2,2,2,2)
        layout.addWidget(self.spin_box)

    def handleValueChanged(self, value):
        self.valueChanged.emit(value)
        
    def paintEvent(self, event):
        """
        Paints the control UI depending on whether it is selected or not.
        """
        painter = QtGui.QPainter(self)
        if self.selected:
            color = QtGui.QColor(200,255,200)
        else:
            color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    def select(self, on_off):
        """
        Indicate that this is the current objective.
        """
        self.selected = on_off
        self.update()

    def setDecimals(self, decimals):
        self.spin_box.setDecimals(decimals)

    def setSingleStep(self, step):
        self.spin_box.setSingleStep(step)

    def value(self):
        return self.spin_box.value()


class ObjLabel(QtWidgets.QLabel):
    """
    This is just a QLabel that we can paint to indicate that it is selected.
    """

    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.selected = False

    def paintEvent(self, event):
        """
        Paints the control UI depending on whether it is selected or not.
        """
        painter = QtGui.QPainter(self)
        if self.selected:
            color = QtGui.QColor(200,255,200)
        else:
            color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())
        QtWidgets.QLabel.paintEvent(self, event)

    def select(self, on_off):
        """
        Indicate that this is the current objective.
        """
        self.selected = on_off
        self.update()
