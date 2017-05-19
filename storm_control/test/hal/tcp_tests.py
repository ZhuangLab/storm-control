#!/usr/bin/env python
import os

import storm_analysis.sa_library.datareader as datareader

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test


#
# Test "Check Focus Lock" message.
#
#
# Test "Set Lock Target" message.
#
class CheckFocusLockAction1(testActionsTCP.CheckFocusLock):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("focus_status"))
        
class CheckFocusLock1(testing.TestingTCP):
    """
    Check that the focus lock returns that it is locked.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActions.Timer(100),
                             CheckFocusLockAction1(focus_scan = False,
                                                   num_focus_checks = 5)]

class CheckFocusLockAction2(testActionsTCP.CheckFocusLock):

    def checkMessage(self, tcp_message):
        assert not (tcp_message.getResponse("focus_status"))

class CheckFocusLock2(testing.TestingTCP):
    """
    Check that the focus lock returns that it is not locked. Note that
    moving the stage x um offsets the locked center position by x um.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActionsTCP.MoveStage(x = 10, y = 0),
                             testActions.Timer(200),
                             CheckFocusLockAction2(focus_scan = False,
                                                   num_focus_checks = 5)]
        
class CheckFocusLock3(testing.TestingTCP):
    """
    Check that the focus lock can find lock again.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActionsTCP.MoveStage(x = -6, y = 0),
                             testActions.Timer(200),
                             CheckFocusLockAction1(focus_scan = True,
                                                   num_focus_checks = 5,
                                                   scan_range = 20)]
        
class CheckFocusLock4(testing.TestingTCP):
    """
    Check that the focus lock can't find lock again 
    if the scan range is too small.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActionsTCP.MoveStage(x = -6, y = 0),
                             testActions.Timer(200),
                             CheckFocusLockAction2(focus_scan = True,
                                                   num_focus_checks = 5,
                                                   scan_range = 4)]

class CheckFocusLockAction3(testActionsTCP.CheckFocusLock):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("duration") == 2)
        
class CheckFocusLock5(testing.TestingTCP):
    """
    Check that the focus lock returns a duration in test mode.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = False),                             
                             CheckFocusLockAction3(focus_scan = False,
                                                   num_focus_checks = 5,
                                                   test_mode = True)]
        

#
# Test "Get Mosaic Settings" message.
#
class GetMosaicSettingsAction1(testActionsTCP.GetMosaicSettings):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("obj1") == "100x,0.160,0.0,0.0")

class GetMosaicSettings1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetMosaicSettingsAction1()]

class GetMosaicSettingsAction2(testActionsTCP.GetMosaicSettings):

    def checkMessage(self, tcp_message):
        pass
        
class GetMosaicSettings2(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetMosaicSettingsAction2(test_mode = True)]


#
# Test "Get Objective" message.
#
class GetObjectiveAction1(testActionsTCP.GetObjective):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("objective") == "100x")

class GetObjective1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetObjectiveAction1()]

#
# Test "Get Stage Position" message.
#
class GetStagePositionAction1(testActionsTCP.GetStagePosition):

    def __init__(self, x = 0.0, y = 0.0, **kwds):
        super().__init__(**kwds)
        self.x = x
        self.y = y
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("stage_x") == self.x)
        assert(tcp_message.getResponse("stage_y") == self.y)

class GetStagePosition1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetStagePositionAction1()]

#
# Test "Move Stage" message.
#
class MoveStageAction1(testActionsTCP.MoveStage):
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("duration") == 1)

class MoveStage1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        #
        # We have to pause for 500ms so that the stage
        # a chance to update it's position.
        #
        x = 10.0
        y = 10.0
        self.test_actions = [testActionsTCP.MoveStage(x = x, y = y),
                             testActions.Timer(500),
                             GetStagePositionAction1(x = x, y = y),
                             MoveStageAction1(test_mode = True, x = 0.0, y = 0.0)]

#
# Test handling of messages that are not supported.
#
class NoSuchMessageAction1(testActionsTCP.NoSuchMessage):

    def checkMessage(self, tcp_message):
        assert tcp_message.hasError()

class NoSuchMessage1(testing.TestingTCP):
    """
    Test sending a message that HAL does not handle.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [NoSuchMessageAction1()]
#                             test_mode = True]

#
# Test "Set Focus Lock Mode" message.
#
class SetFocusLockModeAction1(testActionsTCP.SetFocusLockMode):

    def checkMessage(self, tcp_message):
        assert not tcp_message.hasError()

class SetFocusLockMode1(testing.TestingTCP):
    """
    Test changing to "Always On" and starting the focus lock.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActions.Timer(2000)]

class SetFocusLockModeAction2(testActionsTCP.SetFocusLockMode):

    def checkMessage(self, tcp_message):
        assert tcp_message.hasError()

class SetFocusLockMode2(testing.TestingTCP):
    """
    Test changing trying to change to a mode that does not exist.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [SetFocusLockModeAction2(mode_name = "XYZZY")]

#
# Test "Set Lock Target" message.
#
class SetLockTarget1(testing.TestingTCP):
    """
    Test setting the lock target.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.ShowGUIControl(control_name = "focus lock"),
                             testActions.Timer(100),
                             SetFocusLockModeAction1(mode_name = "Always On",
                                                     locked = True),
                             testActions.Timer(1000),
                             testActionsTCP.SetLockTarget(lock_target = 0.5),
                             testActions.Timer(1000)]

#
# Test "Set Parameters" message.
#
class SetParametersAction1(testActionsTCP.SetParameters):

    def checkMessage(self, tcp_message):
        assert not tcp_message.hasError()
        
class SetParameters1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             SetParametersAction1(name_or_index = fname)]

class SetParametersAction2(testActionsTCP.SetParameters):

    def checkMessage(self, tcp_message):
        assert tcp_message.hasError()

class SetParameters2(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [SetParametersAction2(name_or_index = fname, test_mode = True)]
        
class SetParameters3(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [SetParametersAction2(name_or_index = fname)]
        
class SetParameters4(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             SetParametersAction1(name_or_index = fname, test_mode = True)]

#
# Test "Take Movie" message.
#
class TakeMovieAction1(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        movie = datareader.inferReader(os.path.join(self.directory, self.name + ".dax"))
        assert(movie.filmSize() == [512, 512, self.length])
        
class TakeMovie1(testing.TestingTCP):
    """
    Request a movie by TCP and verify that it is taken & the correct size.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename)]

class TakeMovieAction2(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        assert tcp_message.hasError()

class TakeMovie2(testing.TestingTCP):
    """
    Test TCP movie overwrite handling.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename),
                             TakeMovieAction2(directory = directory,
                                              length = 2,
                                              name = filename,
                                              overwrite = False),
                             TakeMovieAction2(directory = directory,
                                              length = 2,
                                              name = filename,
                                              overwrite = False,
                                              test_mode = True),
                             TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename)]

class TakeMovieAction3(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("disk_usage") == 25.0)
        assert(tcp_message.getResponse("duration") == 1.0)

class TakeMovie3(testing.TestingTCP):
    """
    Simple test of test_mode.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"
            
        self.test_actions = [TakeMovieAction3(directory = directory,
                                              length = 50,
                                              name = filename,
                                              test_mode = True)]

class TakeMovieAction4(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("disk_usage") == 6.25)
        assert(tcp_message.getResponse("duration") == 1.0)

class TakeMovie4(testing.TestingTCP):
    """
    Test test_mode w/ parameters request.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        p_name = "256x256"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(p_name + ".xml")),
                             TakeMovieAction4(directory = directory,
                                              length = 50,
                                              name = filename,
                                              parameters = p_name,
                                              test_mode = True)]

class TakeMovie5(testing.TestingTCP):
    """
    Test test_mode w/ parameters request.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"
        self.test_actions = [TakeMovieAction3(directory = directory,
                                              length = 50,
                                              name = filename,
                                              parameters = "default",
                                              test_mode = True)]

class TakeMovie6(testing.TestingTCP):
    """
    Request a movie by TCP with parameters that exist.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename,
                                              parameters = "default")]

class TakeMovieAction7(testActionsTCP.TakeMovie):

    def checkMessage(self, tcp_message):
        movie = datareader.inferReader(os.path.join(self.directory, self.name + ".dax"))
        assert(movie.filmSize() == [256, 256, self.length])

class TakeMovie7(testing.TestingTCP):
    """
    Request a movie by TCP with parameters that exist but that 
    are not the current parameters.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)

        p_name = "256x256"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(p_name + ".xml")),            
                             TakeMovieAction7(directory = directory,
                                              length = 5,
                                              name = filename,
                                              parameters = p_name)]

class TakeMovie8(testing.TestingTCP):
    """
    Request a movie by TCP with parameters that don't exist (test_mode).
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)

        p_name = "256x256"
        self.test_actions = [TakeMovieAction2(directory = directory,
                                              length = 5,
                                              name = filename,
                                              parameters = p_name,
                                              test_mode = True)]

class TakeMovie9(testing.TestingTCP):
    """
    Request a movie by TCP with parameters that don't exist.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)

        p_name = "256x256"
        self.test_actions = [TakeMovieAction2(directory = directory,
                                              length = 5,
                                              name = filename,
                                              parameters = p_name)]        


