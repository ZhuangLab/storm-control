#!/usr/bin/python
#
## @file
#
# This module provides a layer between the camera and HAL
# enabling the conversion of a single camera frame into
# several independent "feeds" that can be displayed and
# saved.
#
# Hazen 09/15
#

import numpy

from PyQt4 import QtCore

import sc_library.hdebug as hdebug

import camera.frame as frame

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
    return (feed_name[:6] == "camera")

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

# Camera feeds just pass through the camera frames that they match.
class CameraFeed(object):

    @hdebug.debug
    def __init__(self, feed_name, parameters):
        self.feed_name = feed_name

    def newFrame(self, new_frame):
        if (new_frame.which_camera == self.feed_name):
            return [new_frame]

    @hdebug.debug
    def startFeed(self):
        pass

    @hdebug.debug
    def stopFeed(self):
        pass


# The base class for feeds.    
class Feed(object):

    @hdebug.debug
    def __init__(self, feed_name, parameters):
        self.which_camera = parameters.get("feeds." + feed_name + ".source")
        self.feed_name = feed_name
        self.frame_slice = None

        # Get camera binning as we'll use this either way.
        c_x_bin = parameters.get(self.which_camera + ".x_bin")
        c_y_bin = parameters.get(self.which_camera + ".y_bin")

        # See if we need to slice.
        x_start = parameters.get("feeds." + feed_name + ".x_start", 0)
        x_end = parameters.get("feeds." + feed_name + ".x_end", 0)
        y_start = parameters.get("feeds." + feed_name + ".y_start", 0)
        y_end = parameters.get("feeds." + feed_name + ".y_end", 0)

        if (x_start != 0) or (x_end != 0) or (y_start != 0) or (y_end != 0):

            c_x_pixels = parameters.get(self.which_camera + ".x_pixels")/c_x_bin
            c_y_pixels = parameters.get(self.which_camera + ".y_pixels")/c_y_bin

            # Set unset values to those of the corresponding camera.
            if (x_start == 0):
                parameters.set("feeds." + feed_name + ".x_start", x_start)
            if (x_end == 0):
                x_end = c_x_pixels
                parameters.set("feeds." + feed_name + ".x_end", x_end)
            if (y_start == 0):
                parameters.set("feeds." + feed_name + ".y_start", y_start)
            if (y_end == 0):
                y_end = c_y_pixels
                parameters.set("feeds." + feed_name + ".y_end", y_end)

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

        else:
            self.x_pixels = parameters.get(self.which_camera + ".x_pixels")/c_x_bin
            self.y_pixels = parameters.get(self.which_camera + ".y_pixels")/c_y_bin

        parameters.set("feeds." + feed_name + ".x_pixels", self.x_pixels)
        parameters.set("feeds." + feed_name + ".y_pixels", self.y_pixels)
        parameters.set("feeds." + feed_name + ".x_bin", 1)
        parameters.set("feeds." + feed_name + ".y_bin", 1)
        parameters.set("feeds." + feed_name + ".bytes_per_frame", 2 * self.x_pixels * self.y_pixels)

    def newFrame(self, new_frame):
        pass
    
    def sliceFrame(self, new_frame):
        if (new_frame.which_camera == self.which_camera):
            if self.frame_slice is None:
                return new_frame.np_data
            else:
                w = new_frame.image_x
                h = new_frame.image_y
                return numpy.reshape(new_frame.np_data, (h,w))[self.frame_slice]

    @hdebug.debug
    def startFeed(self):
        pass

    @hdebug.debug
    def stopFeed(self):
        pass


# The feed for averaging frames together.
class FeedAverage(Feed):

    @hdebug.debug
    def __init__(self, feed_name, parameters):
        Feed.__init__(self, feed_name, parameters)

        self.average_frame = None
        self.counts = 0
        self.frame_number = -1
        self.frames_to_average = parameters.get("feeds." + self.feed_name + ".frames_to_average")

    def newFrame(self, new_frame):
        sliced_data = Feed.sliceFrame(self, new_frame)
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
        

# Feed for picking out a sub-set of the frames.
class FeedInterval(Feed):

    @hdebug.debug
    def __init__(self, feed_name, parameters):    
        Feed.__init__(self, feed_name, parameters)

        self.capture_frames = parameters.get("feeds." + self.feed_name + ".capture_frames")
        self.cycle_length = parameters.get("feeds." + self.feed_name + ".cycle_length")
        self.frame_number = -1

    def newFrame(self, new_frame):
        sliced_data = Feed.sliceFrame(self, new_frame)
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
        

# Feed for slicing out sub-sets of frames.
class FeedSlice(Feed):

    def newFrame(self, new_frame):
        sliced_data = Feed.sliceFrame(self, new_frame)
        if sliced_data is not None:
            return [frame.Frame(average_frame.astype(numpy.uint16),
                                new_frame.number,
                                self.x_pixels,
                                self.y_pixels,
                                self.feed_name,
                                False)]
        else:
            return []

        
#
# Feed controller
#
class FeedController(object):

    @hdebug.debug
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
                self.feeds.append(CameraFeed(feed_name, self.parameters))
            else:
                feed_type = self.parameters.get("feeds." + feed_name + ".feed_type")
                if (feed_type == "average"):
                    self.feeds.append(FeedAverage(feed_name, self.parameters))
                elif (feed_type == "interval"):
                    self.feeds.append(FeedInterval(feed_name, self.parameters))
                elif (feed_type == "slice"):
                    self.feeds.append(FeedSlice(feed_name, self.parameters))
                else:
                    raise FeedException("Unknown feed type " + feed_type + " in feed " + feed_name)
                    
        # Figure out what feed should be saved to disk during filming.
        for feed_name in self.feed_names:
            if isCamera(feed_name):
                if self.parameters.get(feed_name + ".save", True):
                    self.feed_names_to_save.append(feed_name)
            else:
                if self.parameters.get("feeds." + feed_name + ".save", False):
                    self.feed_names_to_save.append(feed_name)

    @hdebug.debug
    def getCamera(self, feed_name):
        if isCamera(feed_name):
            return feed_name
        else:
            return self.parameters.get("feeds." + feed_name + ".source")

    @hdebug.debug
    def getFeedNames(self):
        return self.feed_names

    @hdebug.debug
    def getFeedNamesToSave(self):
        return self.feed_names_to_save
    
    @hdebug.debug
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
            which_camera = self.parameters.get("feeds." + feed_name + ".camera")
            return self.parameters.get(which_camera + "." + pname, default_value)

    def newFrame(self, new_frame):
        feed_frames = []
        for feed in self.feeds:
            feed_frames += feed.newFrame(new_frame)
        return feed_frames
    
    @hdebug.debug
    def setFeedParameter(self, feed_name, pname, pvalue):
        if isCamera(feed_name):
            self.parameters.set(feed_name + "." + pname, pvalue)
        else:
            self.parameters.set("feeds." + feed_name + "." + pname, pvalue)

    @hdebug.debug
    def startFeeds(self):
        for feed in self.feeds:
            feed.startFeed()

    @hdebug.debug
    def stopFeeds(self):
        for feed in self.feeds:
            feed.stopFeed()

            

