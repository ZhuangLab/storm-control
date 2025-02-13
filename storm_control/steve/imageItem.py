#!/usr/bin/env python
"""
This module handles:

1. The images that Steve displays.
2. Loading images from the disk.

Hazen 10/18
"""
import numpy
import os
import pickle
import warnings
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.steve.coord as coord
import storm_control.steve.mosaicDialog as mosaicDialog
import storm_control.steve.movieReader as movieReader
import storm_control.steve.steveItems as steveItems


def getCameraExtension(movie_xml):
    ext = movie_xml.get("camera1.extension", "")
    if (len(ext) > 0):
        return "_" + ext
    else:
        return ""


class ImageItem(steveItems.SteveItem):
    """
    Base class for image items, this is also the default single
    color image.
    """
    data_type = "image"
    
    def __init__(self, numpy_data = None, objective_name = None, x_um = None, y_um = None, zvalue = None, **kwds):
        super().__init__(**kwds)

        self.magnification = 1.0
        self.numpy_data = numpy_data
        self.objective_name = objective_name
        self.pixmap_max = 0
        self.pixmap_min = 0
        self.x_pix = 0
        self.x_offset_pix = 0
        self.x_um = x_um
        self.y_pix = 0
        self.y_offset_pix = 0
        self.y_um = y_um
        self.zvalue = zvalue

        if x_um is not None:
            self.x_pix = coord.umToPix(x_um)

        if y_um is not None:
            self.y_pix = coord.umToPix(y_um)
        
        self.graphics_item = QtWidgets.QGraphicsPixmapItem()

        print('imageItems item ID', self.item_id)

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
        image[(image > 255.0)] = 255.0
        image[(image < 0.0)] = 0.0
        image = image.astype(numpy.uint8)

        # Create the pixmap
        w, h = image.shape
        q_image = QtGui.QImage(image.data, h, w, QtGui.QImage.Format_Indexed8)
        q_image.ndarray = image
        for i in range(256):
            q_image.setColor(i, QtGui.QColor(i,i,i).rgb())
        q_pixmap = QtGui.QPixmap.fromImage(q_image)
        self.graphics_item.setPixmap(q_pixmap)

    def getContrast(self):
        """
        Return the current contrast values.
        """
        return [self.pixmap_min, self.pixmap_max]
        
    def getDict(self):
        """
        Return the attributes of ImageItem as a dictionary minus the 
        graphics_item attribute.
        """
        save_dict = self.__dict__.copy()
        del save_dict["graphics_item"]
        return save_dict

    def getObjectiveName(self):
        return self.objective_name

#    def getPos(self):
#        return coord.Point(self.x_um, self.y_um, "um")

    def getPosUm(self):
        return [self.x_um, self.y_um]
    
    def getSizeUm(self):
        pixmap = self.graphics_item.pixmap()
        width_um = coord.pixToUm(pixmap.width()/self.magnification)
        height_um = coord.pixToUm(pixmap.height()/self.magnification)
        return (width_um, height_um)
        
    def getZValue(self):
        return self.graphics_item.zValue()

    def initializeWithDictionary(self, a_dict):
        """
        This function initializes the object attributes with values from
        a pickled object. It is used in loading a mosaic file.
        """
        for key in a_dict:

            new_key = key
            
            # Older Steve used 'data', but 'numpy_data' seems like a better name.
            if (new_key == "data"):
                new_key = "numpy_data"

            if hasattr(self, new_key):
                setattr(self, new_key, a_dict[key])
            else:
                warnings.warn("Ignoring unknown attribute " + new_key)

        # Create pixmap & set scale.
        self.dataToPixmap(self.pixmap_min, self.pixmap_max)
        self.setTransform()

        # Position in XYZ.
        self.setPos()
        self.setZValue(self.zvalue)

    def saveItem(self, directory, name_no_extension):
        """
        Save an ImageItem in a mosaic file.
        """
        filename = name_no_extension + "_{0:d}.stv".format(self.getItemID())
        with open(os.path.join(directory, filename), "wb") as fp:
            pickle.dump(self.getDict(), fp)
        return filename

    def setContrast(self, pixmap_min, pixmap_max):
        """
        Set the displayed pixmap's contrast.
        """
        self.dataToPixmap(pixmap_min, pixmap_max)

    def setMagnification(self, obj_um_per_pixel):
        """
        Set the pixmaps scale.

        Magnification is coord.Point.pixels_to_um / image pixel size in micron. For
        example an image with a pixel size of 0.2um would have a magnification of 0.5
        assuming the standard Steve pixels_to_um value of 0.1.

        The pixmap also gets moved in order to stay centered on it's stage position.
        """
        self.magnification = coord.Point.pixels_to_um / obj_um_per_pixel
        self.setTransform()
        self.setPos()

    def setOffset(self, x_um_offset, y_um_offset):
        """
        Set X/Y pixel offsets for the pixmap in the scene.
        """
        self.x_offset_pix = coord.umToPix(x_um_offset)
        self.y_offset_pix = coord.umToPix(y_um_offset)
        self.setPos()

    def setPos(self):
        pixmap = self.graphics_item.pixmap()
        x_pix = self.x_pix - (pixmap.width() * 0.5 / self.magnification)
        y_pix = self.y_pix - (pixmap.height() * 0.5 / self.magnification)
        self.graphics_item.setPos(x_pix + self.x_offset_pix, y_pix + self.y_offset_pix)

    def setTransform(self):
        transform = QtGui.QTransform().scale(1.0/self.magnification, 1.0/self.magnification)
        self.graphics_item.setTransform(transform)
        
    def setZValue(self, zvalue):
        self.zvalue = zvalue
        self.graphics_item.setZValue(zvalue)
        

class ImageItemLoader(steveItems.SteveItemLoader):
    """
    Creates an ImageItem from saved data saved with a mosaic file.
    """
    def load(self, directory, image_filename):
        with open(os.path.join(directory, image_filename), "rb") as fp:
            image_item_dict = pickle.load(fp)
        image_item = ImageItem()

        # FIX sometimes Steve crashes when loading in old mosaics
        # create a copy of the item_id assigned when the object is initialized
        item_id_new = image_item.getItemID()
        image_item.initializeWithDictionary(image_item_dict) # this will overwrite the correct item_id with the stored value
        # re-assign the original item_id
        image_item.item_id = item_id_new

        return image_item

        
class ImageItemLoaderHAL(object):
    """
    This class handles basic image loading into Steve. These are BW single
    channel images. These are images captured by HAL, not the ImageItems
    saved by Steve in the mosaic file.
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
        [obj_um_per_pix, x_um_offset, y_um_offset] = self.objectives.getData(self.getObjectiveName(xml))

        # Location.
        [x_um, y_um] = list(map(float, xml.get("acquisition.stage_position").split(",")))

        # Initial contrast.
        pixmap_min = xml.get("display00.camera1.display_min")
        pixmap_max = xml.get("display00.camera1.display_max")

        image_item = ImageItem(numpy_data = numpy_data,
                               objective_name = self.getObjectiveName(xml),
                               x_um = x_um,
                               y_um = y_um)
        image_item.dataToPixmap(pixmap_min, pixmap_max)
        image_item.setMagnification(obj_um_per_pix)
        image_item.setOffset(x_um_offset, y_um_offset)

        return image_item

    def getObjectiveName(self, xml):
        obj_attr = xml.get("mosaic.objective")
        return xml.get("mosaic." + obj_attr).split(",")[0]

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

        # Fill out fake mosaic settings.
        #
        # HAL uses 'obj1', 'obj2', etc.. for the objective XML tags.
        #
        obj_name = "fake"
        xml.set("mosaic." + obj_name, ",".join(map(str, self.fake_settings[3:])))
        xml.set("mosaic.objective", obj_name)
        xml.set("mosaic.flip_horizontal", self.fake_settings[0])
        xml.set("mosaic.flip_vertical", self.fake_settings[1])
        xml.set("mosaic.transpose", self.fake_settings[2])

    def handleRealXML(self, xml):
        """
        Populate objective group box, if this hasn't already been done.
        """
        if not self.objectives.hasObjective(xml.get("mosaic.objective")):
            i = 1
            while xml.has("mosaic.obj" + str(i)):
                obj_data = xml.get("mosaic.obj" + str(i))
                self.objectives.addObjective(obj_data.split(","))
                i += 1
            
    def loadMovie(self, no_ext_name, frame_number):
        """
        For basic loading we assume that the XML file has the same name
        as the image.
        """
        # Note: In the old version we tried a few times to load the files because
        #       this sometimes failed, possibly due to a race condition. Not sure
        #       if this still a problem with HAL2.
        #

        # Look for XML file.
        xml_name = no_ext_name + ".xml"
        if os.path.exists(xml_name):
            xml = movieReader.paramsToStormXML(xml_name)

        # Try to create fake XML from a .inf file.
        #
        # FIXME: Untested.
        elif os.path.exists(no_ext_name + ".inf"):
            xml = movieReader.infToStormXml(no_ext_name + ".inf")

        # Fail.
        else:
            raise IOError("Could not find an associated .xml or .inf file for " + image_name)

        # Handle Faked XML (i.e. from an inf file).
        if xml.get("faked_xml", False):
            self.handleFakeXML(xml)
        # Handle real XML (fill out the objective group box, if this
        # hasn't already been done).
        else:
            self.handleRealXML(xml)

        # Set currently selected objective to this movies objective.
        self.objectives.changeObjective(self.getObjectiveName(xml))

        # Load movie numpy data.
        mv_reader = movieReader.inferReader(no_ext_name + getCameraExtension(xml) + xml.get("film.filetype"))
        numpy_data = mv_reader.loadAFrame(frame_number)
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
        if xml.get("mosaic.flip_vertical", False):
            numpy_data = numpy.flipud(numpy_data)
        if xml.get("mosaic.transpose", False):
            numpy_data = numpy.transpose(numpy_data)
        return numpy_data



