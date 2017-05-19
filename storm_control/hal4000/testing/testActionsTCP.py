#!/usr/bin/env python
"""
Actions for TCP testing.

Hazen 04/17
"""

import storm_control.sc_library.tcpMessage as tcpMessage

import storm_control.hal4000.testing.testActions as testActions


class TestActionTCP(testActions.TestAction):
    """
    Base class for all TCP test actions.
    """
    def __init__(self, test_mode = False, **kwds):
        super().__init__(**kwds)
        self.tcp_message = None
        self.test_mode = test_mode

    def checkMessage(self, tcp_message):
        """
        Sub-class this to check that the TCP response 
        message is as expected.
        """
        pass
        
    def handleMessageReceived(self, tcp_message):
        """
        The default behavior as most actions are complete 
        when they get a response from HAL.
        """
        self.checkMessage(tcp_message)
        self.actionDone.emit()


class CheckFocusLock(TestActionTCP):
    """
    Check the focus lock and do a scan if it has lost lock.
    """
    def __init__(self,
                 focus_scan = None,
                 num_focus_checks = None,
                 scan_range = None,
                 z_center = None,
                 **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Check Focus Lock",
                                                 message_data = {"focus_scan" : focus_scan,
                                                                 "num_focus_checks" : num_focus_checks,
                                                                 "scan_range" : scan_range,
                                                                 "z_center" : z_center},
                                                 test_mode = self.test_mode)


class FindSum(TestActionTCP):
    """
    Check the focus lock sum and do a scan if it is below requested value.
    """
    def __init__(self,
                 min_sum = None,
                 **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Find Sum",
                                                 message_data = {"min_sum" : min_sum},
                                                 test_mode = self.test_mode)

        
class GetMosaicSettings(TestActionTCP):
    """
    Query HAL for the current mosaic settings.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Mosaic Settings",
                                                 test_mode = self.test_mode)


class GetObjective(TestActionTCP):
    """
    Query HAL for the current objective.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Objective",
                                                 test_mode = self.test_mode)

        
class GetStagePosition(TestActionTCP):
    """
    Query HAL for the current stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Stage Position",
                                                 test_mode = self.test_mode)


class MoveStage(TestActionTCP):
    """
    Tell HAL to move the XY stage.
    """
    def __init__(self, x = None, y = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                                 message_data = {"stage_x" : x,
                                                                 "stage_y" : y},
                                                 test_mode = self.test_mode)
        

class NoSuchMessage(TestActionTCP):
    """
    Send HAL an unsupported message.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "No Such Message",
                                                 test_mode = self.test_mode)

        
class SetFocusLockMode(TestActionTCP):
    """
    Technically this is only supposed to be used for testing.

    Tell HAL to change the (user) selected focus lock mode and locked status.
    """
    def __init__(self, mode_name = None, locked = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Set Focus Lock Mode",
                                                 message_data = {"mode_name" : mode_name,
                                                                 "locked" : locked},
                                                 test_mode = self.test_mode)


class SetLockTarget(TestActionTCP):
    """
    Set the focus lock (offset) target.
    """
    def __init__(self, lock_target = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Set Lock Target",
                                                 message_data = {"lock_target" : lock_target},
                                                 test_mode = self.test_mode)


class SetParameters(TestActionTCP):
    """
    Tell HAL to use a particular parameters file."
    """
    def __init__(self, name_or_index = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Set Parameters",
                                                 message_data = {"parameters" : name_or_index},
                                                 test_mode = self.test_mode)
        

class SetProgression(TestActionTCP):
    """
    Tell HAL to change something in the progressions dialog.
    """
    def __init__(self, filename = None, prog_type = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Set Progression",
                                                 message_data = {"filename" : filename,
                                                                 "type" : prog_type},
                                                 test_mode = self.test_mode)
        
        
class TakeMovie(TestActionTCP):
    """
    Tell HAL to take a movie.
    """
    def __init__(self,
                 directory = None,
                 length = None,
                 name = None,
                 overwrite = True,
                 parameters = None,
                 **kwds):
        super().__init__(**kwds)
        self.directory = directory
        self.length = length
        self.name = name
        self.parameters = parameters

        data_dict = {"directory" : self.directory,
                     "length" : self.length,
                     "name": self.name,
                     "overwrite" : overwrite}
        if parameters is not None:
            data_dict["parameters"] = parameters

        print(data_dict)
        
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                                 message_data = data_dict,
                                                 test_mode = self.test_mode)
