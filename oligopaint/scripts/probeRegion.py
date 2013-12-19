#!/usr/bin/evn python

'''
Created: 7 June 2012
Updated: 30 July 2012

Returns probes covering a specified region in an evenly spaced manner.
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass

def getLines():
    while True:
        try:
            # Required start position
            iLineStart = int(raw_input("Please enter the start coordinate for "
                                       "the region [min = {0}]: ".format(MIN)))
            # Required end position
            iLineEnd = int(raw_input("Please enter the end coordinate for the "
                                     "the region [max = {0}]: ".format(MAX)))
            if iLineStart < 1 or iLineEnd < 1:
                raise ValueError
            else:
                if iLineStart < MIN:
                    print ("Start coordinate is less than minimum start in "
                           "file, correcting to {0}".format(MIN))
                    iLineStart = MIN
                if iLineEnd > MAX:
                    print ("End coordinate is greater than maximum end in file, "
                           "correcting to {0}".format(MAX))
                    iLineEnd = MAX
                if iLineStart > iLineEnd:
                    raise FoundException
                return (iLineStart, iLineEnd)
        except ValueError:
            print "Coordinates must be positive non-zero integers\n"
        except FoundException:
            print ("Start coordinate ({0}) must be less than end "
                   "coordinate ({1})\n".format(iLineStart, iLineEnd))
            
def getProbes():
    while True:
        try:
            # Required probe number
            iProbes = int(raw_input("Please enter the number probes per region "
                                       "[ex. 1000]: "))
            if iProbes < 1:
                raise ValueError
            if iProbes > PROBES_MAX:
                print ("Probe number ({0}) is greater than number of probes in "
                       "file ({1})".format(iProbes, PROBES_MAX))
            else:
                return (iProbes)
        except ValueError:
            print "Probe number must be a positive non-zero integer\n"

def select(aList, iStart, iEnd):
    aGoodLines = []
    for line in aList:
        line_start = int(line[1])
        line_end = int(line[2])
        if (iStart <= line_start) and (iEnd >= line_end):
            aGoodLines.append("\t".join(line))
    return(aGoodLines)

def pick(iProbes, aLines):
    aProbeList = []
    iLen = len(aLines)
    fInterval = float(iLen)/iProbes
    for i in range(iProbes):
        aProbeList.append(aLines[int(round(fInterval * i))])
    return(aProbeList)

def writer(aList, strOutputName):
    with open(strOutputName, "w") as fileOut:
        for line in aList:
            fileOut.write("{0}\n".format(line))
        print "\nWrote to {0}".format(strOutputName)

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

if __name__ == "__main__":
    # Get command-line args
    parser = argparse.ArgumentParser(description="Returns  all probes within "
                                     "a specific region, spaced evenly.")
    parser.add_argument("input", help="a chrN.bed file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-p", "--probes", type = int,
                        help = "number of probes per region [ex. 1000]")
    parser.add_argument("-r", "--region",
                        help="the start and end positions for the region to "
                        "be searched [ex. 1000:5000]")
    parser.add_argument("-o", "--output", help = "name of the output file")
    args = parser.parse_args()

    # Get min start and max end in file
    with open(args.input, "rU") as inFile:
        aLines = [line.strip().split("\t") for line in inFile]
        aStarts = sorted(map(int, zip(*aLines)[1]))
        aEnds = sorted(map(int, zip(*aLines)[2]), reverse=True)
        MIN = aStarts[0]
        MAX = aEnds[0]
        PROBES_MAX = len(aLines)

    # Check if script needs user input:
    if args.interactive is True:
        PROBE_NUMBER = getProbes()
        RANGE_START, RANGE_END = getLines()
    else:
        try:
            if args.probes is None:
                raise ValueError
            iProbeIn = int(args.probes)    
            if iProbeIn < 1:
                print "Probe number must be a positive non-zero integer\n"
                PROBE_NUMBER = getProbes()
            elif iProbeIn > PROBES_MAX:
                print ("Probe number ({0}) is greater than number of probes in "
                       "file ({1})".format(iProbeIn, PROBES_MAX))
                PROBE_NUMBER = getProbes()
            else:
                PROBE_NUMBER = iProbeIn
        except ValueError:
            PROBE_NUMBER = getProbes()
        if args.region is not None:
            aInput = map(int, args.region.strip("[]").split(":"))
            if not len(aInput) == 2:
                print ("Unable to parse --region argument "
                       "(given: {0})".format(args.region))
                RANGE_START, RANGE_END = getLines()
            else:
                iLineStart, iLineEnd = aInput
                if iLineStart < MIN:
                    print ("Start coordinate is less than minimum start in "
                           "file, correcting to {0}".format(MIN))
                    iLineStart = MIN
                if iLineEnd > MAX:
                    print ("End coordinate is greater than maximum end in "
                           "file, correcting to {0}".format(MAX))
                    iLineEnd = MAX
                if iLineStart > iLineEnd:
                    print ("Start coordinate: {0} must be less than end "
                           "coordinate: {1}".format(iLineStart, iLineEnd))
                    RANGE_START, RANGE_END = getLines()
                else:
                    RANGE_START, RANGE_END = iLineStart, iLineEnd
        else:
            RANGE_START, RANGE_END = getLines()
    
    # Narrow down file to selected lines
    while True:
        aProbes = select(aLines, RANGE_START, RANGE_END)
        iLen = len(aProbes)
        print "Found {0} probes in region".format(iLen)
        if PROBE_NUMBER > iLen:
            print ("Less probes found ({0}) than requested "
                   "({1})".format(iLen, PROBE_NUMBER))
            if get_bool("Would you like to change the region size? [Y/n]: "):
                RANGE_START, RANGE_END = getLines()
            elif get_bool("Would you like to reduce the probe number? [Y/n]: "):
                PROBE_NUMBER = getProbes()
            else:
                sys.exit("Could not find enough probes in region")
        else:
            break

    # Pick probes evenly across region
    aProbesOut = pick(PROBE_NUMBER, aProbes)
            
    # Determine output filename and write
    if args.output is not None:
        if os.path.isfile(args.output) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(args.output))
            if bOW is True:
                writer(aProbesOut, args.output)
            else:
                print "\nDid not write {0}".format(args.output)
        else:
            writer(aProbesOut, args.output)
    else:
        # Create output filename from input,keeping relative path
        strInFilePath, strInFileName = os.path.split(args.input)
        strInFileName = strInFileName.rsplit(".")[0]
        strOutFileName = ("{0}_{1}_probes_from_{2}_to_{3}"
                          ".bed".format(strInFileName,PROBE_NUMBER, RANGE_START,
                                        RANGE_END))
        # Check if output file exists
        strOutFilePath = os.path.join(strInFilePath, strOutFileName)
        
        if os.path.isfile(strOutFilePath) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(strOutFileName))
            if bOW is True:
                writer(aProbesOut, strOutFilePath)
            else:
                print "\nDid not write {0}".format(strOutFileName)
        else:
            writer(aProbesOut, strOutFilePath)
