'''
A class for serial interface to an arduino to control TitanEZ chain.

George Emanuel
2/16/2018
'''
import serial
import string
import time

from storm_control.fluidics.valves.valve import AbstractValve

class TitanValve(AbstractValve):
    
    def __init__(self, com_port=2, verbose= False):

        self.com_port = com_port
        self.verbose = verbose
        self.read_length = 64

        self.serial = serial.Serial(port = self.com_port, 
                baudrate = 9600,
                timeout=0.5)
        #give the arduino time to initialize
        time.sleep(2)
        self.port_count = self.getPortCount()
        self.updateValveStatus()


    def getPortCount(self):
        self.write('N?')
        return int(self.read().strip(string.ascii_letters))

    def updateValveStatus(self):
        self.write('P?')
        response = self.read()
        if '!' in response:
            self.moving = True
        else:
            self.moving = False 
            self.current_position = int(response.strip(string.ascii_letters))

        return self.current_position, self.moving

    '''
    Ignores the direction, always moves in the direction to minimize the 
    move distance. ValveID is also ignored.
    '''
    def changePort(self, valve_ID, port_ID, direction = 0):
        if not self.isValidPort(port_ID):
            return False

        self.write('P ' + str(port_ID+1))

    def howManyValves(self):
        return 1

    def close(self):
        self.serial.close()

    def getDefaultPortNames(self, valve_ID):
        return ['Port ' + str(portID + 1) for portID in range(self.port_count)]

    def howIsValveConfigured(self, valve_ID):
        return str(self.port_count) + ' ports'

    def getStatus(self, valve_ID):
        position, moving = self.updateValveStatus()
        return ('Port ' + str(position), moving)

    def resetChain(self):
        pass

    def getRotationDirections(self, valve_ID):
        return ['Least distance']

    def isValidPort(self, port_ID):
        return port_ID < self.port_count

    def write(self, message):
        appendedMessage = message + '\r'
        self.serial.write(appendedMessage.encode())

    def read(self):
        inMessage = self.serial.readline().decode().rstrip()
        return inMessage
        
