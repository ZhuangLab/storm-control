#!/usr/bin/env python
#
## @file
#
# This parses a log file series (i.e. log, log.1, log.2, etc..) and
# outputs timing and call frequency information for the functions
# and methods that were logged. It is used mostly for identifying
# bottle-necks.
#
# Hazen 7/15
#

from datetime import datetime
import os
import sys

if (len(sys.argv) != 2):
    print "usage: <log file>"
    exit()


pattern = '%Y-%m-%d %H:%M:%S,%f'

class Timing(object):

    def __init__(self, time):
        self.counts = 0
        self.elapsed_time = 0.0
        self.start(time)

    def printTiming(self):
        if (self.counts > 0):
            print "Average time:", float(self.elapsed_time)/float(self.counts), "for", self.counts, "events"
        else:
            print "No data."
            
    def start(self, time):
        t_time = datetime.strptime(time, pattern)
        self.start_time = t_time

    def stop(self, time):
        t_time = datetime.strptime(time, pattern)
        self.elapsed_time += (t_time - self.start_time).total_seconds()
        self.counts += 1

    def __str__(self):
        if (self.counts > 0):
            return str(float(self.elapsed_time)/float(self.counts)) + " " + str(self.counts)
        else:
            return "0 0"

def parseCommand(command):
    return command.split(" ")[0]

command_timing = {}

for ext in [".5", ".4", ".3", ".2", ".1", ""]:

    if not os.path.exists(sys.argv[1] + ".out" + ext):
        continue
    
    with open(sys.argv[1] + ".out" + ext) as fp:
        for line in fp:

            try:
                [time, command] = map(lambda x: x.strip(), line.split(":hal4000:INFO:"))
            except ValueError:
                continue

            # Get command start.
            if ("started" in line):
                start_cmd = parseCommand(command)
                if start_cmd in command_timing:
                    command_timing[start_cmd].start(time)
                else:
                    command_timing[start_cmd] = Timing(time)

            # Get command end.
            if ("ended" in line):
                end_cmd = parseCommand(command)
                if end_cmd in command_timing:
                    command_timing[end_cmd].stop(time)
                else:
                    print "Missed command:", end_cmd

            # Time between messages.
            # ...

for key in command_timing:
    print key, command_timing[key]
