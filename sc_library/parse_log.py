#!/usr/bin/env python
#
## @file
#
# This parses log file series (i.e. log, log.1, log.2, etc..) to
# make it easier to see which functions / methods call which other
# functions / methods. It is used mostly to make sure that what
# we expect to happen is actually happening, and to try and
# identify unnecessary function calls.
#
# Hazen 7/15.
#

from datetime import datetime
import os
import sys

if (len(sys.argv) != 2):
    print "usage: <log file>"
    exit()


pattern = '%Y-%m-%d %H:%M:%S,%f'

def parseCommand(command):
    return command.split(" ")[0]

command_timing = {}

indent = 0
start_time = None
for ext in [".5", ".4", ".3", ".2", ".1", ""]:

    if not os.path.exists(sys.argv[1] + ".out" + ext):
        continue
    
    with open(sys.argv[1] + ".out" + ext) as fp:
        for line in fp:

            try:
                [time, command] = map(lambda x: x.strip(), line.split(":hal4000:INFO:"))
            except ValueError:
                continue

            if start_time is None:
                elapsed = "{0:6.2f}".format(0.0)
                start_time = datetime.strptime(time, pattern)
            else:
                cur_time = datetime.strptime(time, pattern)
                elapsed = "{0:6.2f}".format((cur_time - start_time).total_seconds())
                    
            # Command start.
            if (" started" in line):
                print elapsed, " " * indent, command
                indent += 2

            # Command end.
            if (" ended" in line):
                indent -= 2
                if (indent < 0):
                    indent = 0
                print elapsed, " " * indent, command
