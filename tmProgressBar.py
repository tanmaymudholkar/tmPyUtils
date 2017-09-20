from __future__ import print_function, division

import ROOT

import sys, math, time

def toInt(floatValue):
    return int(math.floor(0.5+floatValue))

class tmProgressBar:
    def __init__(self, counterMaxValue = 0):
        self.startTime = 0.
        self.counterMaxValue = counterMaxValue

    def initializeTimer(self):
        self.startTime = time.time()

    def updateBar(self, fractionCompleted, counterCurrentValue = 0):
        fractionRemaining = 1 - fractionCompleted
        percentCompleted = toInt(fractionCompleted*100.)
        currentTime = time.time()
        timeElapsed = currentTime - self.startTime
        try:
            latestEstimateTimeRequired = timeElapsed/fractionCompleted
        except ZeroDivisionError:
            latestEstimateTimeRequired = 0.
        guess_timeRemaining = latestEstimateTimeRequired - timeElapsed
        guess_timeRemainingHoursFloat = math.floor(guess_timeRemaining/3600.)
        guess_timeRemainingHours = toInt(guess_timeRemainingHoursFloat)
        guess_timeRemainingMinutesFloat = math.floor((guess_timeRemaining - 3600.*guess_timeRemainingHoursFloat)/60.)
        guess_timeRemainingMinutes = toInt(guess_timeRemainingMinutesFloat)
        guess_timeRemainingSeconds = guess_timeRemaining - 3600.*guess_timeRemainingHoursFloat - 60.*guess_timeRemainingMinutesFloat
        statusBuffer = '\r    [' + '#'*percentCompleted + '-'*(100-percentCompleted) + "]   %d"%(percentCompleted) + "% done. ETA: " + "%02d h, %02d m, %.1f s"%(guess_timeRemainingHours, guess_timeRemainingMinutes, guess_timeRemainingSeconds) + "."
        if (self.counterMaxValue > 0): statusBuffer += " Completed: %d/%d"%(counterCurrentValue, self.counterMaxValue)
        sys.stdout.write(statusBuffer)
        sys.stdout.flush()
