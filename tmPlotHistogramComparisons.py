#!/usr/bin/env python

from __future__ import print_function, division
import os, sys, argparse, pdb, math, json, subprocess
import tmGeneralUtils

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
            "normX": "1250.0", # the x value at which to scale the bin contents of all histograms to 1
            "plotXMin": "1200.0", # x range min to plot
            "plotXMax": "3500.0", # x range max to plot
            "plotYMin": "0.001", # y range min to plot
            "plotYMax": "2.0", # y range max to plot
            "ratioDenominatorLabel": "signal", # label whose histogram is to be considered as the denominator while taking the ratio
            "ratioYMin": "-0.5", # y range min of ratio plot
            "ratioYMax": "3.5", # y range max of ratio plot
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
            "ratioYMin": "-0.5",
            "ratioYMax": "3.5",
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

    bottomFraction = 0.25
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
            scaleFactor = 1.0/inputHistogramsScaled[label].GetBinContent(inputHistogramsScaled[label].GetXaxis().FindFixBin(float(str(inputDetails["normX"]))))
        except ZeroDivisionError: # It could be that the normalization bin has 0 events... in that case pick the bin with maximum events.
            if (label == str(inputDetails["ratioDenominatorLabel"])):
                sys.exit("You're out of luck: histogram chosen as the basis of comparison has 0 events in the target normalization bin.")
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

    # Find ratios
    ratioHistograms = {}
    fractionalUncertaintiesList = []
    for label in sources_order:
        if ((label == str(inputDetails["ratioDenominatorLabel"])) or (suppress_histogram[label])): continue
        ratioHistograms[label] = inputHistogramsScaled[label].Clone()
        ratioHistograms[label].SetName("ratio_{t}_{l}_to_{ldenominator}".format(t=target, l=label, ldenominator=str(inputDetails["ratioDenominatorLabel"])))
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
                ratioError = ratio*math.sqrt(pow(numeratorError/numerator, 2) + pow(denominatorError/denominator, 2))
                ratioHistograms[label].SetBinContent(xCounter, ratio)
                ratioHistograms[label].SetBinError(xCounter, ratioError)
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
        try:
            ratioHistograms[label].GetYaxis().SetRangeUser(float(str(inputDetails["ratioYMin"])), float(str(inputDetails["ratioYMax"])))
        except KeyError:
            print("min and max values for ratio y-axis not found in input JSON, setting default: (0, 5)")
            ratioHistograms[label].GetYaxis().SetRangeUser(0., 5.)
        plotPropertiesSet = True

    lineAt1 = ROOT.TLine(float(str(inputDetails["plotXMin"])), 1., float(str(inputDetails["plotXMax"])), 1.)
    lineAt1.SetLineColor(colorsDict[str(inputDetails["sources"][inputDetails["ratioDenominatorLabel"]]["color"])])
    lineAt1.SetLineWidth(commonLineWidth)
    lineAt1.Draw()
    lowerPad.cd()
    lowerPad.Update()
    lowerPad.RedrawAxis()
    frame = lowerPad.GetFrame()
    frame.Draw()

    canvas.Update()
    canvas.SaveAs("{oD}/{oP}".format(oD=outputDirectory, oP=str(inputDetails["outputPath"])))

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
