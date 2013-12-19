#!/usr/bin/env python

'''
Created: 15 February 2012
Updated: 30 July 2012

Sorts the given file by the specified column in ascending or descending order. 
'''
import sys

if sys.version_info < (2, 7):
    raise Exception("Python 2.7+ is required")

import argparse
import os.path

class FoundException(Exception): pass

def getCol():
    while True:
        try:
            # Required column 
            iCol = int(raw_input("Please enter the column to sort by [{0} "
                                 "columns in file]: ".format(MAX_COL)))
            if iCol < 1:
                raise ValueError
            else:
                return iCol
        except ValueError:
            print "Column number must be a positive non-zero integer\n"

def getSort():
    while True:
        try:
            # Required sort condition
            strSort = raw_input("Ascending or descending sort? [a/d]: ")
            strSort = strSort.lower()
            if len(strSort) > 1 or strSort not in "ad":
                raise FoundException
            else:
                return strSort
        except ValueError:
            print ("Please enter either a or d to sort in either [a[scending "
                   "or [d]escending order")

def sort(aList, col, order):
    # Test first value in specified column to determine if sort is by float or
    # by string
    test = aList[0][col - 1]
    try:
        test = float(test)
        use_float = True
    except ValueError:
        use_float = False
        
    # Sort on column, converting to numerical sort if possible
    if use_float is True:
        aSort = sorted(aList, key=lambda line: float(line[col - 1]))
    else:
        aSort = sorted(aList, key=lambda line: line[col - 1])

    # Reverse order if sort is descending
    if order.lower() == 'd':
        aSort.reverse()
        return(aSort)
    else:
        return(aSort)

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
            fileOut.write("{0}\n".format("\t".join(line)))
        print "\nWrote to {0}".format(strOutputName)

if __name__ == "__main__":
    # Get command-line args
    parser = argparse.ArgumentParser(description="Sorts a file on the specified"
                                     " columns in either acesending/descending "
                                     "order.")
    parser.add_argument("input", help="any tab-delimited file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        default=False, help="run script interactively")
    parser.add_argument("-c", "--columns", type=int,
                        help="The column to sort the file by")
    parser.add_argument("-s","--sort", choices="ad", default="d",
                        help="The sort order, either [a]scending or "
                        "[d]escending (default= [d]escending)")
    parser.add_argument("-o", "--output", help="name of the output file")
    args = parser.parse_args()

    # Open file
    try:
        with open(args.input, "rU") as fileIn:
            DATA = [line.strip().split("\t") for line in fileIn]
            MAX_COL = len(DATA[0])
    except IOError as err:
        sys.exit("Could not open {0}\nError: {1}".format(args.input, err))

    # Check that adequate information has been given
    if args.interactive is True:
        COLUMN = getCol()
        SORT = getSort()
    else:
        SORT = args.sort
        if args.columns > MAX_COL:
            print ("Column indicated ({0}) is greater than number of columns "
                   "in file ({1})".format(args.columns, MAX_COL))
            COLUMN = getCol()
        elif args.columns < 1:
            print "Column number must be a positive non-zero integer"
            COLUMN = getCol()
        else:
            COLUMN = args.columns
    
    # Sort file
    order = "ascending" if SORT == "a" else "descending"
    print "Sorting {0} by the {1} column in {2} order".format(args.input,
                                                              ordinal(COLUMN),
                                                              order)
    aSorted = sort(DATA, COLUMN, SORT)

    # If output filename specified, check if file already exists
    if args.output is not None:
        if os.path.isfile(args.output) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(args.output))
            if bOW is True:
                writer(aSorted, args.output)
            else:
                print "\nDid not write {0}".format(args.output)
        else:
            writer(aSorted, args.output)
    else:
        # Create output filename from input,keeping relative path
        strInFilePath, strInFileName = os.path.split(args.input)
        strInFileName = strInFileName.rsplit(".")[0]
        strOutFileName = "{0}_sorted.bed".format(strInFileName)
        # Check if output file exists
        strOutFilePath = os.path.join(strInFilePath, strOutFileName)
        if os.path.isfile(strOutFilePath) is True:
            bOW = get_bool("{0} already exists, "
                           "overwrite? [Y/n] ".format(strOutFileName))
            if bOW is True:
                writer(aSorted, strOutFilePath)
            else:
                print "\nDid not write {0}".format(strOutFileName)
        else:
            writer(aSorted, strOutFilePath)
