#!/usr/bin/env python
"""
This module enables the processing of camera frame(s) with
operations like averaging, slicing, etc..

It is also responsible for keeping tracking of how many
different cameras / feeds are available for each parameter
file, whether the cameras / feeds should be saved when
filming and what extension to use when saving.

Hazen 03/17
"""

import numpy

#from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.hal4000.camera.frame as frame
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

#
# We save all the controllers in a dictionary keyed on the
# parameters object. This is done so that we can create
# the feeds with the camera.control.Camera class but we
# use them from any other class. In particular the display
# classes need to access to the feeds to properly get and
# set the display parameters for each feed.
#
feed_controllers = {}

def getFeedController(parameters):
    return feed_controllers[parameters]

def isCamera(feed_name):
    if (len(feed_name) > 6):
        return (feed_name[:6] == "camera") and feed_name[6].isdigit()
    return False

def newFeedController(cameras, parameters):
    global feed_controllers

    # Not that it probably takes very long to create a
    # FeedController, but memoize them anyway.
    if not parameters in feed_controllers:
        feed_controllers[parameters] = FeedController(cameras, parameters)

    return feed_controllers[parameters]


class FeedException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
        

#
# The different kinds of feeds.
#
class Feed(object):
    """
    The base class for all the feeds.
    """

    def __init__(self, feed_name = None):
        self.feed_name = feed_name

    def newFrame(self, new_frame):
        pass

    def sliceFrame(self, new_frame):
        pass

    def startFeed(self):
        pass

    def startFilm(self):
        pass

    def stopFeed(self):
        pass

    def stopFilm(self):
        pass

# Remove this?
class FeedCamera(Feed):
    """
    Camera feeds just pass through the camera frames that they match.
    """
    def newFrame(self, new_frame):
        if (new_frame.which_camera == self.feed_name):
            return [new_frame]



class FeedNC(Feed):
    """
    The base class for the non-camera feeds.
    """
    def __init__(self, parameters = None, **kwds):
        super().__init__(**kwds)
        self.which_camera = parameters.get("feeds." + self.feed_name + ".source")
        self.frame_slice = None

        # Get camera binning as we'll use this either way.
        c_x_bin = parameters.get(self.which_camera + ".x_bin")
        c_y_bin = parameters.get(self.which_camera + ".y_bin")

        # See if we need to slice.
        x_start = parameters.get("feeds." + self.feed_name + ".x_start", 0)
        x_end = parameters.get("feeds." + self.feed_name + ".x_end", 0)
        y_start = parameters.get("feeds." + self.feed_name + ".y_start", 0)
        y_end = parameters.get("feeds." + self.feed_name + ".y_end", 0)

        if (x_start != 0) or (x_end != 0) or (y_start != 0) or (y_end != 0):

            # Determine the size of the camera.
            c_x_pixels = parameters.get(self.which_camera + ".x_pixels")/c_x_bin
            c_y_pixels = parameters.get(self.which_camera + ".y_pixels")/c_y_bin

            # Set unset values based on the camera size.
            if (x_start == 0):
                x_start = 1
                parameters.set("feeds." + self.feed_name + ".x_start", x_start)
            if (x_end == 0):
                x_end = c_x_pixels
                parameters.set("feeds." + self.feed_name + ".x_end", x_end)
            if (y_start == 0):
                y_start = 1
                parameters.set("feeds." + self.feed_name + ".y_start", y_start)
            if (y_end == 0):
                y_end = c_y_pixels
                parameters.set("feeds." + self.feed_name + ".y_end", y_end)

            # Check that slices are inside the camera ROI.
            if (x_start < 1) or (x_start >= c_x_pixels) or (x_start >= x_end):
                raise FeedException("x_start out of range in feed " + self.feed_name + " (" + str(x_start) + ")")
            if (x_end <= x_start) or (x_end > c_x_pixels):
                raise FeedException("x_end out of range in feed " + self.feed_name + " (" + str(x_end) + ")")
            if (y_start < 1) or (y_start >= c_y_pixels) or (y_start >= y_end):
                raise FeedException("y_start out of range in feed " + self.feed_name + " (" + str(y_start) + ")")
            if (y_end <= y_start) or (y_end > c_y_pixels):
                raise FeedException("y_end out of range in feed " + self.feed_name + " (" + str(y_end) + ")")

            # Adjust for 0 indexing.
            x_start -= 1
            y_start -= 1
            
            self.frame_slice = (slice(y_start, y_end),
                                slice(x_start, x_end))

            self.x_pixels = x_end - x_start
            self.y_pixels = y_end - y_start

            # Check that the feed size is a multiple of 4 in x.
            if not ((self.x_pixels % 4) == 0):
                raise FeedException("x size of " + str(self.x_pixels) + " is not a multiple of 4 in feed " + self.feed_name)
            
        else:
            self.x_pixels = parameters.get(self.which_camera + ".x_pixels")/c_x_bin
            self.y_pixels = parameters.get(self.which_camera + ".y_pixels")/c_y_bin

        parameters.set("feeds." + self.feed_name + ".x_pixels", self.x_pixels)
        parameters.set("feeds." + self.feed_name + ".y_pixels", self.y_pixels)
        parameters.set("feeds." + self.feed_name + ".x_bin", 1)
        parameters.set("feeds." + self.feed_name + ".y_bin", 1)
        parameters.set("feeds." + self.feed_name + ".bytes_per_frame", 2 * self.x_pixels * self.y_pixels)

    def sliceFrame(self, new_frame):
        if (new_frame.which_camera == self.which_camera):
            if self.frame_slice is None:
                return new_frame.np_data
            else:
                w = new_frame.image_x
                h = new_frame.image_y
                sliced_frame = numpy.reshape(new_frame.np_data, (h,w))[self.frame_slice]
                return numpy.ascontiguousarray(sliced_frame)


class FeedAverage(FeedNC):
    """
    The feed for averaging frames together.
    """

    def __init__(self, **kwds):
        super().__init__(self, **kwds)

        self.average_frame = None
        self.counts = 0
        self.frame_number = -1
        self.frames_to_average = self.parameters.get("feeds." + self.feed_name + ".frames_to_average")

    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None:
            if self.average_frame is None:
                self.average_frame = sliced_data.astype(numpy.uint32)
            else:
                self.average_frame += sliced_data
            self.counts += 1

        if (self.counts == self.frames_to_average):
            average_frame = self.average_frame/self.frames_to_average                                                         
            self.average_frame = None
            self.counts = 0
            self.frame_number += 1
            return [frame.Frame(average_frame.astype(numpy.uint16),
                                self.frame_number,
                                self.x_pixels,
                                self.y_pixels,
                                self.feed_name,
                                False)]
        else:
            return []
                
    def startFeed(self):
        self.average_frame = None
        self.counts = 0
        self.frame_number = -1
        

class FeedInterval(FeedNC):
    """
    Feed for picking out a sub-set of the frames.
    """
    def __init__(self, **kwds):
        super().__init__(self, **kwds)

        temp = self.parameters.get("feeds." + self.feed_name + ".capture_frames")
        self.capture_frames = map(int, temp.split(","))
        self.cycle_length = self.parameters.get("feeds." + self.feed_name + ".cycle_length")
        self.frame_number = -1

    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None:
            if (new_frame.number % self.cycle_length) in self.capture_frames:
                self.frame_number += 1
                return [frame.Frame(sliced_data,
                                    self.frame_number,
                                    self.x_pixels,
                                    self.y_pixels,
                                    self.feed_name,
                                    False)]
            else:
                return []
        else:
            return []

    def startFeed(self):
        self.frame_number = -1
        

# This one is a bad idea??
class FeedLastFilm(FeedNC):
    """
    Feed for displaying the previous film.
    """
    cur_film_frame = None
    last_film_frame = None

    def __init__(self, **kwds):
        super().__init__(self, **kwds)

        # For updates, update at 2Hz.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.handleTimer)
        self.update = False

        self.which_frame = self.parameters.get("feeds." + self.feed_name + ".which_frame", 0)

    def handleTimer(self):
        self.update = True
        
    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None and (new_frame.number == self.which_frame):
            FeedLastFilm.cur_film_frame = frame.Frame(sliced_data,
                                                      new_frame.number,
                                                      self.x_pixels,
                                                      self.y_pixels,
                                                      self.feed_name,
                                                      False)

        if self.update and FeedLastFilm.last_film_frame is not None:
            if (FeedLastFilm.last_film_frame.image_x == self.x_pixels) and (FeedLastFilm.last_film_frame.image_y == self.y_pixels):
                self.update = False
                return [FeedLastFilm.last_film_frame]
            
        return []

    def startFeed(self):
        self.timer.start()

    def stopFeed(self):
        self.timer.stop()
        
    def stopFilm(self):
        FeedLastFilm.last_film_frame = FeedLastFilm.cur_film_frame


class FeedSlice(FeedNC):
    """
    Feed for slicing out sub-sets of frames.
    """
    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None:
            return [frame.Frame(sliced_data,
                                new_frame.number,
                                self.x_pixels,
                                self.y_pixels,
                                self.feed_name,
                                False)]
        else:
            return []

        
class FeedController(object):
    """
    Feed controller
    """
    def __init__(self, cameras, parameters):

        self.feed_names = list(cameras)
        self.feed_names_to_save = []
        self.feeds = []
        self.parameters = parameters

        # Get the names of the additional feeds (if any).
        if ("feeds" in self.parameters.getAttrs()):
            self.feed_names += self.parameters.get("feeds").getAttrs()

        # Create the feeds.
        for feed_name in self.feed_names:
            if isCamera(feed_name):
                self.feeds.append(FeedCamera(feed_name, self.parameters))
            else:

                # Figure out what type of feed this is.
                fclass = None
                feed_type = self.parameters.get("feeds." + feed_name + ".feed_type")
                if (feed_type == "average"):
                    fclass = FeedAverage
                elif (feed_type == "interval"):
                    fclass = FeedInterval
                elif (feed_type == "lastfilm"):
                    fclass = FeedLastFilm
                elif (feed_type == "slice"):
                    fclass = FeedSlice
                else:
                    QtWidgets.QMessageBox.information(None,
                                                      "Bad Feed Settings",
                                                      "Unknown feed type " + feed_type + " in feed " + feed_name)
                    self.feed_names.remove(feed_name)
                    
                # Try and create a feed of this type.
                if fclass is not None:
                    try:
                        new_feed = fclass(feed_name, self.parameters)
                    except FeedException as e:
                        QtWidgets.QMessageBox.information(None,
                                                          "Bad Feed Settings",
                                                          str(e))
                        self.feed_names.remove(feed_name)
                    else:
                        self.feeds.append(new_feed)
                                    
        # Figure out what feed should be saved to disk during filming.
        for feed_name in self.feed_names:
            if isCamera(feed_name):
                if self.parameters.get(feed_name + ".save", True):
                    self.feed_names_to_save.append(feed_name)
            else:
                if self.parameters.get("feeds." + feed_name + ".save", False):
                    self.feed_names_to_save.append(feed_name)

    def getCamera(self, feed_name):
        if isCamera(feed_name):
            return feed_name
        else:
            return self.parameters.get("feeds." + feed_name + ".source")

    def getFeedNames(self):
        return self.feed_names

    def getFeedNamesToSave(self):
        return self.feed_names_to_save
    
    def getFeedParameter(self, feed_name, pname, default_value = None):

        # If we are asked for a parameter for a camera just return it.
        if isCamera(feed_name):
            return self.parameters.get(feed_name + "." + pname, default_value)

        # If we are asked for a parameter for a feed, return it if it
        # exists, otherwise return the corresponding parameter from
        # camera that the feed is associated with.
        if self.parameters.has("feeds." + feed_name + "." + pname):
            return self.parameters.get("feeds." + feed_name + "." + pname)

        else:
            which_camera = self.parameters.get("feeds." + feed_name + ".source")
            return self.parameters.get(which_camera + "." + pname, default_value)

    def newFrame(self, new_frame):
        feed_frames = []
        for feed in self.feeds:
            feed_frames += feed.newFrame(new_frame)
        return feed_frames
    
    def setFeedParameter(self, feed_name, pname, pvalue):
        if isCamera(feed_name):
            self.parameters.set(feed_name + "." + pname, pvalue)
        else:
            self.parameters.set("feeds." + feed_name + "." + pname, pvalue)

    def startFeeds(self):
        for feed in self.feeds:
            feed.startFeed()

    def startFilm(self):
        for feed in self.feeds:
            feed.startFilm()

    def stopFeeds(self):
        for feed in self.feeds:
            feed.stopFeed()

    def stopFilm(self):
        for feed in self.feeds:
            feed.stopFilm()


class Feeds(halModule.HalModule):
    """
    Feeds controller.

    This sends the following messages:
     'feed list'
    """    

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.feed_list = []

        halMessage.addMessage("feed list")

    def broadcastFeedInfo(self):
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "feed list",
                                                   data = {"feeds" : self.feed_list}))

    def processMessage(self, message):
        super().processMessage(message)
        if (message.level == 1):

            if (message.getType() == "current parameters"):
                data = message.getData()
                if ("camera" in data):
                    self.feed_list.append({"extension" : data["parameters"].get("filename_ext"),
                                           "feed_name" : data["camera"],
                                           "is_camera" : True,
                                           "is_master" : data["master"],
                                           "is_saved" : data["parameters"].get("is_saved")})

            elif (message.getType() == "new parameters"):
                self.feed_list = []

            elif (message.getType() == "configure2"):
                self.broadcastFeedInfo()



