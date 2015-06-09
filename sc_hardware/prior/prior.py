#!/usr/bin/python
#
## @file
#
# Prior stage communication.
#
# Hazen 5/11
#

import time

import sc_hardware.nationalInstruments.nicontrol as nicontrol
import sc_hardware.serial.RS232 as RS232

## Prior
#
# Encapsulates control of a XY Prior stage, possibly with piezo Z control & a filter wheel.
# Communication occurs by RS-232.
#
class Prior(RS232.RS232):

    ## __init__
    #
    # @param port (Optional) The RS-232 port to use, defaults to "COM2".
    # @param timeout (Optional) The time out value for communication, defaults to None.
    # @param baudrate (Optional) The communication baud rate, defaults to 9600.
    # @param wait_time How long to wait between polling events before it is decided that there is no new data available on the port, defaults to 20ms.
    #
    def __init__(self, port = "COM2", timeout = None, baudrate = 9600, wait_time = 0.02):
        self.unit_to_um = 1.0
        self.um_to_unit = 1.0/self.unit_to_um
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        # RS232 stuff
        RS232.RS232.__init__(self, port, timeout, baudrate, "\r", wait_time)
        try:
            test = self.commWithResp("?")
        except:
            self.live = False
        if not self.live:
            print "Prior Stage is not connected? Stage is not on?"
        else:   # this turns off "drift correction".
            self.setServo(False)
            self.setEncoderWindow("X", 2)
            self.setEncoderWindow("Y", 2)

    ## _command
    #
    # @param command The command string to send.
    #
    # @return The response to the command.
    #
    def _command(self, command):
        response = self.commWithResp(command)
        if response:
            return response.split("\r")

    ## active
    #
    # @return True/False The stage is busy doing something.
    #
    def active(self):
        response = self._command("$")[0]
        if (response == "0"):
            return False
        else:
            return True

#        state = self.state()
#        try:
#            state.index("busy")
#            return 1
#        except:
#            return 0

    ## backlashOnOff
    #
    # @param on True/False turn backlash compensation on/off.
    #
    def backlashOnOff(self, on):
        if on:
            self._command("BLSH 1")
        else:
            self._command("BLSH 0")

    ## changeFilter
    #
    # @param filter_index The filter index to change to.
    # @param filter_wheel (Optional) The filter wheel, defaults to 1.
    #
    def changeFilter(self, filter_index, filter_wheel = 1):
        if not (filter_index == self.getFilter(filter_wheel)):
            self.sendCommand("7," + str(filter_wheel) + "," + str(filter_index))
            self.waitResponse()

    ## getFilter
    #
    # @param filter_wheel (Optional) The filter wheel, defaults to 1.
    #
    # @return The current filter position.
    #
    def getFilter(self, filter_wheel = 1):
        try:
            return int(self._command("7," + str(filter_wheel) + ",F")[0])
        except:
            print "Error reading filter position."
            return -1

    ## getServo
    #
    # Returns whether or not the stage is servoing, i.e. updating it
    # position based on the encoders in the event of drift.
    #
    # @return [servo x, servo y].
    #
    def getServo(self):
        return [self._command("SERVO,X"), self._command("SERVO,Y")]

    ## goAbsolute
    #
    # @param x X position in um.
    # @param y Y position in um.
    #
    def goAbsolute(self, x, y):
        self.sendCommand("G " + str(x * self.um_to_unit) + "," + str(y * self.um_to_unit))
        self.waitResponse()

    ## goRelative
    #
    # @param dx Amount to move in x in um.
    # @param dy Amount to move in y in um.
    #
    def goRelative(self, dx, dy):
        self.sendCommand("GR " + str(dx * self.um_to_unit) + "," + str(dy * self.um_to_unit))
        self.waitResponse()

    ## info
    #
    # @return Some information about the stage.
    #
    def info(self):
        return self._command("?")

    ## jog
    #
    # @param x_speed Speed the stage should be moving at in x in um/s.
    # @param y_speed Speed the stage should be moving at in y in um/s.
    #
    def jog(self, x_speed, y_speed):
        #print "VS {0:.1f},{1:.1f}".format(x_speed,y_speed)
        self._command("VS {0:.1f},{1:.1f}".format(x_speed,y_speed))

    ## joystickOnOff
    #
    # @param on True/False enable/disable the stage joystick.
    #
    def joystickOnOff(self, on):
        if on:
            self._command("J")
        else:
            self._command("H")
     
    ## position
    #
    # @return [stage x (um), stage y (um), stage z (um)].
    #
    def position(self):
        try:
            response = self._command("P")[0]
            [self.x, self.y, self.z] = map(int, response.split(","))
        except:
            pass
        return [self.x * self.unit_to_um, 
                self.y * self.unit_to_um, 
                self.z * self.unit_to_um]

    ## setEncoderWindow
    #
    # Sets the amount of diplacement from the correct position that is allowed
    # before the stage will attempt to correct by moving.
    #
    # @param axis The axis to set the window on.
    # @param window The size of the window.
    #
    def setEncoderWindow(self, axis, window):
        assert window >= 0, "setEncoderWindow window is too small " + str(window)
        #assert window <= 4, "setEncoderWindow window is too large " + str(window)
        if (axis == "X"):
            self._command("ENCW X," + str(window))
        if (axis == "Y"):
            self._command("ENCW Y," + str(window))

    ## setServo
    #
    # Set the stage to update (or not) based on the encoders in the
    # event of stage drift.
    #
    # @param servo True/False turn the servo on/off?
    #
    def setServo(self, servo):
        if servo:
            self._command("SERVO,1")
        else:
            self._command("SERVO,0")

    ## setVelocity
    #
    # @param x_vel The maximum stage velocity allowed in x.
    # @param y_vel The maximum stage velocity allowed in y.
    #
    def setVelocity(self, x_vel, y_vel):
        # FIXME: units are 1-100, but not exactly sure what..
        speed = x_vel * 10.0
        if (speed > 100.0):
            speed = 100.0
        self._command("SMS," + str(speed))

    ## state
    #
    # FIXME: Not sure if this works anymore, I can't find this command in the
    #   manual for the ProScanIII stage.
    #
    # @return An array containing the status of each axis ("busy" or "idle").
    #
    def state(self):
        response = self._command("#")[0]
        state = []
        for i in range(len(response)):
            if response[i] == "1":
                state.append("busy")
            else:
                state.append("idle")
        return state

    ## zero
    #
    # Set the current position as the stage zero position.
    #
    def zero(self):
        self._command("P 0,0,0")

    ## zMoveTo
    #
    # @param z The z value to move to the (piezo) stage to.
    #
    def zMoveTo(self, z):
        self._command("<V " + str(z))

    ## zPosition
    #
    # @return The current z position of the (piezo) stage.
    def zPosition(self):
        zpos = self._command("<PZ")
        return zpos[1:]


## PriorNI
#
# National instruments based control.
#
class PriorNI(object):

    def __init__(self):
        self.scale = 1.0/25.0
        #self.ao_task = nicontrol.AnalogOutput("PCI-6713", 0)

    def shutDown(self):
        #self.ao_task.stopTask()
        #self.ao_task.clearTask()
        pass
        
    def zMoveTo(self, z):
        #self.ao_task.output(self.scale * z)
        #nicontrol.setAnalogLine("PCI-6713", 0, self.scale * z)
        nicontrol.setAnalogLine("PCIe-6259", 0, self.scale * z)

## PriorZ
#
# Encapsulates communication via RS-232 with a Prior Z piezo stage.
#
class PriorZ(Prior):

    ## __init__
    #
    # @param port (Optional) The RS-232 port to use, defaults to "COM1".
    # @param timeout (Optional) The time out value for communication, defaults to None.
    # @param baudrate (Optional) The communication baud rate, defaults to 9600.
    #
    def __init__(self, port = "COM1", timeout = None, baudrate = 9600):
        self.z_scale = 1.0

        # Connect to change baud.
        #Prior.__init__(self, port = port, timeout = timeout, baudrate = 9600)
        #self.changeBaudRate(baudrate)
        #self.shutDown()

        # Connect at correct baud.
        Prior.__init__(self, port = port, timeout = timeout, baudrate = baudrate)
        if not self.live:
            print "Failed to connect to Prior piezo controller."

    ## changeBaudRate
    #
    # Change communication baud rate.
    #
    # @param baudrate The communication baud rate.
    #
    def changeBaudRate(self, baudrate):
        self._command("BAUD " + str(baudrate))

    ## getBaudRate
    #
    # @return The current baud rate.
    #
    def getBaudRate(self):
        baudrate = self._command("BAUD")[0]
        return int(baudrate)

    ## zMoveRelative
    #
    # @param dz Amount to move piezo (in um).
    #
    def zMoveRelative(self, dz):
        self._command("U {0:.3f}".format(dz * self.z_scale))

    ## zMoveTo
    #
    # @param z Position to move piezo (in um).
    #
    def zMoveTo(self, z):
        self._command("V {0:.3f}".format(z * self.z_scale))

    ## zPosition
    #
    # @return The current z position of the piezo (in um).
    #
    def zPosition(self):
        zpos = self._command("PZ")[0]
        return float(zpos)/self.z_scale


## PriorFocus
#
# Encapsulates communication via RS-232 with a Prior focus drive motor.
#
class PriorFocus(PriorZ):

    ## __init__
    #
    # @param port (Optional) The RS-232 port to use, defaults to "COM1".
    # @param timeout (Optional) The time out value for communication, defaults to None.
    # @param baudrate (Optional) The communication baud rate, defaults to 9600.
    #
    def __init__(self, port = "COM1", timeout = None, baudrate = 9600):
        PriorZ.__init__(self, port = port, timeout = timeout, baudrate = baudrate)
        self.z_scale = 10.0
        if not self.live:
            print "Failed to connect to Prior focus motor controller."



#
# Testing
# 

if __name__ == "__main__":
    if 1:
        stage = Prior(port = "COM14")
        #stage.setVelocity(1.0, 1.0)
        #print stage._command("SMS")
        #print "enc:", stage._command("ENCODER,X")
        #print "res:", stage._command("RES,X")
        print stage._command("RES,S,1")
        print stage.position()

        for info in stage.info():
            print info

        if 0:
            print stage.getServo()
            stage.setServo(True)
            print stage.getServo()

        if 0:
            stage.changeFilter(1)
            stage.getFilter()

        if 0:
            stage.zero()
            print stage.position()
            stage.goAbsolute(500, 500)
            time.sleep(5)
            print stage.position()
            stage.goAbsolute(0, 0)
            time.sleep(5)
            print stage.position()
            stage.goRelative(-500, -500)
            time.sleep(5)
            print stage.position()
            stage.goAbsolute(0, 0)
            time.sleep(5)
            print stage.position()

        if 0:
            stage.zMoveTo(51.2)
            print stage.zPosition()
            stage.zMoveTo(50.0)
            print stage.zPosition()

    if 0:
        stage = PriorFocus(port = "COM1")
        for info in stage.info():
            print info

        stage.zMoveRelative(5.0)
        print stage.zPosition()
        stage.zMoveRelative(-5.0)
        print stage.zPosition()

    if 0:
        piezo = PriorZ(port = "COM19")
        for info in piezo.info():
            print info

        piezo.zMoveTo(40.0)
        print piezo.zPosition()
        print piezo.getBaudRate()
        

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
