#!/usr/bin/python
#
## @file
#
# Handles section manipulation.
# Classes organized alphabetically.
#
# Hazen 07/13
#

import numpy
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.coord as coord
import storm_control.steve.mosaicView as mosaicView

## SceneEllipseItem
#
# Section ellipse rendering in the QGraphicsScene
#
class SceneEllipseItem(QtWidgets.QGraphicsEllipseItem):

    visible = True

    ## __init__
    #
    # @param x_size The size in x of the ellipse.
    # @param y_size The size in y of the ellipse
    # @param pen The QPen to use when rendering the ellipse.
    # @param brush The QBrush to use when rendering the ellipse.
    #
    def __init__(self, x_size, y_size, pen, brush):
        QtWidgets.QGraphicsEllipseItem.__init__(self, 0, 0, x_size, y_size)
        self.setPen(pen)
        self.setBrush(brush)
        self.setZValue(999.0)

    ## paint
    #
    # Called when the SceneEllipseItem needs to be updated. If the class variable
    # visible is False then the SceneEllipseItem is not displayed.
    #
    # @param painter A QPainter object.
    # @param options A QStyleOptionGraphicsItem object.
    # @param widget A QWidget object.
    #
    def paint(self, painter, options, widget):
        if self.visible:
            QtWidgets.QGraphicsEllipseItem.paint(self, painter, options, widget)


## Section
#
# A Section
#
class Section(QtWidgets.QWidget):

    # Variables.
    brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
    deselected_pen = QtGui.QPen(QtGui.QColor(0,0,255))
    selected_pen = QtGui.QPen(QtGui.QColor(255,0,0))
    x_size = 1
    y_size = 1

    # Signals.
    sectionChanged = QtCore.pyqtSignal()
    sectionCheckBoxChange = QtCore.pyqtSignal()
    sectionSelected = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param section_number The number (index) of this section.
    # @param x_pos The position in x of the section.
    # @param y_pos The position in y of the section.
    # @param angle The orientation angle of the section.
    # @param parent The PyQt parent object of this object.
    #
    def __init__(self, section_number, x_pos, y_pos, angle, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.section_number = section_number

        self.controls = SectionControls(x_pos, y_pos, angle, self)
        self.controls.sectionChanged.connect(self.handleSectionChanged)
        self.controls.sectionCheckBoxChange.connect(self.handleCheckBox)
        self.controls.sectionSelected.connect(self.handleSelection)

        self.scene_ellipse_item = SceneEllipseItem(self.x_size,
                                                   self.y_size,
                                                   self.selected_pen,
                                                   self.brush)
        self.setLocation()

    ## deselect
    #
    # Changes the z value of the item back to the unselected default.
    # Updates the pen used to draw this section in the scene.
    # Deselects the controls UI for this section.
    #
    def deselect(self):
        self.scene_ellipse_item.setZValue(999.0)
        self.scene_ellipse_item.setPen(self.deselected_pen)
        self.controls.deselect()

    ## getAngle
    #
    # @return The current angle of the section
    #
    def getAngle(self):
        return self.controls.currentAngle()

    ## getSceneEllipseItem
    #
    # @return Returns the graphics scene item associated with this section.
    #
    def getSceneEllipseItem(self):
        return self.scene_ellipse_item

    ## getLocation
    #
    # @return The location of the section.
    #
    def getLocation(self):
        return self.controls.currentLocation()

    ## getSectionControls
    #
    # @return The UI controls associated with this section.
    #
    def getSectionControls(self):
        return self.controls

    ## getSectionNumber
    #
    # @return The number (index) of the section.
    #
    def getSectionNumber(self):
        return self.section_number

    ## handleCheckBox
    #
    # Called when the check box in the controls UI is selected.
    # Emits the sectionCheckBoxChange signal.
    #
    def handleCheckBox(self):
        self.sectionCheckBoxChange.emit()

    ## handleSectionChanged
    #
    # Called when the section position or orientation is changed in the controls UI.
    # Updates the section location in the scene and emits the sectionChanged signal.
    #
    def handleSectionChanged(self):
        self.setLocation()
        self.sectionChanged.emit()

    ## handleSelection
    #
    # Called when this section is selected in the controls UI.
    # Emits the sectionSelected signal.
    #
    def handleSelection(self):
        self.sectionSelected.emit(self.section_number)

    ## incrementAngle
    #
    # @param direction The direction in which to increment the section orientation angle.
    #
    def incrementAngle(self, direction):
        self.controls.incrementAngle(direction)

    ## incrementX
    #
    # @param direction The direction in which to increment the x position of the section.
    #
    def incrementX(self, direction):
        self.controls.incrementX(direction)

    ## incrementY
    #
    # @param direction The direction in which to increment the y position of the section.
    #
    def incrementY(self, direction):
        self.controls.incrementY(direction)

    ## isChecked
    #
    # @return True/False if the checkbox in the control UI for this section is checked.
    #
    def isChecked(self):
        return self.controls.isChecked()

#    @staticmethod
#    def load(string):
#        [number, x_pos, y_pos, angle] = string.strip().split(",")
#        return [int(number), float(x_pos), float(y_pos), float(angle)]

    ## saveToMosaicFile
    #
    # Save the section parameters in a mosaic file.
    #
    # @param filep The mosaic file pointer.
    #
    def saveToMosaicFile(self, filep):
        number = self.getSectionNumber()
        a_point = self.getLocation()
        angle = self.getAngle()
        [x_um, y_um] = a_point.getUm()
        filep.write("section," + ",".join(map(str,[number, x_um, y_um, angle])) + "\r\n")

    ## select
    #
    # Changes the z value to the selected default.
    # Changes the section pen to the selected pen.
    # Selects the control UI associated with this section.
    #
    def select(self):
        self.scene_ellipse_item.setZValue(1999.0)
        self.scene_ellipse_item.setPen(self.selected_pen)
        self.controls.select()

    ## setLocation
    #
    # Sets the location in the graphics scene of this section.
    #
    def setLocation(self):
        a_point = self.getLocation()
        self.scene_ellipse_item.setPos(a_point.x_pix - 0.5 * self.x_size,
                                       a_point.y_pix - 0.5 * self.y_size)

    ## setSectionNumber
    #
    # @param number The new number (index) for this section.
    #
    def setSectionNumber(self, number):
        self.section_number = number


## SectionCheckBox
#
# Slightly specialized check box.
#
class SectionCheckBox(QtWidgets.QCheckBox):
    checkBoxSelected = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parent The PyQt parent of this checkbox.
    #
    def __init__(self, parent):
        QtWidgets.QCheckBox.__init__(self, parent)

    #def mousePressEvent(self, event):
    #    QtGui.QCheckBox.mousePressEvent(self, event)
    #    self.checkBoxSelected.emit()


## SectionControls
#
# Section controls class. These are the UI elements that display the
# current section angle and position, as well as being editable so that
# the user can change these values.
#
class SectionControls(QtWidgets.QWidget):
    sectionChanged = QtCore.pyqtSignal()
    sectionCheckBoxChange = QtCore.pyqtSignal()
    sectionSelected = QtCore.pyqtSignal()

    ## __init__
    #
    # @param x_pos The x position of the section.
    # @param y_pos The y position of the section.
    # @param angle The angle of the section.
    # @param parent The PyQt parent of the section.
    #
    def __init__(self, x_pos, y_pos, angle, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.angle = 0.0
        self.angle_step = 1.0
        self.position_step = 1.0
        self.selected = False
        self.x_pos = x_pos
        self.y_pos = y_pos

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(4,4,4,4)
        self.layout.setSpacing(2)

        self.check_box = SectionCheckBox(self)
        self.x_spin_box = SectionSpinBox(-1.0e6, 1.0e6, x_pos, self)
        self.y_spin_box = SectionSpinBox(-1.0e6, 1.0e6, y_pos, self)
        self.angle_spin_box = SectionSpinBox(-180.0, 180.0, angle, self)

        self.check_box.stateChanged.connect(self.handleCheckBox)
        self.check_box.checkBoxSelected.connect(self.handleSelected)
        self.x_spin_box.spinBoxSelected.connect(self.handleSelected)
        self.y_spin_box.spinBoxSelected.connect(self.handleSelected)
        self.angle_spin_box.spinBoxSelected.connect(self.handleSelected)
        
        self.x_spin_box.valueChanged.connect(self.handleValueChange)
        self.y_spin_box.valueChanged.connect(self.handleValueChange)
        self.angle_spin_box.valueChanged.connect(self.handleValueChange)

        self.layout.insertWidget(0, self.check_box)
        self.layout.insertWidget(1, self.x_spin_box)
        self.layout.insertWidget(2, self.y_spin_box)
        self.layout.insertWidget(3, self.angle_spin_box)

    ## currentAngle
    #
    # @return The angle of the section.
    #
    def currentAngle(self):
        return self.angle_spin_box.value()

    ## currentLocation
    #
    # @return The position of the section as a coord.Point object.
    #
    def currentLocation(self):
        return coord.Point(self.x_spin_box.value(), self.y_spin_box.value(), "um")

    ## deselect
    #
    # Deselect these section controls.
    #
    def deselect(self):
        self.selected = False
        self.update()

    ## handleCheckBox
    #
    # Called when the checkbox in the UI is checked/unchecked.
    # Emits the sectionCheckBoxChange signal.
    #
    def handleCheckBox(self):
        self.sectionCheckBoxChange.emit()

    ## handleSelected
    #
    # Called when this section control UI is selected.
    # Emits the sectionSelected signal.
    #
    def handleSelected(self):
        #if self.check_box.isChecked():
        #    self.check_box.setChecked(False)
        self.sectionSelected.emit()

    ## handleValueChange
    #
    # Called when any of the spin boxes in the UI are changed.
    # Emits the sectionChanged signal.
    #
    def handleValueChange(self, value):
        self.sectionChanged.emit()

    ## incrementAngle
    #
    # @param direction The direction to increment the angle spinbox.
    #
    def incrementAngle(self, direction):
        cur_angle = self.angle_spin_box.value()
        if (direction > 0):
            cur_angle += self.angle_step
            if (cur_angle > self.angle_spin_box.maximum()):
                diff = cur_angle - self.angle_spin_box.maximum()
                self.angle_spin_box.setValue(self.angle_spin_box.minimum() + diff)
            else:
                self.angle_spin_box.setValue(cur_angle)
        else:
            cur_angle -= self.angle_step
            if (cur_angle < self.angle_spin_box.minimum()):
                diff = self.angle_spin_box.minimum() - cur_angle
                self.angle_spin_box.setValue(self.angle_spin_box.maximum() - diff)
            else:
                self.angle_spin_box.setValue(cur_angle)

    ## incrementX
    #
    # @param direction The direction and amount to increment the x spin box.
    #
    def incrementX(self, direction):
        self.x_spin_box.setValue(self.x_spin_box.value() + direction)

    ## incrementY
    #
    # @param direction The direction and amount to increment the y spin box.
    #
    def incrementY(self, direction):
        self.y_spin_box.setValue(self.y_spin_box.value() + direction)

    ## isChecked
    #
    # @return True/False if the check box is checked.
    #
    def isChecked(self):
        if self.check_box.isChecked():
            return True
        else:
            return False

    ## mousePressEvent
    #
    # Mouse presses on the control UI cause it to be selected.
    #
    # @param event A PyQt mouse press event.
    #
    def mousePressEvent(self, event):
        self.handleSelected()

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
    # Select these section controls.
    #
    def select(self):
        self.selected = True
        self.update()

## SectionControlsList
#
# Handles display of the list of section controls.
#
class SectionControlsList(QtWidgets.QWidget):
    keyEvent = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parent):
        QtWidgets.QListWidget.__init__(self, parent)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(4,4,4,4)
        self.layout.setSpacing(2)
        self.layout.addSpacerItem(QtWidgets.QSpacerItem(20,
                                                        12,
                                                        QtWidgets.QSizePolicy.Minimum,
                                                        QtWidgets.QSizePolicy.Expanding))

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    ## addSection
    #
    # Adds a section to the list of sections.
    #
    # @param a_section The Section object to add.
    #
    def addSection(self, a_section):
        self.layout.insertWidget(self.layout.count()-1, a_section.getSectionControls())

    ## keyPressEvent
    #
    # Called when a key is pressed when this list has focus.
    # Emits a keyEvent.
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        #print "control:", event.key()
        self.keyEvent.emit(event.key())

    ## removeSection
    #
    # Remove a section from the list of sections.
    #
    # @param a_section The Section object to remove.
    #
    def removeSection(self, a_section):
        controls = a_section.getSectionControls()
        self.layout.removeWidget(controls)
        controls.close()

## SectionRenderer
#
# Handles rendering sections. It works by using the same QGraphicsScene as displayed in 
# the Mosaic tab. To render a section, it centers on the section, adjusts the angle and
# scale rotation as appropriate, then grabs the contents of its viewport.
#
# This object is not actual visible in the UI.
#
class SectionRenderer(QtWidgets.QGraphicsView):
    sceneChanged = QtCore.pyqtSignal()

    ## __init__
    #
    # @param scene A QGraphicsScene object.
    # @param width The width of the sections.
    # @param height The height of the sections.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, scene, width, height, parent):
        QtWidgets.QGraphicsView.__init__(self, parent)

        self.index = 0
        self.scale = 1.0

        self.setScene(scene)
        scene.changed.connect(self.handleSceneChange)

        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        self.setFixedSize(width, height)

    ## handleSceneChange
    #
    # This is called when there is a change in the graphics scene.
    # Emits the sceneChanged signal.
    #
    # @param qlist A list of changes to the scene.
    #
    def handleSceneChange(self, qlist):
        self.sceneChanged.emit()

    ## renderSectionNumpy
    #
    # Draw the section pixmap & convert to a numpy array.
    #
    # @param a_point A coord.Point object defining the section position.
    # @param a_angle The angle of the section.
    #
    # @return A numpy array containing the section image, or False.
    #
    def renderSectionNumpy(self, a_point, a_angle):
        pixmap = self.renderSectionPixmap(a_point, a_angle)
        image = pixmap.toImage()
        ptr = image.bits()
        
        # I'm not sure why, but ptr will sometimes be "None" so we need to catch this.
        if (type(ptr) != type(None)):
            ptr.setsize(image.byteCount())
            numpy_array = numpy.asarray(ptr).reshape(image.height(), image.width(), 4).astype(numpy.float)
            return numpy_array
        else:
            return False

    ## renderSectionPixmap
    #
    # Draw the section pixmap.
    #
    # @param a_point A coord.Point object defining the section position.
    # @param a_angle The angle of the section.
    #
    # @return A QtGui.QPixmap containing the section image.
    #
    def renderSectionPixmap(self, a_point, a_angle):
        #mosaicView.displayEllipseRect(False)
        self.centerOn(a_point.x_pix, a_point.y_pix)
        transform = QtGui.QTransform()
        transform.rotate(a_angle)
        transform.scale(self.scale, self.scale)
        self.setTransform(transform)
        a_pixmap = self.grab()
        #mosaicView.displayEllipseRect(True)

        #a_pixmap.save("RSP" + str(self.index) + ".png")
        #self.index += 1
        return a_pixmap

    ## setRenderSize
    #
    # @param width The new width for rendering the sections.
    # @param height The new height for rendering the sections.
    #
    def setRenderSize(self, width, height):
        self.setFixedSize(width, height)

    ## setScale
    #
    # @param new_scale The scale (magnification) to use when rendering the sections.
    #
    def setScale(self, new_scale):
        self.scale = new_scale

## Sections
#
# Handles all section interaction. This is the object that main part of Steve
# interacts with. It is not directly visible, it orchestrates displaying the
# section(s) and the section control(s) in the appropriate places in the UI.
#
class Sections(QtWidgets.QWidget):
    addPositions = QtCore.pyqtSignal(object)
    takePictures = QtCore.pyqtSignal(object)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param scene A QGraphicsScene object.
    # @param display_frame The UI element where the sections will be displayed.
    # @param scroll_area The UI element where the section controls will be displayed.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, scene, display_frame, scroll_area, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.active_section = False
        self.number_x = 5
        self.number_y = 3
        self.scale = 1.0
        self.scene = scene
        self.sections = []

        Section.deselected_pen.setWidth(parameters.get("pen_width"))
        Section.selected_pen.setWidth(parameters.get("pen_width"))
        Section.x_size = parameters.get("ellipse_size")
        Section.y_size = parameters.get("ellipse_size")

        self.sections_controls_list = SectionControlsList(scroll_area)
        scroll_area.setWidget(self.sections_controls_list)
        scroll_area.setWidgetResizable(True)

        self.sections_view = SectionsView(display_frame)
        layout = QtWidgets.QGridLayout(display_frame)
        layout.addWidget(self.sections_view)
        self.sections_view.show()

        self.section_renderer = SectionRenderer(self.scene,
                                                self.sections_view.width(),
                                                self.sections_view.height(),
                                                self)
        self.section_renderer.hide()
        
        self.section_renderer.sceneChanged.connect(self.viewUpdate)
        self.sections_controls_list.keyEvent.connect(self.handleKeyEvent)
        self.sections_view.keyEvent.connect(self.handleKeyEvent)
        self.sections_view.pictureEvent.connect(self.handlePictures)
        self.sections_view.positionEvent.connect(self.handlePositions)
        self.sections_view.sizeEvent.connect(self.handleSectionSizeChange)
        self.sections_view.zoomEvent.connect(self.handleScaleChange)

    ## addSection
    #
    # Add a new Section object.
    #
    # @param a_point A coord.Point defining where the section should be.
    # @param angle (Optional) The angle of the section (default is 0.0).
    #
    def addSection(self, a_point, angle = 0.0):
        a_section = Section(len(self.sections),
                            a_point.x_um,
                            a_point.y_um,
                            angle,
                            self)
        a_section.sectionChanged.connect(self.handleSectionUpdate)
        a_section.sectionCheckBoxChange.connect(self.updateBackgroundPixmap)
        a_section.sectionSelected.connect(self.handleActiveSectionUpdate)
        self.sections.append(a_section)
        self.sections_controls_list.addSection(a_section)
        self.scene.addItem(a_section.getSceneEllipseItem())
        if not self.active_section:
            self.handleActiveSectionUpdate(0)

    ## changeOpacity
    #
    # Changes the opacity for the section images.
    #
    # @param foreground_opacity The new opacity to use when rendering the sections.
    #
    def changeOpacity(self, foreground_opacity):
        self.sections_view.changeOpacity(foreground_opacity)

    ## gridChange
    #
    # Change the grid size for creating grids of positions where images should be acquired.
    #
    # @param xnum The new grid size in x.
    # @param ynum The new grid size in y.
    #
    def gridChange(self, xnum, ynum):
        self.number_x = xnum
        self.number_y = ynum

    ## handleActiveSectionUpdate
    #
    # Handles the sectionSelected signal from the section(s).
    #
    # @param which_section Which section was selected.
    #
    def handleActiveSectionUpdate(self, which_section):
        if self.active_section:
            if (self.active_section.getSectionNumber() != which_section):
                self.active_section.deselect()
                self.active_section = self.sections[which_section]
                self.active_section.select()
        else:
            self.active_section = self.sections[which_section]
            self.active_section.select()
        #self.currentSectionChange.emit(self.active_section.getLocation())

    ## handleKeyEvent
    #
    # 'key up' Select the previous section in the list.
    # 'key down' Select the next section in the list.
    # 'w' Move the selected section up 0.5 pixels.
    # 's' Move the selected section down 0.5 pixels.
    # 'a' Move the selected section left 0.5 pixels.
    # 'd' Move the selected section right 0.5 pixels.
    # 'q' Rotate the section counter-clockwise 1 degree.
    # 'e' Rotate the section clockwise 1 degree.
    # 'p' Save the all the sections as numpy arrays (this is experimental purposes).
    # 'delete' Delete the selected section.
    # 'u' Force an update of the display (for debugging?).
    #
    # @param which_key A QtCore key code.
    #
    def handleKeyEvent(self, which_key):

        # Change the currently active section.
        if (which_key == QtCore.Qt.Key_Up):
            self.incrementActiveSection(-1)
        elif (which_key == QtCore.Qt.Key_Down):
            self.incrementActiveSection(1)

        # Change the parameters of the active section.
        elif (which_key == QtCore.Qt.Key_W):
            self.active_section.incrementY(-0.5)
        elif (which_key == QtCore.Qt.Key_S):
            self.active_section.incrementY(0.5)
        elif (which_key == QtCore.Qt.Key_A):
            self.active_section.incrementX(-0.5)
        elif (which_key == QtCore.Qt.Key_D):
            self.active_section.incrementX(0.5)
        elif (which_key == QtCore.Qt.Key_Q):
            self.active_section.incrementAngle(-1)
        elif (which_key == QtCore.Qt.Key_E):
            self.active_section.incrementAngle(1)

        # Save the section images as numpy arrays.
        elif (which_key == QtCore.Qt.Key_P):
            self.saveSectionsNumpy()

        # Delete the active section.
        elif (which_key == QtCore.Qt.Key_Delete):
            if self.active_section:
                self.removeActiveSection()

        # Force a display update.
        elif (which_key == QtCore.Qt.Key_U):
            self.viewUpdate()

    ## handlePictures
    #
    # Handles the pictureEvent signal from the sectionsView. This creates a list of 
    # positions where images should be taken and emits the takePictures signal.
    #
    # @param number_pictures The number of pictures to take at position. Positive is a spiral, -1 is a grid.
    #
    def handlePictures(self, number_pictures):
        picture_list = []
        for section in self.sections:
            picture_list.append(section.getLocation())
            if (number_pictures > 1):
                picture_list.extend(mosaicView.createSpiral(number_pictures))
            elif (number_pictures == -1):
                picture_list.extend(mosaicView.createGrid(self.number_x, self.number_y))
        if (len(picture_list) > 0):
            self.takePictures.emit(picture_list)

    ## handlePositions
    #
    # Handles the positionEvent signal from the sectionsView. This creates a list of 
    # positions which should be added to positions list and emits the addPositions signal.
    #
    def handlePositions(self):
        position_list = []
        for section in self.sections:
            position_list.append(section.getLocation())
        if (len(position_list) > 0):
            self.addPositions.emit(position_list)

    ## handleScaleChange
    #
    # Handles the zoomEvent signal from the sectionsView.
    #
    # @param scale_multiplier A number to multiply the current scale by.
    #
    def handleScaleChange(self, scale_multiplier):
        self.scale = self.scale * scale_multiplier
        self.section_renderer.setScale(self.scale)
        self.viewUpdate()

#    # This is triggered by a change in the active section parameters.
#    # It signals mosaicView (via steve) to update the graphics scene.
#    def handleSectionChange(self):
#        # The active section should always be the one that is changing..
#        self.moveSection.emit(self.active_section.getSectionNumber(),
#                              self.active_section.getLocation())

    ## handleSectionSizeChange
    #
    # Handles the sizeEvent signal from the sectionsView.
    #
    # @param width The new width of the section view.
    # @param height The new height of the section view.
    #
    def handleSectionSizeChange(self, width, height):
        self.section_renderer.setRenderSize(width, height)
        self.viewUpdate()

    ## handleSectionUpdate
    #
    # This is called once the scene has been updated to redraw the
    # active section based on its new parameters.
    #
    def handleSectionUpdate(self):
        if self.active_section and self.active_section.isChecked():
            self.updateBackgroundPixmap()
        self.updateForegroundPixmap()

    ## incrementActiveSection
    #
    # Changes the active section based on the offset from the current active section.
    #
    # @param diff The offset from the current active section, typically 1 or -1.
    #
    def incrementActiveSection(self, diff):
        if self.active_section:
            next_section = (self.active_section.getSectionNumber() + diff) % len(self.sections)
            self.handleActiveSectionUpdate(next_section)

    ## loadFromMosaicFileData
    #
    # Add a section to the image based on data from a mosaic file.
    #
    # @param data A data element from the mosaic file.
    # @param directory The directory in which the mosaic file is located.
    #
    # @return True/False if the data element described a section item.
    #
    def loadFromMosaicFileData(self, data, directory):
        if (data[0] == "section"):
            self.addSection(coord.Point(float(data[2]), float(data[3]), "um"),
                            float(data[4]))
            return True
        else:
            return False

    ## removeActiveSection
    #
    # Removes the current active section from the list of sections.
    #
    def removeActiveSection(self):
        # Remove the active section from the scene
        self.scene.removeItem(self.active_section.getSceneEllipseItem())

        # Remove the active section from the list of controls.
        self.sections_controls_list.removeSection(self.active_section)

        # Remove the active section from the list of sections.
        #
        # FIXME? This probably leaks memory since I don't think
        # close is the same thing as destroy. Probably not an issue
        # though given how little memory these things take up..
        #
        which_section = self.active_section.getSectionNumber()
        del self.sections[which_section]
        self.active_section.close()
        self.active_section = False

        # Renumber the remaining sections.
        for i, a_section in enumerate(self.sections):
            a_section.setSectionNumber(i)

        # Update the active section.
        if (len(self.sections) > 0):
            if (which_section > 0):
                self.handleActiveSectionUpdate(which_section-1)
            else:
                self.handleActiveSectionUpdate(0)

        # Notify steve to remove the section circle from the view.
        #self.deleteSection.emit(which_section)

    ## saveToMosaicFile
    #
    # Saves the sections into a mosaic file.
    #
    # @param file_ptr The mosaic file pointer.
    # @param filename The name of the mosaic file.
    #
    def saveToMosaicFile(self, file_ptr, filename):
        for section in self.sections:
            section.saveToMosaicFile(file_ptr)

    ## saveSectionsNumpy
    #
    # This is used for figuring out ways to automatically align sections.
    #
    def saveSectionsNumpy(self):
        index = 0
        for section in self.sections:
            temp = self.section_renderer.renderSectionNumpy(section.getLocation(),
                                                            section.getAngle())
            numpy.save("section_" + str(index), temp)
            index += 1

    ## setSceneItemsVisible
    #
    # Sets whether or not the section ellipses are visible in graphics scene.
    #
    def setSceneItemsVisible(self, visible):
        SceneEllipseItem.visible = visible
        self.handleSectionUpdate()

    ## updateBackgroundPixmap
    #
    # This updates the background pixmap. The background pixmap is created by averaging 
    # together all of the sections whose checkbox has been selected.
    #
    def updateBackgroundPixmap(self):
        if (len(self.sections) == 0):
            return

        counts = 0.0
        numpy_background = False

        for section in self.sections:
            if section.isChecked():
                temp = self.section_renderer.renderSectionNumpy(section.getLocation(),
                                                                section.getAngle())

                if (type(numpy_background) == type(numpy.array([]))):
                    numpy_background += temp
                    counts += 1.0
                elif (type(temp) != type(False)):
                    numpy_background = temp
                    counts += 1.0
                else:
                    print("updateBackgroundPixmap: conversion problem.")

        pixmap = False
        if(type(numpy_background) == type(numpy.array([]))):
            numpy_background = numpy_background / counts

            numpy_background = numpy_background.astype(numpy.uint8)
            image = QtGui.QImage(numpy_background.data,
                                 numpy_background.shape[1],
                                 numpy_background.shape[0],
                                 QtGui.QImage.Format_RGB32)
            image.ndarray = numpy_background
            pixmap = QtGui.QPixmap.fromImage(image)
            pixmap.qtimage = image
        
        self.sections_view.setBackgroundPixmap(pixmap)

    ## updateForegroundPixmap
    #
    # This updates the foreground pixmap. This is the active section.
    #
    def updateForegroundPixmap(self):
        if (not self.active_section):
            return

        pixmap = self.section_renderer.renderSectionPixmap(self.active_section.getLocation(),
                                                           self.active_section.getAngle())
        self.sections_view.setForegroundPixmap(pixmap)

    ## viewUpdate
    #
    # Calls updateBackgroundPixmap and updateForegroundPixmap.
    #
    def viewUpdate(self):
        # Update background pixmap
        self.updateBackgroundPixmap()

        # Update foreground pixmap
        self.updateForegroundPixmap()

## SectionsView
#
# Displays the various sections.
#
class SectionsView(QtWidgets.QWidget):
    keyEvent = QtCore.pyqtSignal(int)
    pictureEvent = QtCore.pyqtSignal(int)
    positionEvent = QtCore.pyqtSignal()
    sizeEvent = QtCore.pyqtSignal(int, int)
    zoomEvent = QtCore.pyqtSignal(float)

    ## __init__
    #
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.background_pixmap = None
        self.foreground_opacity = 0.5
        self.foreground_pixmap = None
        self.old_width = self.width()
        self.old_height = self.height()
        
        self.pictAct = QtWidgets.QAction(self.tr("Take Pictures"), self)
        self.posAct = QtWidgets.QAction(self.tr("Record Positions"), self)

        self.popup_menu = QtWidgets.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.posAct)

        self.pictAct.triggered.connect(self.handlePict)
        self.posAct.triggered.connect(self.handlePos)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    ## changeOpacity
    #
    # @param foreground_opacity The opacity of the foreground pixmap (0.0 - 1.0).
    #
    def changeOpacity(self, foreground_opacity):
        self.foreground_opacity = foreground_opacity
        self.update()

    ## handlePict
    #
    # Handles the take picture action. Emits the pictureEvent signal.
    #
    # @param boolean Dummy parameter.
    #
    def handlePict(self, boolean):
        self.pictureEvent.emit(1)

    ## handlePos
    #
    # Handles the record position action.
    #
    # @param boolean Dummy parameter.
    #
    def handlePos(self, boolean):
        self.positionEvent.emit()

    ## keyPressEvent
    #
    # Handles key press events, can emit a pictureEvent or a keyEvent.
    #
    # '1' Take a single picture at each section.
    # '3' Take a 3 picture spiral at each section.
    # '5' Take a 5 picture spiral at each section.
    # 'g' Take a grid of pictures at each section.
    #
    # All other keys are emitted as a keyEvent.
    #
    # @param event A PyQt key press event.
    #
    def keyPressEvent(self, event):
        # Picture taking.
        if (event.key() == QtCore.Qt.Key_Space):
            self.pictureEvent.emit(1)
        elif (event.key() == QtCore.Qt.Key_3):
            self.pictureEvent.emit(3)
        elif (event.key() == QtCore.Qt.Key_5):
            self.pictureEvent.emit(5)
        elif (event.key() == QtCore.Qt.Key_G):
            self.pictureEvent.emit(-1)

        # Update section active section parameters.
        else:
            self.keyEvent.emit(event.key())

    ## paintEvent
    #
    # Draw a white background, the background pixmap (if it exists), the foreground
    # pixmap (if it exists) and the white centering lines.
    #
    # @param event A PyQt paint event.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw background pixmap
        painter.setOpacity(1.0)
        if self.background_pixmap:
            x_loc = (self.width() - self.background_pixmap.width())/2
            y_loc = (self.height() - self.background_pixmap.height())/2
            painter.drawPixmap(x_loc, y_loc, self.background_pixmap)

        # Draw foreground pixmap
        painter.setOpacity(self.foreground_opacity)
        if self.foreground_pixmap:
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

    ## mousePressEvent
    #
    # If the right button is pressed, bring up the pop-up menu.
    #
    # @param event A PyQt mouse press event.
    #
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.popup_menu.exec_(event.globalPos())

    ## resizeEvent
    #
    # Called when the size of the window is changed.
    #
    # @param A PyQt resize event.
    #
    def resizeEvent(self, event):
        if (self.old_height != self.height()) or (self.old_width != self.width()):
            self.old_height = self.height()
            self.old_width = self.width()
            self.sizeEvent.emit(self.width(), self.height())

    ## setBackgroundPixmap
    #
    # Set the background pixmap to display. This pixmap is the average of all the
    # checked sections.
    #
    # @param pixmap A PyQt QPixmap item.
    #
    def setBackgroundPixmap(self, pixmap):
        self.background_pixmap = pixmap
        self.update()

    ## setForegroundPixmap
    #
    # Set the foreground pixmap to display. This is the active section.
    #
    # @param pixmap A PyQt pixmap item.
    #
    def setForegroundPixmap(self, pixmap):
        self.foreground_pixmap = pixmap
        self.update()

    ## wheelEvent
    #
    # Emits the zoomEvent.
    #
    # @param event A PyQt wheel event.
    #
    def wheelEvent(self, event):
        if not event.angleDelta().isNull():
            if (event.angleDelta().y() > 0):
                self.zoomEvent.emit(1.2)
            else:
                self.zoomEvent.emit(1.0/1.2)

## SectionSpinBox
#
# Slightly specialized double spin box
#
class SectionSpinBox(QtWidgets.QDoubleSpinBox):
    spinBoxSelected = QtCore.pyqtSignal()

    ## __init__
    #
    # @param min_value The spin box minimum value.
    # @param max_value The spin box maximum value.
    # @param parent The PyQt parent of the spin box.
    #
    def __init__(self, min_value, max_value, cur_value, parent):
        QtWidgets.QDoubleSpinBox.__init__(self, parent)

        self.setMinimum(min_value)
        self.setMaximum(max_value)
        self.setValue(cur_value)

    ## focusInEvent
    #
    # Handles focus events. Emits the spinBoxSelected signal.
    #
    # @param event A PyQt focus event.
    #
    def focusInEvent(self, event):
        QtWidgets.QDoubleSpinBox.focusInEvent(self, event)
        self.spinBoxSelected.emit()

    ## mousePressEvent
    #
    # Handles mouse press events. Emits the spinBoxSelected signal.
    #
    # @param event A PyQt mouse press event.
    #
    def mousePressEvent(self, event):
        QtWidgets.QDoubleSpinBox.mousePressEvent(self, event)
        self.spinBoxSelected.emit()


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
