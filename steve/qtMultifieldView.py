#!/usr/bin/python
#
# Class for rendering multiple images in taken
# at different magnifications. This is used
# by the steve software and others for image
# display.
#
# Hazen 02/13
#

import pickle
import numpy
import os

from PyQt4 import QtCore, QtGui

import halLib.daxspereader as datareader


#
# Handles user interaction with the microscope images.
#
# The units here are all in pixels. Subclasses are 
# responsible for keeping track (or not) of object
# locations in microns.
#
class MultifieldView(QtGui.QGraphicsView):

    def __init__(self, parameters, parent = None):
        QtGui.QGraphicsView.__init__(self, parent)

        # class variables
        self.currentz = 0.0
        self.directory = ""
        self.image_items = []
        self.margin = 8000.0
        self.pen_color = QtGui.QColor(parameters.pen_color[0],
                                      parameters.pen_color[1],
                                      parameters.pen_color[2])
        self.pen_width = parameters.pen_width
        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
        self.zoom_in = 1.2
        self.zoom_out = 1.0/self.zoom_in

        self.pen = QtGui.QPen(self.pen_color)
        self.pen.setWidth(self.pen_width)

        # ui initializiation
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(200, 200))

        # scene initialization
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)

        self.updateSceneRect(0, 0, True)
        self.setMouseTracking(True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    def addEllipse(self, x_pix, y_pix, x_size, y_size, pen, z_val):        
        #ellipse = self.scene.addEllipse(0, 
        #                                0,
        #                                x_size,
        #                                y_size,
        #                                pen,
        #                                QtGui.QBrush(QtGui.QColor(255,255,255,0)))
        ellipse = viewEllipseItem(x_size,
                                  y_size,
                                  pen,
                                  QtGui.QBrush(QtGui.QColor(255,255,255,0)))

        ellipse.setPos(x_pix - 0.5*x_size, y_pix - 0.5*y_size)
        ellipse.setZValue(z_val)
        self.scene.addItem(ellipse)
        return ellipse

    def addRectangle(self, x_pix, y_pix, x_size, y_size, pen, z_val):
        #rect = self.scene.addRect(0, 
        #                          0,
        #                          x_size,
        #                          y_size,
        #                          pen,
        #                          QtGui.QBrush(QtGui.QColor(255,255,255,0)))
        rect = viewRectItem(x_size,
                            y_size,
                            pen,
                            QtGui.QBrush(QtGui.QColor(255,255,255,0)))
        rect.setPos(x_pix - 0.5*x_size, y_pix - 0.5*y_size)
        rect.setZValue(z_val)
        self.scene.addItem(rect)
        return rect

    def addViewImageItem(self, image, x_pix, y_pix, x_offset_pix, y_offset_pix, magnification, objective, z_pos):
        a_image_item = viewImageItem(x_pix, y_pix, x_offset_pix, y_offset_pix, magnification, objective, z_pos)
        a_image_item.initializeWithImageObject(image)

        # add the item
        self.image_items.append(a_image_item)
        self.scene.addItem(a_image_item)
        self.centerOn(x_pix, y_pix)
        self.updateSceneRect(x_pix, y_pix)

    def changeImageMagnifications(self, objective, new_magnification):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setMagnification(new_magnification)

    def changeImageXOffsets(self, objective, x_offset_pix):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setXOffset(x_offset_pix)

    def changeImageYOffsets(self, objective, y_offset_pix):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setYOffset(y_offset_pix)

    def clearMosaic(self):
        for item in self.items():
            if(isinstance(item, viewImageItem)):
                self.scene.removeItem(item)
        self.initSceneRect()
        self.currentz = 0.0
        self.image_items = []

    def getImageItems(self):
        return self.image_items

    def handleRemoveLastItem(self):
        if(len(self.image_items) > 0):
            item = self.image_items.pop()
            self.scene.removeItem(item)

#    def initSceneRect(self):
#        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
#        self.setRect()

    def keyPressEvent(self, event):
        # this allows keyboard scrolling to work
        QtGui.QGraphicsView.keyPressEvent(self, event)

    def loadLegacyMosaicFile(self, filename):
        self.filename = filename
        fp = open(filename, "r")

        # First, figure out file size
        fp.readline()
        number_lines = 0
        while 1:
            line = fp.readline()
            if not line: break
            number_lines += 1
        fp.seek(0)

        # Create progress bar
        progress_bar = QtGui.QProgressDialog("Load Files...",
                                             "Abort Load",
                                             0,
                                             number_lines,
                                             self)
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)

        self.directory = os.path.dirname(filename)
        basename = filename[:-4] + "_"
        fp.readline()
        file_number = 1
        z_value = 0.0
        while 1:
            if progress_bar.wasCanceled(): break
            line = fp.readline()
            if not line: break
            data = line.split(",")
            picture_mag = 1.0
            imagename = None
            params = "NA"
            if len(data) == 4:
                [x_um, y_um, x_pix, y_pix] = data
                z_value += 0.01
            elif len(data) == 6:
                [x_um, y_um, x_pix, y_pix, picture_mag, z_value] = data
            elif len(data) == 7:
                [imagename, x_um, y_um, x_pix, y_pix, picture_mag, z_value] = data
            else:
                [imagename, x_um, y_um, x_pix, y_pix, picture_mag, z_value, params] = data

            if not(imagename):
                # Due to a bug, some legacy mosaics do not start at image_1.
                imagename = basename + str(file_number)
                iterations = 0
                while (not os.path.exists(imagename + ".png")) and (iterations < 100):
                    file_number += 1
                    iterations += 1
                    imagename = basename + str(file_number)
            else:
                imagename = self.directory + "/" + imagename

            if os.path.exists(imagename + ".png"):
                self.addViewPixmapItem(QtGui.QPixmap(imagename + ".png"),
                                       float(x_pix),
                                       float(y_pix),
                                       float(x_um),
                                       float(y_um),
                                       float(picture_mag),
                                       os.path.basename(imagename),
                                       params.strip(),
                                       float(z_value))
            else:
                print "Could not find:", imagename + ".png"
            progress_bar.setValue(file_number)
            file_number += 1

        self.currentz = float(z_value) + 0.01
        progress_bar.close()
        fp.close()

    def loadMosaicFile(self, filename):
        self.filename = filename
        fp = open(filename, "r")

        # First, figure out file size
        fp.readline()
        number_lines = 0
        while 1:
            line = fp.readline()
            if not line: break
            number_lines += 1
        fp.seek(0)

        # Create progress bar
        progress_bar = QtGui.QProgressDialog("Load Files...",
                                             "Abort Load",
                                             0,
                                             number_lines,
                                             self)
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)

        self.directory = os.path.dirname(filename)
        file_number = 1
        while 1:
            if progress_bar.wasCanceled(): break
            image_name = fp.readline().rstrip()
            if not image_name: break
            image_dict = pickle.load(open(self.directory + "/" + image_name))
            a_image_item = viewImageItem(0, 0, 0, 0, "na", 1.0, 0.0)
            a_image_item.setState(image_dict)

            self.image_items.append(a_image_item)
            self.scene.addItem(a_image_item)
            self.centerOn(a_image_item.x_pix, a_image_item.y_pix)
            self.updateSceneRect(a_image_item.x_pix, a_image_item.y_pix)

            progress_bar.setValue(file_number)
            file_number += 1

        progress_bar.close()
        fp.close()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))

    def removeCircle(self, circle):
        self.scene.removeItem(circle)

    def removeRectangle(self, rect):
        self.scene.removeItem(rect)

#    def saveLegacyMosaicFile(self, filename):
#        progress_bar = QtGui.QProgressDialog("Saving Files...",
#                                             "Abort Save",
#                                             0,
#                                             len(self.items()),
#                                             self)
#        progress_bar.setWindowModality(QtCore.Qt.WindowModal)
#
#        fp = open(filename, "w")
#        basename = os.path.splitext(os.path.basename(filename))[0]
#        dirname = os.path.dirname(filename) + "/"
#        fp.write("name, x(um), y(um), x(pixels), y(pixels), magnification, z-position parameters\r\n")
#        for i, item in enumerate(self.items()):
#            progress_bar.setValue(i)
#            if progress_bar.wasCanceled(): break
#            if (isinstance(item, viewPixmapItem)):
#                name = basename + "_" + str(i+1)
#                fp.write(name + ", ")
#                fp.write("{0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}, {4:.2f}, {5:.3f}, ".format(item.realX(),
#                                                                                         item.realY(),
#                                                                                         item.x(),
#                                                                                         item.y(),
#                                                                                         item.getMagnification(),
#                                                                                         item.zValue()))
#                fp.write(item.getParameters() + "\r\n")
#                item.getPixmap().save(QtCore.QString(dirname + name + ".png"), "PNG")
#
#        progress_bar.close()
#        fp.close()

    def saveMosaicFile(self, filename):
        progress_bar = QtGui.QProgressDialog("Saving Files...",
                                             "Abort Save",
                                             0,
                                             len(self.items()),
                                             self)
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)

        fp = open(filename, "w")
        basename = os.path.splitext(os.path.basename(filename))[0]
        dirname = os.path.dirname(filename) + "/"

        for i, item in enumerate(self.image_items):
            progress_bar.setValue(i)
            if progress_bar.wasCanceled(): break
            
            name = basename + "_" + str(i+1)
            fp.write(name + ".stv\r\n")

            pickle.dump(item.getState(), open(dirname + name + ".stv", "w"))

        progress_bar.close()
        fp.close()

    def updateSceneRect(self, x_pix, y_pix, update = False):
        needs_update = update

        # update scene rect
        if (x_pix < (self.scene_rect[0] + self.margin)):
            self.scene_rect[0] = x_pix - self.margin
            needs_update = True
        elif (x_pix > (self.scene_rect[2] - self.margin)):
            self.scene_rect[2] = x_pix + self.margin
            needs_update = True
        if (y_pix < (self.scene_rect[1] + self.margin)):
            self.scene_rect[1] = y_pix - self.margin
            needs_update = True
        elif (y_pix > (self.scene_rect[3] - self.margin)):
            self.scene_rect[3] = y_pix + self.margin
            needs_update = True

        if needs_update:
            w = self.scene_rect[2] - self.scene_rect[0]
            h = self.scene_rect[3] - self.scene_rect[1]
            self.scene.setSceneRect(self.scene_rect[0],
                                    self.scene_rect[1],
                                    w,
                                    h)

    def wheelEvent(self, event):
        if event.delta() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def zoomIn(self):
        self.scale(self.zoom_in, self.zoom_in)

    def zoomOut(self):
        self.scale(self.zoom_out, self.zoom_out)


#
# Ellipse rendering.
#
class viewEllipseItem(QtGui.QGraphicsEllipseItem):

    visible = True

    def __init__(self, x_size, y_size, pen, brush):
        QtGui.QGraphicsEllipseItem.__init__(self,
                                            0,
                                            0,
                                            x_size,
                                            y_size)
        self.setPen(pen)
        self.setBrush(brush)

    def paint(self, painter, options, widget):
        if self.visible:
            QtGui.QGraphicsEllipseItem.paint(self, painter, options, widget)


#
# Image handling class.
#
# The real position is the stage position in um where
# the picture was taken. Magnification is relative, with
# 100x defined as 1.0 (so 20x = 0.2).
#
class viewImageItem(QtGui.QGraphicsItem):
    #def __init__(self, pixmap, x_pix, y_pix, x_um, y_um, magnification, name, params, zvalue):
    def __init__(self, x_pix, y_pix, x_offset_pix, y_offset_pix, objective_name, magnification, zvalue):
        QtGui.QGraphicsItem.__init__(self, None)

        self.data = False
        self.height = 0
        self.magnification = magnification
        self.objective_name = str(objective_name)
        self.parameters_file = ""
        self.pixmap = False
        self.pixmap_min = 0
        self.pixmap_max = 0
        self.version = "0.0"
        self.width = 0
        self.x_offset_pix = x_offset_pix
        self.y_offset_pix = y_offset_pix
        self.x_pix = x_pix
        self.y_pix = y_pix
        self.x_um = 0
        self.y_um = 0
        self.zvalue = zvalue

    def boundingRect(self):
        #size_x = int(float(self.pixmap_width)/self.magnification) + 1
        #size_y = int(float(self.pixmap_height)/self.magnification) + 1
        #return QtCore.QRectF(0, 0, size_x, size_y)
        return QtCore.QRectF(0, 0, self.pixmap.width(), self.pixmap.height())

    def createPixmap(self):
        frame = self.data.copy()

        # Rescale & convert to 8bit
        frame = frame.astype(numpy.float)
        frame = 255.0 * (frame - float(self.pixmap_min))/float(self.pixmap_max - self.pixmap_min)
        frame[(frame > 255.0)] = 255.0
        frame[(frame < 0.0)] = 0.0
        frame = frame.astype(numpy.uint8)

        # Create the pixmap
        w, h = frame.shape
        image = QtGui.QImage(frame.data, w, h, QtGui.QImage.Format_Indexed8)
        image.ndarray = frame
        for i in range(256):
            image.setColor(i, QtGui.QColor(i,i,i).rgb())
        self.pixmap = QtGui.QPixmap.fromImage(image)

    def getMagnification(self):
        return self.magnification

    def getObjective(self):
        return self.objective_name

    def getParameters(self):
        return self.parameters

    def getPixmap(self):
        return self.pixmap

    def getPositionUm(self):
        return [self.x_um, self.y_um]

    def getState(self):
        odict = self.__dict__.copy()
        del odict['pixmap']
        return odict

    def initializeWithImageObject(self, image):
        self.data = image.data
        self.height = image.height
        self.parameters_file = image.parameters_file
        self.pixmap_min = image.image_min
        self.pixmap_max = image.image_max
        self.width = image.width
        self.x_um = image.x_um
        self.y_um = image.y_um
        self.createPixmap()

        self.setPixmapGeometry()

    def initializeWithLegacyMosaicFormat(self, legacy_text):
        pass

    def paint(self, painter, options, widget):
        painter.drawPixmap(0, 0, self.pixmap)

    def setPixmapGeometry(self):
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)
        self.setTransform(QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification))
        self.setZValue(self.zvalue)

    # FIXME: This also needs to change the x,y coordinates so the image expands/
    # contracts from its center, not the upper left hand corner.
    def setMagnification(self, magnification):
        self.magnification = magnification
        self.setTransform(QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification))
        #self.setPixmapGeometry()

    def setRealPosition(self, rx, ry):
        self.real_x = rx
        self.real_y = ry

    def setState(self, image_dict):
        self.__dict__.update(image_dict)
        self.createPixmap()
        self.setPixmapGeometry()

    def setXOffset(self, x_offset):
        self.x_offset_pix = x_offset
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)
        #self.setPixmapGeometry()

    def setYOffset(self, y_offset):
        self.y_offset_pix = y_offset
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)
        #self.setPixmapGeometry()


#
# Rectangle rendering.
#
class viewRectItem(QtGui.QGraphicsRectItem):

    visible = True

    def __init__(self, x_size, y_size, pen, brush):
        QtGui.QGraphicsRectItem.__init__(self,
                                         0,
                                         0,
                                         x_size,
                                         y_size)
        self.setPen(pen)
        self.setBrush(brush)

    def paint(self, painter, options, widget):
        if self.visible:
            QtGui.QGraphicsRectItem.paint(self, painter, options, widget)


#
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
