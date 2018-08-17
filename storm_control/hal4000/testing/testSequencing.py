#!/usr/bin/env python
"""
These are for testing that HAL modules process messages in
the expected FIFO fashion.

Hazen 03/18
"""
import time

import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class TestSimpleSequencing(halModule.HalModule):
    """
    This creates a bunch of message sequentially & quickly then checks
    that they are handled in the order received.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        self.processed_messages = ["tss1", "tss2"]

        # Borrowed this one from testing.testing.
        halMessage.addMessage("tests done",
                              validator = {"data" : None, "resp" : None})
                
        halMessage.addMessage("tss1",
                              validator = {"data" : None, "resp" : None})
        
        halMessage.addMessage("tss2",
                              validator = {"data" : None, "resp" : None})
        
        halMessage.addMessage("tss3",
                              validator = {"data" : None, "resp" : None})

    def processMessage(self, message):
        if message.isType("start"):
            self.sendMessage(halMessage.HalMessage(m_type = "tss1"))
            self.sendMessage(halMessage.HalMessage(m_type = "tss2"))
            self.sendMessage(halMessage.HalMessage(m_type = "tss3"))
            
        elif message.isType("tss1"):
            halModule.runWorkerTask(self, message, self.handleTSS1)

        elif message.isType("tss2"):
            halModule.runWorkerTask(self, message, self.handleTSS2)

        elif message.isType("tss3"):
            assert not ("tss2" in self.processed_messages)
            print(">> Okay", self.processed_messages)
            self.newMessage.emit(halMessage.HalMessage(source = self,
                                                       m_type = "tests done"))
            
    def handleTSS1(self):
        time.sleep(0.5)
        self.processed_messages.remove("tss1")

    def handleTSS2(self):
        time.sleep(0.2)
        assert not ("tss1" in self.processed_messages)
        self.processed_messages.remove("tss2")
        
