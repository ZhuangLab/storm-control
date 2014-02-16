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
                 verbose = False):

        # Define attributes
        self.COM_port = COM_port
        self.pump_ID = pump_ID
        self.verbose = verbose
        self.simulate = simulate

        # Create serial port
        if not self.simulate:
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
        self.read_length = 64
        self.message_complete_flag = 128

        # Configure device
        self.disconnectPump()
        self.connectPump()
        
    # ----------------------------------------------------------------------------------------
    # getStatus(pump_ID)
    # ----------------------------------------------------------------------------------------
    # Return the status of the pump

    # ----------------------------------------------------------------------------------------
    # resetChain()
    # ----------------------------------------------------------------------------------------
    # Reset the pump chain

    # ----------------------------------------------------------------------------------------
    # setStatus
    # ----------------------------------------------------------------------------------------
    # Set the pump status display 


    # ------------------------------------------------------------------------------------
    # Close Serial Port
    # ------------------------------------------------------------------------------------ 
    def close(self):
        if not self.simulate:
            self.serial.close()
            if self.verbose: print "Closed Rainin RP1 communication"
        else: ## simulation code
            if self.verbose: print "Closed Simulated Raining RP1"

    # ------------------------------------------------------------------------------------
    # Send Immediate Command
    # ------------------------------------------------------------------------------------ 
    def sendImmediateCommand(self, command):
        # Write single letter command
        self.serial.write(command)
        # Wait >20 ms
        time.sleep(0.1)
        # Read buffer
        message = []
        done = False
        while not done:
            response = self.serial.read(1)
            done = ord(response) and self.message_complete_flag
            if not done:
                message.append(response)
            else
                message.append(chr(ord(response) - self.message_complete_flag))
        return (message, True)

    # ------------------------------------------------------------------------------------
    # Send Buffered Command
    # ------------------------------------------------------------------------------------ 
    def sendBufferedCommand(self, command)
        

    # ------------------------------------------------------------------------------------
    # Read from Serial Port
    # ------------------------------------------------------------------------------------
    def read(self):
        response = self.serial.read(self.read_length)
        if self.verbose:
            print "Received: " + str((response, ""))
        return response
