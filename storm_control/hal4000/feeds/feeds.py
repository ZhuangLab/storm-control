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


class FeedFunctionality(cameraFunctionality.CameraFunctionality):
    """
    Feed functionality in a form that other modules can interact with. These have
    a camera functionality which they are interacting with to create the feed.

    For the most part this just passes through information from the underlying
    camera functionality.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.cam_fn = None
        self.frame_number = 0
        self.frame_slice = None
        self.x_pixels = 0
        self.y_pixels = 0

    def handleEMCCDGain(self, gain):
        self.emcddGain.emit(gain)

    def handleInvalid(self):
        super().setInvalid()
            
    def handleNewFrame(self, new_frame):
        """
        This just does the slicing, if necessary, sub-classes need to convert
        this back into a Frame object & emit the newFrame signal.
        """
        if self.frame_slice is None:
            return new_frame.np_data
        else:
            w = frame.image_x
            h = frame.image_y
            return numpy.reshape(new_frame.np_data, (h,w))[self.frame_slice]

    def handleShutter(self, state):
        self.shutter.emit(state)

    def handleStopped(self):
        self.stopped.emit()

    def handleTemperature(self, t_dict):
        self.temperature.emit(t_dict)
    
    def hasEMCCD(self):
        return self.cam_fn.hasEMCCD()

    def hasPreamp(self):
        return self.cam_fn.hasPreamp()

    def hasShutter(self):
        return self.cam_fn.hasShutter()

    def hasTemperature(self):
        return self.cam_fn.hasTemperature()

    def isCamera(self):
        return False

    def isMaster(self):
        return False

    def reset(self):
        self.frame_number = 0

    def setCameraFunctionality(self, camera_functionality):
        self.cam_fn = camera_functionality

        # Adjust / add parameters from the camera so that the feed will be
        # displayed properly.
        p = self.parameters
        p.add(self.cam_fn.parameters.getp("x_chip").copy())
        p.add(self.cam_fn.parameters.getp("y_chip").copy())

        #
        # The assumption here is that x_start, x_end and x_pixels are all in
        # units of binned pixels. This is also what we assume with the camera.
        #
        # Also, the initial values for x_start and x_end will be 1, if they
        # were not specified in the parameters file.
        #
        for base in ["x_", "y_"]:
            p.set(base + "start", p.get(base +"start") + self.cam_fn.get(base + "start") - 1)

            if (p.get(base + "end") > 1):
                p.set(base + "end", p.get(base + "end") + p.get(base + "start"))
            else:
                p.set(base + "end", self.cam_fn.get(base + "pixels"))

            p.getp(base + "start").setMaximum(self.cam_fn.getParameter(base + "pixels"))
            p.getp(base + "end").setMaximum(self.cam_fn.getParameter(base + "pixels"))

        # Add some of other parameters that we'll need from the camera.
        for pname in ["default_max", "default_min", "flip_horizontal", "flip_vertical", "transpose"]:
            self.parameters.add(self.cam_fn.parameters.getp(pname).copy())

        # And calculate some additional parameters.
        p.set("x_pixels", p.get("x_end") - p.get("x_start") + 1)
        p.set("y_pixels", p.get("y_end") - p.get("y_start") + 1)
        p.set("bytes_per_frame", 2 * p.get("x_pixels") * p.get("y_pixels"))

        # Figure out if we need to slice.
        if (p.get("x_pixels") != self.cam_fn.getParameter("x_pixels")) or\
           (p.get("y_pixels") != self.cam_fn.getParameter("y_pixels")):
            self.frame_slice  = (slice(p.get("y_start") - 1, p.get("y_end")),
                                 slice(p.get("x_start") - 1, p.get("x_end")))
            
        # Connect camera functionality signals. We just pass most of
        # these right through.
        self.cam_fn.emccdGain.connect(self.handleEMCCDGain)
        self.cam_fn.invalid.connect(self.handleInvalid)
        self.cam_fn.newFrame.connect(self.handleNewFrame)
        self.cam_fn.shutter.connect(self.handleShutter)
        self.cam_fn.stopped.connect(self.handleStopped)
        self.cam_fn.temperature.connect(self.handleTemperature)

    def setEMCCDGain(self, gain):
        self.cam_fn.setEMCCDGain(gain)

    def toggleShutter(self):
        self.cam_fn.toggleShutter()


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
        sliced_frame = super().handleNewFrame(new_frame)

        if self.average_frame is None:
            self.average_frame = sliced_frame.astype(numpy.uint32)
        else:
            self.average_frame += sliced_frame
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
        sliced_frame = self.sliceFrame(new_frame)
        if (new_frame.frame_number % self.cycle_length) in self.capture_frames:
            self.newFrame.emit(frame.Frame(sliced_frame,
                                           self.frame_number,
                                           self.x_pixels,
                                           self.y_pixels,
                                           self.camera_name))
            self.frame_number += 1


class FeedFunctionalitySlice(FeedFunctionality):
    """
    The feed functionality for slicing out sub-sets of frames.
    """
    def handleNewFrame(self, new_frame):
        sliced_data = self.sliceFrame(new_frame)
        self.newFrame.emit(frame.Frame(sliced_data,
                                       new_frame.frame_number,
                                       self.x_pixels,
                                       self.y_pixels,
                                       self.camera_name))

        
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

            # Create default feed parameters.
            max_value = 100000
            feed_params = params.StormXMLObject()

            feed_params.add(params.ParameterString(name = "feed_type",
                                                   value = "",
                                                   is_mutable = False))

            feed_params.add(params.ParameterSetBoolean(name = "save",
                                                       value = False))
            
            feed_params.add(params.ParameterString(name = "source",
                                                   value = "",
                                                   is_mutable = False))
            
            feed_params.add(params.ParameterRangeInt(description = "AOI X start.",
                                                     name = "x_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_val))

            feed_params.add(params.ParameterRangeInt(description = "AOI X end.",
                                                     name = "x_end",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_val))

            feed_params.add(params.ParameterRangeInt(description = "AOI Y start.",
                                                     name = "y_start",
                                                     value = 1,
                                                     min_value = 1,
                                                     max_value = max_val))
            
            feed_params.add(params.ParameterRangeInt(description = "AOI Y end.",
                                                     name = "y_end",
                                                     min_value = 1,
                                                     max_value = max_val))
            
            # Figure out what type of feed this is.
            fclass = None
            feed_type = feed_params.get("feed_type")
            if (feed_type == "average"):
                fclass = FeedFunctionalityAverage
                
                feed_params.add(params.ParameterInt(description = "Number of frames to average.",
                                                    name = "frames_to_average"))
                            
            elif (feed_type == "interval"):
                fclass = FeedFunctionalityInterval

                feed_params.add(params.ParameterInt(description = "Interval cycle length.",
                                                    name = "cycle_length"))
                
                feed_params.add(params.ParameterCustom(description = "Frames to capture.",
                                                       name = "capture_frames"))

            elif (feed_type == "slice"):
                fclass = FeedFunctionalitySlice
            else:
                raise FeedException("Unknown feed type '" + feed_type + "' in feed '" + feed_name + "'")

            # Update with values from the parameters file.
            file_params = self.parameters.get(feed_name)
            for attr in file_params.getAttrs():
                feed_params.setv(attr, file_params.get(attr))

            # Replace the values in the parameters that were read from a file
            # with these values.
            self.parameters.addSubSection(feed_name, feed_params, overwrite = True)
            
            self.feeds[feed_name] = fclass(camera_name = feed_name,
                                           parameters = feed_params)

    def getFeed(self, feed_name):
        return self.feeds[feed_name]
        
    def getFeedNames(self):
        return list(self.feeds.keys())

    def getFeeds(self):
        return list(self.feeds.values())
    
    def getParameters(self):
        return self.parameters

    def invalidateFeeds(self):
        for feed in self.feeds:
            feed.setInvalid()
            
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
        self.camera_names = []
        self.feed_controller = None
        self.feed_names = []

        # This is broadcast at startup and when the parameters change
        # to tell other modules what cameras/feeds are available.
        halMessage.addMessage("feed names",
                              validator = {"data" : {"feed names" : [True, list]},
                                           "resp" : None})
                
    def broadcastFeedNames(self):
        """
        Send the 'feeds names' message.

        film.film uses this message to know what all the feeds are.

        display.cameraDisplay uses this message to populate the feed chooser
        combobox.
        """
        self.newMessage.emit(halMessage.HalMessage(source = self,
                                                   m_type = "feed names",
                                                   data = {"feed names" : self.feed_names}))
        
    def processMessage(self, message):

        if message.isType("configure1"):
            for module_name in message.getData()["all_modules"]:
                if module_name.startswith("camera"):
                    self.camera_names.append(module_name)

            if not "camera1" in self.camera_names:
                raise FeedException("There must be at least one camera named camera1.")
            
            self.feed_names = copy.copy(self.camera_names)
            self.broadcastFeedNames()
            
        elif message.isType("get camera functionality"):
            if self.feed_controller is not None:
                feed_name = message.getData()["camera"]
                if feed_name in self.feed_controller.getFeedNames():
                    message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                      data = {"functionality" : self.feed_controller.getFeed(feed_name)}))

        elif message.isType("new parameters"):
            params = message.getData()["parameters"]
            checkParameters(params)
            if self.feed_controller is not None:
                self.feed_controller.invalidateFeeds()
                self.feed_controller = None
            if params.has("feeds"):
                self.feed_controller = FeedController(parameters = params.get("feeds"))
            
        elif message.isType("updated parameters"):
            self.feed_names = copy.copy(self.camera_names)
            if self.feed_controller is not None:
                for feed in self.feed_controller.getFeeds():
                    self.feed_names.append(feed.getCameraName())
                    self.newMessage.emit(halMessage.HalMessage(source = self,
                                                               m_type = "get camera functionality",
                                                               data = {"camera" : feed.getParameter("source")}))
            self.broadcastFeedInfo()

        elif message.isType("start camera"):
            
            # This assumes that there is always at least a "camera1" module.
            if self.feed_controller is not None and (message.getData()["camera"] == "camera1"):
                self.feed_controller.resetFeeds()

        elif message.isType("start film"):
            pass
        
        elif message.isType("stop film"):
            if self.feed_controller is not None:
                message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                                  data = {"parameters" : self.feed_controller.getParameters()}))


#            self.active_camera_count += 1
                
#            if self.feed_controller is not None:

                

#            feed_name = message.getData()["feed_name"]
#            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
#                                                              data = {"feed_name" : feed_name,
#                                                                      "feed_info" : self.feeds_info[feed_name]}))

#        elif message.isType("get feeds information"):
#            self.broadcastFeedInfo()

#        elif message.isType("camera configuration"):
#            #
#            # We get this message at startup from each of the cameras.
#            #
#            camera_name = message.getData()["camera"]
#            camera_config = message.getData()["config"]
#
#            # Sanity check.
#            assert (camera_name == camera_config.getCameraName())
#            
#            #
#            # These are the invariant properties of the camera.
#            #
#            self.camera_info[camera_name] = {"camera" : camera_name,
#                                             "master" : camera_config.isMaster()}
#
#            self.feeds_info[camera_name] = CameraFeedInfo(camera_params = camera_config.getParameters(),
#                                                          camera_name = camera_name,
#                                                          is_master = camera_config.isMaster())

#        elif message.isType("configure2"):
#            self.broadcastFeedInfo()

#        elif message.isType("default colortable"):
#            self.default_colortable = message.getData()["colortable"]

#                                                      camera_info = self.feeds_info)
#                self.feeds_info.update(self.feed_controller.getFeedsInfo())
                
#            # Get camera information.
#            for attr in params.getAttrs():
#                if attr.startswith("camera"):
#                    p = params.get(attr)
#                    self.feeds_info[attr] = CameraFeedInfo(camera_params = p,
#                                                           camera_name = self.camera_info[attr]["camera"],
#                                                           is_master = self.camera_info[attr]["master"])

                

#        if message.isType("camera stopped"):
#            self.active_camera_count -= 1
#            if (self.active_camera_count == 0):
#                self.handleFinished()
            
        
#        #
#        # Add the default color table and 'lock' the info so that we'll get an
#        # error if anything tries to change to them. These are shared as
#        # read-only objects.
#        #
#        for feed_name, feed in self.feeds_info.items():
#            feed.setLocked(False)
#            feed.setParameter("colortable", self.default_colortable)
#            feed.setLocked(True)
#            
#        self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                   m_type = "feeds information",
#                                                   data = {"feeds" : self.feeds_info}))

#    def decUnprocessed(self):
#        self.unprocessed_frames -= 1

#    def handleFinished(self):
#        if (self.unprocessed_frames == 0):
#            self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                       m_type = "feeds stopped"))
#        else:
#            self.finished_timer.start()

#    def incUnprocessed(self):
#        self.unprocessed_frames += 1

#        self.active_camera_count = 0
#        self.camera_info = {}
#        self.default_colortable = None
#        self.feed_controller = None
#        self.feeds_info = {}

#        self.finished_timer = QtCore.QTimer(self)
#        self.unprocessed_frames = 0

#        self.finished_timer.setInterval(10)
#        self.finished_timer.timeout.connect(self.handleFinished)
#        self.finished_timer.setSingleShot(True)        

#        # Sent by other modules to prompt for information about the
#        # current feeds.
#        halMessage.addMessage("get feeds information",
#                              validator = {"data" : None, "resp" : None})
        #
        # This message returns a dictionary keyed by feed name with all
        # relevant parameters for the feed name in another dictionary.
        #
        # e.g. dict["feed_name"]["display_max"] = ?
        #
#        halMessage.addMessage("feeds information",
#                              validator = {"data" : {"feeds" : [True, dict]},
#                                           "resp" : None})

#        # Sent when the feeds stop.
#        halMessage.addMessage("feeds stopped",
#                              validator = {"data" : None, "resp" : None})   

#        # Sent each time a feed generates a frame.
#        # Note: This needs to match the definition in camera.camera.
#        halMessage.addMessage("new frame",
#                              check_exists = False,
#                              validator = {"data" : {"frame" : [True, frame.Frame]},
#                                           "resp" : None})
                
#    def processL2Message(self, message):
#        if self.feed_controller is not None:
#
#            # Don't reprocess our own frames..
#            if(message.getSourceName() == self.module_name):
#                return
#            
#            frame = message.getData()["frame"]
#            feed_frames = self.feed_controller.newFrame(frame)
#            for ff in feed_frames:
#                self.incUnprocessed()
#                self.newMessage.emit(halMessage.HalMessage(source = self,
#                                                           m_type = "new frame",
#                                                           level = 2,
#                                                           data = {"frame" : ff},
#                                                           finalizer = lambda : self.decUnprocessed()))

