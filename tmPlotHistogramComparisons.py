#!/usr/bin/env python

from __future__ import print_function, division
import os, sys, argparse, pdb, math, json, subprocess
import tmGeneralUtils, tmROOTUtils

# Register command line options
inputArgumentsParser = argparse.ArgumentParser(description='General tool to generate a CMS-formatted comparison of various histograms; list is read in from an input JSON file.')
inputArgumentsParser.add_argument('--inputFilePath', required=True, help='Path to input JSON.',type=str)
inputArgumentsParser.add_argument('--userString', default="", help='The set of characters \"{uS}\" in the input JSON is replaced with the value of this argument.',type=str)
inputArgumentsParser.add_argument('--printTemplate', action='store_true', help="Only print template for a skeleton JSON file and exit.")
inputArguments = inputArgumentsParser.parse_args()

def getFormattedInputData(rawSource):
    return ((str(rawSource)).format(uS=inputArguments.userString))

if inputArguments.printTemplate:
    print("Template: ")
    print("""
{
    "outputDirectory": "~/nobackup/temp", # directory in which files given by "outputPath" are written
    "targets": {
        "histograms_2Jets": { # Each set of comparisons to produce is given a label (aka a "target" in the following code). Here we have two sets of comparisons, with the labels "histograms_2Jets" and "histograms_3Jets".
            "outputPath": "STHistograms_2Jets.pdf", # path to output file
            "title": "ST Histograms, 2 Jets", # title, currently not working because it overlaps the CMS logo
            "xLabel": "S_{T} (GeV)", # x-axis label
            "yLabel": "A.U.", # y-axis label
            "logY": "true", # whether or not to set log scale for y-axis
            "drawCMSLumi": "true", # whether or not to write luminosity (should generally be true for data, false for MC)
            "legend": {
                "nColumns": "3" # number of columns in legend
                # optional, not included in this example: edgeLeft, edgeBottom, edgeRight, edgeTop, which control the edges of the legend
            },
            "normType": "integral", # currently only one argument, "integral", is supported; if this is set, the histograms are normalized to the same integral (rather than the same value in a normalization bin)
            "normX": "1250.0", # the x value at which to scale the bin contents of all histograms to 1
            "plotXMin": "1200.0", # x range min to plot
            "plotXMax": "3500.0", # x range max to plot
            "plotYMin": "0.001", # y range min to plot
            "plotYMax": "2.0", # y range max to plot
            "ratioDenominatorLabel": "signal", # label whose histogram is to be considered as the denominator while taking the ratio
            "ratioType": "pull", # can take exactly two arguments: "pull", in which case bottom plot displays (ratio-1)/ratioError, or "nominal", in which case bottom plot displays nominal ratio.
            "saveRatiosToFile": "false", # if set to "true", then ratios are saved separately in a text file given by the argument "saveRatiosFile"
            "saveRatioPlotsToFile": "false", # if set to "true", then ratio plots are saved separately in a file given by the argument "saveRatioPlotsFile"
            "ratioYMin": "-0.5", # y range min of ratio plot
            "ratioYMax": "3.5", # y range max of ratio plot
            "pullYMin": "-0.5", # y range min of pull plot
            "pullYMax": "3.5", # y range max of pull plot
            "order": "signal, signal_loose, control", # order in which to plot the histograms
            "sources": {
                "signal": { # within each set of comparisons to produce, each histogram is given a label. Here we have three histograms in this comparison, with the labels "signal", "signal_loose", and "control".
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_STComparisons_savedSTShapes.root", # path to file containing histogram
                    "histogramName": "h_STDistribution_total_2Jets", # name of histogram within file
                    "color": "blue", # color to use for this histogram.
                    "label": "signal" # what to use as a label in the legend
                },
                "signal_loose": { # same syntax as above
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_loose_STComparisons_savedSTShapes.root",
                    "histogramName": "h_STDistribution_total_2Jets",
                    "color": "red",
                    "label": "loose signal"
                },
                "control": { # same syntax as above
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/control_STComparisons_savedSTShapes.root",
                    "histogramName": "h_STDistribution_total_2Jets",
                    "color": "green",
                    "label": "control"
                }
            }
        },
        "histograms_3Jets": { # same syntax as above
            "outputPath": "STHistograms_3Jets.pdf",
            "title": "ST Histograms, 3 Jets",
            "xLabel": "S_{T} (GeV)",
            "yLabel": "A.U.",
            "logY": "true",
            "drawCMSLumi": "true",
            "legend": {
                "nColumns": "3"
            },
            "normX": "1250.0",
            "plotXMin": "1200.0",
            "plotXMax": "3500.0",
            "plotYMin": "0.001",
            "plotYMax": "2.0",
            "ratioDenominatorLabel": "signal",
            "ratioType": "nominal",
            "ratioYMin": "-0.5",
            "ratioYMax": "3.5",
            "order": "signal, signal_loose, control",
            "sources": {
                "signal": {
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_STComparisons_savedSTShapes.root",
                    "histogramName": "h_STDistribution_total_3Jets",
                    "color": "blue"
                },
                "signal_loose": {
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_loose_STComparisons_savedSTShapes.root",
                    "histogramName": "h_STDistribution_total_3Jets",
                    "color": "red"
                },
                "control": {
                    "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/control_STComparisons_savedSTShapes.root",
                    "histogramName": "h_STDistribution_total_3Jets",
                    "color": "green"
                }
            }
        }
    }
}
    """)
    sys.exit(0)

def saveComparisons(target):
    import ROOT
    colorsDict = {"red": ROOT.kRed+2, "khaki": ROOT.kYellow+2, "green": ROOT.kGreen+2, "teal": ROOT.kCyan+2, "blue": ROOT.kBlue+2, "violet": ROOT.kMagenta+2, "black": ROOT.kBlack, "grey": ROOT.kWhite+2}

    import tdrstyle, CMS_lumi
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.TH1.AddDirectory(ROOT.kFALSE)

    tdrstyle.setTDRStyle()

    commonTitleOffset = 0.7
    commonLineWidth = 3
    commonTitleSize = 0.06
    commonLabelSize = 0.05
    HEIGHT_REF = 600
    WIDTH_REF = 800
    WIDTH = WIDTH_REF
    HEIGHT  = HEIGHT_REF
    TOP = 0.08*HEIGHT_REF
    BOTTOM = 0.12*HEIGHT_REF
    LEFT = 0.12*WIDTH_REF
    RIGHT = 0.04*WIDTH_REF

    print("Saving comparisons for target: {t}".format(t=target))
    inputDetails = inputPlots["targets"][target]

    canvas = ROOT.TCanvas("oC_{t}".format(t=target), "oC_{t}".format(t=target), 50, 50, WIDTH, HEIGHT)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetLeftMargin( LEFT/WIDTH )
    canvas.SetRightMargin( RIGHT/WIDTH )
    canvas.SetTopMargin( TOP/HEIGHT )
    canvas.SetBottomMargin( BOTTOM/HEIGHT )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.Draw()

    bottomFraction = 0.4
    bottomToTopRatio = bottomFraction/(1.0 - bottomFraction)
    upperPad = ROOT.TPad("upperPad_{t}".format(t=target), "upperPad_{t}".format(t=target), 0., bottomFraction, 0.97, 0.97)
    upperPad.SetMargin(0.12, 0.03, 0.025, 0.08) # left, right, bottom, top
    lowerPad = ROOT.TPad("lowerPad_{t}".format(t=target), "lowerPad_{t}".format(t=target), 0., 0., 0.97, bottomFraction)
    lowerPad.SetMargin(0.12, 0.03, 0.38, 0.03) # left, right, bottom, top
    upperPad.Draw()
    lowerPad.Draw()

    upperPad.cd()
    if (str(inputDetails["logY"]) == "true"):
        upperPad.SetLogy()

    legend = None
    try:
        legend = ROOT.TLegend(float(str(inputDetails["legend"]["edgeLeft"])), float(str(inputDetails["legend"]["edgeBottom"])), float(str(inputDetails["legend"]["edgeRight"])), float(str(inputDetails["legend"]["edgeTop"])))
    except KeyError:
        print("Coordinates of edges of legend box not found in input JSON, setting default: 0.4, 0.85, 0.9, 0.9")
        legend = ROOT.TLegend(0.4, 0.85, 0.9, 0.9)
    try:
        legend.SetNColumns(int(0.5 + float(str(inputDetails["legend"]["nColumns"]))))
    except KeyError:
        print("Number of columns in legend not found in input JSON, setting default: 1")
        legend.SetNColumns(1)
    legend.SetBorderSize(commonLineWidth)
    legend.SetFillStyle(0)
    try:
        ROOT.gStyle.SetLegendTextSize(float(str(inputDetails["legend"]["textSize"])))
    except KeyError:
        print("Legend text size not found in input JSON, setting default: 0.05")
        ROOT.gStyle.SetLegendTextSize(0.05)

    # Get "scaled" versions of the input histograms
    inputHistogramsScaled = {}
    normalizeToIntegral = False
    try:
        if (inputDetails["normType"] == "integral"): normalizeToIntegral = True
        else: sys.exit("ERROR: unrecognized \"normType\": {nT}, currently can only take the value \"integral\".".format(nT=inputDetails["normType"]))
    except KeyError:
        pass
    sources_order = [labelWithSpaces.strip() for labelWithSpaces in (str(inputDetails["order"])).split(",")]
    if (sources_order[0] != str(inputDetails["ratioDenominatorLabel"])): sys.exit("ERROR: Code assumes that first element in sources_order is the basis of comparison. Currently, sources_order[0] = {s}, ratioDenominatorLabel = {r}".format(s=sources_order[0], r=str(inputDetails["ratioDenominatorLabel"])))
    suppress_histogram = {}
    for label in sources_order:
        print("Fetching histogram for label: {l}".format(l=label))
        inputHistogram = ROOT.TH1F()
        if ("filePath" in inputDetails["sources"][label]):
            inputFile = ROOT.TFile.Open(getFormattedInputData(inputDetails["sources"][label]["filePath"]), "READ")
            if ((inputFile.IsZombie() == ROOT.kTRUE) or not(inputFile.IsOpen() == ROOT.kTRUE)):
                sys.exit("ERROR in opening file: {f}".format(f=getFormattedInputData(inputDetails["sources"][label]["filePath"])))
            inputFile.GetObject(str(inputDetails["sources"][label]["histogramName"]), inputHistogram)
            if (not(inputHistogram)): sys.exit("Unable to find non-null histogram with name {n} in file {f}".format(n=str(inputDetails["sources"][label]["histogramName"]), f=getFormattedInputData(inputDetails["sources"][label]["filePath"])))
            inputFile.Close()
        elif ("combineSources" in str(inputDetails["sources"][label])):
            filePathHistNamePairs = getFormattedInputData(inputDetails["sources"][label]["combineSources"]).split(";")
            firstPairSplit = (filePathHistNamePairs[0]).split(":")
            firstPair_inputFile = ROOT.TFile.Open(firstPairSplit[0], "READ")
            if ((firstPair_inputFile.IsZombie() == ROOT.kTRUE) or not(firstPair_inputFile.IsOpen() == ROOT.kTRUE)):
                sys.exit("ERROR in opening file: {f}".format(f=firstPairSplit[0]))
            firstPair_inputFile.GetObject(str(firstPairSplit[1]), inputHistogram)
            firstPair_inputFile.Close()
            if (not(inputHistogram)): sys.exit("Unable to find non-null histogram with name {n} in file {f}".format(n=firstPairSplit[1], f=firstPairSplit[0]))
            remainingPairs = filePathHistNamePairs[1:]
            for pair in remainingPairs:
                pairSplit = pair.split(":")
                pair_inputFile = ROOT.TFile.Open(pairSplit[0], "READ")
                if ((pair_inputFile.IsZombie() == ROOT.kTRUE) or not(pair_inputFile.IsOpen() == ROOT.kTRUE)):
                    sys.exit("ERROR in opening file: {f}".format(f=pairSplit[0]))
                inputHistogramTemp = ROOT.TH1F()
                pair_inputFile.GetObject(str(pairSplit[1]), inputHistogramTemp)
                if (not(inputHistogramTemp)): sys.exit("Unable to find non-null histogram with name {n} in file {f}".format(n=pairSplit[1], f=pairSplit[0]))
                inputHistogram.Add(inputHistogramTemp)
                pair_inputFile.Close()
        else:
            sys.exit("ERROR: Expected one of \"filePath\" or \"combineSources\" in input JSON source details for label: {l}, found neither.".format(l=label))
        inputHistogramsScaled[label] = inputHistogram.Clone()
        inputHistogramsScaled[label].SetName("{t}_{l}".format(t=target, l=label))
        scaleFactor = 1.0
        try:
            if normalizeToIntegral:
                scaleFactor = 1.0/tmROOTUtils.getSumOfBinContents(inputTH1=inputHistogramsScaled[label])
            else:
                scaleFactor = 1.0/inputHistogramsScaled[label].GetBinContent(inputHistogramsScaled[label].GetXaxis().FindFixBin(float(str(inputDetails["normX"]))))
        except ZeroDivisionError: # It could be that the normalization bin has 0 events... in that case pick the bin with maximum events.
            if (label == str(inputDetails["ratioDenominatorLabel"])):
                sys.exit("You're out of luck: histogram chosen as the basis of comparison has 0 events in the target normalization bin, or 0 integral.")
            else:
                maximumBin = inputHistogramsScaled[label].GetMaximumBin()
                try:
                    scaleFactor = inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])].GetBinContent(maximumBin)/inputHistogramsScaled[label].GetBinContent(maximumBin)
                    # inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])] is guaranteed to be set first, so this is OK
                except ZeroDivisionError:
                    sys.exit("You're out of luck: histogram with label {l} appears empty".format(l=label))
        suppress_histogram[label] = False
        if ((scaleFactor < 0.00000001) or scaleFactor > 10000000.0):
            suppress_histogram[label] = True
            print("WARNING: Unexpected scale factor: {s} for label: {l}; not drawing histogram.".format(s=scaleFactor, l=label))
        inputHistogramsScaled[label].Scale(scaleFactor) # Scale such that the value in the normalization bin is 1 for all sources

    # Find ratios and, if requested, save them in a file
    saveRatiosToFile = False
    try:
        saveRatiosToFile = (str(inputDetails["saveRatiosToFile"]) == "true")
    except KeyError:
        pass

    # Make ratio plots and, if requested, save them in a file
    saveRatioPlotsToFile = False
    try:
        saveRatioPlotsToFile = (str(inputDetails["saveRatioPlotsToFile"]) == "true")
    except KeyError:
        pass

    ratioHistograms = {}
    ratioGraphs = {}
    ratioPullGraphs = {}
    ratioPullMultigraph = ROOT.TMultiGraph()
    plotPulls = False
    try:
        ratioType = str(inputDetails["ratioType"])
        if (ratioType == "pull"): plotPulls = True
        elif (ratioType == "nominal"): plotPulls = False
        else: sys.exit("ERROR: \"ratioType\" can be either \"pull\" or \"nominal\". Currently, its value is: {rT}".format(rT=ratioType))
    except KeyError:
        sys.exit("ERROR: \"ratioType\" not found; needs to be set explicitly.")
    fractionalUncertaintiesList = []
    for label in sources_order:
        if ((label == str(inputDetails["ratioDenominatorLabel"])) or (suppress_histogram[label])): continue
        ratioHistograms[label] = inputHistogramsScaled[label].Clone()
        ratioHistograms[label].SetName("ratio_{t}_{l}_to_{ldenominator}".format(t=target, l=label, ldenominator=str(inputDetails["ratioDenominatorLabel"])))
        ratioGraphs[label] = ROOT.TGraphErrors()
        ratioGraphs[label].SetName("ratioGraph_{t}_{l}_to_{ldenominator}".format(t=target, l=label, ldenominator=str(inputDetails["ratioDenominatorLabel"])))
        ratioPullGraphs[label] = ROOT.TGraphErrors()
        ratioPullGraphs[label].SetName("ratioPullGraph_{t}_{l}_to_{ldenominator}".format(t=target, l=label, ldenominator=str(inputDetails["ratioDenominatorLabel"])))
        for xCounter in range(1, 1+inputHistogramsScaled[label].GetXaxis().GetNbins()):
            minFractionalError = 0.
            fractionalErrorDown = 0.
            fractionalErrorUp = 0.
            if saveRatiosToFile:
                minFractionalError = float(str(inputDetails["minFractionalError"]))
                fractionalErrorDown = -1.0*minFractionalError
                fractionalErrorUp = minFractionalError
            try:
                numerator = inputHistogramsScaled[label].GetBinContent(xCounter)
                numeratorError = inputHistogramsScaled[label].GetBinError(xCounter)
                denominator = inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])].GetBinContent(xCounter)
                denominatorError = inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])].GetBinError(xCounter)
                ratio = numerator/denominator
                ratioFractionalError = math.sqrt(pow(numeratorError/numerator, 2) + pow(denominatorError/denominator, 2))
                ratioError = ratio*ratioFractionalError
                normBinIndex = inputHistogramsScaled[label].GetXaxis().FindFixBin(float(str(inputDetails["normX"])))
                normBinFractionalError_normNJets = inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])].GetBinError(normBinIndex)/inputHistogramsScaled[str(inputDetails["ratioDenominatorLabel"])].GetBinContent(normBinIndex)
                normBinFractionalError_thisNJets = inputHistogramsScaled[label].GetBinError(normBinIndex)/inputHistogramsScaled[label].GetBinContent(normBinIndex)
                normBinFractionalError = math.sqrt(pow(normBinFractionalError_normNJets, 2) + pow(normBinFractionalError_thisNJets, 2))

                ratioHistograms[label].SetBinContent(xCounter, ratio)
                if normalizeToIntegral:
                    ratioHistograms[label].SetBinError(xCounter, ratioError)
                else:
                    ratioHistograms[label].SetBinError(xCounter, ratio*math.sqrt(pow(ratioFractionalError, 2) + pow(normBinFractionalError, 2)))

                ratioBinIndex = ratioGraphs[label].GetN()
                ratioGraphs[label].SetPoint(ratioBinIndex, ratioHistograms[label].GetBinCenter(xCounter), ratio)
                if normalizeToIntegral:
                    ratioGraphs[label].SetPointError(ratioBinIndex, 0.5*(ratioHistograms[label].GetXaxis().GetBinUpEdge(xCounter) - ratioHistograms[label].GetXaxis().GetBinLowEdge(xCounter)), ratioError)
                else:
                    ratioGraphs[label].SetPointError(ratioBinIndex, 0.5*(ratioHistograms[label].GetXaxis().GetBinUpEdge(xCounter) - ratioHistograms[label].GetXaxis().GetBinLowEdge(xCounter)), ratioError) # norm bin error not included because the intention is to fit to a straight line...

                ratioPullBinIndex = ratioPullGraphs[label].GetN()
                ratioPullGraphs[label].SetPoint(ratioPullBinIndex, ratioHistograms[label].GetBinCenter(xCounter), (ratio - 1.0)/ratioError)
                if normalizeToIntegral:
                    ratioPullGraphs[label].SetPointError(ratioPullBinIndex, 0.5*(ratioHistograms[label].GetXaxis().GetBinUpEdge(xCounter) - ratioHistograms[label].GetXaxis().GetBinLowEdge(xCounter)), 0.)
                else:
                    ratioPullGraphs[label].SetPointError(ratioPullBinIndex, 0.5*(ratioHistograms[label].GetXaxis().GetBinUpEdge(xCounter) - ratioHistograms[label].GetXaxis().GetBinLowEdge(xCounter)), ratio*normBinFractionalError/ratioError)

                if saveRatiosToFile:
                    if (ratio < (1.0 - minFractionalError)):
                        fractionalErrorDown = ratio - 1.0 # lnN (1+delta) = ratio
                        fractionalErrorUp = minFractionalError # lnN (1+delta) = 1 + minFractionalError
                    elif (ratio < (1.0 + minFractionalError)):
                        fractionalErrorDown = -1.0*minFractionalError # lnN (1+delta) = 1 - minFractionalError
                        fractionalErrorUp = minFractionalError # lnN (1+delta) = 1 + minFractionalError
                    else: # ratio > (1 + minFractionalError)
                        fractionalErrorDown = -1.0*minFractionalError # lnN (1+delta) = 1 - minFractionalError
                        fractionalErrorUp = ratio - 1.0 # lnN (1+delta) = ratio
            except ZeroDivisionError:
                ratioHistograms[label].SetBinContent(xCounter, 1.)
                ratioHistograms[label].SetBinError(xCounter, 0.)
                # default: factor-of-5 in both directions
                fractionalErrorDown = -0.8
                fractionalErrorUp = 4.0
                ratioPullBinIndex = ratioPullGraphs[label].GetN()
                ratioPullGraphs[label].SetPoint(ratioPullBinIndex, ratioHistograms[label].GetBinCenter(xCounter), 0.)
                ratioPullGraphs[label].SetPointError(ratioPullBinIndex, 0.5*(ratioHistograms[label].GetXaxis().GetBinUpEdge(xCounter) - ratioHistograms[label].GetXaxis().GetBinLowEdge(xCounter)), 0.)
            if saveRatiosToFile:
                fractionalUncertaintiesList.append(tuple(["float", (str(inputDetails["saveRatiosPatternDown"])).format(i=xCounter, l=label), fractionalErrorDown]))
                fractionalUncertaintiesList.append(tuple(["float", (str(inputDetails["saveRatiosPatternUp"])).format(i=xCounter, l=label), fractionalErrorUp]))
    if saveRatiosToFile: tmGeneralUtils.writeConfigurationParametersToFile(configurationParametersList=fractionalUncertaintiesList, outputFilePath=str(inputDetails["saveRatiosFile"]))

    # Find maximum value for scaled histogram and the label that has it
    runningMaxValue = None
    labelWithMaxValue = None
    for label in sources_order:
        if (suppress_histogram[label]): continue
        currentMax = inputHistogramsScaled[label].GetBinContent(inputHistogramsScaled[label].GetMaximumBin())
        if ((runningMaxValue is None) or (currentMax > runningMaxValue)):
            runningMaxValue = currentMax
            labelWithMaxValue = label

    # First draw the histogram with the max bin
    inputHistogramsScaled[labelWithMaxValue].SetLineColor(colorsDict[str(inputDetails["sources"][labelWithMaxValue]["color"])])
    inputHistogramsScaled[labelWithMaxValue].SetLineWidth(commonLineWidth)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetTitleSize(commonTitleSize)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetLabelSize(commonLabelSize)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetTickLength(0)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetLabelOffset(999)
    try:
        inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitle(str(inputDetails["yLabel"]))
    except KeyError:
        print("yLabel not found in input JSON, setting default: \"A.U.\"")
        inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitle("A.U.")
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitleSize(commonTitleSize)
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetLabelSize(commonLabelSize)
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitleOffset(commonTitleOffset)

    inputHistogramsScaled[labelWithMaxValue].Draw("P0")
    # First "Draw" command is just to initialize the axes etc.; it will get overwritten.
    upperPad.Update()
    try:
        inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetRangeUser(float(str(inputDetails["plotXMin"])), float(str(inputDetails["plotXMax"])))
    except KeyError:
        print("xmin and xmax not found in input JSON, not setting it explicly.")
    try:
        inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetRangeUser(float(str(inputDetails["plotYMin"])), float(str(inputDetails["plotYMax"])))
    except KeyError:
        print("ymin and ymax not found in input JSON, not setting it explicly.")
    upperPad.Update()

    # Next draw all histograms with option "SAME"
    for label in sources_order:
        # if (label == labelWithMaxValue): continue
        if (suppress_histogram[label]): continue
        inputHistogramsScaled[label].SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
        inputHistogramsScaled[label].SetLineWidth(commonLineWidth)
        inputHistogramsScaled[label].Draw("AP0 SAME")
        upperPad.Update()
        legendEntry = legend.AddEntry(inputHistogramsScaled[label], str(inputDetails["sources"][label]["label"]))
        legendEntry.SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
        legendEntry.SetTextColor(colorsDict[str(inputDetails["sources"][label]["color"])])
        legendEntry.SetMarkerColor(colorsDict[str(inputDetails["sources"][label]["color"])])
    legend.Draw()
    upperPad.Update()
    if (str(inputDetails["drawCMSLumi"]) == "true"):
        CMS_lumi.lumi_sqrtS = "13 TeV" # used with iPeriod = 0, e.g. for simulation-only plots (default is an empty string)
        CMS_lumi.lumi_13TeV = "137.2 fb^{-1}"
        CMS_lumi.relPosX    = 0.15
        CMS_lumi.CMS_lumi(canvas, 4, 0)

    upperPad.cd()
    upperPad.Update()
    upperPad.RedrawAxis()
    frame = upperPad.GetFrame()
    frame.Draw()

    yTitleSize_upper = inputHistogramsScaled[labelWithMaxValue].GetYaxis().GetTitleSize()
    yLabelSize_upper = inputHistogramsScaled[labelWithMaxValue].GetYaxis().GetLabelSize()
    yTickLength_upper = inputHistogramsScaled[labelWithMaxValue].GetYaxis().GetTickLength()
    upperPad.Update()

    lowerPad.cd()
    plotPropertiesSet = False
    for label in sources_order:
        if ((label == str(inputDetails["ratioDenominatorLabel"])) or (suppress_histogram[label])): continue
        if plotPulls:
            ratioPullGraphs[label].SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            ratioPullGraphs[label].SetMarkerColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            if not(normalizeToIntegral):
                ratioPullGraphs[label].SetFillColorAlpha(colorsDict[str(inputDetails["sources"][label]["color"])], 0.9)
                ratioPullGraphs[label].SetFillStyle(3001)
            ratioPullGraphs[label].SetLineWidth(commonLineWidth)
            ratioPullMultigraph.Add(ratioPullGraphs[label])
        else:
            ratioHistograms[label].SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            ratioHistograms[label].SetLineWidth(commonLineWidth)
            if (plotPropertiesSet):
                ratioHistograms[label].Draw("AP0 SAME")
                continue
            ratioHistograms[label].GetXaxis().SetTitle(str(inputDetails["xLabel"]))
            ratioHistograms[label].GetXaxis().SetTitleSize(yTitleSize_upper/bottomToTopRatio)
            ratioHistograms[label].GetXaxis().SetLabelSize(yLabelSize_upper/bottomToTopRatio)
            ratioHistograms[label].GetXaxis().SetTickLength(yTickLength_upper)
            ratioHistograms[label].GetXaxis().SetTitleOffset(0.86)
            ratioHistograms[label].GetYaxis().SetTitle("ratio")
            ratioHistograms[label].GetYaxis().SetTitleOffset(1.4*bottomToTopRatio*commonTitleOffset)
            ratioHistograms[label].GetYaxis().SetTitleSize(0.75*yTitleSize_upper/bottomToTopRatio)
            ratioHistograms[label].GetYaxis().SetLabelSize(yLabelSize_upper/bottomToTopRatio)
            ratioHistograms[label].GetYaxis().SetTickLength(yTickLength_upper)
            ratioHistograms[label].GetYaxis().SetNdivisions(2, 0, 0)
            ratioHistograms[label].Draw("P0")
            ratioHistograms[label].GetXaxis().SetRangeUser(float(str(inputDetails["plotXMin"])), float(str(inputDetails["plotXMax"])))
            plotPropertiesSet = True
            try:
                ratioHistograms[label].GetYaxis().SetRangeUser(float(str(inputDetails["ratioYMin"])), float(str(inputDetails["ratioYMax"])))
            except KeyError:
                print("min and max values for ratio y-axis not found in input JSON, setting default: (0, 5)")
                ratioHistograms[label].GetYaxis().SetRangeUser(0., 5.)

    if plotPulls:
        if normalizeToIntegral:
            ratioPullMultigraph.Draw("AP")
        else:
            ratioPullMultigraph.Draw("A2")
            ratioPullMultigraph.Draw("P")
        ratioPullMultigraph.GetXaxis().SetTitle(str(inputDetails["xLabel"]))
        ratioPullMultigraph.GetXaxis().SetTitleSize(yTitleSize_upper/bottomToTopRatio)
        ratioPullMultigraph.GetXaxis().SetLabelSize(yLabelSize_upper/bottomToTopRatio)
        ratioPullMultigraph.GetXaxis().SetTickLength(yTickLength_upper)
        ratioPullMultigraph.GetXaxis().SetTitleOffset(0.86)
        ratioPullMultigraph.GetYaxis().SetTitle("#frac{ratio-1.0}{#Delta ratio}")
        ratioPullMultigraph.GetYaxis().SetTitleOffset(1.4*bottomToTopRatio*commonTitleOffset)
        ratioPullMultigraph.GetYaxis().SetTitleSize(0.75*yTitleSize_upper/bottomToTopRatio)
        ratioPullMultigraph.GetYaxis().SetLabelSize(yLabelSize_upper/bottomToTopRatio)
        ratioPullMultigraph.GetYaxis().SetTickLength(yTickLength_upper)
        ratioPullMultigraph.GetYaxis().SetNdivisions(2, 0, 0)
        ratioPullMultigraph.GetXaxis().SetRangeUser(float(str(inputDetails["plotXMin"])), float(str(inputDetails["plotXMax"])))
        try:
            ratioPullMultigraph.GetYaxis().SetRangeUser(float(str(inputDetails["pullYMin"])), float(str(inputDetails["pullYMax"])))
        except KeyError:
            print("min and max values for ratio y-axis not found in input JSON, not setting explicitly.")
        lowerPad.Update()

    nominalExpectation = 1.
    if plotPulls: nominalExpectation = 0.
    nominalExpectationLine = ROOT.TLine(float(str(inputDetails["plotXMin"])), nominalExpectation, float(str(inputDetails["plotXMax"])), nominalExpectation)
    nominalExpectationLine.SetLineColor(colorsDict[str(inputDetails["sources"][inputDetails["ratioDenominatorLabel"]]["color"])])
    nominalExpectationLine.SetLineWidth(commonLineWidth)
    nominalExpectationLine.Draw()

    lowerPad.cd()
    lowerPad.Update()
    lowerPad.RedrawAxis()
    frame = lowerPad.GetFrame()
    frame.Draw()

    canvas.Update()
    canvas.SaveAs("{oD}/{oP}".format(oD=outputDirectory, oP=str(inputDetails["outputPath"])))

    if saveRatioPlotsToFile:
        canvas = ROOT.TCanvas("oC_ratioGraphs_{t}".format(t=target), "oC_ratioGraphs_{t}".format(t=target), 50, 50, WIDTH, HEIGHT)
        ROOT.gStyle.SetOptStat(0)
        ROOT.gStyle.SetOptFit(0)
        ratioPlotsLegend = ROOT.TLegend(0.17, 0.17, 0.95, 0.45)
        ratioPlotsLegend.SetNColumns(1)
        ratioPlotsLegend.SetBorderSize(commonLineWidth)
        ratioPlotsLegend.SetFillStyle(0)
        ROOT.gStyle.SetLegendTextSize(0.02)
        axesDrawn = False
        for label in sources_order:
            if ((label == str(inputDetails["ratioDenominatorLabel"])) or (suppress_histogram[label])): continue
            ratioGraphs[label].SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            ratioGraphs[label].SetMarkerColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            if not(axesDrawn):
                ratioGraphs[label].Draw("AP")
                ratioGraphs[label].GetXaxis().SetTitle(str(inputDetails["xLabel"]))
                ratioGraphs[label].GetYaxis().SetTitle("ratio")
                ratioGraphs[label].GetXaxis().SetRangeUser(float(str(inputDetails["plotXMin"])), float(str(inputDetails["plotXMax"])))
                try:
                    ratioGraphs[label].GetYaxis().SetRangeUser(float(str(inputDetails["ratioYMin"])), float(str(inputDetails["ratioYMax"])))
                except KeyError:
                    print("min and max values for ratio y-axis not found in input JSON, not setting explicitly.")
                axesDrawn = True
            else: ratioGraphs[label].Draw("P")

            fitFunction_const = ROOT.TF1("constFit_{l}".format(l=label), "pol0", inputHistogramsScaled[label].GetXaxis().GetBinLowEdge(2), inputHistogramsScaled[label].GetXaxis().GetBinUpEdge(inputHistogramsScaled[label].GetXaxis().GetNbins()))
            fitResult_const = ratioGraphs[label].Fit("constFit_{l}".format(l=label), "QREMS+")
            fitFunction_const_plot = ratioGraphs[label].GetFunction("constFit_{l}".format(l=label))
            fitFunction_const_plot.SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            fitFunction_const_plot.SetLineStyle(ROOT.kSolid)
            # fitFunction_const_plot.SetLineWidth(3)
            legendText_const = str(inputDetails["sources"][label]["label"]) + " best fit const: ratio = ({C:.2f} +/- {deltaC:.2f}), #chi^2 /ndf = {chi2perndf:.2f}".format(C=fitResult_const.Parameter(0), deltaC=fitResult_const.ParError(0), chi2perndf=fitResult_const.Chi2()/fitResult_const.Ndf())
            canvas.Update()

            fitFunction_slope = ROOT.TF1("lineFit_{l}".format(l=label), "pol1", inputHistogramsScaled[label].GetXaxis().GetBinLowEdge(2), inputHistogramsScaled[label].GetXaxis().GetBinUpEdge(inputHistogramsScaled[label].GetXaxis().GetNbins()))
            fitResult_slope = ratioGraphs[label].Fit("lineFit_{l}".format(l=label), "QREMS+")
            fitFunction_slope_plot = ratioGraphs[label].GetFunction("lineFit_{l}".format(l=label))
            fitFunction_slope_plot.SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            fitFunction_slope_plot.SetLineStyle(ROOT.kDashed)
            # fitFunction_slope_plot.SetLineWidth(3)
            legendText_slope = str(inputDetails["sources"][label]["label"]) + " best fit line: ratio = ({C:.2f} +/- {deltaC:.2f}) + ({M:.2f} +/- {deltaM:.2f}) (ST/1000), #chi^2 /ndf = {chi2perndf:.2f}".format(C=fitResult_slope.Parameter(0), deltaC=fitResult_slope.ParError(0), M=1000*fitResult_slope.Parameter(1), deltaM=1000*fitResult_slope.ParError(1), chi2perndf=fitResult_slope.Chi2()/fitResult_slope.Ndf())
            canvas.Update()

            legendText = "#splitline{" + legendText_const + "}{" + legendText_slope + "}"
            legendEntry = ratioPlotsLegend.AddEntry(ratioGraphs[label], legendText)
            legendEntry.SetLineColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            legendEntry.SetTextColor(colorsDict[str(inputDetails["sources"][label]["color"])])
            legendEntry.SetMarkerColor(colorsDict[str(inputDetails["sources"][label]["color"])])

            canvas.Update()
        lineAt1 = ROOT.TLine(float(str(inputDetails["plotXMin"])), 1.0, float(str(inputDetails["plotXMax"])), 1.0)
        lineAt1.SetLineColor(colorsDict[str(inputDetails["sources"][inputDetails["ratioDenominatorLabel"]]["color"])])
        lineAt1.SetLineWidth(4)
        lineAt1.SetLineStyle(ROOT.kSolid)
        lineAt1.Draw()
        ratioPlotsLegend.Draw()
        canvas.Update()
        canvas.SaveAs("{oD}/{oP}".format(oD=outputDirectory, oP=str(inputDetails["saveRatioPlotsFile"])))

    del ROOT, tdrstyle, CMS_lumi

inputFileObject = open(inputArguments.inputFilePath, 'r')
inputPlots = json.load(inputFileObject)
inputFileObject.close()
# print("inputPlots: {iP}, type: {t}".format(iP=inputPlots, t = type(inputPlots)))

outputDirectory = getFormattedInputData(inputPlots["outputDirectory"])
if not(os.path.isdir(outputDirectory)): subprocess.check_call("mkdir -p {oD}".format(oD=outputDirectory), shell=True, executable="/bin/bash")

for target in inputPlots["targets"]:
    saveComparisons(target)

print("Done!")
