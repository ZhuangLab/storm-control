#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# The basic I/O class for a Rainin RP1 peristaltic pump
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import serial
import sys
import time

# ----------------------------------------------------------------------------------------
# RaininRP1 Class Definition
# ----------------------------------------------------------------------------------------
class RaininRP1():
    def __init__(self,
                 COM_port = 3,
                 pump_ID = 30,
                 simulate = False,
                 verbose = True):

        # Define attributes
        self.COM_port = COM_port
        self.pump_ID = pump_ID
        self.verbose = verbose
        self.simulate = simulate
        
        # Create serial port
        if not self.simulate:
            print self.simulate
            self.serial = serial.Serial(port = self.COM_port,
                                        baudrate = 19200,
                                        bytesize = serial.EIGHTBITS,
                                        parity = serial.PARITY_EVEN,
                                        stopbits = serial.STOPBITS_ONE,
                                        timeout = 0.1)

        # Define important serial characters
        self.acknowledge = "\x06"
        self.carriage_return = "\x13"
        self.negative_acknowledge = "\x21"
        self.line_feed = '\x12'
        self.pound_sign = '\x35'
        self.disconnect_signal = '\x255'
        self.message_complete_flag = 128
        self.max_attempt_number = 10

        # Define initial pump status
        self.flow_status = "Stopped"
        self.speed = 0.0
        self.direction = "Forward"
        self.control_status = "Keyboard"
        self.auto_start = "Disabled"
        self.error_status = "No Error"
        self.pump_identification = ""
        
        # Configure device
        self.disconnectPump()
        self.connectPump()

    # ------------------------------------------------------------------------------------
    # Connect Pump
    # ------------------------------------------------------------------------------------ 
    def connectPump(self):
        # Connect (or simulate) Serial Connection
        if not self.simulate:
            print "Opening a Rainin RP1 Pump"
            self.serial.write(self.disconnect_signal)
            time.sleep(0.1)
            self.serial.write(str(self.pump_ID))
            
        else:
            print "Simulating a Rainin RP1 Pump"

        print "   " + "COM Port: " + str(self.COM_port)
        print "   " + "Pump ID: " + str(self.pump_ID)

        # Determine Initial Pump Status
        self.pump_identification = self.getPumpIdentification()
        response = self.getStatus()
        response = self.getMode()
            
    # ------------------------------------------------------------------------------------
    # Disconnect Pump
    # ------------------------------------------------------------------------------------ 
    def disconnectPump(self):
        if not self.simulate:
            self.serial.write(self.disconnect_signal)
 
    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def close(self):
        self.disconnectPump()
        if not self.simulate:
            self.serial.close()
            print "Closed Rainin RP1 communication"
        else: ## simulation code
            print "Closed Simulated Raining RP1"

    # ------------------------------------------------------------------------------------
    # Get Pump Identification
    # ------------------------------------------------------------------------------------ 
    def getPumpIdentification(self):
        if not self.simulate:
            message = self.sendImmediateCommand("%")
            self.pump_identification = message
        else:
            self.pump_identification = "Simulated"
        return self.pump_identification
    
    # ------------------------------------------------------------------------------------
    # Get Rainin Mode Status
    # ------------------------------------------------------------------------------------ 
    def getMode(self):
        message = []
        if not self.simulate:
            message = self.sendImmediateCommand("I")

            # Parse Control Status
            self.control_status = {"K": "Keypad", "R": "Remote"}.get(message[0], "Unknown")

            # Parse Error Status
            self.error_status = {" ": "No Error", "S": "Stop Issued"}.get(message[1], "Unknown")

            # Parse Direction
            self.direction = {"F": "Forward", "B": "Backwards"}.get(message[2], "Unknown")

            # Parse Flow
            self.flow_status = {"S": "Stopped", "F": "Flowing"}.get(message[3], "Unknown")
            
        return (self.control_status, self.error_status, self.direction, self.flow_status, message)

    # ------------------------------------------------------------------------------------
    # Read buffer
    # ------------------------------------------------------------------------------------ 
    def getResponse(self):
        message = []
        done = False
        while not done:
            response = self.serial.read(1)
            done = ord(response) and self.message_complete_flag
            if not done:
                message.append(response)
                # Request next message
                self.serial.wite(self.acknowledge)
            else:
                message.append(chr(ord(response) - self.message_complete_flag))
        return message

    # ------------------------------------------------------------------------------------
    # Get Rainin Status
    # ------------------------------------------------------------------------------------ 
    def getStatus(self):
        message = []
        if not self.simulate:
            message = self.sendImmediateCommand("R")

            # Parse direction and movement
            direction = {" ": "Not Running", "+": "Forward", "-": "Reverse"}.get(message[0], "Unknown")
            if directon == "Not Running":
                self.flow_status = "Stopped"
            elif directon == "Forward":
                self.flow_status = "Flowing"
                self.direction = "Forward"
            elif direction == "Reverse":
                self.flow_status = "Flowing"
                self.direction = "Reverse"
            
            # Parse control status
            self.control_status = {"K": "Keypad", "R": "Remote"}.get(message[6], "Unknown")

            # Parse autostart
            self.auto_start = {"*": "Enabled", " ": "Disabled"}.get(message[7], "Unknown")

            # Parse speed
            self.speed = float(message[1:5])

        return (self.direction, self.speed, self.control_status, self.auto_start, message)

    # ------------------------------------------------------------------------------------
    # Overload String Representation Conversion
    # ------------------------------------------------------------------------------------ 
    def __str__(self):
        base_string = "Rainin RP1 Class: \n"
        base_string += "    " + "Pump Information: " + self.pump_identification + "\n"
        base_string += "    " + "PortID: " + str(self.pump_ID) + "\n"
        base_string += "    " + "COM Port: " + str(self.COM_port) + "\n"
        base_string += "    " + "Flow Status: " + self.flow_status + "\n"
        base_string += "    " + "Flow Speed: " + str(self.speed) + "\n"
        base_string += "    " + "Flow Direction: " + self.direction + "\n"
        base_string += "    " + "Control Status: " + self.control_status + "\n"
        base_string += "    " + "Auto Start: " + self.auto_start + "\n"
        base_string += "    " + "Error: " + self.error_status + "\n"

        return base_string

    # ------------------------------------------------------------------------------------
    # Send Buffered Command
    # ------------------------------------------------------------------------------------ 
    def sendBufferedCommand(self, command_string):
        # Compose command message
        command_message = self.line_feed + command_string + self.carraige_return;

        # Write message
        attempt_number = 0
        done = False
        while not done:
            self.serial.write(command_message)
            time.sleep(0.1)
            response = self.serial.read(1)

            if response == self.line_feed:
                done = True
            elif response == self.pound_sign:
                attempt_number += 1
            else:
                if self.verbose:
                    print "Unexpected response when submitting message: " + command_string

            if attempt_number > self.max_attempt_number:
                done = True
        
        # Read response
        message = self.getResponse()
        return message
    
    # ------------------------------------------------------------------------------------
    # Send Immediate Command
    # ------------------------------------------------------------------------------------ 
    def sendImmediateCommand(self, command_letter):
        # Write single letter command
        self.serial.write(command_letter)
        # Wait >20 ms
        time.sleep(0.1)
        # Read response
        message = self.getResponse()
        return message

    # ------------------------------------------------------------------------------------
    # Set remote control: remote_control = True/Falses toggles between remote/keyboard
    # ------------------------------------------------------------------------------------ 
    def setRemoteControl(self, remote_control):
        if not self.simulate:
            if remote_control: control_string = "SR"
            else: control_string = "SK"
            
            response = sendBufferedCommand(rotation_message)

            if not (response == rotation_message):
                self.control_status = "Unknown"
                print "Error setting control status"
                return False

        if remote_control: self.control_status = "Remote"
        else: self.control_status = "Keyboard"

        return True
    # ------------------------------------------------------------------------------------
    # Set Flow Direction: True = Forward; False = Backward
    # ------------------------------------------------------------------------------------ 
    def setFlowDirection(self, forward):
        if not self.simulate:
            if forward: direction_message = "jF"
            else: direction_message = "jB"

            response = sendBufferedCommand(direction_message)

            if not (response == direction_message):
                self.direction = "Unknown"
                print "Error setting flow direction"
                return False
            
        if forward: self.direction = "Forward"
        else: self.direction = "Reverse"

        return True
    # ------------------------------------------------------------------------------------
    # Set Speed in Rotations per Minute
    # ------------------------------------------------------------------------------------ 
    def setSpeed(self, rotation_speed):
        if not self.simulate:
            # Check bounds
            if rotation_speed > 0 and rotation_speed <= 48:
                # Convert rotation speed to the rotation integer that will be sent
                rotation_int = int(rotation_speed*100)
                rotation_message = "R" + ("%04d" % rotation_int)
                response = sendBufferedCommand(rotation_message)

                if not (response == rotation_message):
                    print "Error setting rotation speed"
                    self.speed = -1
                    return False
            else:
                print "The provided speed, " + rotation_speed + ", is too large"
                return False

        if rotation_speed > 0 and rotation_speed <= 48:
            self.speed = rotation_speed

        return True
# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':
    rainin = RaininRP1(COM_port = 3, pump_ID = 30 ,simulate = True, verbose = True)
    print rainin
    rainin.setSpeed(10.00)
    rainin.setFlowDirection(False)
    rainin.setRemoteControl(True)
    print rainin.getStatus()
    print rainin.getMode()
    print rainin
    rainin.close()
    
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
