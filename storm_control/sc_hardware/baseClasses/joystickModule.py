#!/usr/bin/python
"""
Base classes and module for USB Joystick control.

Hazen 09/12
Jeff 09/12
"""
from PyQt5 import QtCore

import storm_control.sc_library.parameters as params

import storm_control.hal4000.film.filmRequest as filmRequest
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halMessageBox as halMessageBox
import storm_control.hal4000.halLib.halModule as halModule


def sign(x):
    if (x > 0.0):
        return 1.0
    elif (x < 0.0):
        return -1.0
    else:
        return 0.0

class JoystickControl(QtCore.QObject):
    """
    Joystick monitoring class.
    """
    lock_jump = QtCore.pyqtSignal(float)
    toggle_film = QtCore.pyqtSignal()

    def __init__(self, joystick = None, joystick_gains = None, **kwds):
        super().__init__(**kwds)

        self.button_timer = QtCore.QTimer(self)
        self.joystick = joystick
        self.joystick_gains = joystick_gains   # XML should be [25.0, 250.0, 2500.0]
        self.old_right_joystick = [0, 0]
        self.old_left_joystick = [0, 0]
        self.stage_functionality = None
        self.to_emit = False

        # The joystick parameters.
        self.parameters = params.StormXMLObject()
        
        self.parameters.add(params.ParameterInt(name = "joystick_gain_index",
                                                value = 0,
                                                is_mutable = False,
                                                is_saved = False))
        
        self.parameters.add(params.ParameterInt(name = "multiplier",
                                                value = 1,
                                                is_mutable = False,
                                                is_saved = False))
        
        self.parameters.add(params.ParameterRangeFloat(description = "Step size in um for hat button press",
                                                       name = "hat_step",
                                                       value = 1.0,
                                                       min_value = 0.0,
                                                       max_value = 10.0))

        self.parameters.add(params.ParameterRangeFloat(description = "X button multiplier for joystick and focus lock",
                                                       name = "joystick_multiplier_value",
                                                       value = 5.0,
                                                       min_value = 0.0,
                                                       max_value = 50.0))
        
        self.parameters.add(params.ParameterSetString(description = "Response mode",
                                                      name = "joystick_mode",
                                                      value = "quadratic",
                                                      allowed = ["linear", "quadratic"]))
        
        self.parameters.add(params.ParameterSetFloat(description = "Sign for x motion",
                                                     name = "joystick_signx",
                                                     value = 1.0,
                                                     allowed = [-1.0, 1.0]))

        self.parameters.add(params.ParameterSetFloat(description = "Sign for y motion",
                                                     name = "joystick_signy",
                                                     value = 1.0,
                                                     allowed = [-1.0, 1.0]))

        self.parameters.add(params.ParameterRangeFloat(description = "Focus lock step size in um",
                                                       name = "lockt_step",
                                                       value = 0.025,
                                                       min_value = 0.0,
                                                       max_value = 1.0))

        self.parameters.add(params.ParameterRangeFloat(description = "Minimum joystick offset to be non-zero",
                                                       name = "min_offset",
                                                       value = 0.1,
                                                       min_value = 0.0,
                                                       max_value = 1.0))

        self.parameters.add(params.ParameterSetBoolean(description = "Swap x and y axises",
                                                       name = "xy_swap",
                                                       value = False))

        self.joystick.start(self.joystickHandler)

        self.button_timer.setInterval(100)
        self.button_timer.setSingleShot(True)
        self.button_timer.timeout.connect(self.buttonDownHandler)

    def buttonDownHandler(self):
        """
        Not used?
        """
        if self.to_emit:
            self.to_emit()
            self.button_timer.start()
            
    def cleanUp(self):
        """
        Shutdown the joystick hardware interface at program closing.
        """
        self.joystick.shutDown()

    def getParameters(self):
        return self.parameters

    def handleMotion(self, x_speed, y_speed):
        if self.stage_functionality is not None:
            self.stage_functionality.jog(x_speed, y_speed)

    def handleStep(self, x_step, y_step):
        if self.stage_functionality is not None:
            self.stage_functionality.goRelative(x_step, y_step)

    def hatEvent(self, sx, sy):
        """
        Emit the appropriate XY stage step event based on sx, sy.
        """
        p = self.parameters
        sx = sx * p.get("hat_step") * p.get("joystick_signx")
        sy = sy * p.get("hat_step") * p.get("joystick_signy")

        if p.get("xy_swap"):
            self.handleStep(sy, sx)
        else:
            self.handleStep(sx, sy)

    def joystickHandler(self, data):
        """
        This handles events that are created by the joystick hardware object.

        The following events are handled:
          1. "left upper trigger" and "Press" - focus up.
          2. "left lower trigger" and "Press" - focus down.
          3. "right upper trigger" and "Press" - start/stop filming.
          4. "back" and "Press" - emergency stage stop.
          5. "left joystick press" and "Press" - toggle stage motion gain.
          6. "X" and "Press" - add a additional multiplier to the XY stage motion.
          7. "X" and "Release" - return to the default multiplier (1.0) for XY stage motion.
          8. "up", "down", "left", "right" and "Press" - hat events for moving the XY stage.
          9. "left joystick" - XY stage motion driven by the left joystick.
        """
        p = self.parameters
        events = self.joystick.dataHandler(data)

        for [e_type, e_data] in events:
            # Buttons
            if(e_type == "left upper trigger") and (e_data == "Press"): # focus up
                self.lock_jump.emit(p.get("multiplier") * p.get("lockt_step"))
            elif(e_type == "left lower trigger") and (e_data == "Press"): # focus down
                self.lock_jump.emit(-p.get("multiplier") * p.get("lockt_step"))
            elif(e_type == "right upper trigger") and (e_data == "Press"): # start/stop film
                self.toggle_film.emit()
            elif(e_type == "back") and (e_data == "Press"): # emergency stage stop
                self.handleMotion(0.0, 0.0)
            elif(e_type == "left joystick press") and (e_data == "Press"): # toggle movement gain
                p.setv("joystick_gain_index", p.get("joystick_gain_index") + 1)
                if(p.get("joystick_gain_index") == len(self.joystick_gains)):
                    p.setv("joystick_gain_index", 0)
            elif(e_type == "X"): # engage/disengage movement multiplier
                if (e_data == "Press"):
                    p.setv("multiplier", p.get("joystick_multiplier_value"))
                else: # "Release"
                    p.setv("multiplier", 1.0)
                # Recall joystick event to reflect changes in gain
                self.leftJoystickEvent(self.old_left_joystick[0], self.old_left_joystick[1])

            # Hat
            elif(e_type == "up") and (e_data == "Press"):
                self.hatEvent(0.0,-1.0)
            elif(e_type == "down") and (e_data == "Press"):
                self.hatEvent(0.0,1.0)
            elif(e_type == "left") and (e_data == "Press"):
                self.hatEvent(-1.0,0.0)
            elif(e_type == "right") and (e_data == "Press"):
                self.hatEvent(1.0,0.0)

            # Joysticks
            elif (e_type == "left joystick"):
                self.leftJoystickEvent(e_data[0], e_data[1])
                self.old_left_joystick = e_data # remember joystick state

    def leftJoystickEvent(self, x_speed, y_speed):
        """
        Emit the appropriate XY state motion event based on x_speed, y_speed.
        There is both a fixed gain value, which can be changed between pre-determined
        defaults specified in the initial parameters XML file by pressing on
        the left joystick and additional multiplier that can be turned on or off
        by holding down the "X" button on the joystick.
        """
        p = self.parameters

        if(abs(x_speed) > p.get("min_offset")) or (abs(y_speed) > p.get("min_offset")):
            if (p.get("joystick_mode") == "quadratic"):
                x_speed = x_speed * x_speed * sign(x_speed)
                y_speed = y_speed * y_speed * sign(y_speed)

                # x_speed and y_speed range from -1.0 to 1.0.
                # convert to units of microns per second
                gain = p.get("multiplier") * self.joystick_gains[p.get("joystick_gain_index")]
                x_speed = gain * x_speed * p.get("joystick_signx")
                y_speed = gain * y_speed * p.get("joystick_signy")

                # The stage and the joystick might have different ideas
                # about which direction is x.
                if p.get("xy_swap"):
                    self.handleMotion(y_speed, x_speed)
                else:
                    self.handleMotion(x_speed, y_speed)
        else:
            self.handleMotion(0.0, 0.0)

    def newParameter(self, parameters):

        # Only update the mutable parameters. I think this is the right
        # thing to do, as the user probably won't expect the gain for
        # example to change to whatever setting was in the parameters
        # that were stored by settings.settings.
        #
        # Or maybe they will? Needs some use testing..
        #
        for pname in parameters.getAttrs():
            prop = parameters.getp(pname)
            if prop.isMutable():
                self.parameters.setv(pname, prop.getv())
    
    def rightJoystickEvent(self, x_speed, y_speed):
        """
        The right joystick is not currently used
        """
        pass

    def setStageFunctionality(self, stage_functionality):
        self.stage_functionality = stage_functionality


class JoystickModule(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.filming = False
        self.waiting_for_film = False

        configuration = module_params.get("configuration")
        self.gains = list(map(float, configuration.get("joystick_gains").split(",")))
        
    def cleanUp(self, qt_settings):
        self.control.cleanUp()

    def handleLockJump(self, delta):
        self.sendMessage(halMessage.HalMessage(m_type = "lock jump",
                                               data = {"delta" : float(delta)}))

    def handleToggleFilm(self):
        if not self.waiting_for_film:
            if self.filming:
                self.sendMessage(halMessage.HalMessage(m_type = "stop film request"))
            else:
                self.sendMessage(halMessage.HalMessage(m_type = "start film request",
                                                       data = {"request" : filmRequest.FilmRequest()}))
            self.waiting_for_film = True

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.control.setStageFunctionality(response.getData()["functionality"])
            
    def processMessage(self, message):

        if message.isType("configuration"):
            if message.sourceIs("stage"):
                stage_fn_name = message.getData()["properties"]["stage functionality name"]
                self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                       data = {"name" : stage_fn_name,
                                                               "extra data" : "stage_fn"}))        

        elif message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.control.getParameters()}))

        elif message.isType("film lockout"):
            # This means that filming has started (True), or stopped (False).
            self.filming = message.getData()["locked out"]

            # HAL has responded so we can stop ignoring the film button.
            self.waiting_for_film = False

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.control.getParameters().copy()}))
            self.control.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.control.getParameters()}))

        elif message.isType("stop film"):
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"parameters" : self.control.getParameters()}))

#
# The MIT License
#
# Copyright (c) 2018 Babcock Lab, Harvard University
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
