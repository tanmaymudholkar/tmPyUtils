from __future__ import print_function, division

import os, sys, math

def getMonotonicFunctionApproximateZero(inputFunction=None, xRange=None, zeroTolerance=None, autoZeroTolerance=False, printDebug=False):
    if (printDebug): print("Called for xRange = {xR}, zeroTolerance={zT}".format(xR=xRange, zT=zeroTolerance))
    if (inputFunction is None): raise TypeError("Error in tmStatsUtils.getZeros(): named argument inputFunction is None")
    if not(callable(inputFunction)): raise TypeError("Error in tmStatsUtils.getZeros(): object passed as named argument inputFunction is not callable")

    if xRange is None: raise TypeError("Error in tmStatsUtils.getZeros(): named argument xRange is None")
    if not(len(xRange) == 2): raise TypeError("Error in tmStatsUtils.getZeros(): Given argument xRange = {xR} does not have exactly two elements".format(xR=xRange))

    xmin = xRange[0]
    xmax = xRange[1]
    if (xmax <= xmin): raise ValueError("Error in tmStatsUtils.getZeros(): Argument xRange needs to have min strictly less than max; currently xmin = {xmin}, xmax={xmax}".format(xmin=xmin, xmax=xmax))

    fmin = inputFunction(xmin)
    fmax = inputFunction(xmax)
    if (fmin == fmax): raise ValueError("Error in tmStatsUtils.getZeros(): Given function has same value {val} at either endpoint of the range {xR}".format(xR=xRange, val=fmin))
    xmid = (xmin + xmax)/2.
    fmid = inputFunction(xmid)
    if printDebug: print("Value of called function at (rangeMin={rmin}, rangeMid={rmid}, rangeMax={rmax}): ({fmin}, {fmid}, {fmax})".format(rmin=xmin, rmid=xmid, rmax=xmax, fmin=fmin, fmid=fmid, fmax=fmax))
    monotonicity1 = (fmid > fmin)
    monotonicity2 = (fmax > fmid)
    if (monotonicity1^monotonicity2): # monotonicity1^monotonicity2 is True iff exactly one of them is True
        raise ValueError("Error in tmStatsUtils.getZeros(): Given function does not appear to be monotonic in xRange {xR}; in this range f({xmin}) = {fmin}, f({xmax}) = {fmax}, f({xmid}) = {fmid}".format(xR=xRange, xmin=xmin, fmin=fmin, xmax=xmax, fmax=fmax, xmid=xmid, fmid=fmid))
    monotonicityUp = (monotonicity1 and monotonicity2) # Condition above means control reaches here only if both are True or both False
    if printDebug:
        if (monotonicityUp): print("Passed function is monotonically increasing.")
        else: print("Passed function is monotonically decreasing.")

    if (not(autoZeroTolerance) and (zeroTolerance is None)): raise TypeError("Error in tmStatsUtils.getZeros(): named argument autoZeroTolerance is False, yet zeroTolerance is None.")
    if (autoZeroTolerance): zeroTolerance = 0.0001*abs(fmax - fmin)
    if printDebug: print("zero tolerance set to {zT}".format(zT=zeroTolerance))
    if (abs(fmid) < zeroTolerance): return xmid
    nextRange=[]
    if ((monotonicityUp and fmid > 0.) or (not(monotonicityUp) and fmid < 0.)): nextRange = [xmin, xmid]
    elif((monotonicityUp and fmid < 0.) or (not(monotonicityUp) and fmid > 0.)): nextRange = [xmid, xmax]
    else: sys.exit("Error in tmStatsUtils.getZeros(): Unknown logic error")
    return getMonotonicFunctionApproximateZero(inputFunction=inputFunction, xRange=nextRange, zeroTolerance=zeroTolerance, printDebug=printDebug)
