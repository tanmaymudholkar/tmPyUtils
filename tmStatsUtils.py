from __future__ import print_function, division

import os, sys, math

DEFAULT_ZERO_TOLERANCE_COEFFICIENT=0.001

def getMonotonicFunctionApproximateZero(inputFunction=None, xRange=None, zeroTolerance=None, autoZeroTolerance=False, printDebug=False):
    if (printDebug): print("getMonotonicFunctionApproximateZero called for xRange = {xR}, zeroTolerance={zT}".format(xR=xRange, zT=zeroTolerance))
    if (inputFunction is None): raise TypeError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): named argument inputFunction is None")
    if not(callable(inputFunction)): raise TypeError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): object passed as named argument inputFunction is not callable")

    if xRange is None: raise TypeError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): named argument xRange is None")
    if not(len(xRange) == 2): raise TypeError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): Given argument xRange = {xR} does not have exactly two elements".format(xR=xRange))

    xmin = xRange[0]
    xmax = xRange[1]
    if (xmax <= xmin): raise ValueError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): Argument xRange needs to have min strictly less than max; currently xmin = {xmin}, xmax={xmax}".format(xmin=xmin, xmax=xmax))

    fmin = inputFunction(xmin)
    fmax = inputFunction(xmax)
    if (fmin == fmax): raise ValueError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): Given function has same value {val} at either endpoint of the range {xR}".format(xR=xRange, val=fmin))
    xmid = (xmin + xmax)/2.
    fmid = inputFunction(xmid)
    if printDebug: print("Value of called function at (rangeMin={rmin}, rangeMid={rmid}, rangeMax={rmax}): ({fmin}, {fmid}, {fmax})".format(rmin=xmin, rmid=xmid, rmax=xmax, fmin=fmin, fmid=fmid, fmax=fmax))
    monotonicity1 = (fmid > fmin)
    monotonicity2 = (fmax > fmid)
    if (monotonicity1^monotonicity2): # monotonicity1^monotonicity2 is True iff exactly one of them is True
        raise ValueError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): Given function does not appear to be monotonic in xRange {xR}; in this range f({xmin}) = {fmin}, f({xmax}) = {fmax}, f({xmid}) = {fmid}".format(xR=xRange, xmin=xmin, fmin=fmin, xmax=xmax, fmax=fmax, xmid=xmid, fmid=fmid))
    monotonicityUp = (monotonicity1 and monotonicity2) # Condition above means control reaches here only if both are True or both False
    if printDebug:
        if (monotonicityUp): print("Passed function is monotonically increasing.")
        else: print("Passed function is monotonically decreasing.")

    if (not(autoZeroTolerance) and (zeroTolerance is None)): raise TypeError("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): named argument autoZeroTolerance is False, yet zeroTolerance is None.")
    if (autoZeroTolerance): zeroTolerance = DEFAULT_ZERO_TOLERANCE_COEFFICIENT*abs(fmax - fmin)
    if printDebug: print("zero tolerance set to {zT}".format(zT=zeroTolerance))
    if (abs(fmid) < zeroTolerance):
        if printDebug:
            print("Found zero within tolerance at: {v}".format(v=xmid))
        return xmid
    else:
        if printDebug:
            print("Midpoint not yet within zero tolerance, trying new range.")
    nextRange=[]
    if ((monotonicityUp and fmid > 0.) or (not(monotonicityUp) and fmid < 0.)): nextRange = [xmin, xmid]
    elif((monotonicityUp and fmid < 0.) or (not(monotonicityUp) and fmid > 0.)): nextRange = [xmid, xmax]
    else: sys.exit("Error in tmStatsUtils.getMonotonicFunctionApproximateZero(): Unknown logic error")
    return getMonotonicFunctionApproximateZero(inputFunction=inputFunction, xRange=nextRange, zeroTolerance=zeroTolerance, printDebug=printDebug)

def getStrictlyConvexFunctionApproximateMinimum(inputFunction=None, xRange=None, zeroTolerance=None, autoZeroTolerance=False, printDebug=False):
    if (printDebug): print("getStrictlyConvexFunctionApproximateMinimum called for xRange = {xR}, zeroTolerance={zT}".format(xR=xRange, zT=zeroTolerance))
    if (inputFunction is None): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): named argument inputFunction is None")
    if not(callable(inputFunction)): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): object passed as named argument inputFunction is not callable")

    if xRange is None: raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): named argument xRange is None")
    if not(len(xRange) == 2): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): Given argument xRange = {xR} does not have exactly two elements".format(xR=xRange))

    xmin = xRange[0]
    xmax = xRange[1]
    if (xmax <= xmin): raise ValueError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): Argument xRange needs to have min strictly less than max; currently xmin = {xmin}, xmax={xmax}".format(xmin=xmin, xmax=xmax))

    # Finding the minimum of a strictly convex function is the same problem as finding the zero of its slope, which should be monotonically increasing
    # In principle, this function could be easily modified to work with strictly concave functions -- just multiply by -1 -- but I don't need that now :-D

    delta_x = DEFAULT_ZERO_TOLERANCE_COEFFICIENT*(xmax - xmin)
    def functionSlope(x=None):
        if x is None: raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum.functionSlope: named argument x is None")
        return ((inputFunction(x+delta_x) - inputFunction(x-delta_x))/(2*delta_x))

    if (printDebug): print("Now passing slope of function to getMonotonicFunctionApproximateZero:")
    return getMonotonicFunctionApproximateZero(inputFunction=functionSlope, xRange=xRange, zeroTolerance=zeroTolerance, autoZeroTolerance=autoZeroTolerance, printDebug=printDebug)

def getGlobalMinimum(inputFunction=None, xRange=None, zeroTolerance=None, autoZeroTolerance=False, printDebug=False):
    # Works for functions that have a well-defined minimum but are not necessarily convex throughout xRange
    if (printDebug): print("getGlobalMinimum called for xRange = {xR}, zeroTolerance={zT}".format(xR=xRange, zT=zeroTolerance))
    if (inputFunction is None): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): named argument inputFunction is None")
    if not(callable(inputFunction)): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): object passed as named argument inputFunction is not callable")

    if xRange is None: raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): named argument xRange is None")
    if not(len(xRange) == 2): raise TypeError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): Given argument xRange = {xR} does not have exactly two elements".format(xR=xRange))

    xmin = xRange[0]
    xmax = xRange[1]
    if (xmax <= xmin): raise ValueError("Error in tmStatsUtils.getStrictlyConvexFunctionApproximateMinimum(): Argument xRange needs to have min strictly less than max; currently xmin = {xmin}, xmax={xmax}".format(xmin=xmin, xmax=xmax))

    # Step 1: find location of global minimum by stepping through the data
    globalMinimum = None
    globalMinimumX = None
    for xcounter in range(0, 101):
        xvalue = xmin + (xcounter/100)*(xmax - xmin)
        functionValue = inputFunction(xvalue)
        if ((globalMinimum is None) or (functionValue < globalMinimum)):
            globalMinimum = functionValue
            globalMinimumX = xvalue
    # Step 2: assume that the function will be convex over 5% of the input range at least (if not, the following will throw an exception)
    return getStrictlyConvexFunctionApproximateMinimum(inputFunction=inputFunction, xRange=[globalMinimumX - 0.025*(xmax - xmin), globalMinimumX + 0.025*(xmax - xmin)], zeroTolerance=zeroTolerance, autoZeroTolerance=autoZeroTolerance, printDebug=printDebug)

def tmStatsUtilsTest():
    print("Beginning tests:")
    nColumns = os.getenv("COLUMNS")
    if nColumns is None: nColumns = 200
    print("~"*nColumns)

    print("Tests for getMonotonicFunctionApproximateZero:")
    def testForApproximateZero_increasing(x):
        return (x - 0.25)*(1 + (x-0.25)*(x-0.25))
    def testForApproximateZero_decreasing(x):
        return (-1.0)*testForApproximateZero_increasing(x)
    testZero = getMonotonicFunctionApproximateZero(inputFunction=testForApproximateZero_increasing, xRange=[-1.2, 1.1], autoZeroTolerance=True, printDebug=True)
    print("Expected: 0.25, found: {tZ}".format(tZ=testZero))
    print("~"*nColumns)
    testZero = getMonotonicFunctionApproximateZero(inputFunction=testForApproximateZero_decreasing, xRange=[-1.2, 1.1], autoZeroTolerance=True, printDebug=True)
    print("Expected: 0.25, found: {tZ}".format(tZ=testZero))
    print("~"*nColumns)

    print("Tests for getStrictlyConvexFunctionApproximateMinimum:")
    def testForApproximateMinimum(x):
        return (-1.5 + (x + 0.25)*(x + 0.25))
    testMinimum = getStrictlyConvexFunctionApproximateMinimum(inputFunction=testForApproximateMinimum, xRange=[-1.2, 1.1], autoZeroTolerance=True, printDebug=True)
    print("Expected: -0.25, found: {tM}".format(tM=testMinimum))
    print("~"*nColumns)

if __name__ == "__main__":
    tmStatsUtilsTest()
