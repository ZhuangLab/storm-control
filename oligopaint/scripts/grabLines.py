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

def getLines(iMax):
    while True:
        try:
            # Required start position
            iLineStart = int(raw_input("Please enter the number of first line "
                                       "needed [min = 1]: "))
            # Required end position
            iLineEnd = int(raw_input("Please enter the number of last line "
                                     "needed [max = {0}]: ".format(iMax)))
            if iLineStart < 1 or iLineEnd < 1:
                raise ValueError
            elif iLineEnd < iLineStart:
                raise FoundException
            else:
                return (iLineStart, iLineEnd)
        except ValueError:
            print "Line numbers must be positive non-zero integers\n"
        except FoundException:
            print "First line must be less than last line\n"

def line_grabber(iStart, iEnd, fileIn):
    '''Return Nth through Jth lines in fileIn where iStart and iEnd define
    N and J respectively
    '''
    # Create output list and calculate total number of lines to be grabbed
    aEntries = []
    iDiff = (iEnd - iStart + 1)
    # Read in all lines into list
    with open(fileIn, "r") as f:
        aLines = f.readlines()
        # Check that lines exist
        try:
            for i in range(iDiff):
                lino = (i + (iStart - 1))
                aEntries.append(aLines[lino])
        except IndexError:
            print ("Cannot find line {0}, ensure range given is valid for "
                   "given file".format(lino + 1))
            sys.exit()
        else:
            return(aEntries)

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

def writer(aList, strOutputName):
    with open(strOutputName, "w") as fileOut:
        for line in aList:
            fileOut.write(line)
        print "\nWrote to {0}".format(strOutputName)

if __name__ == "__main__":
    # Get command-line args
    parser = argparse.ArgumentParser(description="Returns specified range of "
                                     "lines from the given file.")
    parser.add_argument("input", help="a chrN.bed file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-r", "--range", help = "range of lines to grab from "
                        "file [ex. 5:50]")
    parser.add_argument("-o", "--output", help = "name of the output file")
    args = parser.parse_args()

    # Get min start and max end in file
    with open(args.input, "rU") as inFile:
        aLines = [line.strip().split("\t") for line in inFile]
        iMax = len(aLines)

    # Check that adequate information has been given
    if args.interactive is True:
        RANGE_START, RANGE_END = getLines(iMax)
    else:
        aInput = map(int, args.range.strip("[]").split(":"))
        if not len(aInput) == 2:
            print "Unable to parse --range argument (given: {0})".format(args.range)
            RANGE_START, RANGE_END = getLines(iMax)
        elif aInput[1] < aInput[0]:
            print "First line must be less than last line (given: {0})".format(args.range)
            RANGE_START, RANGE_END = getLines(iMax)
        else:
            RANGE_START, RANGE_END = aInput

    # Get relevant lines from file
    aSpecifiedLines = line_grabber(RANGE_START, RANGE_END, args.input)

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
                          "_lines_{0}_to_{1}.bed".format(RANGE_START,
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
