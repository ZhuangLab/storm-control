#!/usr/bin/env python

'''
Created: 15 February 2012
Updated: 30 July 2012

Returns the specified lines from a chrN.bed file. 
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass
class BoundException(Exception): pass

def getLines():
    '''Gets user input about the region start and end coordinates safely'''
    while True:
        try:
            # Required start position
            iLineStart = int(raw_input("Please enter the region start "
                                       "coordinate [min = {0}]: ".format(MIN)))
            # Required end position
            iLineEnd = int(raw_input("Please enter the region end coordinate "
                                     "[max = {0}]: ".format(MAX)))
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
            print ("Start coordinate: {0} must be less than end "
                   "coordinate: {1}\n".format(iLineStart, iLineEnd))
        

def get_bool(sPrompt, iDefault=None):
    '''Gets a boolean (Yes/No) response from a user, with a possible default'''
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

def stats(aList):
    '''Provides statistics about the probe density for the selected region'''
    aList = [line.strip().split("\t") for line in aList]
    iProbes = len(aList)
    # Get the smallest start coord and largest end coord from list
    first_start = sorted(map(int, zip(*aList)[1]))[0]
    last_end = sorted(map(int, zip(*aList)[2]), reverse=True)[0]
    fLen = float((float(last_end) - float(first_start))/1000)
    fDensity = round(float(iProbes/fLen), 3)
    return(iProbes, fDensity)

def select(aList, iStart, iEnd):
    aGoodLines = []
    for line in aList:
        line_start = int(line[1])
        line_end = int(line[2])
        if (iStart <= line_start) and (iEnd >= line_end):
            aGoodLines.append("\t".join(line))
    return(aGoodLines)

def writer(aList, strOutputName):
    with open(strOutputName, "w") as fileOut:
        for line in aList:
            fileOut.write("{0}\n".format(line))
        print "\nWrote to {0}".format(strOutputName)

if __name__ == "__main__":
    # Get command-line args
    parser = argparse.ArgumentParser(description="Returns all lines from the "
                                     "given chrN.bed file that intersect with "
                                     "the specified region.")
    parser.add_argument("input", help="a chrN.bed file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-r", "--region", help = "start and end coordinates of "
                        "target region [ex. 5:50]")
    parser.add_argument("-o", "--output", help = "name of the output file")
    args = parser.parse_args()

    # Get min start and max end in file
    try:
        with open(args.input, "rU") as inFile:
            aLines = [line.strip().split("\t") for line in inFile]
            aStarts = sorted(map(int, zip(*aLines)[1]))
            aEnds = sorted(map(int, zip(*aLines)[2]), reverse=True)
            MIN = aStarts[0]
            MAX = aEnds[0]
    except IOError as err:
        sys.exit("Could not open {0}\nError: {1}".format(args.input, err))        

    # Check that adequate information has been given
    if args.interactive is True or args.region is None:
        RANGE_START, RANGE_END = getLines()
    else:
        aInput = map(int, args.region.strip("[]").split(":"))
        if not len(aInput) == 2:
            print "Unable to parse --range argument (given: {0})".format(args.range)
            RANGE_START, RANGE_END = getLines()
        else:
            iLineStart, iLineEnd = aInput
            if iLineStart < MIN:
                print ("Start coordinate is less than minimum start in file, "
                       "correcting to {0}".format(MIN))
                iLineStart = MIN
            if iLineEnd > MAX:
                print ("End coordinate is greater than maximum end in file, "
                       "correcting to {0}".format(MAX))
                iLineEnd = MAX
            if iLineStart > iLineEnd:
                print ("Start coordinate: {0} must be less than end "
                       "coordinate: {1}".format(iLineStart, iLineEnd))
                RANGE_START, RANGE_END = getLines()
            else:
                RANGE_START, RANGE_END = iLineStart, iLineEnd

    # Get relevant lines from file
    aSpecifiedLines = select(aLines, RANGE_START, RANGE_END)

    # Get stats
    print ("Returned {0} probes with a density of {1} "
           "probes/kb".format(*stats(aSpecifiedLines)))

    # If output filename specified, check if file already exists
    if args.output is not None:
        if os.path.isfile(args.output) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(args.output))
            if bOW is True:
                writer(aSpecifiedLines, args.output)
            else:
                print "\nDid not write {0}".format(args.output)
        else:
            writer(aSpecifiedLines, args.output)
    else:
        # Create output filename from input,keeping relative path
        strInFilePath, strInFileName = os.path.split(args.input)
        strInFileName = strInFileName.rsplit(".")[0]
        strOutFileName = (strInFileName +
                          "_region_{0}_to_{1}.bed".format(RANGE_START,
                                                         RANGE_END))
        # Check if output file exists
        strOutFilePath = os.path.join(strInFilePath, strOutFileName)
        if os.path.isfile(strOutFilePath) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(strOutFileName))
            if bOW is True:
                writer(aSpecifiedLines, strOutFilePath)
            else:
                print "\nDid not write {0}".format(strOutFileName)
        else:
            writer(aSpecifiedLines, strOutFilePath)
