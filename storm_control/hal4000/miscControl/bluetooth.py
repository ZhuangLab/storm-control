#!/usr/bin/env python
"""
Handles communication with a bluetooth device, an Android phone 
for example. It is recommended that your devices support at 
least Bluetooth version 2.0 if you want to send the current 
camera display from HAL to the device.

Hazen 06/18
"""

import bluetooth
import io
from PyQt5 import QtCore, QtGui
import time
import traceback

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halModule as halModule


class BluetoothControl(QtCore.QThread):
    newMessage = QtCore.pyqtSignal(str)
    
    def __init__(self, config = None, **kwds):
        super().__init__(**kwds)

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
        self.parameters = params.StormXMLObject()
        self.running = False
        self.send_pictures = config.get("send_pictures")
        self.show_camera = True
        self.start_time = 0
        self.which_camera = "camera1"

        self.parameters.add(params.ParameterRangeFloat(description = "Z step size in um",
                                                       name = "z_step",
                                                       value = 0.025,
                                                       min_value = 0.0,
                                                       max_value = 1.0))

        # Set current image to default.
        self.current_image = self.default_image

        # Setup bluetooth socket.
        have_bluetooth = True
        try:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("",bluetooth.PORT_ANY))
            self.server_sock.listen(1)

            port = self.server_sock.getsockname()[1]
            print("Bluetooth: Listening on RFCOMM channel {0:d}".format(port))

            uuid = "3e1f9ea8-9c11-11e3-b248-425861b86ab6"
            
            bluetooth.advertise_service(self.server_sock, "halServer",
                                        service_id = uuid,
                                        service_classes = [uuid, bluetooth.SERIAL_PORT_CLASS],
                                        profiles = [bluetooth.SERIAL_PORT_PROFILE])
            
        except bluetooth.btcommon.BluetoothError:
            print(traceback.format_exc())
            print("Failed to start Bluetooth")
            have_bluetooth = False

        if have_bluetooth:

            # Setup timer.
            self.click_timer.setInterval(200)
            self.click_timer.timeout.connect(self.handleClickTimer)
            self.click_timer.setSingleShot(True)

            # Connect signals.
            self.newMessage.connect(self.handleNewMessage)
            self.start(QtCore.QThread.NormalPriority)

    def addMessage(self, message):
        """
        Add a message to the queue, but only if we are connected.
        """
        
        # Check if we connected.
        self.mutex.lock()
        connected = self.connected
        self.mutex.unlock()
        if not connected:
            return

        self.messages.append(message)

    def cleanUp(self):
        self.running = False
        self.wait()

    def clickUpdate(self):
        """
        Handles click events. These are touches that were too short to be drag events.
        """
        dx = int(round(3.0 * self.click_x))
        dy = int(round(3.0 * self.click_y))
#        if ((dx == 0) and (dy == 0)):
#            self.drag_gain += 1.0
#            if (self.drag_gain > 3.1):
#                self.drag_gain = 1.0
#            self.addMessage("gainchange," + str(int(self.drag_gain)))
#        else:
#            self.stepMove.emit(self.click_step * dx, self.click_step * dy)

    def dragUpdate(self):
        """
        Handles moving the stage during drag events.
        """
        dx = self.drag_gain * self.drag_multiplier * (self.drag_x - self.click_x)
        dy = self.drag_gain * self.drag_multiplier * (self.drag_y - self.click_y)
        self.dragMove.emit(self.which_camera, dx, dy)

    def handleClickTimer(self):
        """
        If the user holds down for longer than it takes for this timer
        to fire then the click event becomes a drag event.
        """
        if self.is_down:
            self.is_drag = True
            self.dragStart.emit(self.which_camera)
            self.dragUpdate()

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

    def handleNewCameraPixmap(self, which_camera, new_pixmap):
        if self.show_camera and (self.which_camera == which_camera):
            self.handleNewPixmap(new_pixmap)

    def handleNewMessage(self, message):
        """
        Handles message from the device at the other end of the Bluetooth connection.
        """
        # Check if we are still connected.
        self.mutex.lock()
        connected = self.connected
        self.mutex.unlock()
        if not connected:
            return

        # Messages can come down from the device at any time.
        if (message != "ack") and (message != "newimage"):
            if ("action" in message):
                [mtype, ay, ax] = message.split(",")
                if (mtype == "actiondown"):
                    self.click_x = float(ax)
                    self.click_y = -1.0 * float(ay)
                    self.is_down = True
                    self.click_timer.start()
                if (mtype == "actionmove"):
                    self.drag_x = float(ax)
                    self.drag_y = -1.0 * float(ay)
                    if self.is_drag:
                        self.dragUpdate()
                if (mtype == "actionup"):
                    self.is_down = False
                    if self.is_drag:
                        self.dragUpdate()
                        self.is_drag = False
                    else:
                        self.clickUpdate()
            elif (message == "record"):
                self.toggleFilm.emit()
            elif (message == "focusdown"):
                self.lockJump.emit(-self.lock_jump_size)
            elif (message == "focusup"):
                self.lockJump.emit(self.lock_jump_size)
            elif (message == "lockclick"):
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
                    abuffer = QtCore.QBuffer(byte_array)
                    abuffer.open(QtCore.QIODevice.WriteOnly)
                    self.current_image.save(abuffer, 'JPEG', quality = 50)
                    #self.current_image.save(buffer, 'JPEG')
                
                    image_io = io.BytesIO(byte_array)
                    self.image_data = image_io.getvalue()
                    self.image_data_len = len(self.image_data)
                    self.image_is_new = False

                try:
                    self.client_sock.send("image," + str(self.image_data_len) + ",")
                    self.client_sock.send(self.image_data)
                except: #FIXME: Should be more specific.
                    self.mutex.lock()
                    self.connected = False
                    self.messages = []
                    self.mutex.unlock()

                self.mutex.lock()
                self.images_sent += 1
                self.mutex.unlock()

    def handleNewLockPixmap(self, new_pixmap):
        """
        Send a picture from the focus lock.
        """
        if not self.show_camera:
            self.handleNewPixmap(new_pixmap)

    def handleNewPixmap(self, new_pixmap):
        """
        Update the current picture based on HAL display 0. Currently we 
        limit to just displaying this display as it is the only one that 
        is gauranteed to exist. 

        FIXME: Support swiping to change the current display.
        """
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

#    def newParameters(self, parameters):
#        self.lock_jump_size = parameters.get("bluetooth.z_step")

    def run(self):
        """
        Loop, waiting for connections or data.
        """
        self.running = True        
        while self.running:

            # Block here waiting for a connection.
            [client_sock, client_info] = self.server_sock.accept()

            # Initialization of a new connection.
            print("Bluetooth: Connected.")
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
                data = self.client_sock.recv(1024).decode()
                if (len(data) == 0):
                    self.mutex.lock()
                    connect = False
                    self.connected = False
                    self.drag_gain = 1.0
                    self.messages = []
                    self.show_camera = True
                    images_per_second = float(self.images_sent)/float(time.time() - self.start_time)
                    print("Bluetooth: Disconnected")
                    print("Bluetooth: Sent {0:.2f} images per second.".format(images_per_second))
                    self.mutex.unlock()
                else:
                    for datum in data.split("<>"):
                        if (len(datum) > 0):
                            self.newMessage.emit(datum)

                self.mutex.lock()
                connected = self.connected
                self.mutex.unlock()

    def startFilm(self, film_name, run_shutters):
        self.addMessage("startfilm")
        self.filming = True

    def stopFilm(self, film_writer):
        self.addMessage("stopfilm")
        self.filming = False
                            

class BlueToothModule(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.bt_control = BluetoothControl(config = module_params.get("configuration"))

    def cleanUp(self, qt_settings):
        self.bt_control.cleanUp()
        super().cleanUp(qt_settings)
        
