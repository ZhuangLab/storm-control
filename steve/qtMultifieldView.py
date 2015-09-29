#!/usr/bin/python
#
## @file
#
# Class for rendering multiple images in taken at different magnifications. This is used
# by the steve software and others for image display.
#
# Hazen 07/13
#

import pickle
import numpy
import os

from PyQt4 import QtCore, QtGui


## MultifieldView
#
# Handles user interaction with the microscope images.
#
# The units here are all in pixels. Subclasses are 
# responsible for keeping track (or not) of object
# locations in microns.
#
class MultifieldView(QtGui.QGraphicsView):
    scaleChange = QtCore.pyqtSignal(float)

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this object.
    # 
    def __init__(self, parameters, parent = None):
        QtGui.QGraphicsView.__init__(self, parent)

        # class variables
        self.bg_brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        self.currentz = 0.0
        self.directory = ""
        self.image_items = []
        self.margin = 8000.0
        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
        self.view_scale = 1.0
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

    ## addViewImageItem
    #
    # Adds a ViewImageItem to the QGraphicsScene.
    #
    # We don't use the image objects x and y fields for positioning the image as these give the location
    # of the center of the image and the QGraphicsScene uses the upper left corner of the image.
    #
    # @param image A capure.Image item.
    # @param x_pix The x location of the left edge of the image.
    # @param y_pix The y location of the top edge of the image.
    # @param x_offset_pix The current x offset of this objective relative to the reference objective.
    # @param y_offset_pix The current y offset of this objective relative to the reference objective.
    # @param magnification The magnification of this objective.
    # @param objective The name of the objective (a string).
    # @param z_pos The z value to use for this image, this determines which images are in front of other images in the event of overlap.
    #
    def addViewImageItem(self, image, x_pix, y_pix, x_offset_pix, y_offset_pix, magnification, objective, z_pos):
        a_image_item = viewImageItem(x_pix, y_pix, x_offset_pix, y_offset_pix, magnification, objective, z_pos)
        a_image_item.initializeWithImageObject(image)

        # add the item
        self.image_items.append(a_image_item)
        self.scene.addItem(a_image_item)
        self.centerOn(x_pix, y_pix)
        self.updateSceneRect(x_pix, y_pix)

    ## changeContrast
    #
    # Change the contrast of all image items
    #
    # @param contrast_range The new minimum and maximum contrast values (which will control what is set to 0 and to 255)
    #
    def changeContrast(self, contrast_range):
        for item in self.image_items:
            item.pixmap_min = contrast_range[0]
            item.pixmap_max = contrast_range[1]
            item.createPixmap()

    ## changeImageMagnifications
    #
    # Update the magnifications of the images taken with the specified objective.
    #
    # @param objective The objective (a string).
    # @param new_magnification The new magnification to use when rendering images taken with this objective.
    #
    def changeImageMagnifications(self, objective, new_magnification):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setMagnification(new_magnification)

    ## changeImageXOffsets
    #
    # Update the x offset (relative to the reference objective) of all the images taken with the specified objective.
    #
    # @param objective The objective (a string).
    # @param x_offset_pix The new x offset in pixels.
    #
    def changeImageXOffsets(self, objective, x_offset_pix):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setXOffset(x_offset_pix)

    ## changeImageYOffsets
    #
    # Update the y offset (relative to the reference objective) of all the images taken with the specified objective.
    #
    # @param objective The objective (a string).
    # @param y_offset_pix The new y offset in pixels.
    #
    def changeImageYOffsets(self, objective, y_offset_pix):
        for item in self.image_items:
            if (item.getObjective() == objective):
                item.setYOffset(y_offset_pix)

    ## clearMosaic
    #
    # Removes all the viewImageItems from the QGraphicsScene.
    #
    def clearMosaic(self):
        for image_item in self.image_items:
            self.scene.removeItem(image_item)
        #self.initSceneRect()
        self.currentz = 0.0
        self.image_items = []

    ## getContrast
    #
    # @return The minimum and maximum pixmap values from all image items.
    #
    def getContrast(self):
        if len(self.image_items) >= 1:
            min_value = min(item.pixmap_min for item in self.image_items)
            max_value = max(item.pixmap_max for item in self.image_items)
            return [min_value, max_value]
        else:
            return [None, None]

    ## getImageItems
    #
    # @return An array containing all of the viewImageItems in the scene.
    #
    def getImageItems(self):
        return self.image_items

    ## handleRemoveLastItem
    #
    # Removes the last viewImageItem that was added to the scene.
    #
    # @param boolean Dummy parameter.
    #
    def handleRemoveLastItem(self, boolean):
        if(len(self.image_items) > 0):
            item = self.image_items.pop()
            self.scene.removeItem(item)

#    def initSceneRect(self):
#        self.scene_rect = [-self.margin, -self.margin, self.margin, self.margin]
#        self.setRect()

    ## keyPressEvent
    #
    # @param event A PyQt key press event object.
    #
    def keyPressEvent(self, event):
        # this allows keyboard scrolling to work
        QtGui.QGraphicsView.keyPressEvent(self, event)

    ## loadFromMosaicFileData
    #
    # This is called when we are loading a previously saved mosaic.
    #
    # @param data A data element from the mosaic file.
    # @param directory The directory in which the mosaic file is located.
    #
    # @return True/False if the data element described a viewImageItem.
    #
    def loadFromMosaicFileData(self, data, directory):
        if (data[0] == "image"):
            image_dict = pickle.load(open(directory + "/" + data[1]))
            a_image_item = viewImageItem(0, 0, 0, 0, "na", 1.0, 0.0)
            a_image_item.setState(image_dict)

            self.image_items.append(a_image_item)
            self.scene.addItem(a_image_item)
            self.centerOn(a_image_item.x_pix, a_image_item.y_pix)
            self.updateSceneRect(a_image_item.x_pix, a_image_item.y_pix)        

            if (self.currentz < a_image_item.zvalue):
                self.currentz = a_image_item.zvalue + 0.01
                
            return True
        else:
            return False

    ## mousePressEvent
    #
    # If the left mouse button was pressed, center the scene on the location where the button
    # was pressed.
    #
    # @param event A PyQt mouse press event.
    #
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.centerOn(self.mapToScene(event.pos()))

    ## saveToMosaicFile
    #
    # Saves all the viewImageItems in the scene into the mosaic file. This adds a line
    # to the mosaic file for each viewImageItem containing the file name where the
    # viewImageItem was stored. Each viewImageItem is pickled and saved in it's own
    # separate file.
    #
    # @param fileptr The mosaic file pointer.
    # @param filename The name of the mosaic file.
    #
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

    ## setScale
    #
    # Sets the current scale of the view.
    #
    def setScale(self, scale):
        self.view_scale = scale
        a_matrix = QtGui.QMatrix()
        a_matrix.scale(scale, scale)
        self.setMatrix(a_matrix)

    ## updateSceneRect
    #
    # This updates the rectangle describing the overall size of the QGraphicsScene.
    #
    # @param x_pix A new location in pixels that needs to be visible in the scene.
    # @param y_pix A new location in pixels that needs to be visible in the scene.
    # @param update (Optional) True/False to force and update of the scene rectangle regardless of x_pix, y_pix.
    #
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

    ## wheelEvent
    #
    # Handles mouse wheel events, changes the scale at which the scene is rendered
    # to emulate zooming in / out.
    #
    # @param event A PyQt mouse wheel event.
    #
    def wheelEvent(self, event):
        if event.delta() > 0:
            self.view_scale = self.view_scale * self.zoom_in
            self.setScale(self.view_scale)
        else:
            self.view_scale = self.view_scale * self.zoom_out
            self.setScale(self.view_scale)
        self.scaleChange.emit(self.view_scale)


## viewImageItem
#
# Image handling class.
#
# The real position is the stage position in um where
# the picture was taken. Magnification is relative, with
# 100x defined as 1.0 (so 20x = 0.2).
#
class viewImageItem(QtGui.QGraphicsItem):
    #def __init__(self, pixmap, x_pix, y_pix, x_um, y_um, magnification, name, params, zvalue):

    ## __init__
    #
    # @param x_pix X location of the image in pixels.
    # @param y_pix Y location of the image in pixels.
    # @param x_offset_pix The offset for this objective in x relative to the reference objective in pixels.
    # @param y_offset_pix The offset fot this objective in y relative to the reference objective in pixels.
    # @param objective_name The name of the objective, a string.
    # @param magnification The magnification of the objective.
    # @param zvalue The z position of this image.
    #
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

    ## boundingRect
    #
    # @return QtCore.QRectF containing the size of the image.
    #
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.pixmap.width(), self.pixmap.height())

    ## createPixmap
    #
    # Converts the numpy image from HAL to a QtGui.QPixmap.
    #
    def createPixmap(self):
        
        # This just undoes the transpose that we applied when the image was loaded. It might
        # make more sense not to transpose the image in the first place, but this is the standard
        # for the storm-analysis project so we maintain that here.
        frame = numpy.transpose(self.data.copy())

        # Rescale & convert to 8bit
        frame = numpy.ascontiguousarray(frame, dtype = numpy.float32)
        frame = 255.0 * (frame - float(self.pixmap_min))/float(self.pixmap_max - self.pixmap_min)
        frame[(frame > 255.0)] = 255.0
        frame[(frame < 0.0)] = 0.0
        frame = frame.astype(numpy.uint8)

        # Create the pixmap
        w, h = frame.shape
        image = QtGui.QImage(frame.data, h, w, QtGui.QImage.Format_Indexed8)
        image.ndarray = frame
        for i in range(256):
            image.setColor(i, QtGui.QColor(i,i,i).rgb())
        self.pixmap = QtGui.QPixmap.fromImage(image)

    ## getMagnification
    #
    # @return The magnification of the image.
    #
    def getMagnification(self):
        return self.magnification

    ## getObjective
    #
    # @return The objective the image was taken with.
    #
    def getObjective(self):
        return self.objective_name

    ## getParameters
    #
    # This is not used. self.parameters is also not defined..
    #
    # @return self.parameters.
    #
    def getParameters(self):
        return self.parameters

    ## getPixmap
    #
    # @return The image as a QtGui.QPixmap.
    #
    def getPixmap(self):
        return self.pixmap

    ## getPositionUm
    #
    # @return [x (um), y (um)]
    #
    def getPositionUm(self):
        return [self.x_um, self.y_um]

    ## getState
    #
    # This is used to pickle objects of this class.
    #
    # @return The dictionary for this object, with 'pixmap' element removed.
    #
    def getState(self):
        odict = self.__dict__.copy()
        del odict['pixmap']
        return odict

    ## initializeWithImageObject
    #
    # Set member variables from a capture.Image object.
    #
    # @param image A capture.Image object.
    #
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

    ## initializeWithLegacyMosaicFormat
    #
    # This is a place-holder, it currently does nothing.
    #
    # @param legacy_text The text that specifies some of the image properties.
    #
    def initializeWithLegacyMosaicFormat(self, legacy_text):
        pass

    ## paint
    #
    # Called by PyQt to render the image.
    #
    # @param painter A QPainter object.
    # @param option A QStyleOptionGraphicsItem object.
    # @param widget A QWidget object.
    #
    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.pixmap)

    ## setPixmapGeometry
    #
    # Sets the position, scale and z value of the image.
    #
    def setPixmapGeometry(self):
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)
        self.setTransform(QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification))
        self.setZValue(self.zvalue)

    ## setMagnification
    #
    # FIXME: This also needs to change the x,y coordinates so the image expands/
    # contracts from its center, not the upper left hand corner.
    #
    # @param magnification The new magnification to use for this image.
    #
    def setMagnification(self, magnification):
        self.magnification = magnification
        self.setTransform(QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification))

    ## setRealPosition
    #
    # This is not used..
    #
    # @param rx The real position in x.
    # @param ry The real position in y.
    #
    def setRealPosition(self, rx, ry):
        self.real_x = rx
        self.real_y = ry

    ## setState
    #
    # This is used to unpickle objects of this class.
    #
    # @param image_dict A dictionary that defines the object members.
    #
    def setState(self, image_dict):
        self.__dict__.update(image_dict)
        self.createPixmap()
        self.setPixmapGeometry()

    ## setXOffset
    #
    # @param x_offset The new x_offset to use for positioning this image.
    #
    def setXOffset(self, x_offset):
        self.x_offset_pix = x_offset
        self.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)

    ## setYOffset
    #
    # @param y_offset The new y_offset to use for positioning this image.
    #
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
