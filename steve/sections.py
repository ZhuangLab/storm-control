#!/usr/bin/python
#
# Handles section manipulation.
# Classes organized alphabetically.
#
# Hazen 03/13
#

import numpy
from PyQt4 import QtCore, QtGui

import coord
import mosaicView

#
# A Section
#
class Section(QtGui.QWidget):
    sectionChanged = QtCore.pyqtSignal()
    sectionCheckBoxChange = QtCore.pyqtSignal()
    sectionSelected = QtCore.pyqtSignal(int)

    def __init__(self, section_number, x_pos, y_pos, angle, parent):
        QtGui.QWidget.__init__(self, parent)

        self.section_number = section_number

        self.controls = SectionControls(x_pos, y_pos, angle, self)
        self.controls.sectionChanged.connect(self.handleSectionChanged)
        self.controls.sectionCheckBoxChange.connect(self.handleCheckBox)
        self.controls.sectionSelected.connect(self.handleSelection)

    def deselect(self):
        self.controls.deselect()

    def getAngle(self):
        return self.controls.currentAngle()

    def getLocation(self):
        return self.controls.currentLocation()

    def getSectionControls(self):
        return self.controls

    def getSectionNumber(self):
        return self.section_number

    def handleCheckBox(self):
        self.sectionCheckBoxChange.emit()

    def handleSectionChanged(self):
        self.sectionChanged.emit()

    def handleSelection(self):
        self.sectionSelected.emit(self.section_number)

    def incrementAngle(self, direction):
        self.controls.incrementAngle(direction)

    def incrementX(self, direction):
        self.controls.incrementX(direction)

    def incrementY(self, direction):
        self.controls.incrementY(direction)

    def isChecked(self):
        return self.controls.isChecked()

    def select(self):
        self.controls.select()

    def setSectionNumber(self, number):
        self.section_number = number


#
# Slightly specialized check box.
#
class SectionCheckBox(QtGui.QCheckBox):
    checkBoxSelected = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtGui.QCheckBox.__init__(self, parent)

    #def mousePressEvent(self, event):
    #    QtGui.QCheckBox.mousePressEvent(self, event)
    #    self.checkBoxSelected.emit()


#
# Section controls class.
#
class SectionControls(QtGui.QWidget):
    sectionChanged = QtCore.pyqtSignal()
    sectionCheckBoxChange = QtCore.pyqtSignal()
    sectionSelected = QtCore.pyqtSignal()

    def __init__(self, x_pos, y_pos, angle, parent):
        QtGui.QWidget.__init__(self, parent)

        self.angle = 0.0
        self.angle_step = 1.0
        self.position_step = 1.0
        self.selected = False
        self.x_pos = x_pos
        self.y_pos = y_pos

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setMargin(4)
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

    def currentAngle(self):
        return self.angle_spin_box.value()

    def currentLocation(self):
        return coord.Point(self.x_spin_box.value(), self.y_spin_box.value(), "um")

    def deselect(self):
        self.selected = False
        self.update()

    def handleCheckBox(self):
        self.sectionCheckBoxChange.emit()

    def handleSelected(self):
        #if self.check_box.isChecked():
        #    self.check_box.setChecked(False)
        self.sectionSelected.emit()

    def handleValueChange(self, value):
        self.sectionChanged.emit()

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

    def incrementX(self, direction):
        self.x_spin_box.setValue(self.x_spin_box.value() + direction)

    def incrementY(self, direction):
        self.y_spin_box.setValue(self.y_spin_box.value() + direction)

    def isChecked(self):
        if self.check_box.isChecked():
            return True
        else:
            return False

    def mousePressEvent(self, event):
        self.handleSelected()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.selected:
            color = QtGui.QColor(200,255,200)
        else:
            color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

    def select(self):
        self.selected = True
        self.update()

#
# Handles display of the list of section controls.
#
class SectionControlsList(QtGui.QWidget):
    keyEvent = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        QtGui.QListWidget.__init__(self, parent)

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setMargin(4)
        self.layout.setSpacing(2)
        self.layout.addSpacerItem(QtGui.QSpacerItem(20,
                                                    12,
                                                    QtGui.QSizePolicy.Minimum,
                                                    QtGui.QSizePolicy.Expanding))

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def addSection(self, a_section):
        self.layout.insertWidget(self.layout.count()-1, a_section.getSectionControls())

    def keyPressEvent(self, event):
        #print "control:", event.key()
        self.keyEvent.emit(event.key())

    def removeSection(self, section):
        controls = section.getSectionControls()
        self.layout.removeWidget(controls)
        controls.close()

#
# Handles rendering sections.
#
class SectionRenderer(QtGui.QGraphicsView):
    sceneChanged = QtCore.pyqtSignal()

    def __init__(self, scene, width, height, parent):
        QtGui.QGraphicsView.__init__(self, parent)

        self.setScene(scene)
        scene.changed.connect(self.handleSceneChange)

        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        self.setFixedSize(width, height)

    def handleSceneChange(self, qlist):
        self.sceneChanged.emit()

    # Draw the section pixmap & convert to a numpy array.
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

    # Draw the section pixmap.
    def renderSectionPixmap(self, a_point, a_angle):
        self.centerOn(a_point.x_pix, a_point.y_pix)
        transform = QtGui.QTransform()
        transform.rotate(a_angle)
        self.setTransform(transform)
        a_pixmap = QtGui.QPixmap.grabWidget(self.viewport())

        return a_pixmap

    def setRenderSize(self, width, height):
        self.setFixedSize(width, height)

#
# Handles all section interaction.
#
class Sections(QtGui.QWidget):
    addPositions = QtCore.pyqtSignal(object)
    currentSectionChange = QtCore.pyqtSignal(object)
    deleteSection = QtCore.pyqtSignal(int)
    moveSection = QtCore.pyqtSignal(int, object)
    takePictures = QtCore.pyqtSignal(object)

    def __init__(self, view_object, display_frame, scroll_area, section_width, section_height, parent):
        QtGui.QWidget.__init__(self, parent)

        self.active_section = False
        self.number_x = 5
        self.number_y = 3
        self.sections = []
        self.view_object = view_object

        self.section_renderer = SectionRenderer(self.view_object.getScene(),
                                                section_width,
                                                section_height,
                                                self)
        self.section_renderer.hide()
        
        self.sections_controls_list = SectionControlsList(scroll_area)
        scroll_area.setWidget(self.sections_controls_list)
        scroll_area.setWidgetResizable(True)

        self.sections_view = SectionsView(display_frame)
        layout = QtGui.QGridLayout(display_frame)
        layout.addWidget(self.sections_view)
        self.sections_view.show()

        self.section_renderer.sceneChanged.connect(self.viewUpdate)
        self.sections_controls_list.keyEvent.connect(self.handleKeyEvent)
        self.sections_view.keyEvent.connect(self.handleKeyEvent)
        self.sections_view.pictureEvent.connect(self.handlePictures)
        self.sections_view.positionEvent.connect(self.handlePositions)

    def addSection(self, a_point):
        a_section = Section(len(self.sections),
                            a_point.x_um,
                            a_point.y_um,
                            0.0,
                            self)
        a_section.sectionChanged.connect(self.handleSectionChange)
        a_section.sectionCheckBoxChange.connect(self.updateBackgroundPixmap)
        a_section.sectionSelected.connect(self.handleActiveSectionUpdate)
        self.sections.append(a_section)
        self.sections_controls_list.addSection(a_section)
        if not self.active_section:
            self.handleActiveSectionUpdate(0)

    def changeOpacity(self, foreground_opacity):
        self.sections_view.changeOpacity(foreground_opacity)

    def gridChange(self, xnum, ynum):
        self.number_x = xnum
        self.number_y = ynum

    def handleActiveSectionUpdate(self, which_section):
        if self.active_section:
            if (self.active_section.getSectionNumber() != which_section):
                self.active_section.deselect()
                self.active_section = self.sections[which_section]
                self.active_section.select()
        else:
            self.active_section = self.sections[which_section]
            self.active_section.select()
        self.currentSectionChange.emit(self.active_section.getLocation())

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

        # Delete the active section.
        elif (which_key == QtCore.Qt.Key_Delete):
            if self.active_section:
                self.removeActiveSection()

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

    def handlePositions(self):
        position_list = []
        for section in self.sections:
            position_list.append(section.getLocation())
        if (len(position_list) > 0):
            self.addPositions.emit(position_list)

    # This is triggered by a change in the active section parameters.
    # It signals mosaicView (via steve) to update the graphics scene.
    def handleSectionChange(self):
        # The active section should always be the one that is changing..
        self.moveSection.emit(self.active_section.getSectionNumber(),
                              self.active_section.getLocation())

    # This is called once the scene has been updated to redraw the
    # active section based on its new parameters.
    def handleSectionChanged(self):
        if self.active_section.isChecked():
            self.updateBackgroundPixmap()
        self.updateForegroundPixmap()

    def incrementActiveSection(self, diff):
        if self.active_section:
            next_section = (self.active_section.getSectionNumber() + diff) % len(self.sections)
            self.handleActiveSectionUpdate(next_section)

    def removeActiveSection(self):
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
        self.deleteSection.emit(which_section)
        
    def sectionSizeChange(self, width, height):
        self.section_renderer.setRenderSize(width, height)
        self.viewUpdate()

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
                    print "updateBackgroundPixmap: conversion problem."

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

    def updateForegroundPixmap(self):
        if (not self.active_section):
            return

        pixmap = self.section_renderer.renderSectionPixmap(self.active_section.getLocation(),
                                                           self.active_section.getAngle())
        self.sections_view.setForegroundPixmap(pixmap)

    def viewUpdate(self):
        # Update background pixmap
        self.updateBackgroundPixmap()

        # Update foreground pixmap
        self.updateForegroundPixmap()

#
# Displays the various sections.
#
class SectionsView(QtGui.QWidget):
    keyEvent = QtCore.pyqtSignal(int)
    pictureEvent = QtCore.pyqtSignal(int)
    positionEvent = QtCore.pyqtSignal()

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.foreground_opacity = 0.5
        self.foreground_pixmap = None
        self.background_pixmap = None
        
        self.pictAct = QtGui.QAction(self.tr("Take Pictures"), self)
        self.posAct = QtGui.QAction(self.tr("Record Positions"), self)

        self.popup_menu = QtGui.QMenu(self)
        self.popup_menu.addAction(self.pictAct)
        self.popup_menu.addAction(self.posAct)

        self.pictAct.triggered.connect(self.handlePict)
        self.posAct.triggered.connect(self.handlePos)

        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def changeOpacity(self, foreground_opacity):
        self.foreground_opacity = foreground_opacity
        self.update()

    def handlePict(self):
        self.pictureEvent.emit(1)

    def handlePos(self):
        self.positionEvent.emit()

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
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        color = QtGui.QColor(255,255,255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

        painter.setOpacity(1.0)
        if self.background_pixmap:
            x_loc = (self.width() - self.background_pixmap.width())/2
            y_loc = (self.height() - self.background_pixmap.height())/2
            painter.drawPixmap(x_loc, y_loc, self.background_pixmap)

        painter.setOpacity(self.foreground_opacity)
        if self.foreground_pixmap:
            x_loc = (self.width() - self.foreground_pixmap.width())/2
            y_loc = (self.height() - self.foreground_pixmap.height())/2
            painter.drawPixmap(x_loc, y_loc, self.foreground_pixmap)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.popup_menu.exec_(event.globalPos())

    def setBackgroundPixmap(self, pixmap):
        self.background_pixmap = pixmap
        self.update()

    def setForegroundPixmap(self, pixmap):
        self.foreground_pixmap = pixmap
        self.update()

#
# Slightly specialized double spin box
#
class SectionSpinBox(QtGui.QDoubleSpinBox):
    spinBoxSelected = QtCore.pyqtSignal()

    def __init__(self, min_value, max_value, cur_value, parent):
        QtGui.QDoubleSpinBox.__init__(self, parent)

        self.setMinimum(min_value)
        self.setMaximum(max_value)
        self.setValue(cur_value)

    def focusInEvent(self, event):
        QtGui.QDoubleSpinBox.focusInEvent(self, event)
        self.spinBoxSelected.emit()

    def mousePressEvent(self, event):
        QtGui.QDoubleSpinBox.mousePressEvent(self, event)
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
