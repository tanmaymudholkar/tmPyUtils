from __future__ import print_function, division

import ROOT

import sys, math, time

def toInt(floatValue):
    return int(math.floor(0.5+floatValue))

class tmProgressBar:
    def __init__(self, counterMaxValue=0, progressBarCharacter=">"):
        self.timeAtLastCheck = 0.
        self.fractionCompletedAtLastCheck = 0.
        self.counterMaxValue = counterMaxValue
        self.progressBarCharacter = progressBarCharacter
        self.formatString = ""
        if counterMaxValue > 0:
            nDigitsCounterMax = len(str(counterMaxValue))
            self.formatString = "{n}d".format(n=nDigitsCounterMax)

    def initializeTimer(self):
        self.timeAtLastCheck = time.time()
        self.fractionCompletedAtLastCheck = 0.

    def updateBar(self, fractionCompleted, counterCurrentValue = 0):
        fractionRemaining = 1 - fractionCompleted
        percentCompleted = toInt(fractionCompleted*100.)
        currentTime = time.time()
        timeElapsed = currentTime - self.timeAtLastCheck
        fractionCompletedSinceLastCheck = fractionCompleted - self.fractionCompletedAtLastCheck
        completionRate = fractionCompletedSinceLastCheck/timeElapsed
        try:
            latestEstimateTimeRequired = fractionRemaining/completionRate
        except ZeroDivisionError:
            latestEstimateTimeRequired = 0.
        guess_timeRemaining = latestEstimateTimeRequired - timeElapsed
        guess_timeRemainingHoursFloat = math.floor(guess_timeRemaining/3600.)
        guess_timeRemainingHours = toInt(guess_timeRemainingHoursFloat)
        guess_timeRemainingMinutesFloat = math.floor((guess_timeRemaining - 3600.*guess_timeRemainingHoursFloat)/60.)
        guess_timeRemainingMinutes = toInt(guess_timeRemainingMinutesFloat)
        guess_timeRemainingSeconds = guess_timeRemaining - 3600.*guess_timeRemainingHoursFloat - 60.*guess_timeRemainingMinutesFloat
        statusBuffer = '\r    [' + (self.progressBarCharacter)*percentCompleted + '-'*(100-percentCompleted) + ("]   {pC:3d} % done. ETA: {hours:2d} h: {minutes:2d} m: {seconds:>04.1f} s.").format(pC=percentCompleted, hours=guess_timeRemainingHours, minutes=guess_timeRemainingMinutes, seconds=guess_timeRemainingSeconds)
        if (self.counterMaxValue > 0): statusBuffer += (" Completed: {currentValue:" + self.formatString + "}/{maxValue:" + self.formatString + "}.").format(currentValue=counterCurrentValue, maxValue=self.counterMaxValue)
        sys.stdout.write(statusBuffer)
        sys.stdout.flush()
        self.timeAtLastCheck = currentTime
        self.fractionCompletedAtLastCheck = fractionCompleted

    def terminate(self):
        # self.updateBar(1., self.counterMaxValue) # Commented to catch potential bugs with loop exiting before expected end. Side-effect of the commenting is that it makes the bar uglier in the output...
        print("")

def tmProgressBarTest():
    print("Beginning tests...")
    progressBar = tmProgressBar(counterMaxValue=1000, progressBarCharacter="+")
    progressBar.initializeTimer()
    for testCounter in range(1, 1001):
        if (testCounter < 900):
            time.sleep(0.01)
        else:
            time.sleep(0.1)
        progressBar.updateBar(testCounter/1000, testCounter)
    progressBar.terminate()
    print("Finished tests.")

if __name__ == "__main__":
    tmProgressBarTest()
