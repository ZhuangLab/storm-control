#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A basic class for the control of the PSD4 syringe pump from Hamilton
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 11/20/21
# jeffrey.moffitt@childrens.harvard.edu
#
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time
import serial

class APump():
    def __init__(self,
                 parameters = False):

        # Define attributes
        self.com_port = parameters.get("pump_com_port", "COM3")
        self.pump_ID = parameters.get("pump_ID", "PSD4")
        self.verbose = parameters.get("verbose", True)
        self.simulate = parameters.get("simulate_pump", False)
        self.serial_verbose = parameters.get("serial_verbose", False)
        self.high_res_mode = parameters.get("high_res", True)
        self.syringe_volume = parameters.get("syringe_volume", 12.5)
        self.syringe_type = parameters.get("syringe_type", "standard")
        
        self.min_velocity_in_steps_s = 2
        self.max_velocity_in_steps_s = 10000
        self.min_stroke_in_steps = 0
        self.max_stroke_in_steps = None

        # Check syringe type
        if self.syringe_type == "standard":
            self.high_res_step = 24000.0
            self.low_res_step = 3000.0
        elif self.syringe_type == "smooth_flow":
            self.high_res_step = 192000.0
            self.low_res_step = 24000.0
        else:
            print("The provided syringe type for the PSD4 is not valid")
            assert False

        # Define the resolution mode
        if self.high_res_mode:
            self.max_stroke_in_steps = self.high_res_step
        else:
            self.max_stroke_in_steps = self.low_res_step
           
        self.steps_to_volume = self.syringe_volume/self.max_stroke_in_steps
        
        # Create serial port
        self.serial = serial.Serial(port = self.com_port, 
                                    timeout=0.1)

        # Define initial pump status
        self.flow_status = "Stopped"
        self.speed = 0.0
        self.num_ports = 0
        
        # Configure pump
        self.configurePump()
        self.identification = "PSD4"
        
        # Report configuration
        print("--------------------------------")
        print("Configured PSD4 Syringe Pump")
        print("   PSD4 Type: " + str(self.syringe_type))
        print("   Syringe Volume: " + str(self.syringe_volume) + " mL")
        print("   High Res Mode: " + str(self.high_res_mode))
        print("   Steps for Full Fill: " + str(self.max_stroke_in_steps))
        print("   Minimum Speed: " + str(self.min_velocity_in_steps_s * self.syringe_volume * (4/self.high_res_step) * 60 ) + " mL/min")

    def initializePump(self):
        message = "/1ZR\r"
        self.write(message)
        response = self.read()
        
        if len(response) < 2:
            print("PSD4 not found")
            assert False

    def configurePump(self):
        
        # Determine the port configuration
        message = "/1?21000R\r"
        self.write(message)
        response = self.read()
        
        if len(response) < 2:
            assert False
        
        num_ports_dict = {'0': 3,
                          '1': 4,
                          '2': 3,
                          '3': 8,
                          '4': 4,
                          '6': 6}
        
        self.num_ports = num_ports_dict[chr(response[3])]
                
        # Set the resolution
        if self.high_res_mode:
            message = '/1N1R\r'
        else:
            message = '/1N0R\r'
            
        self.write(message)
        response = self.read()
        if len(response) < 2:
            assert False

        
    def getStatus(self):
        # Determine if is moving
        message = "/1Q\r"
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False
        
        response_char = chr(response[2])
        if response_char == '@':
            is_moving = True
        elif response_char == "`":
            is_moving = False
        else:
            print("Unknown response from PSD4")
            print(response)
            assert False
        
        # Determine the syringe position and return in mL
        message = '/1?R\r'
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False

        start_pos = 3
        end_pos = response.find('\x03'.encode())
        pos_in_units = float(response[start_pos:end_pos].decode())
        pos_in_mL = pos_in_units*self.steps_to_volume
        
        # Determine current speed
        message = '/1?2R\r'
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False

        start_pos = 3
        end_pos = response.find('\x03'.encode())
        vel_in_units = float(response[start_pos:end_pos].decode())
        vel_in_mLmin = vel_in_units*self.syringe_volume*60/(self.high_res_step/4)
    
        # Determine valve numerical position
        message = '/1?24000R\r'
        
        self.write(message)
        response = self.read()
    
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False

        start_pos = 3
        end_pos = response.find('\x03'.encode())
        valve_pos = int(response[start_pos:end_pos].decode())
        
        return (is_moving, pos_in_mL, vel_in_mLmin, valve_pos)
            
    def setPort(self, port_id):
        # Check to see if it is within the number of ports
        if port_id >= self.num_ports:
            print("An invalid port was requested for the PSD4")
            assert False
        
        # Set the port
        message = "/1h2500" + str(port_id+1) + "R\r"
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False
        
    def close(self):
        self.serial.close()
    
    def setSpeed(self, fill_speed_in_mLmin):
        
        # Convert the requested speed to steps per s
        fill_speed_in_mLs = fill_speed_in_mLmin/60
        new_speed_value = int((fill_speed_in_mLs/self.syringe_volume) * (self.high_res_step/4))
        
        # Coerce to the hardware limits
        if new_speed_value < self.min_velocity_in_steps_s:
            new_speed_value = self.min_velocity_in_steps_s
            print("Coerced pump speed to lowest value")
        
        if new_speed_value > self.max_velocity_in_steps_s:
            new_speed_value = self.max_velocity_in_steps_s
            print("Coerced pump speed to highest value")
        
        message = '/1V' + str(new_speed_value) + 'R\r'
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False

    def startFill(self, new_volume):
        # Define the volume
        new_step_pos = int(new_volume/self.steps_to_volume)
        
        # Coerce to the hardware limits
        if new_step_pos < self.min_stroke_in_steps:
            new_step_pos = self.min_stroke_in_steps
            print("Coerced pump fill to lowest value")
        
        if new_step_pos > self.max_stroke_in_steps:
            new_step_pos = self.max_stroke_in_steps
            print("Coerced pump fill to highest value")

        # Define and write the message
        message = '/1A' + str(new_step_pos) + 'R\r'
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False

    def stopFill(self):
        message = '/1TR\r'
        
        self.write(message)
        response = self.read()
        
        if len(response)<2:
            print("Unknown response from PSD4")
            assert False
    
    def read(self):
       # response = self.serial.readline().decode()
        response = self.serial.readline()

        if self.verbose:
            print("Received: " + str((response, "")))
        return response

    def write(self, message):
        self.serial.write(message.encode())
        if self.verbose:
            print("Wrote: " + message[:-1]) # Display all but final carriage return


#
# The MIT License
#
# Copyright (c) 2021 Moffitt Laboratory, Boston Children's Hospital
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

