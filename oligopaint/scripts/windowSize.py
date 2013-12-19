#!/usr/bin/env python

'''
Created: 21 February 2012
Updated: 30 July 2012

Parses a chrN.bed file consisting of probe coordinates by a user-defined window
size and returns the number of probes, probe density and start and stop
coordinates for each possible window.
'''

import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path
from operator import itemgetter

class FoundException(Exception): pass

def getSize():
    ''' Get user input'''
    while True:
        try:
            iSize = int(raw_input("Please enter window size in kb: "))
            if iSize < 1:
                raise ValueError
            else:
                return(iSize)
        except ValueError:
            print "Window size must a be positive non-zero integer.\n"

def getTol():
    while True:
        try:
            usrTol = raw_input("Please enter size tolerance as a fraction of "
                               "window size [default = 0.1]: ")
            if not usrTol:
                # Take default value
                fTol = float(0.1)
                return(fTol)
            fTol = float(usrTol)
            
            if fTol < 0:
                raise ValueError
            else:
                return(fTol)
        except ValueError:
            print "Window size tolerance must a be positive non-zero value.\n"   


def bed_parser(fileIn, iWindowSize, dTolerance):
    # Convert window size into bp from kb
    iRealWS = iWindowSize * 1000
    # Build window size tolerances
    dWSMax = iRealWS + (iRealWS * dTolerance)
    dWSMin = iRealWS - (iRealWS * dTolerance)
##    print "Minimum window size = " + str(dWSMax) + "WSMin = " + str(dWSMin)
    # Clear counters and lists
    aOutputList = []
    iEndLineCount = iStartLineCount = 0
    iSkipCount = 0
    # Read file into a list of lines, get length 
    with open(fileIn, "r") as oligoFile:
        aaLines = [line.strip().split("\t") for line in oligoFile]
        iLen = len(aaLines) - 1
        for line in aaLines:
            # Check that EndLineCount is not at the last line of the file
            if iEndLineCount <= iLen:
                ''' 
                Parse the leftmost oligo at the line marked by
                iStartLineCountwhich will be the left-most oligo for this
                search iteration, then parse the oligo marked by iEndLineCount
                ''' 
                aLeftOligo = aaLines[iStartLineCount]
                aRightOligo = aaLines[iEndLineCount]
                # Get the start and end coordinates from the left and right
                # oligos, respectively
                iStartPos = (int(aLeftOligo[1]) + iRealWS)
                iEndPos = int(aRightOligo[2])
                # Check if the start coordinate + the window is right of
                # the end coordinate
                if iStartPos > iEndPos:
                    # If it is, iterate the count and start a new iteration
                    iEndLineCount += 1
                else:
                    # Count how many lines (probes) have been iterated over
                    iProbeCount = int(iEndLineCount - iStartLineCount)
                    # Get end coordinate from previous line and calculate diff
                    aRealRightOligo = aaLines[iEndLineCount - 1]
                    diff = float(aRealRightOligo[2]) - float(aLeftOligo[1])
                    # Check interval size and correct if possible
                    if diff < dWSMin:
                        # Advance to next oligo
                        aBetterRightOligo = aaLines[iEndLineCount]
                        diff = (float(aBetterRightOligo[2]) -
                                float(aLeftOligo[1]))
                        # If interval too large, skip w/o appending
                        if diff > dWSMax:
                            iStartLineCount += 1
                            iSkipCount += 1
                        else:
                            # Calculate probe density
                            density = round(float(iProbeCount)/(diff/1000), 2)
                            # Append assembly, start, stop, probe density
                            # and probe count
                            aOutputList.append(str(aLeftOligo[0]) + "\t" +
                                               str(aLeftOligo[1]) + "\t" +
                                               str(aRealRightOligo[2]) + "\t" +
                                               str(density) + "\t" +
                                               str(iProbeCount))
                            # Increase start iterator so search starts
                            # on next oligo
                            iStartLineCount += 1
                    else:
                        # Calculate probe density
                        density = round(float(iProbeCount)/(diff/1000), 2)
                        aOutputList.append(str(aLeftOligo[0]) + "\t" +
                                           str(aLeftOligo[1]) + "\t" +
                                           str(aRealRightOligo[2]) + "\t" +
                                           str(density) + "\t" +
                                           str(iProbeCount))
                        # Increase start iterator so search starts
                        # on next oligo
                        iStartLineCount += 1
            else:
                # If out of oligos, force last line as end
                aLastOligo = aaLines[iLen]
                diff = int(aLastOligo[2]) - int(aLeftOligo[1])
                # Calculate probe count and density
                iProbeCount = int(iEndLineCount - iStartLineCount)
                density = round(float(iProbeCount)/(diff/1000), 2)
                aOutputList.append(str(aLeftOligo[0]) + "\t" +
                                   str(aLeftOligo[1]) + "\t" +
                                   str(aLastOligo[2]) + "\t" + str(density) +
                                   "\t" + str(iProbeCount))
                break
            oligoFile.seek(0,0)
    return(aOutputList, iSkipCount)

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

def writer(aList, strOutputName, bSort=False):
    with open(strOutputName, "w") as fileOut:
        if bSort:
            print "Sorting " + strOutputName
            # Sort on probe density descending
            aList.sort(key= lambda line: float(line.split('\t')[3]),
                       reverse=True)
            fileOut.write("\n".join(aList))
            print "Wrote to " + strOutputName
        else:
            fileOut.write("\n".join(aList))
            print "Wrote to " + strOutputName

if __name__ == "__main__":
    # Get command-line arguments
    parser = argparse.ArgumentParser(description="Parse a chrN.bed file into "
                                     "windows of a specified size, returning "
                                     "the coordinates, probe density and number "
                                     "of probes for each possible window")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-s", "--sort", action="store_true", default=False,
                        help="Sort output file by probe density in descending "
                        "order [default: False]")
    parser.add_argument("-w", "--window", type=int, metavar="SIZE",
                        help="Window size in kb")
    parser.add_argument("-t", "--tolerance", type=float, default=0.10,
                        help="Window size tolerance as a fraction of window "
                        "size [default: 0.1]")
    parser.add_argument("-o", "--output", help="name of the output file")
    parser.add_argument("input", help="a chrN.bed file")
    args = parser.parse_args()
    
    # Get variables not specified on command-line
    if args.interactive is True:
        iSize = getSize()
        fTol = getTol()
        bSort = get_bool("Sort output by probe density in descending order? "
                         "[Y/n]: ", False)
    else:
        bSort = args.sort
        if args.window is None:
            iSize = getSize()
            if args.tolerance is not None:
                fTol = args.tolerance
            else:
                fTol = getTol()
        elif args.tolerance is None:
            iSize = args.window
            fTol = getTol()
        else:
            iSize = args.window
            fTol = args.tolerance

##    print args
##    print "\n"
    
    # Get output list
    aLines, iSkipCount = bed_parser(args.input, iSize, args.tolerance)

    # If output filename specified, check if file already exists
    if args.output is not None:
        if os.path.isfile(args.output) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(args.output))
            if bOW is True:
                writer(aLines, args.output, bSort)
            else:
                print "\nDid not write {0}".format(args.output)
        else:
            writer(aLines, args.output, bSort)
    else:
        # Create output filename from input,keeping relative path
        strInFilePath, strInFileName = os.path.split(args.input)
        strInFileName = strInFileName.rsplit(".")[0]
        strOutFileName = ("{0}_{1}kb.txt".format(strInFileName, iSize))
        # Check if output file exists
        strOutFilePath = os.path.join(strInFilePath, strOutFileName)
        if os.path.isfile(strOutFilePath) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(strOutFileName))
            if bOW is True:
                writer(aLines, strOutFilePath, bSort)
            else:
                print "\nDid not write {0}".format(strOutFileName)
        else:
            writer(aLines, strOutFilePath, bSort)


