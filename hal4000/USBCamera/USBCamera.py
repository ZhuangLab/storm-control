#!/usr/bin/python
#
# Capture pictures from a USB camera (used as
# the focus lock detector in some setups).
#
# This requires the PIL and numpy libraries.
#
# Hazen 03/12
#

import cv2.cv as cv
import numpy
from PIL import Image
#import pygame
#import pygame.camera
import time

from VideoCapture import Device

#pygame.init()
#pygame.camera.init()

class VCCamera():
    def __init__(self, camera_num = 0, xmin = 0, xmax = 150, ymin = 0, ymax = 300):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.cam = Device(devnum = camera_num)

    def capture(self):
        # These do the same thing, but the second one is much faster..
        if 0:
            image = self.cam.getImage()
            data = numpy.array(image.getdata(), numpy.uint8).reshape(image.size[1], image.size[0], 3)
        if 1:
            buf = self.cam.getBuffer()
            x_size = buf[1]
            y_size = buf[2]
            data = numpy.fromstring(buf[0], numpy.uint8).reshape(y_size, x_size, 3)
            data = data[self.xmin:self.xmax,self.ymin:self.ymax]
        data = numpy.average(data, 2)
        return data

class openCvCamera():
    def __init__(self, camera_num = 0, xmin = 0, xmax = 300, ymin = 0, ymax = 300):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.cam = cv.CaptureFromCAM(camera_num)
        print "W:", cv.GetCaptureProperty(self.cam, cv.CV_CAP_PROP_FRAME_WIDTH)
        print "H:", cv.GetCaptureProperty(self.cam, cv.CV_CAP_PROP_FRAME_HEIGHT)
        print "M:", cv.GetCaptureProperty(self.cam, cv.CV_CAP_PROP_MODE)

    def capture(self):
        frame = cv.QueryFrame(self.cam)

#class PyGCamera():
#    def __init__(self, camera_num = 0, xmin = 0, xmax = 300, ymin = 0, ymax = 300):
#        self.xmin = xmin
#        self.xmax = xmax
#        self.ymin = ymin
#        self.ymax = ymax
#
#        self.size = (640,480)
#        self.clist = pygame.camera.list_cameras()
#        print self.clist
#        if not self.clist:
#            raise ValueError("Sorry, no camera detected")
#        self.cam = pygame.camera.Camera(self.clist[0], self.size)
#        self.cam.start()
#
#    def capture(self):
#        print self.cam.query_image()
#        buf = self.cam.get_raw()
#        print len(buf)

class USBQPD(VCCamera):
    def __init__(self, camera_num = 0, x_center = 150, y_center = 150, im_size = 300):
        VCCamera.__init__(self,
                          camera_num = camera_num)
#                          xmin = x_center - im_size/2,
#                          xmax = x_center + im_size/2,
#                          ymin = y_center - im_size/2,
#                          ymax = y_center + im_size/2)
        self.image = None
        self.X = numpy.arange(150, 300) - float(im_size)*0.5
        self.last_sum = 0

    def capture(self):
        # We check that the current image is not identical to the last image.
        self.image = VCCamera.capture(self)
        cur_sum = numpy.sum(self.image)
        while(cur_sum == self.last_sum):
            #time.sleep(0.1)
            self.image = VCCamera.capture(self)
            cur_sum = numpy.sum(self.image)
        self.last_sum = cur_sum
        return self.image

    def getImage(self):
        return self.image

    def qpdScan(self):
        data = self.capture()
        data_ave = numpy.average(data, axis=1)
        power = numpy.sum(data_ave)
        x_offset = numpy.sum(self.X * data_ave)
        y_offset = 0.0
        return [power, x_offset, y_offset]

    def shutDown(self):
        pass

#
# Testing.
#

if __name__ == "__main__":
    if 1:
        cam = VCCamera()
        image = cam.capture()
        im = Image.fromarray(image)
        im.show()

#        for i in range(5):
#            cam.capture()
#            print i
            #image = cam.capture()
            #print image.shape
        #image = image[0:300,0:300]
#        #    print numpy.min(image), numpy.max(image)
#        #    max_loc = numpy.argmax(image)
#        im = Image.fromarray(image)
#        im.show()
    if 0:
        qpd = USBQPD()
        #for i in range(10):
        while True:
            scan = qpd.qpdScan()
            print scan[1]/scan[0], scan[1], scan[0]

    if 0:
        qpd = USBQPD()
        image = qpd.capture()
        print image.shape
        print numpy.sum(image[:,0:150])
        print numpy.sum(image[:,150:-1])
        print numpy.sum(image[0:150,:])
        print numpy.sum(image[150:-1,:])
        im = Image.fromarray(image)
        im.show()

    if 0:
        pts = 10
        #qpd = USBQPD()
        start = time.time()
        cam = openCvCamera()
        for i in range(pts):
            print i
            cam.capture()
            #print i, qpd.qpdScan()
        stop = time.time()
        print "Got", pts, "points in", stop - start, "seconds"
        print "FPS:", float(pts)/(stop - start)

        
#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
