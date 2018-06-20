from __future__ import print_function, division

import ROOT

import os, sys, math

ONE_SIGMA_GAUSS = 0.682689492

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
        ratioValue = 0.
        ratioError = 0.
        if (denominatorValue > 0.):
            ratioValue = numeratorValue/denominatorValue
            numeratorError = numeratorHistogram.GetBinError(binNumber)
            denominatorError = denominatorHistogram.GetBinError(binNumber)
            ratioError = math.sqrt(math.pow(numeratorError,2) + math.pow(denominatorError*ratioValue,2))/denominatorValue
        ratioGraph.SetPoint(binNumber-1, xValue, ratioValue)
        ratioGraph.SetPointError(binNumber-1, xBinWidth, ratioError)
    return ratioGraph

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
    zeroTolerance = 0.000001*inputTH2.GetBinContent(inputTH2.GetMaximumBin())
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

def getNEventsInNamedRangeInRooDataSet(inputRooDataSet, rangeName):
    reducedRooDataSet = inputRooDataSet.reduce(ROOT.RooFit.CutRange(rangeName), ROOT.RooFit.Name(inputRooDataSet.GetName() + "_reduced"), ROOT.RooFit.Title(inputRooDataSet.GetTitle() + "_reduced"))
    return (reducedRooDataSet.numEntries())

def getPoissonConfidenceInterval(confidenceLevel = ONE_SIGMA_GAUSS, observedNEvents = 0):
    # Copied from TH1 source code: https://github.com/root-project/root/blob/master/hist/hist/src/TH1.cxx
    alpha = 1. - confidenceLevel
    lowerLimit = 0.
    if observedNEvents > 0: lowerLimit = ROOT.Math.gamma_quantile((alpha/2.), observedNEvents, 1.)
    upperLimit = ROOT.Math.gamma_quantile_c((alpha/2.), 1+observedNEvents, 1.)
    outputDict = {"lower": lowerLimit, "upper": upperLimit}
    return outputDict
