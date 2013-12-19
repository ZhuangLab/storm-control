#!/usr/bin/env python

'''
Created: 23 February 2012
Updated: 30 July 2012

Returns all regions containing the specified numbers of probes from a chrN.bed
file. The -r option confines the search to the given region. The probe density
for each region is also reported.
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass

def getLines(iMin, iMax):
    while True:
        try:
            # Required start position
            iLineStart = int(raw_input("Please enter the start coordinate for "
                                       "the region [min = {0}]: ".format(iMin)))
            # Required end position
            iLineEnd = int(raw_input("Please enter the end coordinate for the "
                                     "the region [max = {0}]: ".format(iMax)))
            if iLineStart < 1 or iLineEnd < 1:
                raise ValueError
            else:
                if iLineStart < iMin:
                    print ("Start coordinate is less than minimum start in "
                           "file, correcting to {0}".format(iMin))
                    iLineStart = iMin
                if iLineEnd > iMax:
                    print ("End coordinate is greater than maximum end in file, "
                           "correcting to {0}".format(iMax))
                    iLineEnd = iMax
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
            else:
                return (iProbes)
        except ValueError:
            print "Probe number must be a positive non-zero integer\n"

def select(aList, iStart, iEnd):
    aGoodLines = []
    for line in aList:
        line = line.strip().split("\t")
        line_start = int(line[1])
        line_end = int(line[2])
        if (iStart <= line_start) and (iEnd >= line_end):
            aGoodLines.append("\t".join(line))
    return(aGoodLines)


def parse(iProbes, aLines):
    aProbeList = []
    iMaxLen = (len(aLines) - 1)
    for i in range(iMaxLen - (iProbes-2)):
        iStart = i
        iEnd = i + (iProbes - 1)
        iFirstPos = aLines[iStart].strip().split("\t")[1]
        iLastPos = aLines[iEnd].strip().split("\t")[2]
        strChr = aLines[iStart].strip().split("\t")[0]
        aProbeList.append([strChr, iFirstPos, iLastPos])
    return(aProbeList)

def stats(aList):
    aOutputList = []
    for line in aList:
        # Get length of window in kb
        fLen = float((float(line[2]) - float(line[1]))/1000)
        fDensity = round(float(PROBE_NUMBER/fLen), 3)
        aOutputList.append("{0}\t{1}\t{2}\t{3}\n".format(line[0], line[1],
                                                         line[2], fDensity))
    return(aOutputList)

def writer(aList, strOutputName):
    with open(strOutputName, "w") as fileOut:
        for line in aList:
            fileOut.write(line)
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
    parser = argparse.ArgumentParser(description="Obtains all regions "
                                     "containing the specified number of probes"
                                     " from the given file")
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
        iMinStart = aStarts[0]
        iMaxEnd = aEnds[0]

    # Check if script needs user input:
    if args.interactive is True:
        PROBE_NUMBER = getProbes()
        if get_bool("Would you like to specify a region to search within the "
                    "file? [Y/n]: ") == True:
            SELECT = True
            RANGE_START, RANGE_END = getLines(iMinStart, iMaxEnd)
        else:
            SELECT = False
    else:
        try:
            if args.probes is None:
                raise ValueError
            iProbeIn = int(args.probes)    
            if iProbeIn >= 1:
                PROBE_NUMBER = iProbeIn
            else:
                raise ValueError
        except ValueError:
            PROBE_NUMBER = getProbes()
        if args.region is not None:
            SELECT = True
            aInput = map(int, args.region.strip("[]").split(":"))
            if not len(aInput) == 2:
                print ("Unable to parse --region argument "
                       "(given: {0})".format(args.region))
                RANGE_START, RANGE_END = getLines(iMinStart, iMaxEnd)
            elif aInput[1] < aInput[0]:
                print ("Start coordinate must be less than "
                       "end coordinate (given: {0})".format(args.region))
                RANGE_START, RANGE_END = getLines(iMinStart, iMaxEnd)
            else:
                RANGE_START, RANGE_END = aInput
        else:
            SELECT = False

    # Run parser using specified values and get stats, reducing search to region
    # if specified
    with open(args.input, "rU") as f:
        aFile = f.readlines()
        if SELECT == True:
            aGoodLines = select(aFile, RANGE_START, RANGE_END)
            aProbes = parse(PROBE_NUMBER, aGoodLines)
        else:
            aProbes = parse(PROBE_NUMBER, aFile)

    aProbesOut = stats(aProbes)

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
        if SELECT == True:
            strOutFileName = ("{0}_{1}_probe_regions_from_"
                              "{2}_to_{3}.bed".format(strInFileName,
                                                      PROBE_NUMBER,
                                                      RANGE_START,
                                                      RANGE_END))
        else:
            strOutFileName = "{0}_{1}_probe_regions.bed".format(strInFileName,
                                                                PROBE_NUMBER)
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
