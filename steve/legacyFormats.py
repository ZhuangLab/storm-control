#!/usr/bin/python
#
## @file
#
# Code for loading legacy mosaic file formats. This is not currently used,
# nor would it actually work. It is preserved here for reference purposes.
#
# Hazen 07/13
#


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
