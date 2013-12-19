#!/usr/bin/env python

'''
Created: 23 February 2012
Updated: 30 July 2012

Creates an order file based upon primers the user specifies and a given
Oligopaiints .bed file
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass

def getPrimer(iCount):
    iMax = MAX_LINES
    TestChars = "0123456789-,"
    strOrd = ordinal(iCount)
    print "Enter primers 5' to 3'"
    # Forward primer
    strInForward = raw_input("Please enter the {0} forward "
                             "primer: ".format(strOrd))
    # Reverse primer
    strInReverse = raw_input("Please enter the {0} reverse "
                             "primer: ".format(strOrd))
    strForward = strInForward.strip().upper()
    # Get reverse complement
    strReverse = reverse_comp(strInReverse.strip().upper())
    
    while True:
        print "The maximum probe range is 1-{0}".format(iMax)
        try:
            primerRange = raw_input("Enter the range of probes for this primer "
                                    "to cover [ex. 1-30,41-60]: ").strip()
            # Check that ranges only contain digits, commas and dashes
            if any([char not in TestChars for char in set(primerRange)]):
                raise FoundException
            aRanges = [map(int, ranges.split("-")) for ranges in
                       primerRange.split(",")]
            # Check that all given ranges are valid
            for aRange in aRanges:
                if not len(aRange) == 2:
                    raise FoundException
            # Check that maximum range given is not larger than max possible
            if max(max(aRanges)) > iMax:
                print ("Range given {0} is too large".format(max(aRanges)))
            else:
                return([strForward, strReverse, aRanges])

        except FoundException:
            print ("\nCould not parse primer range (given \"{0}\")\n"
                   "Please enter a range as two numbers seperated by a dash\n"
                   "Multiple ranges should be seperated by commas\n".format(primerRange))

def reverse_comp(DNAstring):
    # DNA library
    hComplement = {'A':'T', 'G':'C', 'C':'G', 'T':'A', 'N':'N'}
    revcomp = []
    try:
        for base in DNAstring:
            revcomp.append(hComplement[base])
        return("".join(revcomp)[::-1])
    except KeyError:
        sys.exit("Check primers, could not recognize character {0} in primer "
                 "sequence.".format(base))
    
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

def primers():
    aPrimers = []
    while True:
        try:
            iTotPrimers = int(raw_input("Number of primers: "))
            if iTotPrimers < 1:
                raise ValueError
            else:
                for iPrimerCount in range(1, iTotPrimers+1):
                    aPrimers.append(getPrimer(iPrimerCount))
                return(aPrimers)
        except ValueError:
            print ("Please enter a positive, non-zero integer for the number "
                   "of primers")

def unique(aList):
    # Check line start coordinates
    aStarts = map(lambda line: int(line.split("\t")[0]), aOrderList)
    if len(aStarts) != len(set(aStarts)):
        return False
    else:
        return True

def primerFile(inFile):
    aPrimers = []
    iMax = MAX_LINES
    TestChars = "0123456789-,"
    for line in inFile:
        line = line.strip().split("\t")
        strForward = line[0].upper()
        strReverse = line[1].upper()[::-1]
        primerRange = line[2]
        
        # Check that ranges only contain digits, commas and dashes
        if any([char not in TestChars for char in set(primerRange)]):
            print "Could not parse primer file, please enter primers manually\n"
            return(primers())
        
        aRanges = [map(int, ranges.split("-")) for ranges in
                   primerRange.split(",")]
        # Check that maximum range given is not larger than max possible
        if max(max(aRanges)) > iMax:
            print "Could not parse primer file, please enter primers manually\n"
            return(primers())
        
        aPrimers.append([strForward, strReverse, aRanges])
    return(aPrimers)
    
def order(aPrimers, aProbes):
    aOrder = []
    for primerPair in aPrimers:
        iRangeCount = len(primerPair[2])
        aRanges = primerPair[2]
        fivePrime, threePrime = primerPair[:2]
        if iRangeCount > 1:
            for i in range(iRangeCount):
                iStart, iEnd = aRanges[i]
                for j in range(iStart - 1, iEnd):
                    line = aProbes[j].strip().split("\t")
                    aOrder.append("{0}\t{1}{2}{3}".format(line[1], fivePrime,
                                                          line[3], threePrime))
        else:
            iStart, iEnd = aRanges[0]
            for j in range(iStart - 1, iEnd):
                line = aProbes[j].strip().split("\t")
                aOrder.append("{0}\t{1}{2}{3}".format(line[1], fivePrime,
                                                      line[3], threePrime))
    return(aOrder)

def writer(aList, filename):
    with open(filename, "w") as f:
        for line in aList:
            f.write("{0}\n".format(line))
    print "Wrote to {0}".format(filename)
    
            
def ordinal(value):
    try:
        value = int(value)
    except ValueError:
        return value

    if value % 100//10 != 1:
        if value % 10 == 1:
            ordval = "{0}st".format(value)
        elif value % 10 == 2:
            ordval = "{0}nd".format(value)
        elif value % 10 == 3:
            ordval = "{0}rd".format(value)
        else:
            ordval = "{0}th".format(value)
    else:
        ordval = "{0}th".format(value)

    return ordval
            
if __name__ == "__main__":
    # Get command-line args
    parser = argparse.ArgumentParser(description="Prepares an order from the "
                                     "given chrN.bed file using the specified "
                                     "primers")
    parser.add_argument("input", help="a chrN.bed file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-p", "--primers", type=argparse.FileType("rU"),
                        help = "a file containing primer information")
    parser.add_argument("-o", "--output", help = "name of the output file")
    args = parser.parse_args()

    # Get last probe number from file length
    with open(args.input, "rU") as inFile:
        aProbes = inFile.readlines()
        MAX_LINES = len(aProbes)
        
    # Get primer list
    if args.interactive is True or args.primers is None:
        aPrimers = primers()
    else:
        aPrimers = primerFile(args.primers)
    
    # Generate primer orders
    aOrderList = order(aPrimers, aProbes)
    aOrderList.sort(key=lambda line: int(line.split("\t")[0]))
    # Check for duplicate entries
    if unique(aOrderList) is False:
        print ("WARNING: Duplicate probe lines found in order file. "
               "Check primer ranges.")
    # Determine output filename and write
    if args.output is not None:
        if os.path.isfile(args.output) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(args.output))
            if bOW is True:
                writer(aOrderList, args.output)
            else:
                print "\nDid not write {0}".format(args.output)
        else:
            writer(aOrderList, args.output)
    else:
        # Create output filename from input,keeping relative path
        strInFilePath, strInFileName = os.path.split(args.input)
        strInFileName = strInFileName.rsplit(".")[0]
        strOutFileName = "{0}_order.txt".format(strInFileName)
        # Check if output file exists
        strOutFilePath = os.path.join(strInFilePath, strOutFileName)
        
        if os.path.isfile(strOutFilePath) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(strOutFileName))
            if bOW is True:
                writer(aOrderList, strOutFilePath)
            else:
                print "\nDid not write {0}".format(strOutFileName)
        else:
            writer(aOrderList, strOutFilePath)
