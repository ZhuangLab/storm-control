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

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.camera.frame as frame
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


def createCameraFeedInfo(cam_params, camera_name, is_master):
    """
    Create a feed information dictionary for a camera.
    """
    return {"bytes_per_frame" : cam_params.get("bytes_per_frame"),
            "default_max" : cam_params.get("default_max"),
            "default_min" : cam_params.get("default_min"),
            "extension" : cam_params.get("filename_ext"),
            "feed_name" : camera_name,
            "flip_horizontal" : cam_params.get("flip_horizontal"),
            "flip_vertical" : cam_params.get("flip_vertical"),
            "is_camera" : True,
            "is_master" : is_master,
            "is_saved" : cam_params.get("is_saved"),
            "max_intensity" : cam_params.get("max_intensity"),
            "transpose" : cam_params.get("transpose"),
            "x_pixels" : cam_params.get("x_pixels"),
            "y_pixels" : cam_params.get("y_pixels")}

    
def getCameraFeedName(feed_name):
    """
    Use this to separate the camera and the feed name from a feed name string.
    """
    tmp = feed_name.split("-")
    if (len(tmp) > 1):
        return tmp
    else:
        return [tmp[0], None]
    

class FeedException(halExceptions.HalException):
    pass
        

class FeedNC(object):
    """
    The base class for all the feeds.
    """
    
    def __init__(self, camera_name = None, camera_parameters = None, feed_name = None, feed_parameters = None, **kwds):
        """
        camera_name - The name of the camera module the feed is derived from.
        camera_parameters - The parameters of the corresponding camera.
        feed_parameters - The parameters of this feed (not all of them in aggregate).
        """
        super().__init__(**kwds)
        self.camera_name = camera_name
        self.feed_name = camera_name + "-" + feed_name
        self.parameters = feed_parameters

        self.frame_number = -1
        self.frame_slice = None

        # Shorten the names..
        cp = camera_parameters
        fp = feed_parameters
        
        # Figure out what to slice, if anything.
        x_start = fp.get("x_start", 1)
        x_end = fp.get("x_end", cp.get("x_pixels"))
        y_start = fp.get("y_start", 1)
        y_end = fp.get("y_end", cp.get("y_pixels"))

        # Check if we actually need to slice.
        if (x_start != 1) or (x_end != cp.get("x_pixels")) or (y_start != 1) or (y_start != cp.get("y_pixels")):
            self.frame_slice = (slice(y_start-1, y_end),
                                slice(x_start-1, x_end))

        self.x_pixels = x_end - x_start + 1
        self.y_pixels = y_end - y_start + 1
        bytes_per_frame = 2 * self.x_pixels * self.y_pixels
        
        # Check that the feed size is a multiple of 4 in x.
        if not ((self.x_pixels % 4) == 0):
            raise FeedException("x size of " + str(self.x_pixels) + " is not a multiple of 4 in feed " + feed_name)

        # This is everything that display.cameraFrameDisplay and film.film need
        # to know about a feed.
        self.feed_info = {"bytes_per_frame" : bytes_per_frame,
                          "colortable" : fp.get("colortable", "none"),
                          "default_max" : fp.get("default_max", cp.get("default_max")),
                          "default_min" : fp.get("default_min", cp.get("default_min")),
                          "extension" : feed_name,
                          "feed_name" : self.feed_name,
                          "flip_horizontal" : cp.get("flip_horizontal"),
                          "flip_vertical" : cp.get("flip_vertical"),
                          "is_camera" : False,
                          "is_master" : False,
                          "is_saved" : feed_parameters.get("save", True),
                          "max_intensity" : fp.get("max_intensity", cp.get("max_intensity")),
                          "transpose" : cp.get("transpose"),
                          "x_pixels" : self.x_pixels,
                          "y_pixels" : self.y_pixels}

    def getFeedInfo(self):
        return self.feed_info

    def reset(self):
        self.frame_number = -1
    
    def sliceFrame(self, new_frame):
        if (new_frame.which_camera == self.camera_name):
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
        super().__init__(**kwds)

        self.average_frame = None
        self.counts = 0
        self.frames_to_average = self.parameters.get("frames_to_average")

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
                                self.feed_name)]
        else:
            return []

    def reset(self):
        super().reset()
        self.average_frame = None
        self.counts = 0
        
    
class FeedInterval(FeedNC):
    """
    Feed for picking out a sub-set of the frames.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        temp = self.parameters.get("capture_frames")
        self.capture_frames = list(map(int, temp.split(",")))
        self.cycle_length = self.parameters.get("cycle_length")

    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None:
            if (new_frame.frame_number % self.cycle_length) in self.capture_frames:
                self.frame_number += 1
                return [frame.Frame(sliced_data,
                                    self.frame_number,
                                    self.x_pixels,
                                    self.y_pixels,
                                    self.feed_name)]
            else:
                return []
        else:
            return []


# This one is a bad idea?? Yeah, probably, dropped for now..
"""
class FeedLastFilm(FeedNC):
    ""
    Feed for displaying the previous film.
    ""
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
"""

class FeedSlice(FeedNC):
    """
    Feed for slicing out sub-sets of frames.
    """
    def newFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        if sliced_data is not None:
            return [frame.Frame(sliced_data,
                                new_frame.frame_number,
                                self.x_pixels,
                                self.y_pixels,
                                self.feed_name)]
        else:
            return []

        
class FeedController(object):
    """
    Feed controller.
    """
    def __init__(self, parameters = None, **kwds):
        """
        parameters - This is all of the current parameters as we'll also need
                     information about the cameras.
        """
        super().__init__(**kwds)

        self.feeds = []
        self.parameters = None

        # Get the names of the additional feeds (if any).
        if not parameters.has("feeds"):
            return

        # Create the feeds.
        self.parameters = parameters.get("feeds")
        for feed_name in self.parameters.getAttrs():
            feed_params = self.parameters.get(feed_name)
            camera_name = feed_params.get("source")
            camera_params = parameters.get(camera_name)
            
            # Figure out what type of feed this is.
            fclass = None
            feed_type = feed_params.get("feed_type")
            if (feed_type == "average"):
                fclass = FeedAverage
            elif (feed_type == "interval"):
                fclass = FeedInterval
            elif (feed_type == "lastfilm"):
                fclass = FeedLastFilm
            elif (feed_type == "slice"):
                fclass = FeedSlice
            else:
                raise FeedException("Unknown feed type '" + feed_type + "' in feed '" + feed_name + "'")

            self.feeds.append(fclass(camera_name = camera_name,
                                     camera_parameters = camera_params,
                                     feed_name = feed_name,
                                     feed_parameters = feed_params))

    def getFeedsInfo(self):
        feeds_info = {}
        for feed in self.feeds:
            f_info = feed.getFeedInfo()
            feeds_info[f_info["feed_name"]] = f_info
        return feeds_info

    def getParameters(self):
        return self.parameters

    def haveFeeds(self):
        return (len(self.feeds) > 0)
    
    def newFrame(self, new_frame):
        feed_frames = []
        for feed in self.feeds:
            feed_frames += feed.newFrame(new_frame)
        return feed_frames

    def resetFeeds(self):
        for feed in self.feeds:
            feed.reset()
            

class Feeds(halModule.HalModule):
    """
    Feeds controller.

    This sends the following messages:
     'feed list'
    """    

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.camera_info = {}
        self.feed_controller = None
        self.feeds_info = {}
        
        #
        # This message returns a dictionary keyed by feed name with all
        # relevant parameters for the feed name in another dictionary.
        #
        # e.g. dict["feed_name"]["display_max"] = ?
        #
        halMessage.addMessage("feeds information",
                              validator = {"data" : {"feeds" : [True, dict]}})

        # Sent each time a feed generates a frame.
        halMessage.addMessage("new frame", check_exists = False)
        
    def broadcastFeedInfo(self):
        """
        Send the 'feeds information' message.

        film.film uses this message to figure out which cameras / feeds to save.

        display.cameraDisplay uses this message to populate the feed chooser
        combobox.
        """
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "feeds information",
                                                   data = {"feeds" : self.feeds_info}))

    def processL1Message(self, message):

        if (message.getType() == "configure2"):
            self.broadcastFeedInfo()

        elif (message.getType() == "get feed information"):
            feed_name = message.getData()["feed_name"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"feed_name" : feed_name,
                                                                      "feed_info" : self.feeds_info[feed_name]}))

        elif (message.getType() == "initial parameters"):
            #
            # We get this message when the camera (and also other modules) respond
            # with their initial parameters. For each of the cameras we get all of
            # the key information. The information is then broadcast in the 'feed list'
            # message.
            #
            data = message.getData()
            if ("camera" in data):
                p = data["parameters"]

                #
                # These are the invariant properties of the camera. We could also
                # get the from the camera by sending a 'get feed config' message,
                # but it is easiest to just keep a record of all them at
                # initialization.
                #
                self.camera_info[data["camera"]] = {"camera" : data["camera"],
                                                    "master" : data["master"]}

                self.feeds_info[data["camera"]] = createCameraFeedInfo(p,
                                                                       data["camera"],
                                                                       data["master"])

        elif (message.getType() == "new parameters"):
            self.feed_controller = FeedController(parameters = message.getData()["parameters"])
            if not self.feed_controller.haveFeeds():
                self.feed_controller = None
            
        elif (message.getType() == "updated parameters"):
            self.feeds_info = {}
            params = message.getData()["parameters"]

            # Get camera information.
            for attr in params.getAttrs():
                if attr.startswith("camera"):
                    p = params.get(attr)
                    self.feeds_info[attr] = createCameraFeedInfo(p,
                                                                 self.camera_info[attr]["camera"],
                                                                 self.camera_info[attr]["master"])

            # Get feed information.
            if self.feed_controller is not None:
                self.feeds_info.update(self.feed_controller.getFeedsInfo())

            print("")
            for elts in self.feeds_info:
                print(elts)
                for elt in self.feeds_info[elts]:
                    print("  ", elt, self.feeds_info[elts][elt])
            print("")
                
            self.broadcastFeedInfo()

#        elif (message.getType() == "start camera"):
#            self.active = True

        elif (message.getType() == "start film"):
            if self.feed_controller is not None:
                self.feed_controller.resetFeeds()

#        elif (message.getType() == "start camera"):
#            self.active = False
            
        elif (message.getType() == "stop film"):
            if self.feed_controller is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"parameters" : self.feed_controller.getParameters()}))
                self.feed_controller.resetFeeds()

    def processL2Message(self, message):
        if self.feed_controller is not None:
            frame = message.getData()["frame"]
            feed_frames = self.feed_controller.newFrame(frame)
            for ff in feed_frames:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "new frame",
                                                           level = 2,
                                                           data = {"frame" : ff}))

