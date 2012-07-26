#!/usr/bin/python
#
# Class for rendering multiple images in taken
# at different magnifications. This is used
# by the steve software and others for image
# display.
#
# Hazen 06/11
#

import os

from PyQt4 import QtCore, QtGui


#
# Image handling class.
#
# The real position is the stage position in um where
# the picture was taken. Magnification is relative, with
# 100x defined as 1.0 (so 20x = 0.2).
#
class viewPixmapItem(QtGui.QGraphicsItem):
    def __init__(self, pixmap, x_pix, y_pix, x_um, y_um, magnification, name, params, zvalue):
        QtGui.QGraphicsItem.__init__(self, None)
        size = pixmap.size()
        self.magnification = magnification
        self.name = name
        self.parameters = params
        self.pixmap = pixmap
        self.p_width = size.width()
        self.p_height = size.height()
        self.real_x = x_um
        self.real_y = y_um
        
        self.setPos(x_pix, y_pix)
        self.setTransform(QtGui.QTransform().scale(1.0/magnification, 1.0/magnification))
        self.setZValue(zvalue)


    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.p_width, self.p_height)

    def getMagnification(self):
        return self.magnification

    def getName(self):
        return self.name

    def getParameters(self):
        return self.parameters

    def getPixmap(self):
        return self.pixmap

    def getRealPosition(self):
        return [self.real_x, self.real_y]

    def paint(self, painter, options, widget):
        painter.drawPixmap(0, 0, self.pixmap)

    def realX(self):
        return self.real_x

    def realY(self):
        return self.real_y

    def setRealPosition(self, rx, ry):
        self.real_x = rx
        self.real_y = ry




#
# Handles user interaction with the microscope images.
#
# The units here are all in pixels. Subclasses are 
# responsible for keeping track (or not) of object
# locations in microns.
#
class MultifieldView(QtGui.QGraphicsView):
    def __init__(self, parameters, parent = None):
        super(MultifieldView, self).__init__(parent)

        # class variables
        self.currentz = 0.0
        self.directory = ""
        self.view_items = []
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
        self.initSceneRect()
        self.setMouseTracking(True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    def addRectangle(self, x_pix, y_pix, x_size, y_size, pen, z_val):
        rect = self.scene.addRect(0, 
                                  0,
                                  x_size,
                                  y_size,
                                  pen,
                                  QtGui.QBrush(QtGui.QColor(255,255,255,0)))
        rect.setPos(x_pix - 0.5*x_size, y_pix - 0.5*y_size)
        rect.setZValue(z_val)
        return rect

    def addViewPixmapItem(self, pixmap, x_pix, y_pix, x_um, y_um, mag, name, params, z_pos):
        a_graphics_item = viewPixmapItem(pixmap, x_pix, y_pix, x_um, y_um, mag, name, params, z_pos)

        # update scene rect
        if (x_pix < (self.scene_rect[0] + self.margin)):
            self.scene_rect[0] = x_pix - self.margin
            self.setRect()
        elif (x_pix > (self.scene_rect[2] - self.margin)):
            self.scene_rect[2] = x_pix + self.margin
            self.setRect()
        if (y_pix < (self.scene_rect[1] + self.margin)):
            self.scene_rect[1] = y_pix - self.margin
            self.setRect()
        elif (y_pix > (self.scene_rect[3] - self.margin)):
            self.scene_rect[3] = y_pix + self.margin
            self.setRect()

        # add the item
        self.view_items.append(a_graphics_item)
        self.scene.addItem(a_graphics_item)
        self.centerOn(x_pix, y_pix)

    def clearMosaic(self):
        for item in self.items():
            if(isinstance(item, viewPixmapItem)):
                self.scene.removeItem(item)
        self.initSceneRect()
        self.currentz = 0.0
        self.view_items = []

    def handleRemoveLastItem(self):
        if(len(self.view_items) > 0):
            item = self.view_items.pop()
            self.scene.removeItem(item)

    def initSceneRect(self):
        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
        self.setRect()

    def keyPressEvent(self, event):
        # this allows keyboard scrolling to work
        super(MultifieldView, self).keyPressEvent(event)

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

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))

    def removeRectangle(self, rect):
        self.scene.removeItem(rect)

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
        fp.write("name, x(um), y(um), x(pixels), y(pixels), magnification, z-position parameters\r\n")
        for i, item in enumerate(self.items()):
            progress_bar.setValue(i)
            if progress_bar.wasCanceled(): break
            if (isinstance(item, viewPixmapItem)):
                name = basename + "_" + str(i+1)
                fp.write(name + ", ")
                fp.write("{0:.2f}, {1:.2f}, {2:.2f}, {3:.2f}, {4:.2f}, {5:.3f}, ".format(item.realX(),
                                                                                         item.realY(),
                                                                                         item.x(),
                                                                                         item.y(),
                                                                                         item.getMagnification(),
                                                                                         item.zValue()))
                fp.write(item.getParameters() + "\r\n")
                item.getPixmap().save(QtCore.QString(dirname + name + ".png"), "PNG")

        progress_bar.close()
        fp.close()

    def setRect(self):
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
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
