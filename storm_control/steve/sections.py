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
            self.angle += df
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
    """
    This is the main class / the interface with steve.
    """
    @hdebug.debug
    def __init__(self, image_capture = None, **kwds):
        super().__init__(**kwds)

        self.image_capture = image_capture

        SectionItem.ellipse_size = self.parameters.get("ellipse_size")
        SectionItem.deselected_pen.setWidth(self.parameters.get("pen_width"))
        SectionItem.selected_pen.setWidth(self.parameters.get("pen_width"))
        
        self.ui = sectionsUi.Ui_Form()
        self.ui.setupUi(self)

        # Model to store sections.
        self.sections_model = QtGui.QStandardItemModel()
        self.sections_model.setHorizontalHeaderLabels([""] + SectionItem.fields)

        # Section renderer.
        self.sections_renderer = SectionsRenderer(scene = self.item_store.getScene())

        # View to manipulate sections.
        self.sections_table_view = SectionsTableView(item_store = self.item_store,
                                                     step_size = self.parameters.get("step_size"))
        
        self.sections_table_view.setModel(self.sections_model)
        self.sections_table_view.setTitleBar(self.ui.sectionsGroupBox)
        self.sections_table_view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout(self.ui.sectionsGroupBox)
        layout.addWidget(self.sections_table_view)
        layout.setContentsMargins(0,0,0,0)
        self.ui.sectionsGroupBox.setLayout(layout)

        # View to display section renders.
        self.sections_view = SectionsView()

        layout = QtWidgets.QVBoxLayout(self.ui.sectionsDisplayFrame)
        layout.addWidget(self.sections_view)
        self.ui.sectionsDisplayFrame.setLayout(layout)

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
        item = QtGui.QStandardItem()
        item.setCheckable(True)
        #item.setSizeHint(QtCore.QSize(1,1))
        row.append(item)
        
        for field in section_item.fields:
            row.append(SectionsStandardItem(field = field,
                                            section_item = section_item))
        self.sections_model.appendRow(row)
        self.sections_table_view.updateTitle()
        
    def handleAddSection(self, ignored):
        """
        This is called by the popup menu in the mosaic tab or a 
        key press event in the mosiacs view.
        """
        self.addSection(self.mosaic_event_coord, 0)


class SectionsRenderer(QtWidgets.QGraphicsView):
    """
    Handles rendering sections. It works by using the same QGraphicsScene as displayed in 
    the Mosaic tab. To render a section, it centers on the section, adjusts the angle and
    scale rotation as appropriate, then grabs the contents of its viewport.
    
    This object is not actual visible in the UI.
    """
    def __init__(self, scene = None, **kwds):
        super().__init__(**kwds)

        self.scale = 1.0

        self.setScene(scene)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    def renderSectionNumpy(self, a_point, a_angle):
        """
        Draw the section pixmap & convert to a numpy array.
        """
        pixmap = self.renderSectionPixmap(a_point, a_angle)
        image = pixmap.toImage()
        ptr = image.bits()

        ptr.setsize(image.byteCount())
        numpy_array = numpy.asarray(ptr).reshape(image.height(), image.width(), 4).astype(numpy.float)
        return numpy_array
        
#        # I'm not sure why, but ptr will sometimes be "None" so we need to catch this.
#        if (type(ptr) != type(None)):
#            ptr.setsize(image.byteCount())
#            numpy_array = numpy.asarray(ptr).reshape(image.height(), image.width(), 4).astype(numpy.float)
#            return numpy_array
#        else:
#            return False

    def renderSectionPixmap(self, a_point, a_angle):
        """
        Draw the section pixmap.
        """
        self.centerOn(a_point.x_pix, a_point.y_pix)
        transform = QtGui.QTransform()
        transform.rotate(a_angle)
        transform.scale(self.scale, self.scale)
        self.setTransform(transform)
        return self.grab()

    def setRenderScale(self, new_scale):
        self.scale = new_scale
        
    def setRenderSize(self, width, height):
        self.setFixedSize(width, height)


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

        
class SectionsTableView(QtWidgets.QTableView):

    def __init__(self, item_store = None, step_size = None, **kwds):
        super().__init__(**kwds)

        self.initialized_widths = False
        self.item_store = item_store
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

#            self.setColumnWidth(0, 10)
#            width = int(self.width()/3) - 30
#            for i in range(self.model().columnCount()-1):
#                self.setColumnWidth(i + 1, width)
        
    def setTitleBar(self, title_bar):
        self.title_bar = title_bar
                
    def updateTitle(self):
        if self.title_bar is not None:
            n = self.model().rowCount()
            if (n == 0):
                self.title_bar.setTitle("Sections")
            else:
                self.title_bar.setTitle("Sections ({0:d} total)".format(n))


class SectionsView(QtWidgets.QWidget):
    """
    Displays the sections.
    """
    changeSizeEvent = QtCore.pyqtSignal(int, int)
    changeZoomEvent = QtCore.pyqtSignal(float)
    pictureEvent = QtCore.pyqtSignal(int)
    positionEvent = QtCore.pyqtSignal()

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.background_pixmap = None
        self.foreground_opacity = 0.5
        self.foreground_pixmap = None
        
        self.pictAct = QtWidgets.QAction(self.tr("Take Pictures"), self)
        self.posAct = QtWidgets.QAction(self.tr("Record Positions"), self)

        self.popup_menu = QtWidgets.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.posAct)

        self.pictAct.triggered.connect(self.handlePictAct)
        self.posAct.triggered.connect(self.handlePosAct)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def changeOpacity(self, foreground_opacity):
        self.foreground_opacity = foreground_opacity
        self.update()

    def handlePictAct(self, boolean):
        self.pictureEvent.emit(1)

    def handlePosAct(self, boolean):
        self.positionEvent.emit()

    def keyPressEvent(self, event):
        """
        '1' Take a single picture at each section.
        '3' Take a 3 picture spiral at each section.
        '5' Take a 5 picture spiral at each section.
        'g' Take a grid of pictures at each section.
        """
        
        # Picture taking.
        if (event.key() == QtCore.Qt.Key_Space):
            self.pictureEvent.emit(1)
        elif (event.key() == QtCore.Qt.Key_3):
            self.pictureEvent.emit(3)
        elif (event.key() == QtCore.Qt.Key_5):
            self.pictureEvent.emit(5)
        elif (event.key() == QtCore.Qt.Key_G):
            self.pictureEvent.emit(-1)

        super().keyPressEvent(event)

    def paintEvent(self, event):
        """
        Draw a white background, the background pixmap (if it exists), the foreground
        pixmap (if it exists) and the white centering lines.
        """
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw background pixmap
        painter.setOpacity(1.0)
        if self.background_pixmap is not None:
            x_loc = (self.width() - self.background_pixmap.width())/2
            y_loc = (self.height() - self.background_pixmap.height())/2
            painter.drawPixmap(x_loc, y_loc, self.background_pixmap)

        # Draw foreground pixmap
        painter.setOpacity(self.foreground_opacity)
        if self.foreground_pixmap is not None:
            x_loc = (self.width() - self.foreground_pixmap.width())/2
            y_loc = (self.height() - self.foreground_pixmap.height())/2
            painter.drawPixmap(x_loc, y_loc, self.foreground_pixmap)

        # Draw guides lines
        #color = QtGui.QColor(128,128,128)
        #painter.setPen(color)
        #painter.setOpacity(1.0)
        painter.setOpacity(0.2)
        x_mid = self.width()/2
        y_mid = self.height()/2
        painter.drawLine(0, y_mid, self.width(), y_mid)
        painter.drawLine(x_mid, 0, x_mid, self.height())

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.popup_menu.exec_(event.globalPos())

    def resizeEvent(self, event):
        self.changeSizeEvent.emit(self.width(), self.height())

    def setBackgroundPixmap(self, pixmap):
        self.background_pixmap = pixmap
        self.update()

    def setForegroundPixmap(self, pixmap):
        self.foreground_pixmap = pixmap
        self.update()

    def wheelEvent(self, event):
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.changeZoomEvent.emit(1.2)
            else:
                self.changeZoomEvent.emit(1.0/1.2)

