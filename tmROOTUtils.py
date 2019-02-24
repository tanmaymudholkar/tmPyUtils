from __future__ import print_function, division

import ROOT

import os, sys, math, array

ONE_SIGMA_GAUSS = 0.682689492
ZERO_TOLERANCE = 0.000001

def addInputFilesToTree(inputTree, listOfFilesToAdd):
    print ("Adding input files to tree...")
    for filename in listOfFilesToAdd:
        print("Adding: {filename}".format(**locals()))
        inputTree.AddFile(filename)
    print ("Finished adding input files to tree.")

def getMaxValueFromListOfHistograms(listOfInputHistograms):
    runningMaxValue = 0.
    for inputHistogram in listOfInputHistograms:
        currentMaxValue = inputHistogram.GetBinContent(inputHistogram.GetMaximumBin())
        if (runningMaxValue == 0. or currentMaxValue > runningMaxValue): runningMaxValue = currentMaxValue
    return runningMaxValue

def getMinValueFromListOfHistograms(listOfInputHistograms):
    runningMinValue = 0.
    for inputHistogram in listOfInputHistograms:
        currentMinValue = inputHistogram.GetBinContent(inputHistogram.GetMinimumBin())
        if (runningMinValue == 0. or currentMinValue < runningMinValue): runningMinValue = currentMinValue
    return runningMinValue

def setYRangesToListMax(listOfInputHistograms):
    maximumValue = getMaxValueFromListOfHistograms(listOfInputHistograms)
    for inputHistogram in listOfInputHistograms:
        inputHistogram.GetYaxis().SetRangeUser(0., 1.1*maximumValue)

def getRatioGraph(numeratorHistogram, denominatorHistogram):
    graphXAxis = numeratorHistogram.GetXaxis()
    nXBins = graphXAxis.GetNbins()
    ratioGraph = ROOT.TGraphErrors(nXBins)
    for binNumber in range(1, 1+nXBins):
        xValue = graphXAxis.GetBinCenter(binNumber)
        xBinWidth = graphXAxis.GetBinWidth(binNumber)
        numeratorValue = numeratorHistogram.GetBinContent(binNumber)
        denominatorValue = denominatorHistogram.GetBinContent(binNumber)
        ratioValue = 1.
        ratioError = 1.
        if (denominatorValue > 0.):
            ratioValue = numeratorValue/denominatorValue
            numeratorError = numeratorHistogram.GetBinError(binNumber)
            denominatorError = denominatorHistogram.GetBinError(binNumber)
            ratioError = (1.0/denominatorValue)*math.sqrt(math.pow(numeratorError,2) + math.pow(denominatorError*ratioValue,2))
        ratioGraph.SetPoint(binNumber-1, xValue, ratioValue)
        ratioGraph.SetPointError(binNumber-1, xBinWidth, ratioError)
    return ratioGraph

def getGraphOfRatioOfAsymmErrorsGraphToHistogram(numeratorGraph=None, denominatorHistogram=None, outputName="g", outputTitle="", printDebug=False):
    if ((numeratorGraph is None) or (denominatorHistogram is None)):
        sys.exit("ERROR: numeratorGraph or denominatorHistogram are either not passed or None.")
    if not(numeratorGraph.ClassName() == "TGraphAsymmErrors"): sys.exit("ERROR: numeratorGraph is not a TGraphAsymmErrors; its class is {c}".format(c=numeratorGraph.ClassName()))
    if not(denominatorHistogram.InheritsFrom("TH1")): sys.exit("ERROR: denominatorHistogram does not inherit from TH1; its class is {c}".format(c=denominatorHistogram.ClassName()))
    nNumeratorPoints = numeratorGraph.GetN()
    nDenominatorBins = denominatorHistogram.GetXaxis().GetNbins()
    if not(nNumeratorPoints == nDenominatorBins): sys.exit("Binning error: number of points in numerator graph, {n}, is not equal to the number of bins in the denominator histogram, {d}".format(n=nNumeratorPoints, d=nDenominatorBins))
    outputGraph = ROOT.TGraphAsymmErrors(nNumeratorPoints)
    outputGraph.SetName(outputName)
    outputGraph.SetTitle(outputTitle)
    xvalues = numeratorGraph.GetX()
    yvalues = numeratorGraph.GetY()
    for binIndex in range(1, 1+nDenominatorBins):
        pointIndex = binIndex-1
        # numeratorGraph.GetPoint(pointIndex, ROOT.Double(xvalues[pointIndex]), ROOT.Double(yvalues[pointIndex]))
        error_xhigh = numeratorGraph.GetErrorXhigh(pointIndex)
        error_xlow = numeratorGraph.GetErrorXlow(pointIndex)
        error_yhigh = numeratorGraph.GetErrorYhigh(pointIndex)
        error_ylow = numeratorGraph.GetErrorYlow(pointIndex)
        binCenter = denominatorHistogram.GetXaxis().GetBinCenter(binIndex)
        if not(abs(binCenter - xvalues[pointIndex]) < ZERO_TOLERANCE*abs(binCenter)): sys.exit("ERROR: at bin index = {bI}, denominator bin center = {dBC}, graph point x: {x}".format(bI=binIndex, dBC=binCenter, x = xvalues[pointIndex]))
        binContent = denominatorHistogram.GetBinContent(binIndex)
        if (binContent > 0):
            outputGraph.SetPoint(pointIndex, xvalues[pointIndex], yvalues[pointIndex]/binContent)
            outputGraph.SetPointEXlow(pointIndex, error_xlow)
            outputGraph.SetPointEXhigh(pointIndex, error_xhigh)
            outputGraph.SetPointEYlow(pointIndex, error_ylow/binContent)
            outputGraph.SetPointEYhigh(pointIndex, error_yhigh/binContent)
            if printDebug: print("Setting point: x={x1} (-{x2}+{x3}), y={y1}(-{y2}+{y3})".format(x1=xvalues[pointIndex], x2=error_xlow, x3=error_xhigh, y1=yvalues[pointIndex]/binContent, y2=error_ylow/binContent, y3=error_yhigh/binContent))
        else:
            print("WARNING: at bin index = {bI}, histogram contents = 0; setting ratio to 0".format(bI=binIndex))
            outputGraph.SetPoint(pointIndex, xvalues[pointIndex], 0.)
            outputGraph.SetPointEXlow(pointIndex, error_xlow)
            outputGraph.SetPointEXhigh(pointIndex, error_xhigh)
            outputGraph.SetPointEYlow(pointIndex, 0.)
            outputGraph.SetPointEYhigh(pointIndex, 0.)
            if printDebug: print("Setting point: x={x1} (-{x2}+{x3}), y=0.0(-0.0+0.0)".format(x1=xvalues[pointIndex], x2=error_xlow, x3=error_xhigh))
    return outputGraph

def normalizeHistogam(inputHist):
    normalizationFactor = inputHist.Integral("width")
    try:
        inputHist.Scale(1./normalizationFactor)
    except ZeroDivisionError:
        print("No entries in histogram with title " + inputHist.GetTitle() + " to normalize")

def getSumOfBinContents(inputTH1):
    nBins = inputTH1.GetXaxis().GetNbins()
    sumBinContents = 0
    for binCounter in range(0, 2+nBins):
        sumBinContents += inputTH1.GetBinContent(binCounter)
    return sumBinContents

def extractTH2Contents(inputTH2, outputFileName, columnTitles=None, quantityName=None, includeOverflow=False, formatSpecifiers=None, onlyOutputNonzero=True, printRangeX=False, printRangeY=False):
    zeroTolerance = ZERO_TOLERANCE*inputTH2.GetBinContent(inputTH2.GetMaximumBin())
    print("Extracting info from histogram...")
    outputFile = open(outputFileName, 'w')
    xAxis = inputTH2.GetXaxis()
    yAxis = inputTH2.GetYaxis()
    if columnTitles is None: columnTitles = [xAxis.GetTitle(), yAxis.GetTitle()]
    if quantityName is None: quantityName = "Quantity"
    if formatSpecifiers is None: formatSpecifiers = ["%.1f", "%.1f", "%.3e"]
    titlesLine = "# "
    for columnTitle in columnTitles:
        titlesLine += "%s    "%(columnTitle)
    titlesLine += "%s\n"%(quantityName)
    outputFile.write(titlesLine)
    nBinsX = xAxis.GetNbins()
    nBinsY = yAxis.GetNbins()
    xBinCounter = 1
    xBinMax = nBinsX
    if includeOverflow:
        xBinCounter = 0
        xBinMax = nBinsX + 1
        
    while (xBinCounter <= xBinMax):
        xBinCenterValue = xAxis.GetBinCenter(xBinCounter)
        xBinLowEdge = xAxis.GetBinLowEdge(xBinCounter)
        xBinUpEdge = xAxis.GetBinUpEdge(xBinCounter)
        lineToOutputPrefix = ("%s    "%(formatSpecifiers[0]))%(xBinCenterValue)
        if (printRangeX): lineToOutputPrefix = ("%s    %s    "%(formatSpecifiers[0], formatSpecifiers[0]))%(xBinLowEdge, xBinUpEdge)
        yBinCounter = 1
        yBinMax = nBinsY
        if includeOverflow:
            yBinCounter = 0
            yBinMax = nBinsY + 1
        while (yBinCounter <= yBinMax):
            yBinCenterValue = yAxis.GetBinCenter(yBinCounter)
            yBinLowEdge = yAxis.GetBinLowEdge(yBinCounter)
            yBinUpEdge = yAxis.GetBinUpEdge(yBinCounter)
            globalBinNumber = inputTH2.GetBin(xBinCounter, yBinCounter)
            histContent = inputTH2.GetBinContent(globalBinNumber)
            lineToOutput = lineToOutputPrefix + ("%s    %s\n"%(formatSpecifiers[1], formatSpecifiers[2]))%(yBinCenterValue, histContent)
            if (printRangeY): lineToOutput = lineToOutputPrefix + ("%s    %s    %s\n"%(formatSpecifiers[1], formatSpecifiers[1], formatSpecifiers[2]))%(yBinLowEdge, yBinUpEdge, histContent)
            if (not(onlyOutputNonzero) or (histContent > zeroTolerance)): outputFile.write(lineToOutput)
            yBinCounter += 1
        xBinCounter += 1
    outputFile.close()
    print("Histogram contents saved to file %s"%(outputFileName))

def plotObjectsOnCanvas(listOfObjects=None, canvasName="", outputROOTFile=None, outputDocumentName="", outputDocumentExtension="png", canvas_xPixels=1024, canvas_yPixels=768, customOptStat=None, customTextFormat=None, customPlotOptions_firstObject="", enableLogX = False, enableLogY = False, enableLogZ = False, customXRange=None, customYRange=None, customZRange=None):
    if (listOfObjects is None): sys.exit("Error in plotObjectsOnCanvas: no object found in listOfObjects.")
    if (canvasName == ""): sys.exit("Error in plotObjectsOnCanvas: No name specified for canvas.")
    if ((outputROOTFile is None) and (outputDocumentName == "")): sys.exit("Error in plotObjectsOnCanvas: Neither output ROOT file nor output document name specified.")
    if not(customOptStat is None): ROOT.gStyle.SetOptStat(customOptStat)
    if not(customTextFormat is None): ROOT.gStyle.SetPaintTextFormat(customTextFormat)
    canvas = ROOT.TCanvas(canvasName, canvasName, canvas_xPixels, canvas_yPixels)
    canvas.SetBorderSize(0)
    canvas.SetFrameBorderMode(0)
    if enableLogX: ROOT.gPad.SetLogx()
    if enableLogY: ROOT.gPad.SetLogy()
    if enableLogZ: ROOT.gPad.SetLogz()
    def printInfo(obj):
        print("Drawing object with name={n}, title={t}, class={c}".format(n=obj.GetName(), t=obj.GetTitle(), c=obj.ClassName()))
    listOfObjects[0].Draw(customPlotOptions_firstObject)
    printInfo(listOfObjects[0])
    if not(customXRange is None): listOfObjects[0].GetXaxis().SetRangeUser(customXRange[0], customXRange[1])
    if not(customYRange is None): listOfObjects[0].GetYaxis().SetRangeUser(customYRange[0], customYRange[1])
    if not(customZRange is None): listOfObjects[0].GetZaxis().SetRangeUser(customZRange[0], customZRange[1])
    if not(outputROOTFile is None): outputROOTFile.WriteTObject(listOfObjects[0])
    # Rest of objects need to be drawn with option "same"
    for objectCounter in range(1, len(listOfObjects)):
        listOfObjects[objectCounter].Draw("same")
        printInfo(listOfObjects[objectCounter])
        if not(outputROOTFile is None): outputROOTFile.WriteTObject(listOfObjects[objectCounter])
    if not(outputDocumentName == ""): canvas.SaveAs("{outputDocumentName}.{outputDocumentExtension}".format(outputDocumentName=outputDocumentName, outputDocumentExtension=outputDocumentExtension))
    if not(outputROOTFile is None): outputROOTFile.WriteTObject(canvas)
    return canvas

def get2DHistogramContentAndErrorAtCoordinates(inputTH2=None, xValue=None, yValue=None, haveStrictRangeChecks=True):
    if (inputTH2 is None): sys.exit("The named variable inputTH2 points to None.")
    if (xValue is None or yValue is None): sys.exit("Both xValue and yValue need to be specified.")
    nBinsX = inputTH2.GetXaxis().GetNbins()
    nBinsY = inputTH2.GetYaxis().GetNbins()
    insideRange = True
    xBin = inputTH2.GetXaxis().FindFixBin(xValue)
    if (xBin == 0 or xBin == 1+nBinsX): insideRange = False
    yBin = inputTH2.GetYaxis().FindFixBin(yValue)
    if (yBin == 0 or yBin == 1+nBinsY): insideRange = False
    if (haveStrictRangeChecks and not(insideRange)):
        axes_xMin = inputTH2.GetXaxis().GetXmin()
        axes_xMax = inputTH2.GetXaxis().GetXmax()
        axes_yMin = inputTH2.GetYaxis().GetXmin() # "xmin" is a confusing name
        axes_yMax = inputTH2.GetYaxis().GetXmax() # "xmax" is a confusing name
        sys.exit("Given coordinates: ({xval}, {yval}) are not inside the 2D range of the input TH2 axes: ({xmin}, {ymin}) ---> ({xmax}, {ymax})".format(xval=xValue, yval=yValue, xmin=axes_xMin, ymin=axes_yMin, xmax=axes_xMax, ymax=axes_yMax))
    globalBinIndex = inputTH2.GetBin(xBin, yBin)
    binContent = inputTH2.GetBinContent(globalBinIndex)
    binError = inputTH2.GetBinError(globalBinIndex)
    outputDict = {"content": binContent, "error": binError}
    return outputDict

def getNEventsInNamedRangeInRooDataSet(inputRooDataSet, rangeName, forceNumEntries=False): # By default enter "sumEntries" which accounts for the weight, otherwise return "numEntries"
    if forceNumEntries:
        reducedRooDataSet = inputRooDataSet.reduce(ROOT.RooFit.CutRange(rangeName), ROOT.RooFit.Name(inputRooDataSet.GetName() + "_reduced"), ROOT.RooFit.Title(inputRooDataSet.GetTitle() + "_reduced"))
        return reducedRooDataSet.numEntries()
    return inputRooDataSet.sumEntries("1 > 0", rangeName)

def getPoissonConfidenceInterval(confidenceLevel = ONE_SIGMA_GAUSS, observedNEvents = 0):
    # Copied from TH1 source code: https://github.com/root-project/root/blob/master/hist/hist/src/TH1.cxx
    alpha = 1. - confidenceLevel
    lowerLimit = 0.
    if observedNEvents > 0: lowerLimit = ROOT.Math.gamma_quantile((alpha/2.), observedNEvents, 1.)
    upperLimit = ROOT.Math.gamma_quantile_c((alpha/2.), 1+observedNEvents, 1.)
    outputDict = {"lower": lowerLimit, "upper": upperLimit}
    return outputDict

def rescale1DHistogramByBinWidth(input1DHistogram = None):
    if (input1DHistogram is None): sys.exit("option input1DHistogram is not passed or is None.")
    if (input1DHistogram.InheritsFrom("TH1")):
        if (input1DHistogram.InheritsFrom("TH2") or input1DHistogram.InheritsFrom("TH3")):
            sys.exit("Unable to scale 2D or 3D histograms.")
    else:
        sys.exit("Input histogram does not inherit from TH1. Class: {c}".format(c=input1DHistogram.ClassName()))
    inputClone = input1DHistogram.Clone()
    input1DHistogram.Reset()
    input1DHistogram.SetBinErrorOption(inputClone.GetBinErrorOption())
    if(inputClone.GetBinErrorOption() == ROOT.TH1.kPoisson):
        print("WARNING: trying to rescale histogram with name {n} with Poisson errors: unsure if error bars will work correctly, trying anyway...".format(n=inputClone.GetName()))
    inputXAxis = inputClone.GetXaxis()
    for binCounter in range(0, 2+inputXAxis.GetNbins()):
        binCenter = inputXAxis.GetBinCenter(binCounter)
        binContent = inputClone.GetBinContent(binCounter)
        binError = inputClone.GetBinError(binCounter)
        binWidth = inputXAxis.GetBinWidth(binCounter)
        if(inputClone.GetBinErrorOption() == ROOT.TH1.kPoisson):
            if (abs(int(0.5+binContent)-binContent) <= ZERO_TOLERANCE*binContent): # Because "getBinContent", even on ROOT's TH1I, apparently returns a float
                for uglyHackCounter in range(0, int(0.5+binContent)):
                    input1DHistogram.Fill(binCenter, 1.0/binWidth)
            else:
                sys.exit("input histogram has Poisson errors but a non-integer number of events {n} in bin {i}. Don't know how to rescale...".format(n=binContent, i=binCounter))
        else:
            input1DHistogram.SetBinContent(binCounter, binContent/binWidth)
            input1DHistogram.SetBinError(binCounter, binError/binWidth)

def printHistogramContents(inputHistogram = None):
    if (inputHistogram is None): sys.exit("option inputHistogram is not passed or is None.")
    if (inputHistogram.InheritsFrom("TH1")):
        if (inputHistogram.InheritsFrom("TH2") or inputHistogram.InheritsFrom("TH3")):
            sys.exit("Printing contents of 2D or 3D histograms not supported for now...")
    else:
        sys.exit("Input histogram does not inherit from TH1. Class: {c}".format(c=inputHistogram.ClassName()))
    print("Printing contents of histogram with name = {n}, title = {t}".format(n=inputHistogram.GetName(), t=inputHistogram.GetTitle()))
    inputXAxis = inputHistogram.GetXaxis()
    for binCounter in range(0, 2+inputXAxis.GetNbins()):
        binEdgeLow = inputXAxis.GetBinLowEdge(binCounter)
        binEdgeHigh = inputXAxis.GetBinUpEdge(binCounter)
        binContent = inputHistogram.GetBinContent(binCounter)
        binError = inputHistogram.GetBinError(binCounter)
        binErrorLow = binError
        binErrorHigh = binError
        if(inputHistogram.GetBinErrorOption() == ROOT.TH1.kPoisson):
            binErrorLow = inputHistogram.GetBinErrorLow(binCounter)
            binErrorHigh = inputHistogram.GetBinErrorUp(binCounter)
        print("Bin index {i}: {l} < var < {h}; content: {c} (- {el} + {eh})".format(i=binCounter, l=binEdgeLow, h=binEdgeHigh, c=binContent, el=binErrorLow, eh=binErrorHigh))

def getTLineAngleInDegrees(pad, tline, printDebug = False):
    x1 = pad.XtoPixel(tline.GetX1())
    y1 = (-1)*pad.YtoPixel(tline.GetY1()) # y axis is "flipped" in pixels: top left is (0, 0)
    x2 = pad.XtoPixel(tline.GetX2())
    y2 = (-1)*pad.YtoPixel(tline.GetY2()) # y axis is "flipped" in pixels: top left is (0, 0)
    if (printDebug): print("line: (x1, y1) = ({x1}, {y1}), (x2, y2) = ({x2}, {y2})".format(x1=x1, y1=y1, x2=x2, y2=y2))

    # Deal with horizontal and vertical lines first
    if ((x1 == x2) and (y1 == y2)):
        sys.exit("ERROR: TLine does not have well-defined distinct endpoints. Found in pixel coordinates: (x1, y1) = ({x1}, {y1}), (x2, y2) = ({x2}, {y2})".format(x1=x1, y1=y1, x2=x2, y2=y2))
    if (y1 == y2): #  horizontal
        if (x2 > x1): #  left to right
            if (printDebug): print("TLine is horizontal left to right.")
            return 0.
        else: #  right to left
            if (printDebug): print("TLine is horizontal right to left.")
            return 180.
    if (x1 == x2): #  vertical
        if (y2 > y1): #  bottom to top
            if (printDebug): print("TLine is vertical bottom to top.")
            return 90.
        else: #  top to bottom
            if (printDebug): print("TLine is vertical top to bottom.")
            return 270.

    # Find quadrant
    quadrant = 0
    if (x2 > x1): #  left to right
        if (y2 > y1): # bottom to top
            if (printDebug): print("TLine belongs to first quadrant.")
            quadrant = 1
        else: # top to bottom
            if (printDebug): print("TLine belongs to fourth quadrant.")
            quadrant = 4
    else: # right to left
        if (y2 > y1): # bottom to top
            if (printDebug): print("TLine belongs to second quadrant.")
            quadrant = 2
        else: # top to bottom
            if (printDebug): print("TLine belongs to third quadrant.")
            quadrant = 3

    width_x = abs(x2-x1)
    width_y = abs(y2-y1)
    if (printDebug): print("width_x = {wx}, width_y = {wy}".format(wx=width_x, wy=width_y))
    angleInDegreesWithRespectToHorizontal = (180./math.pi)*math.atan(width_y/width_x)
    fullAngleInDegrees = 0.
    if (quadrant == 1):
        fullAngleInDegrees = angleInDegreesWithRespectToHorizontal
    elif (quadrant == 2):
        fullAngleInDegrees = 180.- angleInDegreesWithRespectToHorizontal
    elif (quadrant == 3):
        fullAngleInDegrees = 180. + angleInDegreesWithRespectToHorizontal
    elif (quadrant == 4):
        fullAngleInDegrees = 360. - angleInDegreesWithRespectToHorizontal
    else:
        sys.exit("Unknown quadrant: {q}".format(q=quadrant))
    if (printDebug): print("Found angle: {a}".format(a=fullAngleInDegrees))
    return fullAngleInDegrees
