'''
Abstract class for controlling a hardware valve. Function names were derived from original valveChain and hamilton classes.

George Emanuel
2/16/2018
'''
from abc import ABC, abstractmethod


class AbstractValve(ABC):

    @abstractmethod
    def changePort(self, valve_ID, port_ID, direction = 0):
        pass

    @abstractmethod
    def howManyValves(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def getDefaultPortNames(self, valve_ID):
        pass

    @abstractmethod
    def howIsValveConfigured(self, valve_ID):
        pass

    @abstractmethod
    def getStatus(self, valve_ID):
        pass

    @abstractmethod
    def resetChain(self):
        pass

    @abstractmethod
    def getRotationDirections(self, valve_ID):
        pass
