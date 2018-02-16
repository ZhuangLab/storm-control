#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# The basic I/O class for a Gibson peristaltic pump
# ----------------------------------------------------------------------------------------
# George Emanuel with modifications by Jeff Moffitt
# 11/16/15
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import serial
import time

acknowledge = '\x06'
start = '\x0A'
stop = '\x0D'

# ----------------------------------------------------------------------------------------
# GlisonMP3 Class Definition
# ----------------------------------------------------------------------------------------
class APump():
    def __init__(self,
                 parameters = False):

        # Define attributes
        self.com_port = parameters.get("pump_com_port", "COM3")
        self.pump_ID = parameters.get("pump_ID", 30)
        self.verbose = parameters.get("verbose", True)
        self.simulate = parameters.get("simulate_pump", True)
        self.serial_verbose = parameters.get("serial_verbose", False)
        self.flip_flow_direction = parameters.get("flip_flow_direction", False)
        
        # Create serial port
        self.serial = serial.Serial(port = self.com_port, 
                                    baudrate = 19200, 
                                    parity= serial.PARITY_EVEN, 
                                    bytesize=serial.EIGHTBITS, 
                                    stopbits=serial.STOPBITS_TWO, 
                                    timeout=0.1)

        # Define initial pump status
        self.flow_status = "Stopped"
        self.speed = 0.0
        self.direction = "Forward"
        
        self.disconnect()
        self.enableRemoteControl(1)
        self.startFlow(self.speed, self.direction)
        self.identification = self.getIdentification()

    def getIdentification(self):
        return self.sendImmediate(self.pump_ID, "%")

    def enableRemoteControl(self, remote):
        if remote:
            self.sendBuffered(self.pump_ID, "SR")
        else:
            self.sendBuffered(self.pump_ID, "SK")

    def readDisplay(self):
        return self.sendImmediate(self.pump_ID, "R")

    def getStatus(self):
        message = self.readDisplay()

        if self.flip_flow_direction:
            direction = {" ": "Not Running", "-": "Forward", "+": "Reverse"}.\
                    get(message[0], "Unknown")
        else:
            direction = {" ": "Not Running", "+": "Forward", "-": "Reverse"}.\
                    get(message[0], "Unknown")
        
        status = "Stopped" if direction == "Not Running" else "Flowing"

        control = {"K": "Keypad", "R": "Remote"}.get(message[-1], "Unknown")

        auto_start = "Disabled"

        speed = float(message[1:len(message) - 1])

        return (status, speed, direction, control, auto_start, "No Error")

    def close(self):
        self.enableRemoteControl(0)

    def setFlowDirection(self, forward):
        if self.flip_flow_direction:
            if forward:
                self.sendBuffered(self.pump_ID, "K<")
            else:
                self.sendBuffered(self.pump_ID, "K>")
        else:
            if forward:
                self.sendBuffered(self.pump_ID, "K>")
            else:
                self.sendBuffered(self.pump_ID, "K<")
    
    def setSpeed(self, rotation_speed):
        if rotation_speed >= 0 and rotation_speed <= 48:
            rotation_int = int(rotation_speed*100)
            self.sendBuffered(self.pump_ID, "R" + ("%04d" % rotation_int))

    def startFlow(self, speed, direction = "Forward"):
        self.setSpeed(speed)
        self.setFlowDirection(direction == "Forward")

    def stopFlow(self):
        self.setSpeed(0.0)
        return True

    def sendImmediate(self, unitNumber, command):
        self.selectUnit(unitNumber)
        self.sendString(command[0])
        newCharacter = self.getResponse()
        response = ""
        while not (ord(newCharacter) & 0x80):
            response += newCharacter.decode()
            self.sendString(acknowledge)
            newCharacter = self.getResponse()

        response += chr(ord(newCharacter) & ~0x80)
        self.disconnect()

        return response

    def sendBuffered(self, unitNumber, command):
        self.selectUnit(unitNumber)
        self.sendAndAcknowledge(start + command + stop)
        self.disconnect()

    def disconnect(self):
        self.sendAndAcknowledge('\xff')

    def selectUnit(self, unitNumber):
        devSelect = chr(0x80 | unitNumber)
        self.sendString(devSelect) 

        return self.getResponse() == devSelect

    def sendAndAcknowledge(self, string):
        for i in range(0, len(string)):
            self.sendString(string[i])
            self.getResponse()

    def sendString(self, string):
        self.serial.write(string.encode())

    def getResponse(self):
        return self.serial.read()
        #return self.serial.read().decode()



