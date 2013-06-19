#!/usr/bin/python
#
# Spot counter.
#
# Hazen 12/12
#

import sys
from PyQt4 import QtCore, QtGui
import sip

import qtWidgets.qtAppIcon as qtAppIcon

import halLib.parameters as params

# Debugging.
import halLib.hdebug as hdebug

# The module that actually does the analysis.
import qtWidgets.qtSpotCounter as qtSpotCounter


#
# Widget for keeping the various count display up to date.
#
class Counter():
    def __init__(self, q_label1, q_label2):
        self.counts = 0
        self.q_label1 = q_label1
        self.q_label2 = q_label2
        self.updateCounts(0)

    def getCounts(self):
        return self.counts

    def reset(self):
        self.counts = 0
        self.updateCounts(0)

    def updateCounts(self, counts):
        self.counts += counts
        self.q_label1.setText(str(self.counts))
        self.q_label2.setText(str(self.counts))

#
# Spot Count Graphing Widget.
#
class QSpotGraph(QtGui.QWidget):
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

    def changeYRange(self, y_min = None, y_max = None):
        if y_min:
            self.y_min = y_min
        if y_max:
            self.y_max = y_max
        self.range = self.y_max - self.y_min

    def newParameters(self, colors, total_points):
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

    def paintEvent(self, Event):
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
                    qtcolor = QtGui.QColor(0, 0, 0)
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

    def updateGraph(self, frame_index, spots):
        self.data[frame_index % self.x_points] = spots
        self.update()

#
# STORM image display widget.
#
class QImageGraph(QtGui.QWidget):
    def __init__(self, x_size, y_size, flip_horizontal, flip_vertical, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.buffer = QtGui.QPixmap(x_size, y_size)
        self.flip_horizontal = flip_horizontal
        self.flip_vertical = flip_vertical
        self.x_size = x_size
        self.y_size = y_size

        self.colors = [False]
        self.points_per_cycle = len(self.colors)
        self.scale_bar_len = 1
        self.x_scale = 1.0
        self.y_scale = 1.0

    def blank(self):
        painter = QtGui.QPainter(self.buffer)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)
        self.update()

    def newParameters(self, colors, flip_horizontal, flip_vertical, scale_bar_len, x_range, y_range):
        self.colors = colors
        self.flip_horizontal = flip_horizontal
        self.flip_vertical = flip_vertical
        self.points_per_cycle = len(colors)
        self.scale_bar_len = int(round(scale_bar_len))
        self.x_scale = float(self.x_size)/float(x_range)
        self.y_scale = float(self.y_size)/float(y_range)
        self.blank()

    def paintEvent(self, Event):
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

    def saveImage(self, filename):
        self.buffer.save(filename, "PNG", -1)

    def updateImage(self, index, x_locs, y_locs, spots):
        painter = QtGui.QPainter(self.buffer)
        color = self.colors[index % self.points_per_cycle]
        if color:
            qtcolor = QtGui.QColor(color[0], color[1], color[2], 5)
            painter.setPen(qtcolor)
            for i in range(spots):
                ix = int(self.x_scale * x_locs[i])
                iy = int(self.y_scale * y_locs[i])
                painter.drawPoint(ix, iy)
            self.update()

#
#
# Spot Counter Dialog Box
#
class SpotCounter(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, single_camera, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        self.counters = [False, False]
        self.filming = 0
        self.filenames = [False, False]
        self.image_graphs = [False, False]
        self.number_cameras = 1
        self.spot_counter = False
        self.spot_graphs = [False, False]

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup.
        if single_camera:
            import qtdesigner.spotcounter_ui as spotCounterUi
        else:
            import qtdesigner.dualspotcounter_ui as spotCounterUi
            self.number_cameras = 2

        self.ui = spotCounterUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Spot Counter")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Setup Counter objects.
        if single_camera:
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
                                             parameters.min_spots,
                                             parameters.max_spots,
                                             parent = parents[i])
            self.spot_graphs[i].setGeometry(2, 2, graph_w, graph_h)
            self.spot_graphs[i].show()

        # Setup STORM image(s).
        if (self.number_cameras == 1):
            parents = [self.ui.imageFrame]
        else:
            parents = [self.ui.imageFrame, self.ui.imageFrame2]

        for i in range(self.number_cameras):
            camera_params = parameters
            if hasattr(parameters, "camera" + str(i+1)):
                camera_params = getattr(parameters, "camera" + str(i+1))

            image_w = parents[i].width() - 4
            image_h = parents[i].height() - 4
            scale_bar_len = (parameters.scale_bar_len / parameters.nm_per_pixel) * \
                float(image_w) / float(camera_params.x_pixels * camera_params.x_bin)

            self.image_graphs[i] = QImageGraph(image_w,
                                               image_h,
                                               camera_params.flip_horizontal,
                                               camera_params.flip_vertical,
                                               parent = parents[i])
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

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def getCounts(self):
        return self.counters[0].getCounts()
        
    @hdebug.debug
    def handleMaxChange(self, new_max):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_max = new_max)
        self.ui.minSpinBox.setMaximum(new_max - 10)
        self.parameters.max_spots = new_max

    @hdebug.debug
    def handleMinChange(self, new_min):
        for i in range(self.number_cameras):
            self.spot_graphs[i].changeYRange(y_min = new_min)
        self.ui.maxSpinBox.setMinimum(new_min + 10)
        self.parameters.max_spots = new_min

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    def newFrame(self, frame):
        if self.spot_counter:
            self.spot_counter.newImageToCount(frame)

    @hdebug.debug
    def newParameters(self, parameters, colors):
        self.parameters = parameters

        # Update counters, count graph(s) & STORM image(s).
        points_per_cycle = len(colors)
        total_points = points_per_cycle
        while total_points < 100:
            total_points += points_per_cycle

        for i in range(self.number_cameras):
            self.counters[i].reset()
            self.spot_graphs[i].newParameters(colors, total_points)

            camera_params = parameters
            if hasattr(parameters, "camera" + str(i+1)):
                camera_params = getattr(parameters, "camera" + str(i+1))
            scale_bar_len = (parameters.scale_bar_len / parameters.nm_per_pixel) * \
                float(self.image_graphs[i].width()) / float(camera_params.x_pixels * camera_params.x_bin)
            self.image_graphs[i].newParameters(colors,
                                               camera_params.flip_horizontal,
                                               camera_params.flip_vertical,
                                               scale_bar_len,
                                               camera_params.x_pixels / camera_params.x_bin,
                                               camera_params.y_pixels / camera_params.y_bin)

        # UI update.
        self.ui.maxSpinBox.setValue(parameters.max_spots)
        self.ui.minSpinBox.setValue(parameters.min_spots)

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

    @hdebug.debug        
    def quit(self):
        pass

    @hdebug.debug
    def shutDown(self):
        if self.spot_counter:
            self.spot_counter.shutDown()

    @hdebug.debug
    def startCounter(self, name):
        if self.spot_counter:
            for i in range(self.number_cameras):
                self.counters[i].reset()
                self.image_graphs[i].blank()
            self.filming = True
            self.filenames = [False, False]
            if name:
                if (self.number_cameras == 1):
                    self.filenames[0] = name + ".png"
                else:
                    self.filenames[0] = name + "_cam1.png"
                    self.filenames[1] = name + "_cam2.png"

    @hdebug.debug
    def stopCounter(self):
        self.filming = False
        if self.filenames[0]:
            for i in range(self.number_cameras):
                self.image_graphs[i].saveImage(self.filenames[i])


#
# testing
#

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    spotCounter = SpotCounter(parameters)
    spotCounter.show()
    app.exec_()


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

