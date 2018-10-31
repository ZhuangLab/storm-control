#!/usr/bin/env python
"""
Handles objectives manipulation.

X/Y offsets are in units of microns.

Hazen 10/18
"""
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.imageItem as imageItem
import storm_control.steve.steveItems as steveItems
    
    
class Objective(QtCore.QObject):
    """
    Handles controls for a single objective.
    """
    magnificationChanged = QtCore.pyqtSignal(str, float)
    offsetChanged = QtCore.pyqtSignal(str, float, float)

    def __init__(self, fixed = None, objective_item = None, objective_name = None, **kwds):
        super().__init__(**kwds)
        
        self.fixed = fixed
        self.objective_item = objective_item
        self.qt_widgets = []

        # Add objective name.
        self.qt_widgets.append(ObjLabel(self.objective_item.objective_name))
        
        # Add fixed elements.
        if fixed:
            for elt in self.objective_item.getData():
                self.qt_widgets.append(ObjLabel("{0:.2f}".format(elt)))

        # Or add adjustable elements.
        else:
            
            # Microns per pixel.
            sbox = ObjDoubleSpinBox(self.objective_item.um_per_pixel, 0.01, 100.0)
            sbox.setDecimals(2)
            sbox.setSingleStep(0.01)
            sbox.valueChanged.connect(self.handleMagChanged)
            self.qt_widgets.append(sbox)

            # X offset in microns.
            sbox = ObjDoubleSpinBox(self.objective_item.x_offset, -10000.0, 10000.0)
            sbox.valueChanged.connect(self.handleXOffsetChanged)
            self.qt_widgets.append(sbox)

            # Y offset in microns.
            sbox = ObjDoubleSpinBox(self.objective_item.y_offset, -10000.0, 10000.0)
            sbox.valueChanged.connect(self.handleYOffsetChanged)
            self.qt_widgets.append(sbox)

    def getData(self):
        """
        Return the data for the objective.
        """
        return self.objective_item.getData()
        
    def getQtWidgets(self):
        """
        Return a list of QtWidgets associated with this objective.
        """
        return self.qt_widgets

    def handleMagChanged(self, value):
        self.objective_item.um_per_pixel = value
        self.magnificationChanged.emit(self.objective_item.objective_name,
                                       self.objective_item.um_per_pixel)

    def handleXOffsetChanged(self, value):
        self.objective_item.x_offset = value
        self.offsetChanged.emit(self.objective_item.objective_name,
                                self.objective_item.x_offset,
                                self.objective_item.y_offset)

    def handleYOffsetChanged(self, value):
        self.objective_item.y_offset = value
        self.offsetChanged.emit(self.objective_item.objective_name,
                                self.objective_item.x_offset,
                                self.objective_item.y_offset)

    def select(self, on_off):
        """
        Indicate that this is the current objective.
        """
        for widget in self.qt_widgets:
            widget.select(on_off)


class ObjectiveItem(steveItems.SteveItem):
    """
    The settings for a objective are saved with the mosaic file. This
    class handles this feature.
    """
    data_type = "objective"

    def __init__(self, objective_name = None, um_per_pixel = None, x_offset = None, y_offset = None, **kwds):
        super().__init__(**kwds)

        self.objective_name = objective_name
        self.um_per_pixel = um_per_pixel
        self.x_offset = x_offset
        self.y_offset = y_offset

    def getData(self):
        return [self.um_per_pixel, self.x_offset, self.y_offset]

    def saveItem(self, directory, name_no_extension):
        text = self.objective_name
        text += ",{0:.2f},{1:.2f},{2:.2f}".format(self.um_per_pixel, self.x_offset, self.y_offset) 
        return text


class ObjectiveItemLoader(steveItems.SteveItemLoader):
    """
    Creates a ObjectiveItem from saved data and adds to ObjectivesGroupBox instance.
    """
    def __init__(self, objective_group_box = None, **kwds):
        super().__init__(**kwds)
        self.objective_group_box = objective_group_box

    def load(self, directory, *data):
        self.objective_group_box.addObjective(data)
        

class ObjectivesGroupBox(QtWidgets.QGroupBox):
    """
    Handle display and interaction with all the objectives.

    self.objectives is keyed by the objective name, see addObjective().
    """
    
    def __init__(self, parent):
        super().__init__(parent)

        self.item_store = None
        self.last_objective = None
        self.layout = QtWidgets.QGridLayout(self)
        self.objectives = {}

        self.layout.setContentsMargins(4,4,4,4)
        self.layout.setSpacing(0)

    def addObjective(self, data):
        """
        data is a list containing [objective name, um_per_pixel, x offset, y offset].
        """
        # Add headers if necessary.
        if (len(self.objectives) == 0):
            for i, label_text in enumerate(["Objective", "Um / Pixel", "X Offset", "Y Offset"]):
                text_item = QtWidgets.QLabel(label_text, self)
                self.layout.addWidget(text_item, 0, i)

        # Return if this objective already exists.
        if data[0] in self.objectives:
            return

        # Create objective item.
        obj_item = ObjectiveItem(objective_name = data[0],
                                 um_per_pixel = float(data[1]),
                                 x_offset = float(data[2]),
                                 y_offset = float(data[3]))
        self.item_store.addItem(obj_item)

        # Create objective managing object.
        obj = Objective(fixed = False,
                        objective_item = obj_item,
                        parent = self)
        obj.magnificationChanged.connect(self.handleMagnificationChanged)
        obj.offsetChanged.connect(self.handleOffsetChanged)
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

    def handleMagnificationChanged(self, objective_name, magnification):
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getObjectiveName() == objective_name):
                item.setMagnification(magnification)

    def handleOffsetChanged(self, objective_name, x_offset, y_offset):
        for item in self.item_store.itemIterator(item_type = imageItem.ImageItem):
            if (item.getObjectiveName() == objective_name):
                item.setOffset(x_offset, y_offset)
    
    def hasObjective(self, objective_name):
        return (objective_name in self.objectives)
    
    def setItemStore(self, item_store):
        self.item_store = item_store
    
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

    def __init__(self, val, minimum, maximum):
        super().__init__()
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

    def __init__(self, text):
        super().__init__(text)
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
