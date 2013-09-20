#!/usr/bin/python
#
# Class for rendering multiple images in taken
# at different magnifications. This is used
# by the steve software and others for image
# display.
#
# Hazen 07/13
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
        self.bg_brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        self.currentz = 0.0
        self.directory = ""
        self.image_items = []
        self.margin = 8000.0
        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
        self.zoom_in = 1.2
        self.zoom_out = 1.0/self.zoom_in

        self.setMinimumSize(QtCore.QSize(200, 200))

        # background brush
        self.setBackgroundBrush(self.bg_brush)

        # scene initialization
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)

        self.updateSceneRect(0, 0, True)
        self.setMouseTracking(True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

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
        for image_item in self.image_items:
            self.scene.removeItem(image_item)
        #self.initSceneRect()
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

    def loadFromMosaicFileData(self, data, directory):
        if (data[0] == "image"):
            image_dict = pickle.load(open(directory + "/" + data[1]))
            a_image_item = viewImageItem(0, 0, 0, 0, "na", 1.0, 0.0)
            a_image_item.setState(image_dict)

            self.image_items.append(a_image_item)
            self.scene.addItem(a_image_item)
            self.centerOn(a_image_item.x_pix, a_image_item.y_pix)
            self.updateSceneRect(a_image_item.x_pix, a_image_item.y_pix)        

            return True
        else:
            return False

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))

    def saveToMosaicFile(self, fileptr, filename):
        progress_bar = QtGui.QProgressDialog("Saving Files...",
                                             "Abort Save",
                                             0,
                                             len(self.items()),
                                             self)
        progress_bar.setWindowModality(QtCore.Qt.WindowModal)

        basename = os.path.splitext(os.path.basename(filename))[0]
        dirname = os.path.dirname(filename) + "/"

        for i, item in enumerate(self.image_items):
            progress_bar.setValue(i)
            if progress_bar.wasCanceled(): break
            
            name = basename + "_" + str(i+1)
            fileptr.write("image," + name + ".stv\r\n")

            pickle.dump(item.getState(), open(dirname + name + ".stv", "w"))

        progress_bar.close()

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

    def setYOffset(self, y_offset):
        self.y_offset_pix = y_offset
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)


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
