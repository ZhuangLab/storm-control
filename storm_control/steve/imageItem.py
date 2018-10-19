#!/usr/bin/env python
"""
Deals with the images that Steve will display.

Hazen 10/18
"""
import os
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.coord as coord
import storm_control.steve.mosaicDialog as mosaicDialog
import storm_control.steve.movieReader as movieReader
import storm_control.steve.steveItems as steveItems


class ImageItem(steveItems.SteveItem):
    """
    Base class for image items, this is also the default single
    color image.
    """
    def __init__(self, numpy_data = None, x_pix = None, y_pix = None, **kwds):
        super().__init__(**kwds)

        self.item_type = "image"
        self.graphics_item = QtWidgets.QGraphicsPixmapItem()

        self.magnification = 1.0
        self.numpy_data = numpy_data
        self.objective = "na"
        self.pixmap_max = 0
        self.pixmap_min = 0
        self.x_pix = x_pix
        self.x_pix_offset = 0
        self.y_pix = y_pix
        self.y_pix_offset = 0

    def dataToPixmap(self, pixmap_min, pixmap_max):
        """
        Create a QtGui.QPixmap item from the numpy data.
        """
        self.pixmap_min = pixmap_min
        self.pixmap_max = pixmap_max

        image = self.numpy_data.copy()

        # Rescale & convert to 8bit
        image = numpy.ascontiguousarray(image, dtype = numpy.float32)
        image = 255.0 * (image - float(self.pixmap_min))/float(self.pixmap_max - self.pixmap_min)
        image[(frame > 255.0)] = 255.0
        image[(frame < 0.0)] = 0.0
        image = image.astype(numpy.uint8)

        # Create the pixmap
        w, h = image.shape
        q_image = QtGui.QImage(frame.data, h, w, QtGui.QImage.Format_Indexed8)
        q_image.ndarray = image
        for i in range(256):
            q_image.setColor(i, QtGui.QColor(i,i,i).rgb())
        q_pixmap = QtGui.QPixmap.fromImage(q_image)
        self.graphics_item.setPixmap(q_pixmap)

    def setOffset(self, x_um_offset, y_um_offset):
        """
        Set X/Y pixel offsets for the pixmap in the scene.
        """
        self.x_pix_offset = coord.umToPix(x_um_offset)
        self.y_pix_offset = coord.umToPix(y_um_offset)
        self.graphics_item.setPos(self.x_pix + self.x_offset_pix, self.y_pix + self.y_offset_pix)

    def setMagnification(self, obj_um_per_pixel):
        """
        Set the pixmaps scale.

        Magnification is coord.Point.pixels_to_um / image pixel size in micron. For
        example an image with a pixel size of 0.2um would have a magnification of 0.5
        assuming the standard Steve pixels_to_um value of 0.1.
        """
        self.magnification = coord.Point.pixels_to_um / obj_um_per_pixel
        transform = QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification)
        self.graphics_item.setTransform(transform)
        

class ImageLoader(object):
    """
    This class handles basic image loading into Steve. These are BW single
    channel images.
    """
    def __init__(self, objectives = None, **kwds):
        super().__init__(**kwds)

        self.fake_got_settings = False
        self.fake_settings = False
        
        # This is the objectives.ObjectiveGroupBox item, which is what
        # we're using to store the information about the different objectives.
        #
        self.objectives = objectives

    def dataXMLToImageItem(self, numpy_data, xml):
        """
        Create an Image Item from numpy_data and the corresponding XML.

        Note: This assumes that there is a camera1
        """
        # Size and offsets.
        [obj_um_per_pix, x_um_offset, y_um_offset] = self.objectives.getData(xml.get("mosaic.objective"))

        # Location.
        [x_um, y_um] = list(map(float, xml.get("acquisition.stage_position").split(",")))

        # HAL1 movies (or a faked XML file).
        if xml.has("camera1.scalemin"):
            pixmap_min = xml.get("camera1.scalemin")
            pixmap_max = xml.get("camera1.scalemax")

        # HAL2 movies.
        else:
            pixmap_min = xml.get("display00.camera1.display_min")
            pixmap_max = xml.get("display00.camera1.display_max")

        image_item = ImageItem(numpy_data = numpy_data,
                               x_pix = coord.umToPix(x_um),
                               y_pix = coord.umToPix(y_um))
        image_item.dataToPixmap(pixmap_min, pixmap_max)
        image_item.setOffset(x_um_offset, y_um_offset)
        image_item.setMagnification(obj_um_per_pix)

        return image_item

    def handleFakeXML(self, xml):
        """
        Handle XML that was faked for an image that did not have the 
        appropriate XML.
        """
        # Prompt user for settings for the first film.
        if not self.fake_got_settings:
            self.fake_got_settings = True
            self.fake_settings = mosaicDialog.execMosaicDialog()
            self.objectives.addObjective(self.fake_settings[3:])

        obj_name = "obj1"
        xml.set("mosaic." + obj_name, ",".join(map(str, self.fake_settings[3:])))
        xml.set("mosaic.objective", obj_name)
        xml.set("mosaic.flip_horizontal", self.fake_settings[0])
        xml.set("mosaic.flip_vertical", self.fake_settings[1])
        xml.set("mosaic.transpose", self.fake_settings[2])

    def handleRealXML(self, xml):
        """
        Populate objective group box, if this hasn't already been done.
        """
        if not objectives.hasObjective(xml.get("mosaic.objective")):
            i = 1
            while xml.has("mosaic.obj" + str(i)):
                obj_data = xml.get("mosaic.obj" + str(i))
                self.objectives.addObjective(obj_data.split(","))
                i += 1
            
    def loadImage(self, image_name):
        """
        For basic loading we assume that the XML file has the same name
        as the image.
        """
        no_ext_name = os.path.splitext(image_name)[0]

        # Look for XML file.
        xml_name = no_ext_name + ".xml")
        if os.path.exists(xml_name):
            xml = movieReader.paramsToStormXML(xml_name)
        elif os.path.exists(no_ext_name + ".inf"):
            xml = infToXmlObject(no_ext_name + ".inf")
        else:
            raise IOError("Could not find an associated .xml or .inf file for " + image_name)

        # Handle Faked XML (i.e. from an inf file).
        if xml.get("faked_xml", False):
            self.handleFakeXML(xml)
        # Handle real XML (fill out the objective group box, if this
        # hasn't already been done.
        else:
            self.handleRealXML(xml)

        # Set currently selected objective to this movies objective.
        self.objectives.changeObjective(xml.get("mosaic.objective"))

        # Load movie numpy data.
        mv_reader = movieReader.inferReader(image_name)
        numpy_data = mv_reader.loadAFrame(0)
        mv_reader.close()

        # Orient.
        numpy_data = self.orientNumpyData(numpy_data, xml)

        # Create ImageItem.
        image_item = self.dataXMLToImageItem(numpy_data, xml)

        return image_item

    def orientNumpyData(self, numpy_data, xml):
        """
        Orients numpy data array based on XML.
        """
        if xml.get("mosaic.flip_horizontal", False):
            numpy_data = numpy.fliplr(numpy_data)
        if movie.xml.get("mosaic.flip_vertical", False):
            numpy_data = numpy.flipud(numpy_data)
        if movie.xml.get("mosaic.transpose", False):
            numpy_data = numpy.transpose(numpy_data)
        return numpy_data


