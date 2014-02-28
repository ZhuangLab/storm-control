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
                 com_port = 3,
                 pump_ID = 30,
                 simulate = False,
                 verbose = True,
                 serial_verbose = False):

        # Define attributes
        self.com_port = com_port
        self.pump_ID = pump_ID
        self.verbose = verbose
        self.simulate = simulate
        self.serial_verbose = serial_verbose
        
        # Create serial port
        if not self.simulate:
            self.serial = serial.Serial(port = self.com_port,
                                        baudrate = 19200,
                                        bytesize = serial.EIGHTBITS,
                                        parity = serial.PARITY_EVEN,
                                        stopbits = serial.STOPBITS_ONE,
                                        timeout = 0.1)

        # Define important serial characters
        self.acknowledge = '\x06'
        self.carriage_return = '\x0D'
        self.ready_signal = '\x0A'
        self.negative_acknowledge = '\x15'
        self.line_feed = '\x0A'
        self.pound_sign = '\x23'
        self.disconnect_signal = '\xFF'
        self.message_complete_flag = 128
        self.max_attempt_number = 10

        # Define initial pump status
        self.flow_status = "Stopped"
        self.speed = 0.0
        self.direction = "Forward"
        self.control_status = "Keypad"
        self.auto_start = "Disabled"
        self.error_status = "No Error"
        self.identification = ""
        
        # Configure device
        self.connectPump()

    # ------------------------------------------------------------------------------------
    # Connect Pump
    # ------------------------------------------------------------------------------------ 
    def connectPump(self):
        if not self.simulate:
            print "----------------------------------------------------------------------"
            print "Opening a Rainin RP1 Pump"
            self.write(self.disconnect_signal)
            time.sleep(0.1)
            self.read(1)
            self.write(chr(self.pump_ID + 128))
            self.read(1)
        else:
            print "Simulating a Rainin RP1 Pump"

        print "   " + "COM Port: " + str(self.com_port)
        print "   " + "Pump ID: " + str(self.pump_ID)

        # Place pump in remote control
        self.enableRemoteControl(True)
        
        # Determine Initial Pump Status
        self.identification = self.getPumpIdentification()
        self.requestStatus()
        self.readDisplay()
            
    # ------------------------------------------------------------------------------------
    # Disconnect Pump
    # ------------------------------------------------------------------------------------ 
    def disconnectPump(self):
        if not self.simulate:
            if self.control_status == "Remote": self.enableRemoteControl(False)
            self.write(self.disconnect_signal)
 
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
    # Toggle Remote Control Status
    # ------------------------------------------------------------------------------------ 
    def enableRemoteControl(self, remote_control):
        if not self.simulate:
            if remote_control:
                self.sendBufferedCommand("L")
            else:
                self.sendBufferedCommand("U")
        else:
            if remote_control: self.control_status == "Remote"
            else: self.control_status == "Keypad"
        if self.verbose:
            if self.control_status == "Remote":
                print "Enabled Remote Control"
            elif self.control_status == "Keypad":
                print "Disabled Remote Control"
            else:
                print "Unknown Status"
            
    # ------------------------------------------------------------------------------------
    # Get Pump Identification
    # ------------------------------------------------------------------------------------ 
    def getPumpIdentification(self):
        if self.verbose: print "Requesting Pump ID"
        if not self.simulate:
            message = self.sendImmediateCommand("%")
            self.identification = message
        else:
            self.identification = "Simulated"
        return self.identification
    
    # ------------------------------------------------------------------------------------
    # Return the status of the pump
    # ------------------------------------------------------------------------------------ 
    def getStatus(self):
        # Update the status from the current display
        self.readDisplay()
        # Update the status from a status inquiry
        self.requestStatus()

        return (self.flow_status, self.speed, self.direction,
                self.control_status, self.auto_start, self.error_status)

    # ------------------------------------------------------------------------------------
    # Get Rainin Status from Current Display
    # ------------------------------------------------------------------------------------ 
    def readDisplay(self):
        message = []
        if not self.simulate:
            message = self.sendImmediateCommand("R")

            # Parse direction and movement
            direction = {" ": "Not Running", "+": "Forward", "-": "Reverse"}.get(message[0], "Unknown")
            if direction == "Not Running":
                self.flow_status = "Stopped"
            elif direction == "Forward":
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

    # ------------------------------------------------------------------------------------
    # Determine the Rainin Status
    # ------------------------------------------------------------------------------------ 
    def requestStatus(self):
        message = []
        if not self.simulate:
            message = self.sendImmediateCommand("?")
            
            # Parse Control Status
            self.control_status = {"K": "Keypad", "R": "Remote"}.get(message[0], "Unknown")

            # Parse Error Status
            self.error_status = {" ": "No Error", "S": "Stop Issued"}.get(message[1], "Unknown")

            # Parse Direction
            self.direction = {"F": "Forward", "B": "Reverse"}.get(message[2], "Unknown")

            # Parse Flow
            self.flow_status = {"S": "Stopped", "F": "Flowing"}.get(message[3], "Unknown")

    # ------------------------------------------------------------------------------------
    # Overload String Representation Conversion
    # ------------------------------------------------------------------------------------ 
    def __str__(self):
        base_string = "Rainin RP1 Class: \n"
        base_string += "    " + "Pump Information: " + str(self.identification) + "\n"
        base_string += "    " + "PortID: " + str(self.pump_ID) + "\n"
        base_string += "    " + "COM Port: " + str(self.com_port) + "\n"
        base_string += "    " + "Flow Status: " + str(self.flow_status) + "\n"
        base_string += "    " + "Flow Speed: " + str(self.speed) + "\n"
        base_string += "    " + "Flow Direction: " + str(self.direction) + "\n"
        base_string += "    " + "Control Status: " + str(self.control_status) + "\n"
        base_string += "    " + "Auto Start: " + str(self.auto_start) + "\n"
        base_string += "    " + "Error: " + str(self.error_status) + "\n"

        return base_string

    # ------------------------------------------------------------------------------------
    # Send Buffered Command
    # ------------------------------------------------------------------------------------ 
    def sendBufferedCommand(self, command_string):
        # Compose command message
        command_message = command_string + self.carriage_return;

        # Poll pump to determine if ready for buffered command
        ready = False
        attempt_number = 0
        while not ready:
            self.write(self.line_feed)
            response = self.read(1)
            if response == self.ready_signal:
                ready = True
                self.read(10) # Clear buffer
                if self.serial_verbose: print "Received Ready Signal"
            else:
                attempt_number += 1
                if self.serial_verbose: print "Received Busy Signal"
            if attempt_number > self.max_attempt_number:
                ready = True
                print "Error in sending buffered command: Pump not ready"
        
        # Write buffered command
        attempt_number = 0
        for character in command_message:
            received = False
            while not received:
                self.write(chr(ord(character)))
                response = self.read(1)
                if response == character:
                    received = True
                else:
                    if self.verbose: print "Error in transmission of " + str((character, ''))

        # Update the pump status after a buffered command
        self.getStatus()
        
    # ------------------------------------------------------------------------------------
    # Send Immediate Command
    # ------------------------------------------------------------------------------------ 
    def sendImmediateCommand(self, command_letter):
        # Write single letter command
        self.write(chr(ord(command_letter)))

        # Get response
        message = []
        done = False
        attempt_number = 0
        while not done:
            response = self.read(1)
            
            if ord(response) > 128:
                done = True
                message.append( chr(ord(response)-128))
            else:
                message.append(response)
                self.write(chr(ord(self.acknowledge)))
                   
        return ''.join(message) # Convert list of char to string
    
    # ------------------------------------------------------------------------------------
    # Set Flow Direction: True = Forward; False = Backward
    # ------------------------------------------------------------------------------------ 
    def setFlowDirection(self, forward):
        if not self.simulate:
            if forward: direction_message = "jF"
            else: direction_message = "jB"

            self.sendBufferedCommand(direction_message)

            # Check status to see if the desired change was made
            ## NEED CODE HERE
            
        if forward: self.direction = "Forward"
        else: self.direction = "Reverse"
        if self.verbose:
            print "   " + "Set Direction: " + str(self.direction)
        return True
    
    # ------------------------------------------------------------------------------------
    # Set Speed in Rotations per Minute
    # ------------------------------------------------------------------------------------ 
    def setSpeed(self, rotation_speed):
        if not self.simulate:
            # Check bounds
            if rotation_speed >= 0 and rotation_speed <= 48:
                # Convert rotation speed to the rotation integer that will be sent
                rotation_int = int(rotation_speed*100)
                rotation_message = "R" + ("%04d" % rotation_int)
                self.sendBufferedCommand(rotation_message)

                # Check status to see if the desired change was made
                ## NEED CODE HERE

            else:
                print "The provided speed, " + rotation_speed + ", is too large"
                return False

        if rotation_speed >= 0 and rotation_speed <= 48:
            if self.verbose:
                print "   " + "Set Speed: " + str(self.speed)
        return True

    # ------------------------------------------------------------------------------------
    # Start pump
    # ------------------------------------------------------------------------------------ 
    def startFlow(self, speed, direction = "Forward"):
        if self.verbose: print "Starting pump"

        # Handle the reverse direction case
        if not (self.direction == direction):
            self.setSpeed(0.0) # Stop pump then set direction
            if direction == "Forward": self.setFlowDirection(True)
            else: self.setFlowDirection(False)
        
        # Set speed
        self.setSpeed(speed)
        # Set direction (and start pump if stopped)
        if direction == "Forward": self.setFlowDirection(True)
        elif direction == "Reverse": self.setFlowDirection(False)
        else: return False

        if self.simulate:
            self.flow_status = "Flowing"
        return True

    # ------------------------------------------------------------------------------------
    # Stop Pump
    # ------------------------------------------------------------------------------------ 
    def stopFlow(self):
        if self.verbose: print "Stopping pump"
        self.setSpeed(0.0)
        if self.simulate:
            self.flow_status = "Stopped"
        return True

    # ------------------------------------------------------------------------------------
    # Write to Serial Port
    # ------------------------------------------------------------------------------------ 
    def write(self, message):
        self.serial.write(message)
        if self.serial_verbose: print "Wrote: " + str(("", message))

    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------ 
    def read(self, num_char):
        response = self.serial.read(num_char)
        if self.serial_verbose: print "Read: " + str(("", response))
        return response
    
# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if __name__ == '__main__':

    rainin = RaininRP1(com_port = 4, pump_ID = 30, simulate = False, verbose = True, serial_verbose = False)
    print rainin

    rainin.stopFlow()
    time.sleep(5)
    print rainin
    rainin.startFlow(10.00, direction = "Forward")
    time.sleep(5)
    print rainin

    rainin.stopFlow()
    time.sleep(5)
    print rainin

    rainin.startFlow(5.00, direction = "Reverse")
    time.sleep(5)
    print rainin

    rainin.startFlow(10.00, direction = "Reverse")
    time.sleep(5)
    print rainin

    rainin.startFlow(10.00, direction = "Forward")
    time.sleep(5)
    print rainin

    rainin.stopFlow()
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
