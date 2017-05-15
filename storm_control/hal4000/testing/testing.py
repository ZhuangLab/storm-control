#!/usr/bin/env python
"""
The HAL testing module, basically this just sends messages
to HAL and verifies that response / behavior is correct.

Testing is done by sub-classing this module and providing
it with a series of test actions, a little bit like what
Dave does when controlling HAL.

Hazen 04/17
"""

import storm_control.sc_library.tcpClient as tcpClient

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP


class Testing(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.all_modules = None
        self.current_action = None
        self.test_actions = []

        # This message type is just a place holder.
        halMessage.addMessage("na",
                              validator = {"data" : None, "resp" : None})
        
        # This message is sent but does not do anything.
        halMessage.addMessage("noop",
                              validator = {"data" : None, "resp" : None})

        # This message is sent when all the tests finish. HAL should
        # close when it gets this message.
        halMessage.addMessage("tests done",
                              validator = {"data" : None, "resp" : None})

    def handleActionDone(self):

        #
        # If there are no more actions, send the 'tests done' message
        # which will cause HAL to close.
        #
        if (len(self.test_actions) == 0):
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "tests done"))

        #
        # Otherwise start the next action.
        #
        else:            
            if self.current_action is not None:
                self.current_action.actionDone.disconnect()
            self.current_action = self.test_actions[0]
            self.test_actions = self.test_actions[1:]

            self.current_action.start()
            self.current_action.actionDone.connect(self.handleActionDone)
            message = halMessage.HalMessage(source = self.all_modules[self.current_action.getSourceName()],
                                            m_type = self.current_action.getMessageType(),
                                            data = self.current_action.getMessageData(),
                                            finalizer = self.current_action.finalizer)
            self.current_action.setMessage(message)
            self.newMessage.emit(message)

    def handleResponses(self, message):

        if message.hasResponses():
            if message.isType(self.current_action.getResponseFilter()):
                self.current_action.handleResponses(message)

    def processMessage(self, message):

        if message.isType("configure1"):
            self.all_modules = message.getData()["all_modules"]
            
        elif message.isType("start"):
            self.handleActionDone()

        if self.current_action is not None:
            if message.isType(self.current_action.getMessageFilter()):
                self.current_action.handleMessage(message)


class TestingTCP(Testing):
    """
    This adds the ability to test HAL's handling of TCP commands.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.hal_client = None

    def handleActionDone(self):
        
        # This is little fiddly as it needs to handle both
        # TestAction and TestActionTCP actions.

        # If there are no more actions, close the TCP connection to HAL.
        done = False
        if (len(self.test_actions) == 0):
            self.hal_client.stopCommunication()
            self.hal_client.close()
            done = True

        # Super class handles TestActions. Note that for TestActionTCP
        # this will send a "noop" message through HAL's queue.
        super().handleActionDone()

        # Check if this TestActionTCP and we need to send a TCPMessage.
        if not done and isinstance(self.current_action, testActionsTCP.TestActionTCP):
            self.hal_client.sendMessage(self.current_action.tcp_message)

    def handleMessageReceived(self, tcp_message):
        """
        Handle a TCP (response) message from HAL.
        """
        self.current_action.handleMessageReceived(tcp_message)
        
    def processMessage(self, message):

        if message.isType("start"):
            self.hal_client = tcpClient.TCPClient(port = 9000,
                                                  server_name = "HAL",
                                                  verbose = False)
            self.hal_client.messageReceived.connect(self.handleMessageReceived)
            self.hal_client.startCommunication()

        super().processMessage(message)
