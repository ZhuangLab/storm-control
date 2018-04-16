#!/usr/bin/python
#
## @file
#
# Joystick monitoring class.
#
# Hazen 09/12
# Jeff 09/12

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halModule as halModule
import storm_control.sc_library.parameters as params

# Debugging
import storm_control.sc_library.hdebug as hdebug

## JoystickObject
#
# Joystick monitoring class.
#
class JoystickObject(QtCore.QObject, halModule.HalModule):
    lock_jump = QtCore.pyqtSignal(float)
    motion = QtCore.pyqtSignal(float, float)
    step = QtCore.pyqtSignal(int, int)
    toggle_film = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parameters A parameters object.
    # @param joystick A hardware specific joystick interface object similar to that defined in logitech\gamepad310.py.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, joystick, parent = None):
        QtCore.QObject.__init__(self, parent)
        halModule.HalModule.__init__(self, parent)

        self.button_timer = QtCore.QTimer(self)
        self.jstick = joystick
        self.old_right_joystick = [0, 0]
        self.old_left_joystick = [0, 0]
        self.to_emit = False

        # Add joystick specific parameters.
        js_params = parameters.addSubSection("joystick")
        js_params.add("joystick_gain_index", params.ParameterInt("",
                                                                 "joystick_gain_index",
                                                                 0,
                                                                 is_mutable = False,
                                                                 is_saved = False))
        js_params.add("multiplier", params.ParameterInt("",
                                                        "multiplier",
                                                        1,
                                                        is_mutable = False,
                                                        is_saved = False))
        js_params.add("hat_step", params.ParameterRangeFloat("Step size in um for hat button press",
                                                             "hat_step",
                                                             1.0, 0.0, 10.0))
        js_params.add("joystick_gain", [25.0, 250.0, 2500.0])
        js_params.add("joystick_multiplier_value", params.ParameterRangeFloat("X button multiplier for joystick and focus lock",
                                                                              "joystick_multiplier_value",
                                                                              5.0, 0.0, 50.0))
        js_params.add("joystick_mode", params.ParameterSetString("Response mode",
                                                                 "joystick_mode",
                                                                 "quadratic",
                                                                 ["linear", "quadratic"]))
        js_params.add("joystick_signx", params.ParameterSetFloat("Sign for x motion",
                                                                 "joystick_signx",
                                                                 1.0, [-1.0, 1.0]))
        js_params.add("joystick_signy", params.ParameterSetFloat("Sign for y motion",
                                                                 "joystick_signy",
                                                                 1.0, [-1.0, 1.0]))
        js_params.add("lockt_step", params.ParameterRangeFloat("Focus lock step size in um",
                                                               "lockt_step",
                                                               0.025, 0.0, 1.0))
        js_params.add("min_offset", params.ParameterRangeFloat("Minimum joystick offset to be non-zero",
                                                               "min_offset",
                                                               0.1, 0.0, 1.0))
        js_params.add("xy_swap", params.ParameterSetBoolean("Swap x and y axises",
                                                            "xy_swap",
                                                            False))
        self.parameters = js_params

        self.jstick.start(self.joystickHandler)

        self.button_timer.setInterval(100)
        self.button_timer.setSingleShot(True)
        self.button_timer.timeout.connect(self.buttonDownHandler)

    ## buttonDownHandler
    #
    # Not used?
    #
    def buttonDownHandler(self):
        if self.to_emit:
            self.to_emit()
            self.button_timer.start()

    ## cleanup
    #
    # Shutdown the joystick hardware interface at program closing.
    #
    @hdebug.debug
    def cleanup(self):
        self.jstick.shutDown()

    ## getSignals
    #
    # @return An array of signals provided by the module.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "lockJump", self.lock_jump],
                [self.hal_type, "jstickMotion", self.motion],
                [self.hal_type, "stepMove", self.step],
                [self.hal_type, "toggleFilm", self.toggle_film]]

    ## hatEvent
    #
    # Emit the appropriate XY stage step event based on sx, sy.
    #
    # @param sx One of -1.0, 0.0, 1.0
    # @param sy One of -1.0, 0.0, 1.0
    #
    def hatEvent(self, sx, sy):
        p = self.parameters
        sx = sx * p.get("hat_step") * p.get("joystick_signx")
        sy = sy * p.get("hat_step") * p.get("joystick_signy")

        if p.get("xy_swap"):
            self.step.emit(sy, sx)
        else:
            self.step.emit(sx,sy)

    ## rightJoystickEvent
    #
    # Not used.
    #
    def rightJoystickEvent(self, x_speed, y_speed):
        # the right joystick is not currently used
        pass

    ## leftJoystickEvent
    #
    # Emit the appropriate XY state motion event based on x_speed, y_speed.
    # There is both a fixed gain value, which can be changed between pre-determined
    # defaults specified in the initial parameters XML file by pressing on
    # the left joystick and additional multiplier that can be turned on or off
    # by holding down the "X" button on the joystick.
    #
    # @param x_speed The x displacement value from the joystick.
    # @param y_speed The y displacement value from the joystick.
    #
    def leftJoystickEvent(self, x_speed, y_speed):
        p = self.parameters

        if(abs(x_speed) > p.get("min_offset")) or (abs(y_speed) > p.get("min_offset")):
            if (p.get("joystick_mode") == "quadratic"):
                x_speed = x_speed * x_speed * cmp(x_speed, 0.0)
                y_speed = y_speed * y_speed * cmp(y_speed, 0.0)

                # x_speed and y_speed range from -1.0 to 1.0.
                # convert to units of microns per second
                gain = p.get("multiplier") * p.get("joystick_gain")[p.get("joystick_gain_index")]
                x_speed = gain * x_speed * p.get("joystick_signx")
                y_speed = gain * y_speed * p.get("joystick_signy")

                # The stage and the joystick might have different ideas
                # about which direction is x.
                if p.get("xy_swap"):
                    self.motion.emit(y_speed, x_speed)
                else:
                    self.motion.emit(x_speed, y_speed)
        else:
            self.motion.emit(0.0, 0.0)

    ## joystickHandler
    #
    # This handles events that are created by the joystick hardware object.
    # The following events are handled:
    #  1. "left upper trigger" and "Press" - focus up.
    #  2. "left lower trigger" and "Press" - focus down.
    #  3. "right upper trigger" and "Press" - start/stop filming.
    #  4. "back" and "Press" - emergency stage stop.
    #  5. "left joystick press" and "Press" - toggle stage motion gain.
    #  6. "X" and "Press" - add a additional multiplier to the XY stage motion.
    #  7. "X" and "Release" - return to the default multiplier (1.0) for XY stage motion.
    #  8. "up", "down", "left", "right" and "Press" - hat events for moving the XY stage.
    #  9. "left joystick" - XY stage motion driven by the left joystick.
    #
    # @param data A python array of joystick events.
    #
    def joystickHandler(self, data):
        p = self.parameters
        events = self.jstick.dataHandler(data)

        for [e_type, e_data] in events:
            # Buttons
            if(e_type == "left upper trigger") and (e_data == "Press"): # focus up
                self.lock_jump.emit(p.get("multiplier") * p.get("lockt_step"))
            elif(e_type == "left lower trigger") and (e_data == "Press"): # focus down
                self.lock_jump.emit(-p.get("multiplier") * p.get("lockt_step"))
            elif(e_type == "right upper trigger") and (e_data == "Press"): # start/stop film
                self.toggle_film.emit()
            elif(e_type == "back") and (e_data == "Press"): # emergency stage stop
                self.motion.emit(0.0, 0.0)
            elif(e_type == "left joystick press") and (e_data == "Press"): # toggle movement gain
                p.set("joystick_gain_index", p.get("joystick_gain_index") + 1)
                if(p.get("joystick_gain_index") == len(p.get("joystick_gain"))):
                    p.set("joystick_gain_index", 0)
            elif(e_type == "X"): # engage/disengage movement multiplier
                if (e_data == "Press"):
                    p.set("multiplier", p.get("joystick_multiplier_value"))
                else: # "Release"
                    p.set("multiplier", 1.0)
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
