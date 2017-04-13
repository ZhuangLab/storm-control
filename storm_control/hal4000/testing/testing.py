#!/usr/bin/env python
"""
The HAL testing module, basically this just sends messages
to HAL and verifies that response / behavior is correct.

Testing is done by sub-classing this module and providing
it with a series of test actions, a little bit like what
Dave does when controlling HAL.

Hazen 04/17
"""

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


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
