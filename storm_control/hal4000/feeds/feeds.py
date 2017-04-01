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

import copy
import numpy

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.frame as frame
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


def checkParameters(parameters):
    """
    Checks parameters to verify that there won't be any errors
    when we actually try to create the feeds.

    Throw an exception if there are any problems.
    """
    if not parameters.has("feeds"):
        return

    # Check the feed parameters. For now all we are doing is
    # verifying that the feed x size is a multiple of 4.
    feed_parameters = parameters.get("feeds")
    for feed_name in feed_parameters.getAttrs():
        fp = feed_parameters.get(feed_name)
        cp = parameters.get(fp.get("source"))

        x_start = fp.get("x_start", 1)
        x_end = fp.get("x_end", cp.get("x_pixels"))
        x_pixels = x_end - x_start + 1
        
        # Check that the feed size is a multiple of 4 in x.
        if not ((x_pixels % 4) == 0):
            raise FeedException("x size of " + str(x_pixels) + " is not a multiple of 4 in feed " + feed_name)

    
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


class CameraFeedInfo(object):
    """
    This class stores all the information necessary to render and save
    the image from a camera/feed, along with some coordinate transform
    functions.
    """
    def __init__(self, camera_params = None, camera_name = None, is_master = False, **kwds):
        """
        This will automatically make a copy of camera_params.
        """
        super().__init__(**kwds)

        # Copy all of the camera parameters.
        self.parameters = camera_params.copy()

        # Add some additional parameters.

        # display.display will replace the colortable parameter with correct value.
        self.parameters.add(params.ParameterString(name = "colortable",
                                                   value = ""))
        self.parameters.add(params.ParameterString(name = "feed_name",
                                                   value = camera_name))
        self.parameters.add(params.ParameterSetBoolean(name = "is_camera",
                                                       value = True))
        self.parameters.add(params.ParameterSetBoolean(name = "is_master",
                                                       value = is_master))

        # These are for the various geometry calculations.
        self.camera_chip_x = self.parameters.getp("x_end").getMaximum()
        self.camera_chip_y = self.parameters.getp("y_end").getMaximum()
        self.camera_x_bin = self.parameters.get("x_bin")
        self.camera_x_pixels = self.parameters.get("x_pixels")
        self.camera_x_start = self.parameters.get("x_start")
        self.camera_y_bin = self.parameters.get("y_bin")
        self.camera_y_pixels = self.parameters.get("y_pixels")
        self.camera_y_start = self.parameters.get("y_start")
        self.feed_x_pixels = self.camera_x_pixels
        self.feed_x_start = 0
        self.feed_y_pixels = self.camera_y_pixels
        self.feed_y_start = 0
        self.flip_horizontal = self.parameters.get("flip_horizontal")
        self.flip_vertical = self.parameters.get("flip_vertical")
        self.transpose = self.parameters.get("transpose")

        # Delete all the parameters we won't need. Probably not necessary
        # but it at least keeps us from using them accidentally.
        to_keep = ["bytes_per_frame",
                   "colortable",
                   "default_max",
                   "default_min",
                   "extension",
                   "feed_name",
                   "flip_horizontal",
                   "flip_vertical",
                   "is_camera",
                   "is_master",
                   "max_intensity",
                   "saved",
                   "transpose",
                   "x_pixels",
                   "y_pixels",
                   "x_start",
                   "y_start"]
        
        for attr in list(self.parameters.getAttrs()):
            if not attr in to_keep:
                self.parameters.delete(attr)

    def addFeedInfo(self, feed_params):
        """
        This will update the object to give the right values for a feed
        derived from the camera the object was created with.

        Note: All transforms will adjusted by the feeds parameters.
        """
        for attr in self.parameters.getAttrs():
            if feed_params.has(attr):
                self.parameters.set(attr, feed_params.get(attr))
        self.feed_x_pixels = self.parameters.get("x_pixels")
        self.feed_x_start = self.parameters.get("x_start")
        self.feed_y_pixels = self.parameters.get("y_pixels")
        self.feed_y_start = self.parameters.get("y_start")

    def getChipMax(self):
        return self.camera_chip_x if (self.camera_chip_x > self.camera_chip_y)\
            else self.camera_chip_y

    def getChipSize(self):
        return [self.camera_chip_x, self.camera_chip_y]
#        if self.transpose:
#            return [self.camera_chip_y, self.camera_chip_x]
#        else:
#            return [self.camera_chip_x, self.camera_chip_y]

    def getFeedName(self):
        return self.parameters.get("feed_name")

    def getFrameCenter(self):
        """
        Center point of the frame in display coordinates.
        """
        cx = self.camera_x_bin*(self.camera_x_start + self.feed_x_start + int(0.5 * self.feed_x_pixels))
        cy = self.camera_y_bin*(self.camera_y_start + self.feed_y_start + int(0.5 * self.feed_y_pixels))
        return [cx, cy]
#        return self.transformChipToDisplay(cx, cy)
    
    def getFrameMax(self):
        xp = self.feed_x_pixels * self.camera_x_bin
        yp = self.feed_y_pixels * self.camera_y_bin
        return xp if (xp > yp) else yp

    def getFrameScale(self):
        return [self.camera_x_bin, self.camera_y_bin]        
#        if self.transpose:
#            return [self.camera_y_bin, self.camera_x_bin]
#        else:
#            return [self.camera_x_bin, self.camera_y_bin]
    
#    def getFrameSize(self):
#        if self.transpose:
#            return [self.feed_y_pixels, self.feed_x_pixels]
#        else:
#            return [self.feed_x_pixels, self.feed_y_pixels]

    def getFrameZeroZero(self):
        """
        Where to place the frame in the display.
        """
        zx = self.camera_x_bin*(self.camera_x_start + self.feed_x_start)
        zy = self.camera_y_bin*(self.camera_y_start + self.feed_y_start)
        return [zx, zy]
        #return self.transformChipToDisplay(zx, zy)
        
    def getParameter(self, name):
        return self.parameters.get(name)

    def setParameter(self, name, value):
        self.parameters.set(name, value)

#    def transformChipToDisplay(self, cx, cy):
#        """
#        Go from chip coordinates to display coordinates.
#        """
#        if self.flip_horizontal:
#            cx = self.camera_chip_x - cx
#        if self.flip_vertical:
#            cy = self.camera_chip_y - cy
#        if self.transpose:
#            [cx, cy] = [cy, cx]
#
#        return [cx, cy]

    def transformChipToFrame(self, cx, cy):
        """
        Go from chip coodinates to frame coordinates. Typically frame 
        will only be part of the camera chip not the entire chip.
        """
        cx -= (self.camera_x_start + self.feed_x_start)
        cy -= (self.camera_y_start + self.feed_y_start)
        cx = int(cx/self.camera_x_bin)
        cy = int(cy/self.camera_y_bin)
        return [cx, cy]

#    def transfromDisplayToChip(self, dx, dy):
#        """
#        Go from display coordinate to chip coordinates.
#        """
#        if self.transpose:
#            [dx, dy] = [dy, dx]
#        if self.flip_vertical:
#            dy = self.camera_chip_y - dy
#        if self.flip_horizontal:
#            dx = self.camera_chip_x - dx
#
#        return [dx, dy]

    
class FeedNC(object):
    """
    The base class for all the feeds.
    """
    
    def __init__(self, camera_feed_info = None, feed_name = None, feed_parameters = None, **kwds):
        """
        camera_feed_info - The CameraFeedInfo object this seed is derived from.
        feed_name - The name of this feed, this will be combined with the camera name
                    to create the final feed name.
        feed_parameters - The parameters of this feed (not all of them in aggregate).
        """
        super().__init__(**kwds)
        self.camera_name = camera_feed_info.getFeedName()
        self.feed_info = copy.deepcopy(camera_feed_info)
        self.feed_name = self.camera_name + "-" + feed_name
        self.frame_number = -1
        self.frame_slice = None
        self.parameters = feed_parameters

        # Shorten the names..
        cfi = camera_feed_info
        fp = feed_parameters.copy()
        
        # Figure out what to slice, if anything.
        x_start = fp.get("x_start", 1)
        x_end = fp.get("x_end", cfi.getParameter("x_pixels"))
        y_start = fp.get("y_start", 1)
        y_end = fp.get("y_end", cfi.getParameter("y_pixels"))

        # Check if we actually need to slice.
        if (x_start != 1) or (x_end != cfi.getParameter("x_pixels")) or\
           (y_start != 1) or (y_start != cfi.getParameter("y_pixels")):
            self.frame_slice = (slice(y_start-1, y_end),
                                slice(x_start-1, x_end))

        self.x_pixels = x_end - x_start + 1
        self.y_pixels = y_end - y_start + 1
        
        # Check that the feed size is a multiple of 4 in x.
        if not ((self.x_pixels % 4) == 0):
            raise FeedException("x size of " + str(self.x_pixels) + " is not a multiple of 4 in feed " + feed_name)

        # Configure parameters for addition to the CameraFeedInfo structure.
        fp.set("bytes_per_frame", 2 * self.x_pixels * self.y_pixels)
        fp.set("extension", feed_name)
        fp.set("feed_name", self.feed_name)
        fp.set("is_camera", False)
        fp.set("is_master", False)
        if not fp.has("saved"):
            fp.set("saved", True)
        fp.set("x_pixels", self.x_pixels)
        fp.set("x_start", x_start)
        fp.set("y_pixels", self.y_pixels)
        fp.set("y_start", y_start)

        # Add feed information to the CameraFeedInfo structure.
        self.feed_info.addFeedInfo(fp)

    def getFeedInfo(self):
        return self.feed_info

    def reset(self):
        self.frame_number = -1
    
    def sliceFrame(self, new_frame):
        """
        This also selects for only those frames from the correct camera.
        """
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
    def __init__(self, parameters = None, camera_info = None, **kwds):
        """
        parameters - This is just the 'feed' section of the parameters.
        camera_info - This is a dictionary of CameraFeedInfo objects
                      keyed by camera name. We'll use these to create
                      equivalent objects for each feed.
        """
        super().__init__(**kwds)

        self.feeds = []
        if parameters is None:
            return
        
        self.parameters = None

        # Create the feeds.
        self.parameters = parameters
        for feed_name in self.parameters.getAttrs():
            feed_params = self.parameters.get(feed_name)
            camera_name = feed_params.get("source")
            
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

            self.feeds.append(fclass(camera_feed_info = camera_info[camera_name],
                                     feed_name = feed_name,
                                     feed_parameters = feed_params))

    def getFeedsInfo(self):
        feeds_info = {}
        for feed in self.feeds:
            f_info = feed.getFeedInfo()
            feeds_info[f_info.getFeedName()] = f_info
        return feeds_info

    def getParameters(self):
        return self.parameters

#    def haveFeeds(self):
#        return (len(self.feeds) > 0)
    
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

        self.active = False
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
                              validator = {"data" : {"feeds" : [True, dict]},
                                           "resp" : None})

        # Sent each time a feed generates a frame.
        # Note: This needs to match the definition in camera.camera.
        halMessage.addMessage("new frame",
                              check_exists = False,
                              validator = {"data" : {"frame" : [True, frame.Frame]},
                                           "resp" : None})
        
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

        if message.isType("configure2"):
            self.broadcastFeedInfo()

        elif message.isType("get feed information"):
            feed_name = message.getData()["feed_name"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"feed_name" : feed_name,
                                                                      "feed_info" : self.feeds_info[feed_name]}))

        elif message.isType("camera configuration"):
            #
            # We get this message at startup from each of the cameras.
            #
            data = message.getData()
            p = data["parameters"]

            #
            # These are the invariant properties of the camera.
            #
            self.camera_info[data["camera"]] = {"camera" : data["camera"],
                                                "master" : data["master"]}

            self.feeds_info[data["camera"]] = CameraFeedInfo(camera_params = p,
                                                             camera_name = data["camera"],
                                                             is_master = data["master"])

        elif message.isType("new parameters"):
            checkParameters(message.getData()["parameters"])
            
        elif message.isType("updated parameters"):
            self.feed_controller = None
            self.feeds_info = {}
            params = message.getData()["parameters"]

            # Get camera information.
            for attr in params.getAttrs():
                if attr.startswith("camera"):
                    p = params.get(attr)
                    self.feeds_info[attr] = CameraFeedInfo(camera_params = p,
                                                           camera_name = self.camera_info[attr]["camera"],
                                                           is_master = self.camera_info[attr]["master"])

            # Get feed information.
            if params.has("feeds"):
                self.feed_controller = FeedController(parameters = params.get("feeds"),
                                                      camera_info = self.feeds_info)
                self.feeds_info.update(self.feed_controller.getFeedsInfo())

            self.broadcastFeedInfo()

        elif message.isType("start camera"):
            self.active = True

        elif message.isType("start film"):
            if self.feed_controller is not None:
                self.feed_controller.resetFeeds()

        elif message.isType("stop camera"):
            self.active = False
            
        elif message.isType("stop film"):
            if self.feed_controller is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"parameters" : self.feed_controller.getParameters()}))
                self.feed_controller.resetFeeds()

    def processL2Message(self, message):
        if self.feed_controller is not None and self.active:
            frame = message.getData()["frame"]
            feed_frames = self.feed_controller.newFrame(frame)
            for ff in feed_frames:
                self.newMessage.emit(halMessage.HalMessage(source = self,
                                                           m_type = "new frame",
                                                           level = 2,
                                                           data = {"frame" : ff}))

