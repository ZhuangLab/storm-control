#!/usr/bin/env python

'''
Created: 15 February 2012
Updated: 30 July 2012

Calculates the number of windows meeting the coverage criteria for
a genome spacing file
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass

def coverage(fileIn, iKb, iMinProbes):
    with open(fileIn, "r") as f:
        aOligoSpacing = f.readlines()
        iOligoSpacingLen = len(aOligoSpacing)
        iMaxRange = iOligoSpacingLen - iKb + 1
        iWindowCount = 0
        for i in range(iMaxRange):
            iLineMin = i
            iLineMax = iKb + i
            aProbeLines = [line.strip().split("\t") for line
                           in aOligoSpacing[iLineMin:iLineMax]]
            aProbeNumbers = [int(line[3]) for line in aProbeLines]
            iTotalProbes = sum(aProbeNumbers)
            if iTotalProbes >= iMinProbes:
                iWindowCount += 1
        # Calculate kb covered by min # of probes by multiplying window size
        # by number of windows with min # of probes
        iKbCovered = iKb * iWindowCount
        # Calculate number of windows found over number of possible windows
        fCoverage = float(iWindowCount)/float(iMaxRange)
        return(iKbCovered, fCoverage)

def get_bool(sPrompt, iDefault=None):
    while True:
        try:
            sLine = raw_input(sPrompt)
            # If no user entry and default value exists, return default
            if not sLine and iDefault is not None:
                return iDefault
            sLine = sLine.strip().lower() # case-insensitive
            if sLine == 'y':
                return True
            elif sLine == 'n':
                return False
            else:
                raise ValueError
        except ValueError, EOFError:
            print("Please enter [Y/n]")

def getProbes():
    while True:
        try:
            iMinProbes = int(raw_input("Please enter the minimum number of "
                                       "probes per window: "))
            if iMinProbes < 1:
                raise ValueError
            else:
                return(iMinProbes)
        except ValueError:
            print ("The minimum probes/window must be a positive non-zero "
                   "interger")

def getWindow():
    while True:
        try:
            iWindow = int(raw_input("Please enter the window size in kb: "))
            if iWindow < 1:
                raise ValueError
            else:
                return(iMinProbes)
        except ValueError:
            print "The window size must be a positive non-zero interger"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Returns the fraction of "
                                     "windows with the minimum number of probes"
                                     " specified from the given genome spacing "
                                     "file")
    parser.add_argument("input", help="a genome spacing file")
    parser.add_argument("-w", "--window", type=int, metavar="SIZE",
                        help="Window size (kb)")
    parser.add_argument("-p", "--probes", type=int, metavar="MIN PROBES/WINDOW",
                        help="Minimum number of probes/window")
    parser.add_argument("-o", "--output", help = "name of the output file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    args = parser.parse_args()
    # Get necessary information
    if args.interactive is True:
        window = getWindow()
        probes = getProbes()
    else:
        if args.probes is not None:
            if args.window is not None:
                window = args.window
                probes = args.probes
            else:
                window = getWindow()
                probes = args.probes
        else:
            if args.Window is not None:
                window = args.window
                probes = getProbes()
            else:
                window = getWindow()
                probes = getProbes()

    # Calculate and display coverage
    iTotalWindowKb, fCoverage = coverage(args.input, window, probes)
    print "Coverage: {0}".format(round(fCoverage, 3))
            
