#!/usr/bin/env python
"""
This parses a log file series (i.e. log, log.1, log.2, etc..) and
outputs timing and call frequency information for HAL messages.

Hazen 5/18
"""
from datetime import datetime
import os


pattern = '%Y-%m-%d %H:%M:%S,%f'


class Message(object):
    """
    Storage for the timing of a single message.
    """
    def __init__(self, m_type = None, source = None, time = None, **kwds):
        super().__init__(**kwds)
        self.m_type = m_type
        self.processing_time = None
        self.queued_time = None
        self.n_workers = 0
        self.source = source
        
        self.temp = self.parseTime(time)

    def getNWorkers(self):
        """
        Return the number of workers (QRunnables) that were employed
        to process this message.
        """
        return self.n_workers
        
    def getProcessingTime(self):
        """
        Return time to process in seconds.
        """
        return self.processing_time
        
    def getQueuedTime(self):
        """
        Return time queued in seconds.
        """
        return self.queued_time

    def getSource(self):
        """
        Returns the source of a message.
        """
        return self.source
    
    def getType(self):
        """
        Return the message type.
        """
        return self.m_type

    def incNWorkers(self):
        self.n_workers += 1
        
    def isComplete(self):
        """
        Returns true if we have all the timing data for this message.
        """
        return (self.processing_time != None)

    def parseTime(self, time):
        return datetime.strptime(time, pattern)

    def processed(self, time):
        t_time = self.parseTime(time)
        self.processing_time = (t_time - self.temp).total_seconds()
        
    def sent(self, time):
        t_time = self.parseTime(time)
        self.queued_time = (t_time - self.temp).total_seconds()
        self.temp = t_time


def groupByMType(messages, ignore_incomplete = True):
    """
    Returns a dictionary keyed by message type, with a list of one or
    more message objects per message type.
    """
    mtype_groups = {}
    for msg in messages.values():

        # Ignore messages that we don't have all the timing for.
        if msg.isComplete() or not ignore_incomplete:
            m_type = msg.getType()
            if m_type in mtype_groups:
                mtype_groups[m_type].append(msg)
            else:
                mtype_groups[m_type] = [msg]
                
    return mtype_groups
        

def logTiming(basename):
    """
    Returns a dictionary of Message objects keyed by their ID number.
    """
    messages = {}

    for ext in [".5", ".4", ".3", ".2", ".1", ""]:

        if not os.path.exists(basename + ".out" + ext):
            continue
    
        with open(sys.argv[1] + ".out" + ext) as fp:
            for line in fp:

                try:
                    [time, command] = map(lambda x: x.strip(), line.split(":hal4000:INFO:"))
                except ValueError:
                    continue

                # Message queued.
                if (command.startswith("queued,")):
                    [m_id, source, m_type] = command.split(",")[1:]
                    messages[m_id] = Message(m_type = m_type,
                                             source = source,
                                             time = time)
                              
                # Message sent.
                elif (command.startswith("sent,")):
                    m_id = command.split(",")[1]
                    messages[m_id].sent(time)

                # Message processed.
                elif (command.startswith("processed,")):
                    m_id = command.split(",")[1]
                    messages[m_id].processed(time)

                elif (command.startswith("worker done,")):
                    m_id = command.split(",")[1]
                    messages[m_id].incNWorkers()

    return messages


def processingTime(list_of_messages):
    """
    Returns the total processing time for a list of messages.
    """
    accum_time = 0
    for msg in list_of_messages:
        accum_time += msg.getProcessingTime()
    return accum_time


def queuedTime(list_of_messages):
    """
    Returns the total queued time for a list of messages.
    """
    accum_time = 0
    for msg in list_of_messages:
        accum_time += msg.getQueuedTime()
    return accum_time


if (__name__ == "__main__"):

    import sys
    
    if (len(sys.argv) != 2):
        print("usage: <log file>")
        exit()

    messages = logTiming(sys.argv[1])
    groups = groupByMType(messages)
    
    for key in sorted(groups):
        grp = groups[key]
        print(key + ", {0:0d} counts, {1:.3f} seconds".format(len(grp), processingTime(grp)))




