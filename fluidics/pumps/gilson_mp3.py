import serial
import time

acknowledge = '\x06'
start = '\x0A'
stop = '\x0D'


class GilsonMP3():

    def __init__(self, com_port = "COM20"):

        self.pump_ID = 30
        
        self.serial = serial.Serial(port = "COM22", 
                baudrate = 19200, 
                parity= serial.PARITY_EVEN, 
                bytesize=serial.EIGHTBITS, 
                stopbits=serial.STOPBITS_TWO, 
                timeout=0.1)

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
            response += newCharacter
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
        self.serial.write(string)

    def getResponse(self):
        return self.serial.read()



