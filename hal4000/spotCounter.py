#!/usr/bin/python
#
## @file
#
# Spot counter. This performs real time analysis of the frames from
# camera. It uses a fairly simple object finder. It's purpose is to
# provide the user with a rough idea of the quality of the data
# that they are taking.
#
# Hazen 08/13
#

import sys
from PyQt4 import QtCore, QtGui
import sip
import time

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.halModule as halModule
import sc_library.parameters as params

# Debugging.
import sc_library.hdebug as hdebug

# The module that actually does the analysis.
import qtWidgets.qtSpotCounter as qtSpotCounter

## Counter
#
# Widget for keeping the various count displays up to date.
#
class Counter():

    ## __init__
    #
    # Initialize the counter object. This keeps track of the total
    # number of counts. One label is on the spot graph and the 
    # other label is on the image.
    #
    # @param q_label1 The first QLabel UI element.
    # @param q_label2 The second QLabel UI element.
    #
    def __init__(self, q_label1, q_label2):
        self.counts = 0
        self.q_label1 = q_label1
        self.q_label2 = q_label2
        self.updateCounts(0)

    ## getCounts
    #
    # Returns the total number of counts.
    #
    # @return Returns the total number of counts.
    #
    def getCounts(self):
        return self.counts

    ## reset
    #
    # Reset the counts to zero & update the labels.
    #
    def reset(self):
        self.counts = 0
        self.updateCounts(0)

    ## updateCounts
    #
    # Increments the number of counts by the number of objects
    # found in the most recent frame. Updates the labels accordingly.
    #
    # @param counts The number of objects in the frame that was analyzed.
    #
    def updateCounts(self, counts):
        self.counts += counts
        self.q_label1.setText(str(self.counts))
        self.q_label2.setText(str(self.counts))

## OfflineDriver
#
# Offline analysis driver widget. This is used to analyze saved films
# for the purpose of testing and evaluating the object finder.
#
class OfflineDriver(QtCore.QObject):

    ## __init__
    #
    # Initiailize the offline driver.
    #
    # @param spot_counter The spot counter GUI object.
    # @param data_file The data_file to analyze.
    # @param png_filename The png file to save the resulting image in.
    # @param parent (Optional) PyQt parent of this object.
    #
    def __init__(self, spot_counter, data_file, png_filename, parent = None):
        QtCore.QObject.__init__(self, parent)

        self.begin_time = 0
        self.cur_frame = 0
        self.data_file = data_file
        self.png_filename = png_filename
        self.spot_counter = spot_counter
        
        [self.width, self.height, self.length] = data_file.filmSize()

        self.start_timer = QtCore.QTimer(self)
        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.startAnalysis)
        self.start_timer.setInterval(500)
        self.start_timer.start()

        self.spot_counter.imageProcessed.connect(self.nextImage)

    ## nextImage
    #
    # This is called when the spot counter finishes processing a frame. It
    # loads the next frame from the file and passes it to the spot counter.
    #
    def nextImage(self):
        if (self.cur_frame < self.length):
        #if (self.cur_frame < 5):
            np_data = data_file.loadAFrame(self.cur_frame)
            np_data = numpy.ascontiguousarray(np_data, dtype=numpy.int16)
            self.spot_counter.newFrame(frame.Frame(np_data.ctypes.data,
                                                   self.cur_frame,
                                                   self.width,
                                                   self.height,
                                                   "camera1",
                                                   True),
                                       True)
            self.cur_frame += 1
            if ((self.cur_frame % 100) == 0):
                print "Frame:", self.cur_frame, "(", self.length, ")"
        else:
            elapsed_time = time.time() - self.begin_time
            self.spot_counter.stopFilm(False)
            print "Finished Analysis"
            print self.length, "Frames analyzed in", elapsed_time, "seconds (", float(self.length)/elapsed_time, ") FPS."

    ## startAnalysis
    #
    # This starts the analysis. It is called after a 500 millisecond
    # delay to give PyQt a chance to get everything setup.
    #
    def startAnalysis(self):
        self.spot_counter.startFilm(self.png_filename, False)
        self.begin_time = time.time()
        self.nextImage()

## QSpotGraph
#
# Spot Count Graphing Widget.
#
class QSpotGraph(QtGui.QWidget):

    ## __init__
    #
    # Create a spot graph object.
    #
    # @param x_size The x size (in pixels) of this widget.
    # @param y_size The y size (in pixels) of this widget.
    # @param y_min The graph's minimum value.
    # @param y_max The graph's maximum value.
    # @param parent (Optional) The PyQt parent of this object.
    #
    def __init__(self, x_size, y_size, y_min, y_max, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.range = y_max - y_min
        self.x_size = x_size
        self.y_size = y_size
        self.y_min = float(y_min)
        self.y_max = float(y_max)

        self.colors = [False]
        self.points_per_cycle = len(self.colors)
        self.x_points = 100

        self.x_scale = float(self.x_size)/float(self.x_points)
        self.y_scale = float(y_size)/5.0
        self.cycle = 0
        if self.points_per_cycle > 1:
            self.cycle = self.x_scale * float(self.points_per_cycle)

        self.data = []
        for i in range(self.x_points):
            self.data.append(0)

    ## changeYRange
    #
    # @param y_min (Optional) The new y minimum of the graph.
    # @param y_max (Optional) The new y maximum of the graph.
    #
    def changeYRange(self, y_min = None, y_max = None):
        if y_min:
            self.y_min = y_min
        if y_max:
            self.y_max = y_max
        self.range = self.y_max - self.y_min

    ## newColors
    #
    # @param colors The colors to use for the points in the graph. This is based on the values specified in the shutter file.
    # @param total_points The total number of points in x.
    #
    def newColors(self, colors, total_points):
        self.colors = colors
        self.points_per_cycle = len(colors)
        self.x_points = total_points

        self.x_scale = float(self.x_size)/float(self.x_points)
        self.cycle = 0
        if self.points_per_cycle > 1:
            self.cycle = self.x_scale * float(self.points_per_cycle)

        self.data = []
        for i in range(self.x_points):
            self.data.append(0)

        self.update()

    ## paintEvent
    #
    # Redraw the graph.
    #
    # @param event A PyQt event object.
    #
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # Background
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

        # Draw lines in y to denote the start of each cycle, but only
        # if we have at least 2 points per cycle.
        #
        # Draw grid lines in x.
        if self.cycle:
            painter.setPen(QtGui.QColor(200, 200, 200))
            x = 0.0
            while x < float(self.x_size):
                ix = int(x)
                painter.drawLine(ix, 0, ix, self.y_size)
                x += self.cycle

            y = 0.0
            while y < float(self.y_size):
                iy = int(y)
                painter.drawLine(0, iy, self.x_size, iy)
                y += self.y_scale

        if (len(self.data)>0):
            # Lines
            painter.setPen(QtGui.QColor(0, 0, 0))
            x1 = int(self.x_scale * float(0))
            y1 = self.y_size - int((self.data[0] - self.y_min)/self.range * float(self.y_size))
            for i in range(len(self.data)-1):
                x2 = int(self.x_scale * float(i+1))
                y2 = self.y_size - int((self.data[i+1] - self.y_min)/self.range * float(self.y_size))
                painter.drawLine(x1, y1, x2, y2)
                x1 = x2
                y1 = y2

            # Points
            for i in range(len(self.data)):
                color = self.colors[i % self.points_per_cycle]
                qtcolor = 0
                if color:
                    qtcolor = QtGui.QColor(color[0], color[1], color[2])
                else:
                    qtcolor = QtGui.QColor(255, 255, 255)
                painter.setPen(QtGui.QColor(0, 0, 0))
#                painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0),0))
                painter.setBrush(qtcolor)

                x = int(self.x_scale * float(i))
                y = self.y_size - int((self.data[i] - self.y_min)/self.range * float(self.y_size))
                if y < 0:
                    y = 0
                if y > self.y_size:
                    y = self.y_size
                painter.drawEllipse(x - 2, y - 2, 4, 4)

    ## updateGraph
    #
    # Updates the graph given a frame number and the number of spots in the frame.
    #
    # @param frame_index The frame number.
    # @param spots The number of spots in the frame.
    #
    def updateGraph(self, frame_index, spots):
        self.data[frame_index % self.x_points] = spots
        self.update()

## QImageGraph
#
# STORM image display widget.
#
class QImageGraph(QtGui.QWidget):

    ## __init__
    #
    # Create a STORM image display widget.
    #
    # @param x_size The x size of the widget in pixels.
    # @param y_size The y size of the widget in pixels.
    # @param parent The PyQt parent of this widget.
    #
    def __init__(self, x_size, y_size, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.buffer = QtGui.QPixmap(x_size, y_size)
        self.flip_horizontal = False
        self.flip_vertical = False
        self.transpose = False
        self.x_end = x_size
        self.y_end = y_size
        self.x_size = x_size
        self.y_size = y_size

        self.colors = [False]
        self.points_per_cycle = len(self.colors)
        self.scale_bar_len = 1
        self.p_scale = 1.0
        self.x_scale = 1.0
        self.y_scale = 1.0

    ## blank
    #
    # Resets the image to black.
    #
    def blank(self):
        painter = QtGui.QPainter(self.buffer)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)
        self.update()

    ## newColors
    #
    # Set new colors
    #
    # @param colors The colors to draw the pixels. This the same as for the spot graph.
    #
    def newColors(self, colors):
        self.colors = colors
        self.points_per_cycle = len(colors)

    ## newParameters
    #
    # Set new parameters.
    #
    # @param camera_params A parameters object.
    # @param scale_bar_len The length of the scale bar (in pixels).
    #
    def newParameters(self, camera_params, scale_bar_len):
        self.flip_horizontal = camera_params.flip_horizontal
        self.flip_vertical = camera_params.flip_vertical
        self.scale_bar_len = int(round(scale_bar_len))
        self.transpose = camera_params.transpose

        self.x_end = self.x_size
        self.y_end = self.y_size

        self.x_scale = float(self.x_size)/float(camera_params.x_pixels / camera_params.x_bin)
        self.y_scale = float(self.y_size)/float(camera_params.y_pixels / camera_params.y_bin)

        if (self.x_scale > self.y_scale):
            self.p_scale = self.y_scale
            self.x_end = int(float(self.x_size) * self.y_scale/self.x_scale)
        else:
            self.p_scale = self.x_scale
            self.y_end = int(float(self.y_size) * self.x_scale/self.y_scale)

        self.blank()

    ## paintEvent
    #
    # Redraw the image.
    # 
    # @param event A PyQt event object.
    #
    def paintEvent(self, event):
        # Draw the scale bar.
        painter = QtGui.QPainter(self.buffer)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(5, 5, 5 + self.scale_bar_len, 5)

        # Mirror as necessary.
        #self.image = self.image.mirrored(self.flip_horizontal, self.flip_vertical)
            
        # Transfer to display.
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.buffer)

    ## saveImage
    #
    # Saves the image in a file.
    #
    # @param filename The name of the file to save the image in.
    #
    def saveImage(self, filename):
        self.buffer.save(filename, "PNG", -1)

    ## updateImage
    #
    # Add the objects found in a frame to the image.
    #
    # @param index The frame number of the image.
    # @param x_locs The x locations of the objects.
    # @param y_locs The y locations of the objects.
    # @param spots The number of objects.
    #
    def updateImage(self, index, x_locs, y_locs, spots):
        painter = QtGui.QPainter(self.buffer)
        color = self.colors[index % self.points_per_cycle]
        if color:
            qtcolor = QtGui.QColor(color[0], color[1], color[2], 5)
            painter.setPen(qtcolor)
            for i in range(spots):
                ix = int(self.p_scale * x_locs[i])
                iy = int(self.p_scale * y_locs[i])
                if self.flip_horizontal:
                    ix = self.x_end - ix
                if self.flip_vertical:
                    iy = self.y_end - iy
                if self.transpose:
                    [ix, iy] = [iy, ix]
                #print ix, x_locs[i], iy, y_locs[i]
                painter.drawPoint(ix, iy)
            self.update()

## SpotCounter
#
# Spot Counter Dialog Box
#
class SpotCounter(QtGui.QDialog, halModule.HalModule):
    imageProcessed = QtCore.pyqtSignal()

    ## __init__
    #
    # Create the spot counter dialog box.
    #
    # @param parameters The initial parameters.
    # @param parent The PyQt parent of this dialog box.
    #
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QDialog.__init__(self, parent)
        halModule.HalModule.__init__(self)

        self.counters = [False, False]
        self.filming = 0
        self.filenames = [False, False]
        self.frame_interval = parameters.get("interval", 1)
        self.image_graphs = [False, False]
        self.parameters = parameters
        self.spot_counter = False
        self.spot_graphs = [False, False]

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup.
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Spot Counter")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Setup Counter objects.
        if (self.number_cameras == 1):
            self.counters = [Counter(self.ui.countsLabel1, self.ui.countsLabel2)]
        else:
            self.counters = [Counter(self.ui.countsLabel1, self.ui.countsLabel2),
                             Counter(self.ui.countsLabel3, self.ui.countsLabel4)]

        # Setup spot counter.
        self.spot_counter = qtSpotCounter.QObjectCounter(parameters)
        self.spot_counter.imageProcessed.connect(self.updateCounts)

        # Setup spot counts graph(s).
        if (self.number_cameras == 1):
            parents = [self.ui.graphFrame]
        else:
            parents = [self.ui.graphFrame, self.ui.graphFrame2]

        for i in range(self.number_cameras):
            graph_w = parents[i].width() - 4
            graph_h = parents[i].height() - 4
            self.spot_graphs[i] = QSpotGraph(graph_w,
                                             graph_h,
                                             parameters.get("min_spots"),
                                             parameters.get("max_spots"),
                                             parent = parents[i])
            self.spot_graphs[i].setGeometry(2, 2, graph_w, graph_h)
            self.spot_graphs[i].show()

        # Setup STORM image(s).
        if (self.number_cameras == 1):
            parents = [self.ui.imageFrame]
        else:
            parents = [self.ui.imageFrame, self.ui.imageFrame2]

        for i in range(self.number_cameras):
            image_w = parents[i].width() - 4
            image_h = parents[i].height() - 4

            self.image_graphs[i] = QImageGraph(image_w, image_h, parent = parents[i])
            self.image_graphs[i].setGeometry(2, 2, image_w, image_h)
            self.image_graphs[i].blank()
            self.image_graphs[i].show()

        # Connect signals.
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)
        self.ui.maxSpinBox.valueChanged.connect(self.handleMaxChange)
        self.ui.minSpinBox.valueChanged.connect(self.handleMinChange)

        # Set modeless.
        self.setModal(False)

        
    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        self.spot_counter.shutDown()

    ## closeEvent
    #
    # Handle close events. The event is ignored and the dialog box is simply
    # hidden if the dialog box has a parent.
    #
    # @param event A QEvent object.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:

            if (signal[1] == "newColors"):
                signal[2].connect(self.newColors)

    ## getCounts
    #
    # Returns the number of objects detected. If the movie is requested
    # by TCP/IP this number is passed back to the calling program.
    #
    #@hdebug.debug
    #def getCounts(self):
    #    return self.counters[0].getCounts()

    ## handleMaxChange
    #
    # Handles changing the maximum of the spot graph.
    #
    # @param new_max The new maximum.
    #
    @hdebug.debug
    def handleMaxChange(self, new_max):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_max = new_max)
        self.ui.minSpinBox.setMaximum(new_max - 10)
        self.parameters.set("max_spots", new_max)

    ## handleMinChange
    #
    # Handles changing the minimum of the spot graph.
    #
    # @param new_min The new minimum.
    #
    @hdebug.debug
    def handleMinChange(self, new_min):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_min = new_min)
        self.ui.maxSpinBox.setMinimum(new_min + 10)
        self.parameters.set("min_spots", new_min)

    ## handleOk
    #
    # Handles the close button, hides the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleQuit
    #
    # Handles the quit button, closes the dialog box.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## newColors
    #
    # Called when the spot colors need to be changed, as for example
    # when a new shutters file is selected.
    #
    # @param colors A colors array.
    #
    def newColors(self, colors):

        # If colors is an empty array then we use the default color (white).
        if (len(colors) == 0):
            colors = [[255, 255, 255]]
        points_per_cycle = len(colors)
        total_points = points_per_cycle
        while total_points < 100:
            total_points += points_per_cycle

        for i in range(self.number_cameras):
            self.spot_graphs[i].newColors(colors, total_points)
            self.image_graphs[i].newColors(colors)

    ## newFrame
    #
    # Called when there is a new frame from the camera.
    #
    # @param frame A frame object.
    # @param filming True/False if we are currently filming.
    #
    def newFrame(self, frame, filming):
        if self.spot_counter and ((frame.number % self.frame_interval) == 0):
            self.spot_counter.newImageToCount(frame)

    ## newParameters
    #
    # Called when the parameters are changed. Updates the spot graphs
    # and image display with the new parameters.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters

        self.frame_interval = parameters.get("interval", 1)
        self.spot_counter.newParameters(parameters)

        # Update counters, count graph(s) & STORM image(s).
        for i in range(self.number_cameras):
            self.counters[i].reset()

            camera_params = parameters.get("camera" + str(i+1), parameters)
            #if hasattr(parameters, "camera" + str(i+1)):
            #    camera_params = getattr(parameters, "camera" + str(i+1))
            scale_bar_len = (parameters.get("scale_bar_len") / parameters.get("nm_per_pixel")) * \
                float(self.image_graphs[i].width()) / float(camera_params.get("x_pixels") * camera_params.get("x_bin"))
            self.image_graphs[i].newParameters(camera_params, scale_bar_len)

        # UI update.
        self.ui.maxSpinBox.setValue(parameters.get("max_spots"))
        self.ui.minSpinBox.setValue(parameters.get("min_spots"))

    ## updateCounts
    #
    # Called when the objects in a frame have been localized.
    #
    # @param which_camera This is one of "camera1" or "camera2"
    # @param frame_number The frame number of the frame that was analyzed.
    # @param x_locs The x locations of the objects that were found.
    # @param y_locs The y locations of the objects that were found.
    # @param spots The total number of spots that were found.
    #
    def updateCounts(self, which_camera, frame_number, x_locs, y_locs, spots):
        if (which_camera == "camera1"):
            self.spot_graphs[0].updateGraph(frame_number, spots)
            if self.filming:
                self.counters[0].updateCounts(spots)
                self.image_graphs[0].updateImage(frame_number, x_locs, y_locs, spots)
        elif (which_camera == "camera2"):
            self.spot_graphs[1].updateGraph(frame_number, spots)
            if self.filming:
                self.counters[1].updateCounts(spots)
                self.image_graphs[1].updateImage(frame_number, x_locs, y_locs, spots)
        else:
            print "spotCounter.update Unknown camera:", which_camera
        self.imageProcessed.emit()

    ## startCounter
    #
    # Called at the start of filming to reset the spot graphs and the
    # images. If name is not False then this is assumed to be root
    # filename to save the spot counter images in when filming is finished.
    #
    # @param film_name The name of the film without any extensions, or False if the film is not being saved.
    # @param run_shutters True/False the shutters should be run or not.
    #
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        for i in range(self.number_cameras):
            self.counters[i].reset()
            self.image_graphs[i].blank()
        self.filming = True
        self.filenames = [False, False]
        if film_name:
            if (self.number_cameras == 1):
                self.filenames[0] = film_name + ".png"
            else:
                self.filenames[0] = film_name + "_cam1.png"
                self.filenames[1] = film_name + "_cam2.png"

    ## stopFilm
    #
    # Called at the end of filming.
    #
    # @param film_writer The film writer object.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        self.filming = False
        if self.filenames[0]:
            for i in range(self.number_cameras):
                self.image_graphs[i].saveImage(self.filenames[i])
        if film_writer:
            film_writer.setSpotCounts(self.counters[0].getCounts())


## SingleSpotCounter
#
# Spot counter dialog box for a single camera.
#
class SingleSpotCounter(SpotCounter):

    ## __init__
    #
    # @param hardware A hardware parameters object.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this dialog box.
    #
    def __init__(self, hardware, parameters, parent = None):
        self.number_cameras = 1
        
        import qtdesigner.spotcounter_ui as spotCounterUi
        self.ui = spotCounterUi.Ui_Dialog()
        
        SpotCounter.__init__(self, parameters, parent)

## DualSpotCounter
#
# Spot counter dialog box for a two camera setup.
#
class DualSpotCounter(SpotCounter):

    ## __init__
    #
    # @param hardware A hardware parameters object.
    # @param parameters A parameters object.
    # @param parent (Optional) The PyQt parent of this dialog box.
    #
    def __init__(self, hardware, parameters, parent = None):
        self.number_cameras = 2
        
        import qtdesigner.dualspotcounter_ui as spotCounterUi
        self.ui = spotCounterUi.Ui_Dialog()
        
        SpotCounter.__init__(self, parameters, parent)


# Testing.
#
#   Load a movie file, analyze it & save the result.
#
if __name__ == "__main__":

    import numpy

    import camera.frame as frame

    # This file is available in the ZhuangLab storm-analysis project on github.
    import sa_library.datareader as datareader

    if (len(sys.argv) != 4):
        print "usage: <settings> <movie_in> <png_out>"
        exit()

    # Open movie & get size.
    data_file = datareader.inferReader(sys.argv[2])
    [width, height, length] = data_file.filmSize()

    # Start spotCounter as a stand-alone application.
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters(sys.argv[1], is_HAL = True)
    parameters.set("setup_name", "offline")
    
    parameters.set("x_pixels", width)
    parameters.set("y_pixels", height)
    parameters.set("x_bin", 1)
    parameters.set("y_bin", 1)

    spotCounter = SingleSpotCounter(None, parameters)
    #spotCounter.newParameters(parameters, [[255,255,255]])
    spotCounter.newParameters(parameters)

    # Start driver.
    driver = OfflineDriver(spotCounter, data_file, sys.argv[3])

    # Show window & start application.
    spotCounter.show()
    app.exec_()


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

