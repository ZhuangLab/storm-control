#!/usr/bin/python
#
## @file
#
# Thread for handling communication with a bluetooth device, an
# android phone for example. It is recommended that your devices
# support at least Bluetooth version 2.0 if you want to send the
# current camera display from HAL to the device.
#
# Hazen 02/14
#

import bluetooth
from cStringIO import StringIO
from PyQt4 import QtCore, QtGui
import time
import traceback

import halLib.halModule as halModule

import sc_library.hdebug as hdebug

## HalBluetooth
#
# QThread for communication with a bluetooth device.
#
# Currently this shows the same images as in the viewer for camera1
# and it sends movement signals as if it was the viewer for camera1.
#
class HalBluetooth(QtCore.QThread, halModule.HalModule):
    dragStart = QtCore.pyqtSignal(str)
    dragMove = QtCore.pyqtSignal(str, float, float)
    lockJump = QtCore.pyqtSignal(float)
    newData = QtCore.pyqtSignal(object)
    stepMove = QtCore.pyqtSignal(float, float)
    toggleFilm = QtCore.pyqtSignal()

    ## __init__
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent The PyQt parent.
    #
    def __init__(self, hardware, parameters, parent):
        QtCore.QThread.__init__(self, parent)
        halModule.HalModule.__init__(self)

        self.click_step = 1.0
        self.click_timer = QtCore.QTimer(self)
        self.click_x = 0.0
        self.click_y = 0.0
        self.client_sock = False
        self.connected = False
        self.default_image = QtGui.QImage("bt_image.png")
        self.drag_gain = 1.0
        self.drag_multiplier = 100.0
        self.drag_x = 0.0
        self.drag_y = 0.0
        self.filming = False
        self.image_is_new = True
        self.images_sent = 0
        self.is_down = False
        self.is_drag = False
        self.lock_jump_size = 0.025
        self.messages = []
        self.mutex = QtCore.QMutex()
        self.send_pictures = hardware.send_pictures
        self.show_camera = True
        self.start_time = 0
        self.which_camera = "camera1"

        # Set current image to default.
        self.current_image = self.default_image

        # Setup bluetooth socket.
        have_bluetooth = True
        try:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("",bluetooth.PORT_ANY))
            self.server_sock.listen(1)

            port = self.server_sock.getsockname()[1]
            hdebug.logText("Bluetooth: Listening on RFCOMM channel {0:d}".format(port))

            uuid = "3e1f9ea8-9c11-11e3-b248-425861b86ab6"
            
            bluetooth.advertise_service( self.server_sock, "halServer",
                                         service_id = uuid,
                                         service_classes = [ uuid, bluetooth.SERIAL_PORT_CLASS ],
                                         profiles = [ bluetooth.SERIAL_PORT_PROFILE ],
                                         )
        except:
            print traceback.format_exc()
            hdebug.logText("Failed to start Bluetooth")
            have_bluetooth = False

        if have_bluetooth:

            # Setup timer.
            self.click_timer.setInterval(200)
            self.click_timer.timeout.connect(self.handleClickTimer)
            self.click_timer.setSingleShot(True)

            # Connect signals.
            self.newData.connect(self.handleNewData)

            self.start(QtCore.QThread.NormalPriority)

    ## addMessage
    #
    # @param message The message to add to the queue, but only if we are connected.
    #
    def addMessage(self, message):

        # Check if we connected.
        self.mutex.lock()
        connected = self.connected
        self.mutex.unlock()
        if not connected:
            return

        self.messages.append(message)

    ## cleanup
    #
    # Stop the thread.
    #
    def cleanup(self):
        self.quit()

    ## clickUpdate
    #
    # Handles click events. These are touches that were too short to be drag events.
    #
    def clickUpdate(self):
        dx = int(round(3.0 * self.click_x))
        dy = int(round(3.0 * self.click_y))
        if ((dx == 0) and (dy == 0)):
            self.drag_gain += 1.0
            if (self.drag_gain > 3.1):
                self.drag_gain = 1.0
            self.addMessage("gainchange," + str(int(self.drag_gain)))
        else:
            self.stepMove.emit(self.click_step * dx, self.click_step * dy)

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "frameCaptured"):
                signal[2].connect(self.handleNewCameraPixmap)
            elif (signal[1] == "focusLockStatus"):
                signal[2].connect(self.handleFocusLockStatus)
            elif (signal[1] == "focusLockDisplay"):
                signal[2].connect(self.handleNewLockPixmap)

    ## dragUpdate
    #
    # Emits drag signal based on displacement and drag multiplier.
    #
    def dragUpdate(self):
        dx = self.drag_gain * self.drag_multiplier * (self.drag_x - self.click_x)
        dy = self.drag_gain * self.drag_multiplier * (self.drag_y - self.click_y)
        self.dragMove.emit(self.which_camera, dx, dy)
        
    ## getSignals
    #
    # @return An array of signals provided by the module.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "dragMove", self.dragMove],
                [self.hal_type, "dragStart", self.dragStart],
                [self.hal_type, "lockJump", self.lockJump],
                [self.hal_type, "stepMove", self.stepMove],
                [self.hal_type, "toggleFilm", self.toggleFilm]]

    ## handleClickTimer
    #
    # If the user holds down for longer than it takes for this timer
    # to fire then the click event becomes a drag event.
    #
    def handleClickTimer(self):
        if self.is_down:
            self.is_drag = True
            self.dragStart.emit(self.which_camera)
            self.dragUpdate()

    ## handleFocusLockStatus
    #
    # @param lock_offset The current focus lock offset (nominally 0.0 - 1.0).
    # @param lock_sum The current focus lock sum (nominally 0.0 - 1.0).
    #
    def handleFocusLockStatus(self, lock_offset, lock_sum):

        # Enforce 0.0 - 1.0 range.
        if (lock_offset < 0.0):
            lock_offset = 0.0
        elif (lock_offset > 1.0):
            lock_offset = 1.0
        if (lock_sum < 0.0):
            lock_sum = 0.0
        elif (lock_sum > 1.0):
            lock_sum = 1.0

        # Put the message in the queue.
        self.addMessage("lockupdate,{0:.3f},{1:.3f}".format(lock_offset, lock_sum))

    ## handleNewCameraPixmap
    #
    # @param new_pixmap A QPixmap object from the camera display.
    #
    def handleNewCameraPixmap(self, which_camera, new_pixmap):
        if self.show_camera and (self.which_camera == which_camera):
            self.handleNewPixmap(new_pixmap)

    ## handleNewData
    #
    # Handles message from the device at the other end of the Bluetooth connection.
    # handleNewMessage would probably be a better name for this method..
    #
    # @param data A string containing the message from the device.
    #
    def handleNewData(self, data):

        # Check if we are still connected.
        self.mutex.lock()
        connected = self.connected
        self.mutex.unlock()
        if not connected:
            return

        # Messages can come down from the device at any time.
        if (data != "ack") and (data != "newimage"):
            if ("action" in data):
                [type, ay, ax] = data.split(",")
                if (type == "actiondown"):
                    self.click_x = float(ax)
                    self.click_y = -1.0 * float(ay)
                    self.is_down = True
                    self.click_timer.start()
                if (type == "actionmove"):
                    self.drag_x = float(ax)
                    self.drag_y = -1.0 * float(ay)
                    if self.is_drag:
                        self.dragUpdate()
                if (type == "actionup"):
                    self.is_down = False
                    if self.is_drag:
                        self.dragUpdate()
                        self.is_drag = False
                    else:
                        self.clickUpdate()
            elif (data == "record"):
                self.toggleFilm.emit()
            elif (data == "focusdown"):
                self.lockJump.emit(-self.lock_jump_size)
            elif (data == "focusup"):
                self.lockJump.emit(self.lock_jump_size)
            elif (data == "lockclick"):
                self.show_camera = not self.show_camera
                if self.show_camera:
                    self.addMessage("showgain,1")
                else:
                    self.addMessage("showgain,0")
                self.current_image = self.default_image
                self.image_is_new = True

        # Messages are only sent up to the device when the device requests a new image
        # or acknowledges the receipt of a previous message.
        else:

            # Send all the new messages first (one at time) as this should be fast.
            if (len(self.messages) > 0):
                to_send = self.messages.pop(0)
                try:
                    self.client_sock.send(to_send)
                except:
                    self.mutex.lock()
                    self.connected = False
                    self.messages = []
                    self.mutex.unlock()

            # If there are no remaining messages to send then send the new image.
            else:

                #
                # This comes from here:
                #  http://stackoverflow.com/questions/13302524/pyqt-qpixmap-save-to-stringio
                #
                if (self.image_is_new):
                    byte_array = QtCore.QByteArray()
                    buffer = QtCore.QBuffer(byte_array)
                    buffer.open(QtCore.QIODevice.WriteOnly)
                    self.current_image.save(buffer, 'JPEG', quality = 50)
                    #self.current_image.save(buffer, 'JPEG')
                
                    image_io = StringIO(byte_array)
                    self.image_data = image_io.getvalue()
                    self.image_data_len = len(self.image_data)
                    self.image_is_new = False

                try:
                    self.client_sock.send("image," + str(self.image_data_len) + ",")
                    self.client_sock.send(self.image_data)
                except:
                    self.mutex.lock()
                    self.connected = False
                    self.messages = []
                    self.mutex.unlock()

                self.mutex.lock()
                self.images_sent += 1
                self.mutex.unlock()

    ## handleNewLockPixmap
    #
    # @param new_pixmap A QPixmap object from the focus lock.
    #
    def handleNewLockPixmap(self, new_pixmap):
        if not self.show_camera:
            self.handleNewPixmap(new_pixmap)

    ## handleNewPixmap
    #
    # @param new_pixmap A QPixmap object.
    #
    def handleNewPixmap(self, new_pixmap):

        #
        # If we are not supposed to send pictures, just keep sending 
        # the default picture which is hopefully small enough not
        # to cause too much of a load on the connection.
        #
        # Needs to be tested with an older phone..
        #
        if not self.send_pictures:
            return
        
        # Create a pixmap & color it black.
        self.current_image = QtGui.QPixmap(256, 256)
        painter = QtGui.QPainter(self.current_image)
        painter.setPen(QtGui.QColor(0, 0, 0))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        painter.drawRect(self.current_image.rect())

        # Figure out bounding rectangle to use.
        width = new_pixmap.width()
        height = new_pixmap.height()
        if (width >= height):
            xi = 0
            xf = 255
            ysize = int(255.0 * float(height) / float(width))
            margin = (255 - ysize)/2
            yi = margin
            yf = 255 - margin
        else:
            yi = 0
            yf = 255
            xsize = int(255.0 * float(width) / float(height))
            margin = (255 - xsize)/2
            xi = margin
            xf = 255 - margin

        # Draw (rotated) image in pixmap
        painter.translate(256,0)
        painter.rotate(90)
        painter.drawPixmap(QtCore.QRect(xi, yi, xf - xi, yf - yi), new_pixmap, new_pixmap.rect())

        # Close painter.
        painter.end()

        self.image_is_new = True

    ## newParameters
    #
    # @param parameters A parameters object.
    #
    def newParameters(self, parameters):
        self.lock_jump_size = parameters.get("joystick.lockt_step")

    ## run
    #
    # Loop, waiting for connections or data.
    #
    def run(self):
        while True:

            # Block here waiting for a connection.
            [client_sock, client_info] = self.server_sock.accept()

            # Initialization of a new connection.
            hdebug.logText("Bluetooth: Connected.")
            self.mutex.lock()
            self.client_sock = client_sock
            connected = True
            self.connected = True
            self.images_sent = 0
            self.start_time = time.time()
            
            # Send initial configuration information.
            if self.filming:
                self.messages.append("startfilm")
            else:
                self.messages.append("stopfilm")

            self.mutex.unlock()

            while connected:
                
                # Block here waiting for a string from the paired device.
                data = self.client_sock.recv(1024)
                if (len(data) == 0):
                    self.mutex.lock()
                    connect = False
                    self.connected = False
                    self.drag_gain = 1.0
                    self.messages = []
                    self.show_camera = True
                    images_per_second = float(self.images_sent)/float(time.time() - self.start_time)
                    hdebug.logText("Bluetooth: Disconnected")
                    hdebug.logText("Bluetooth: Sent {0:.2f} images per second.".format(images_per_second))
                    self.mutex.unlock()
                else:
                    for datum in data.split("<>"):
                        if (len(datum) > 0):
                            self.newData.emit(datum)

                self.mutex.lock()
                connected = self.connected
                self.mutex.unlock()

    ## startFilm
    #
    # @param film_name This is ignored.
    # @param run_shutters Also ignored.
    #
    @hdebug.debug
    def startFilm(self, film_name, run_shutters):
        self.addMessage("startfilm")
        self.filming = True

    ## stopFilm
    #
    # @param film_writer This is ignored.
    #
    @hdebug.debug
    def stopFilm(self, film_writer):
        self.addMessage("stopfilm")
        self.filming = False
                            
#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
