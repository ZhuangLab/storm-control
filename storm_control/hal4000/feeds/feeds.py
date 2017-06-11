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

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.frame as frame
import storm_control.hal4000.camera.cameraFunctionality as cameraFunctionality
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

    # Check the feed parameters. For now all we are doing is verifying that
    # the feed ROI area is a multiple of 4.
    #
    # FIXME: There are many possible problems here. Some cameras don't use
    #        'x_pixels' and 'y_pixels' so these only get set to meaningful
    #        values when the camera's newParameters method is called, which
    #        may or may not happen before this function gets called.
    #
    feed_parameters = parameters.get("feeds")
    for feed_name in feed_parameters.getAttrs():
        fp = feed_parameters.get(feed_name)
        cp = parameters.get(fp.get("source"))

        x_start = fp.get("x_start", 1)
        x_end = fp.get("x_end", cp.get("x_pixels"))
        x_pixels = x_end - x_start + 1

        y_start = fp.get("y_start", 1)
        y_end = fp.get("y_end", cp.get("y_pixels"))
        y_pixels = y_end - y_start + 1
        
        # Check that the feed size is a multiple of 4 in x.
        if not ((x_pixels % 4) == 0):
            raise FeedException("The x size of the feed ROI must be a multiple of 4 in " + feed_name)


class FeedException(halExceptions.HalException):
    pass


class FeedFunctionality(cameraFunctionality.CameraFunctionality):
    """
    Feed functionality in a form that other modules can interact with. These have
    a camera functionality which they are interacting with to create the feed.

    For the most part this just passes through information from the underlying
    camera functionality.

    Some functionality is explicitly blocked so we get an error if we accidentally
    try and use this exactly like a camera functionality.
    """
    def __init__(self, feed_name = None, **kwds):
        super().__init__(**kwds)
        self.cam_fn = None
        self.feed_name = feed_name
        self.frame_number = 0
        self.frame_slice = None
        self.number_connections = 0
        self.x_pixels = 0
        self.y_pixels = 0

    def connectCameraFunctionality(self):
        """
        Connect the feed to it's camera functionality
        """
        # sanity check.
        assert(self.number_connections == 0)
        self.number_connections += 1
        
        self.cam_fn.newFrame.connect(self.handleNewFrame)
        self.cam_fn.started.connect(self.handleStarted)
        self.cam_fn.stopped.connect(self.handleStopped)

    def disconnectCameraFunctionality(self):
        """
        Disconnect the feed from it's camera functionality.
        """
        # sanity check.
        assert(self.number_connections == 1)
        self.number_connections += 1
        
        if self.cam_fn is not None:
            self.cam_fn.newFrame.disconnect(self.handleNewFrame)
            self.cam_fn.started.disconnect(self.handleStarted)
            self.cam_fn.stopped.disconnect(self.handleStopped)

    def getCameraFunctionality(self):
        """
        Return the camera functionality this feed is using.
        """
        return self.cam_fn

    def getFeedName(self):
        """
        Return the name of the feed (as specified in the XML file).
        """
        return self.feed_name

    def handleNewFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        self.newFrame.emit(frame.Frame(sliced_data,
                                       new_frame.frame_number,
                                       self.x_pixels,
                                       self.y_pixels,
                                       self.camera_name))

    def handleStarted(self):
        self.started.emit()

    def handleStopped(self):
        self.stopped.emit()

    def hasEMCCD(self):
        assert False
        
    def hasPreamp(self):
        assert False

    def hasShutter(self):
        assert False

    def hasTemperature(self):
        assert False

    def haveCameraFunctionality(self):
        return (not self.cam_fn is None)
        
    def isCamera(self):
        return False

    def isMaster(self):
        return False

    def reset(self):
        self.frame_number = 0

    def setCameraFunctionality(self, camera_functionality):
        self.cam_fn = camera_functionality

        #
        # The assumption here is that x_start, x_end and x_pixels are all in
        # units of binned pixels. This is also what we assume with the camera.
        #
        # Also, the initial values for x_start and x_end will be 1, if they
        # were not specified in the parameters file.
        #
        p = self.parameters

        # Figure out if we need to slice.
        if (p.get("x_end") == 1):
            p.setv("x_end", self.cam_fn.getParameter("x_end"))
        if (p.get("y_end") == 1):
            p.setv("y_end", self.cam_fn.getParameter("y_end"))

        p.set("x_pixels", p.get("x_end") - p.get("x_start") + 1)
        p.set("y_pixels", p.get("y_end") - p.get("y_start") + 1)
        p.set("bytes_per_frame", 2 * p.get("x_pixels") * p.get("y_pixels"))

        self.x_pixels = p.get("x_pixels")
        self.y_pixels = p.get("y_pixels")

        if (p.get("x_pixels") != self.cam_fn.getParameter("x_pixels")) or\
           (p.get("y_pixels") != self.cam_fn.getParameter("y_pixels")):
            self.frame_slice  = (slice(p.get("y_start") - 1, p.get("y_end")),
                                 slice(p.get("x_start") - 1, p.get("x_end")))

        # Adjust / add parameters from the camera so that the feed will be
        # displayed properly.
        p.add(self.cam_fn.parameters.getp("x_chip").copy())
        p.add(self.cam_fn.parameters.getp("y_chip").copy())

        p.setv("x_start", self.cam_fn.getParameter("x_start") + p.get("x_start") - 1)
        p.setv("x_end", p.get("x_start") + p.get("x_pixels") - 1)
        
        p.setv("y_start", self.cam_fn.getParameter("y_start") + p.get("y_start") - 1)
        p.setv("y_end", p.get("y_start") + p.get("y_pixels") - 1)

        # Set the maximums so that the editor will work better.
        p.getp("x_start").setMaximum(self.cam_fn.getParameter("x_pixels"))
        p.getp("x_end").setMaximum(self.cam_fn.getParameter("x_end"))
        p.getp("y_start").setMaximum(self.cam_fn.getParameter("y_pixels"))
        p.getp("y_end").setMaximum(self.cam_fn.getParameter("y_end"))

        # Add some of other parameters that we need to behave like a camera functionality. These
        # are just duplicates from the corresponding camera.
        for pname in ["default_max", "default_min", "flip_horizontal", "flip_vertical",
                      "fps", "max_intensity", "transpose", "x_bin", "y_bin"]:
            p.add(self.cam_fn.parameters.getp(pname).copy())

        # Connect camera functionality signals. We just pass most of
        # these through.
        self.connectCameraFunctionality()

    def sliceFrame(self, new_frame):
        """
        Slices out a part of the frame based on self.frame_slice.
        """
        if self.frame_slice is None:
            return new_frame.np_data
        else:
            w = new_frame.image_x
            h = new_frame.image_y
            sliced_frame = numpy.reshape(new_frame.np_data, (h,w))[self.frame_slice]
            return numpy.ascontiguousarray(sliced_frame)

    def toggleShutter(self):
        assert False


class FeedFunctionalityAverage(FeedFunctionality):
    """
    The feed functionality for averaging frames together.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.average_frame = None
        self.counts = 0
        self.frames_to_average = self.parameters.get("frames_to_average")

    def handleNewFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)

        if self.average_frame is None:
            self.average_frame = sliced_data.astype(numpy.uint32)
        else:
            self.average_frame += sliced_data
        self.counts += 1

        if (self.counts == self.frames_to_average):
            average_frame = self.average_frame/self.frames_to_average
            self.newFrame.emit(frame.Frame(average_frame.astype(numpy.uint16),
                                           self.frame_number,
                                           self.x_pixels,
                                           self.y_pixels,
                                           self.camera_name))
            self.average_frame = None
            self.counts = 0
            self.frame_number += 1

    def reset(self):
        super().reset()
        self.average_frame = None
        self.counts = 0
        
    
class FeedFunctionalityInterval(FeedFunctionality):
    """
    The feed functionality for picking out a sub-set of the frames.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        temp = self.parameters.get("capture_frames")
        self.capture_frames = list(map(int, temp.split(",")))
        self.cycle_length = self.parameters.get("cycle_length")

    def handleNewFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        
        if (new_frame.frame_number % self.cycle_length) in self.capture_frames:
            self.newFrame.emit(frame.Frame(sliced_data,
                                           self.frame_number,
                                           self.x_pixels,
                                           self.y_pixels,
                                           self.camera_name))
            self.frame_number += 1


class FeedFunctionalitySlice(FeedFunctionality):
    """
    The feed functionality for slicing out sub-sets of frames.
    """
    pass

        
class FeedController(object):
    """
    Feed controller.
    """
    def __init__(self, parameters = None, **kwds):
        """
        parameters - This is just the 'feed' section of the parameters.
        """
        super().__init__(**kwds)

        self.feeds = {}
        if parameters is None:
            return

        # Create the feeds.
        self.parameters = parameters
        for feed_name in self.parameters.getAttrs():
            file_params = self.parameters.get(feed_name)
            
            # Create default feed parameters.
            max_value = 100000
            feed_params = params.StormXMLObject()

            # Feeds are saved with their name as the extension.
            feed_params.add(params.ParameterString(name = "extension",
                                                   value = feed_name,
                                                   is_mutable = True))
            
            feed_params.add(params.ParameterString(name = "feed_type",
                                                   value = "",
                                                   is_mutable = False))

            feed_params.add(params.ParameterSetBoolean(name = "saved",
                                                       value = False))

            # This is the camera that drives the feed.
            feed_params.add(params.ParameterString(name = "source",
                                                   value = "",
                                                   is_mutable = False))
            
            feed_params.add(params.ParameterRangeInt(description = "AOI X start.",
                                                     name = "x_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_value))

            feed_params.add(params.ParameterRangeInt(description = "AOI X end.",
                                                     name = "x_end",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_value))

            feed_params.add(params.ParameterRangeInt(description = "AOI Y start.",
                                                     name = "y_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_value))
            
            feed_params.add(params.ParameterRangeInt(description = "AOI Y end.",
                                                     name = "y_end",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_value))

            # Figure out what type of feed this is.
            fclass = None
            feed_type = file_params.get("feed_type")
            if (feed_type == "average"):
                fclass = FeedFunctionalityAverage
                
                feed_params.add(params.ParameterInt(description = "Number of frames to average.",
                                                    name = "frames_to_average",
                                                    value = 1))
                            
            elif (feed_type == "interval"):
                fclass = FeedFunctionalityInterval

                feed_params.add(params.ParameterInt(description = "Interval cycle length.",
                                                    name = "cycle_length",
                                                    value = 1))
                
                feed_params.add(params.ParameterCustom(description = "Frames to capture.",
                                                       name = "capture_frames",
                                                       value = "1"))

            elif (feed_type == "slice"):
                fclass = FeedFunctionalitySlice
            else:
                raise FeedException("Unknown feed type '" + feed_type + "' in feed '" + feed_name + "'")

            # Update with values from the parameters file.
            for attr in file_params.getAttrs():
                feed_params.setv(attr, file_params.get(attr))

            # Replace the values in the parameters that were read from a file with these values.
            self.parameters.addSubSection(feed_name, feed_params, overwrite = True)

            camera_name = feed_params.get("source") + "." + feed_name
            self.feeds[camera_name] = fclass(feed_name = feed_name,
                                             camera_name = camera_name,
                                             parameters = feed_params)

    def allFeedsFunctional(self):
        for feed in self.getFeeds():
            if not feed.haveCameraFunctionality():
                return False
        return True

    def disconnectFeeds(self):
        """
        Disconnect the feeds from their camera functionalities.
        """
        for feed in self.getFeeds():
            feed.disconnectCameraFunctionality()

    def getFeed(self, feed_name):
        return self.feeds[feed_name]
        
    def getFeedNames(self):
        return list(self.feeds.keys())

    def getFeeds(self):
        return list(self.feeds.values())
    
    def getParameters(self):
        return self.parameters

    def resetFeeds(self):
        for feed in self.getFeeds():
            feed.reset()
            

class Feeds(halModule.HalModule):
    """
    Feeds controller.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.camera_names = []
        self.feed_controller = None
        self.feed_names = []
        
        # This message comes from the display.display when it creates a new
        # viewer.
        halMessage.addMessage("get feed names",
                              validator = {"data" : {"extra data" : [False, str]},
                                           "resp" : {"feed names" : [True, list]}})
        
    def broadcastCurrentFeeds(self):
        """
        Send a 'configuration' message with the current feed names.

        film.film uses this message to know what all the feeds are.

        display.cameraDisplay uses this message to populate the feed chooser
        combobox.
        """
        props = {"feed names" : self.feed_names}
        self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                               data = {"properties" : props}))

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            feed = self.feed_controller.getFeed(message.getData()["extra data"])
            feed.setCameraFunctionality(response.getData()["functionality"])

        #
        # If we have camera functionality for all the feeds then it is safe to
        # broadcast the new feed information.
        #
        if self.feed_controller.allFeedsFunctional():
            self.broadcastCurrentFeeds()

            # And we are done with the parameter change.
            self.sendMessage(halMessage.HalMessage(m_type = "parameters changed"))

    def processMessage(self, message):

        if message.isType("configure1"):
            for module_name in message.getData()["all_modules"]:
                if module_name.startswith("camera"):
                    self.camera_names.append(module_name)

            # Let the settings.settings module know that it needs
            # to wait for us during a parameter change.
            self.sendMessage(halMessage.HalMessage(m_type = "wait for",
                                                   data = {"module names" : ["settings"]}))
            
            self.feed_names = copy.copy(self.camera_names)
            self.broadcastCurrentFeeds()

        elif message.isType("get functionality"):
            if self.feed_controller is not None:
                feed_name = message.getData()["name"]
                if feed_name in self.feed_controller.getFeedNames():
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.feed_controller.getFeed(feed_name)}))

        elif message.isType("get feed names"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"feed names" : self.feed_names}))
            
        elif message.isType("new parameters"):
            params = message.getData()["parameters"]
            checkParameters(params)
            if self.feed_controller is not None:
                self.feed_controller.disconnectFeeds()
                self.feed_controller = None
            if params.has("feeds"):
                self.feed_controller = FeedController(parameters = params.get("feeds"))
            
        elif message.isType("updated parameters"):
            self.feed_names = copy.copy(self.camera_names)
            if self.feed_controller is not None:
                for feed in self.feed_controller.getFeeds():
                    self.feed_names.append(feed.getCameraName())
                    self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                           data = {"name" : feed.getParameter("source"),
                                                                   "extra data" : feed.getCameraName()}))
            else:
                self.broadcastCurrentFeeds()
                self.sendMessage(halMessage.HalMessage(m_type = "parameters changed"))

        elif message.isType("start film"):
            if self.feed_controller is not None:
                self.feed_controller.resetFeeds()
        
        elif message.isType("stop film"):
            if self.feed_controller is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"parameters" : self.feed_controller.getParameters()}))

