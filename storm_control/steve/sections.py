#!/usr/bin/env python
"""
The handles all the UI elements in the Mosaic tab.

Hazen 10/18
"""
import numpy
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.sc_library.hdebug as hdebug

import storm_control.steve.coord as coord
import storm_control.steve.qtdesigner.sections_ui as sectionsUi
import storm_control.steve.steveItems as steveItems
import storm_control.steve.steveModule as steveModule


class SectionItem(steveItems.SteveItem):

    brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
    deselected_pen = QtGui.QPen(QtGui.QColor(0,0,255))
    fields = ["x", "y", "angle"]
    selected_pen = QtGui.QPen(QtGui.QColor(255,0,0))
    ellipse_size = 1
    
    def __init__(self, a_point = None, **kwds):
        super().__init__(**kwds)

        self.a_point = None
        self.angle = 0
        self.text = ""

        self.x_size = coord.umToPix(self.ellipse_size)
        self.y_size = coord.umToPix(self.ellipse_size)
        
        self.graphics_item = QtWidgets.QGraphicsEllipseItem(0, 0, self.x_size, self.y_size)
        self.graphics_item.setBrush(self.brush)
        self.graphics_item.setPen(self.deselected_pen)
        self.graphics_item.setZValue(999.0)
        self.setLocation(a_point)

    def changeField(self, field, df):
        if (field == "x"):
            self.movePosition(df, 0.0)
        elif (field == "y"):
            self.movePosition(0.0, df)
        elif (field == "angle"):
            self.angle += d_angle
            if (self.angle > 360.0):
                self.angle -= 360.0
            if (self.angle < 0.0):
                self.angle += 360.0
        else:
            assert False, "No field " + field + "!"
            
    def getField(self, field):

        # These need to match self.fields.
        if (field == "x"):
            return self.a_point.x_um
        elif (field == "y"):
            return self.a_point.y_um
        elif (field == "angle"):
            return self.angle
        else:
            assert False, "No field " + field + "!"
        
    def movePosition(self, dx_um, dy_um):
        a_point = coord.Point(self.a_point.x_um + dx_um,
                              self.a_point.y_um + dy_um,
                              "um")
        self.setLocation(a_point)

#    def saveItem(self, directory, name_no_extension):
#        return self.text

    def setAngle(self, angle):
        self.angle = angle

#        self.text = "{0:.2f},{1:.2f}".format(a_point.x_um, a_point.y_um)

    def setLocation(self, a_point):
        self.a_point = a_point
        self.graphics_item.setPos(a_point.x_pix - 0.5 * self.x_size,
                                  a_point.y_pix - 0.5 * self.y_size)

    def setSelected(self, selected):
        """
        If the object is selected, increase it's z value and change the pen
        color, otherwise set the object's z value and pen color back to the
        unselected values.
        """
        if selected:
            self.graphics_item.setZValue(1999.0)
            self.graphics_item.setPen(self.selected_pen)
        else:
            self.graphics_item.setZValue(999.0)
            self.graphics_item.setPen(self.deselected_pen)
        


class Sections(steveModule.SteveModule):

    @hdebug.debug
    def __init__(self, image_capture = None, **kwds):
        super().__init__(**kwds)

        self.image_capture = image_capture

        SectionItem.ellipse_size = self.parameters.get("ellipse_size")
        SectionItem.deselected_pen.setWidth(self.parameters.get("pen_width"))
        SectionItem.selected_pen.setWidth(self.parameters.get("pen_width"))
        
        self.ui = sectionsUi.Ui_Form()
        self.ui.setupUi(self)

        self.sections_model = QtGui.QStandardItemModel()
        self.sections_model.setHorizontalHeaderLabels(SectionItem.fields)
        
        self.sections_view = SectionsTableView(step_size = self.parameters.get("step_size"))
        self.sections_view.setModel(self.sections_model)
        self.sections_view.setTitleBar(self.ui.sectionsGroupBox)

        layout = QtWidgets.QVBoxLayout(self.ui.sectionsGroupBox)
        layout.addWidget(self.sections_view)
        layout.setContentsMargins(0,0,0,0)
        self.ui.sectionsGroupBox.setLayout(layout)
        
    def addSection(self, a_point, a_angle):
        """
        Add a single section to the model & the scene.
        """
        # Create section item.
        section_item = SectionItem(a_point = a_point)
        section_item.setAngle(a_angle)

        # Add to scene.
        self.item_store.addItem(section_item)
        
        # Add to model. The elements in a row all share the same item.
        row = []
        for field in section_item.fields:
            row.append(SectionsStandardItem(field = field,
                                            section_item = section_item))
        self.sections_model.appendRow(row)
        
    def handleAddSection(self, ignored):
        """
        This is called by the popup menu in the mosaic tab or a 
        key press event in the mosiacs view.
        """
        self.addSection(self.mosaic_event_coord, 0)


class SectionsTableView(QtWidgets.QTableView):

    def __init__(self, step_size = None, **kwds):
        super().__init__(**kwds)

        self.initialized_widths = False
        self.step_size = step_size

        # Disable direct editting.
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.setToolTip("'w','s' to change selected cell value, 'backspace' to delete row, arrow keys to change cells.")

    def keyPressEvent(self, event):
        current_item = self.model().itemFromIndex(self.currentIndex())
        if isinstance(current_item, SectionsStandardItem):
            which_key = event.key()

            # Delete current item.
            if (which_key == QtCore.Qt.Key_Backspace) or (which_key == QtCore.Qt.Key_Delete):
                self.model().removeRow(self.currentIndex().row())
                self.item_store.removeItem(current_item.section_item.getItemID())
                self.updateTitle()
                
            elif (which_key == QtCore.Qt.Key_W):
                current_item.changeValue(-self.step_size)
            elif (which_key == QtCore.Qt.Key_S):
                current_item.changeValue(self.step_size)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def resizeEvent(self, event):
        if not self.initialized_widths:
            self.initialized_widths = True
                        
            width = int(self.width()/3) - 5
            for i in range(self.model().columnCount()):
                self.setColumnWidth(i, width)
        
    def setTitleBar(self, title_bar):
        self.title_bar = title_bar
                
    def updateTitle(self):
        if self.title_bar is not None:
            n = self.model().rowCount()
            if (n == 0):
                self.title_bar.setTitle("Sections")
            else:
                self.title_bar.setTitle("Sections ({0:d} total)".format(n))


class SectionsStandardItem(QtGui.QStandardItem):

    def __init__(self, field = "", section_item = None, **kwds):
        super().__init__(**kwds)

        self.field = field
        self.section_item = section_item
        self.updateSectionText()

    def changeValue(self, df):
        self.section_item.changeField(self.field, df)
        self.updateSectionText()
        
    def updateSectionText(self):
        self.setText("{0:.2f}".format(self.section_item.getField(self.field)))

