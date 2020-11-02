#!/usr/bin/env python

from __future__ import print_function, division
import os, sys, argparse, pdb, math, json
import tmGeneralUtils

# Register command line options
inputArgumentsParser = argparse.ArgumentParser(description='General tool to generate a CMS-formatted comparison of various histograms; list is read in from an input JSON file whose syntax is explained in the comment immediately following the argument parser setup.')
inputArgumentsParser.add_argument('--inputFilePath', required=True, help='Path to input JSON.',type=str)
inputArgumentsParser.add_argument('--outputDirectory', required=True, help='Output directory in which to store the plots.',type=str)
inputArguments = inputArgumentsParser.parse_args()

# If ROOT is imported before the input arguments parser, the default "help" message is not the right one
import ROOT
import tdrstyle, CMS_lumi
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.AddDirectory(ROOT.kFALSE)

# The input JSON file is formatted as in the following example:
# {
#     "targets": {
#         "histograms_2Jets": { # Each set of comparisons to produce is given a label (aka a "target" in the following code). Here we have two sets of comparisons, with the labels "histograms_2Jets" and "histograms_3Jets".
#             "outputPath": "STHistograms_2Jets.pdf", # path to output file
#             "title": "ST Histograms, 2 Jets", # title, currently not working because it overlaps the CMS logo
#             "xLabel": "S_{T} (GeV)", # x-axis label
#             "yLabel": "A.U.", # y-axis label
#             "logY": "true", # whether or not to set log scale for y-axis
#             "drawCMSLumi": "true", # whether or not to write luminosity (should generally be true for data, false for MC)
#             "legend": {
#                 "nColumns": "3" # number of columns in legend
#                 # optional, not included in this example: edgeLeft, edgeBottom, edgeRight, edgeTop, which control the edges of the legend
#             },
#             "normX": "1250.0", # the x value at which to scale the bin contents of all histograms to 1
#             "plotXMin": "1200.0", # x range min to plot
#             "plotXMax": "3500.0", # x range max to plot
#             "plotYMin": "0.001", # y range min to plot
#             "plotYMax": "2.0", # y range max to plot
#             "ratioDenominatorLabel": "signal", # label whose histogram is to be considered as the denominator while taking the ratio
#             "ratioYMin": "-0.5", # y range min of ratio plot
#             "ratioYMax": "3.5", # y range max of ratio plot
#             "sources": {
#                 "signal": { # within each set of comparisons to produce, each histogram is given a label. Here we have three histograms in this comparison, with the labels "signal", "signal_loose", and "control".
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_STComparisons_savedSTShapes.root", # path to file containing histogram
#                     "histogramName": "h_STDistribution_total_2Jets", # name of histogram within file
#                     "color": "blue", # color to use for this histogram.
#                     "label": "signal" # what to use as a label in the legend
#                 },
#                 "signal_loose": { # same syntax as above
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_loose_STComparisons_savedSTShapes.root",
#                     "histogramName": "h_STDistribution_total_2Jets",
#                     "color": "red",
#                     "label": "loose signal"
#                 },
#                 "control": { # same syntax as above
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/control_STComparisons_savedSTShapes.root",
#                     "histogramName": "h_STDistribution_total_2Jets",
#                     "color": "green",
#                     "label": "control"
#                 }
#             }
#         },
#         "histograms_3Jets": { # same syntax as above
#             "outputPath": "STHistograms_3Jets.pdf",
#             "title": "ST Histograms, 3 Jets",
#             "xLabel": "S_{T} (GeV)",
#             "yLabel": "A.U.",
#             "logY": "true",
#             "drawCMSLumi": "true",
#             "legend": {
#                 "nColumns": "3"
#             },
#             "normX": "1250.0",
#             "plotXMin": "1200.0",
#             "plotXMax": "3500.0",
#             "plotYMin": "0.001",
#             "plotYMax": "2.0",
#             "ratioDenominatorLabel": "signal",
#             "ratioYMin": "-0.5",
#             "ratioYMax": "3.5",
#             "sources": {
#                 "signal": {
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_STComparisons_savedSTShapes.root",
#                     "histogramName": "h_STDistribution_total_3Jets",
#                     "color": "blue"
#                 },
#                 "signal_loose": {
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/signal_loose_STComparisons_savedSTShapes.root",
#                     "histogramName": "h_STDistribution_total_3Jets",
#                     "color": "red"
#                 },
#                 "control": {
#                     "filePath": "/uscms/home/tmudholk/nobackup/analysisAreas/analysis/publicationPlots/control_STComparisons_savedSTShapes.root",
#                     "histogramName": "h_STDistribution_total_3Jets",
#                     "color": "green"
#                 }
#             }
#         }
#     }
# }


inputFileObject = open(inputArguments.inputFilePath, 'r')
inputPlots = json.load(inputFileObject)
inputFileObject.close()
# print("inputPlots: {iP}, type: {t}".format(iP=inputPlots, t = type(inputPlots)))

colorsDict = {"red": ROOT.kRed+2, "blue": ROOT.kBlue+2, "green": ROOT.kGreen+2, "black": ROOT.kBlack}

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

def saveComparisons(target):
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
    if (inputDetails["logY"] == "true"):
        upperPad.SetLogy()

    legend = None
    try:
        legend = ROOT.TLegend(float(inputDetails["legend"]["edgeLeft"]), float(inputDetails["legend"]["edgeBottom"]), float(inputDetails["legend"]["edgeRight"]), float(inputDetails["legend"]["edgeTop"]))
    except KeyError:
        legend = ROOT.TLegend(0.4, 0.85, 0.9, 0.9)
    try:
        legend.SetNColumns(int(0.5 + float(inputDetails["legend"]["nColumns"])))
    except KeyError:
        legend.SetNColumns(1)
    legend.SetBorderSize(commonLineWidth)
    legend.SetFillStyle(0)
    ROOT.gStyle.SetLegendTextSize(0.05)

    # Get "scaled" versions of the input histograms
    inputHistogramsScaled = {}
    for label in inputDetails["sources"]:
        print("Fetching histogram for label: {l}".format(l=label))
        inputFile = ROOT.TFile.Open(inputDetails["sources"][label]["filePath"], "READ")
        if ((inputFile.IsZombie() == ROOT.kTRUE) or not(inputFile.IsOpen() == ROOT.kTRUE)):
            sys.exit("ERROR in opening file: {f}".format(f=inputDetails["sources"][label]["filePath"]))
        inputHistogram = ROOT.TH1F()
        inputFile.GetObject(str(inputDetails["sources"][label]["histogramName"]), inputHistogram)
        if (not(inputHistogram)): sys.exit("Unable to find non-null histogram with name {n} in file {f}".format(n=inputDetails["sources"][label]["histogramName"], f=inputDetails["sources"][label]["filePath"]))
        inputHistogramsScaled[label] = inputHistogram.Clone()
        inputFile.Close()
        inputHistogramsScaled[label].SetName("{t}_{l}".format(t=target, l=label))
        scaleFactor = 1.0/inputHistogramsScaled[label].GetBinContent(inputHistogramsScaled[label].GetXaxis().FindFixBin(float(inputDetails["normX"])))
        inputHistogramsScaled[label].Scale(scaleFactor) # Scale such that the value in the normalization bin is 1 for all sources

    # Find ratios
    ratioHistograms = {}
    for label in inputDetails["sources"]:
        if (label == inputDetails["ratioDenominatorLabel"]): continue
        ratioHistograms[label] = inputHistogramsScaled[label].Clone()
        ratioHistograms[label].SetName("ratio_{t}_{l}_to_{ldenominator}".format(t=target, l=label, ldenominator=inputDetails["ratioDenominatorLabel"]))
        for xCounter in range(1, 1+inputHistogramsScaled[label].GetXaxis().GetNbins()):
            try:
                numerator = inputHistogramsScaled[label].GetBinContent(xCounter)
                numeratorError = inputHistogramsScaled[label].GetBinError(xCounter)
                denominator = inputHistogramsScaled[inputDetails["ratioDenominatorLabel"]].GetBinContent(xCounter)
                denominatorError = inputHistogramsScaled[inputDetails["ratioDenominatorLabel"]].GetBinError(xCounter)
                ratio = numerator/denominator
                ratioError = ratio*math.sqrt(pow(numeratorError/numerator, 2) + pow(denominatorError/denominator, 2))
                ratioHistograms[label].SetBinContent(xCounter, ratio)
                ratioHistograms[label].SetBinError(xCounter, ratioError)
            except ZeroDivisionError:
                ratioHistograms[label].SetBinContent(xCounter, 1.)
                ratioHistograms[label].SetBinError(xCounter, 0.)

    # Find maximum value for scaled histogram and the label that has it
    runningMaxValue = None
    labelWithMaxValue = None
    for label in inputDetails["sources"]:
        currentMax = inputHistogramsScaled[label].GetBinContent(inputHistogramsScaled[label].GetMaximumBin())
        if ((runningMaxValue is None) or (currentMax > runningMaxValue)):
            runningMaxValue = currentMax
            labelWithMaxValue = label

    # First draw the histogram with the max bin
    inputHistogramsScaled[labelWithMaxValue].SetLineColor(colorsDict[inputDetails["sources"][labelWithMaxValue]["color"]])
    inputHistogramsScaled[labelWithMaxValue].SetLineWidth(commonLineWidth)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetTitleSize(commonTitleSize)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetLabelSize(commonLabelSize)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetTickLength(0)
    inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetLabelOffset(999)
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitle("A.U.")
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitleSize(commonTitleSize)
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetLabelSize(commonLabelSize)
    inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetTitleOffset(commonTitleOffset)

    inputHistogramsScaled[labelWithMaxValue].Draw("P0")
    upperPad.Update()
    legendEntry = legend.AddEntry(inputHistogramsScaled[labelWithMaxValue], inputDetails["sources"][labelWithMaxValue]["label"])
    legendEntry.SetLineColor(colorsDict[inputDetails["sources"][labelWithMaxValue]["color"]])
    legendEntry.SetTextColor(colorsDict[inputDetails["sources"][labelWithMaxValue]["color"]])
    legendEntry.SetMarkerColor(colorsDict[inputDetails["sources"][labelWithMaxValue]["color"]])
    try:
        inputHistogramsScaled[labelWithMaxValue].GetXaxis().SetRangeUser(float(inputDetails["plotXMin"]), float(inputDetails["plotXMax"]))
    except KeyError:
        pass
    try:
        inputHistogramsScaled[labelWithMaxValue].GetYaxis().SetRangeUser(float(inputDetails["plotYMin"]), float(inputDetails["plotYMax"]))
    except KeyError:
        pass
    upperPad.Update()

    # Next draw the other histograms
    for label in inputDetails["sources"]:
        if (label == labelWithMaxValue): continue
        inputHistogramsScaled[label].SetLineColor(colorsDict[inputDetails["sources"][label]["color"]])
        inputHistogramsScaled[label].SetLineWidth(commonLineWidth)
        inputHistogramsScaled[label].Draw("AP0 SAME")
        upperPad.Update()
        legendEntry = legend.AddEntry(inputHistogramsScaled[label], inputDetails["sources"][label]["label"])
        legendEntry.SetLineColor(colorsDict[inputDetails["sources"][label]["color"]])
        legendEntry.SetTextColor(colorsDict[inputDetails["sources"][label]["color"]])
        legendEntry.SetMarkerColor(colorsDict[inputDetails["sources"][label]["color"]])
    legend.Draw()
    upperPad.Update()
    if (inputDetails["drawCMSLumi"] == "true"):
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
    for label in inputDetails["sources"]:
        if (label == inputDetails["ratioDenominatorLabel"]): continue
        ratioHistograms[label].SetLineColor(colorsDict[inputDetails["sources"][label]["color"]])
        ratioHistograms[label].SetLineWidth(commonLineWidth)
        if (plotPropertiesSet):
            ratioHistograms[label].Draw("AP0 SAME")
            continue
        ratioHistograms[label].GetXaxis().SetTitle(inputDetails["xLabel"])
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
        ratioHistograms[label].GetXaxis().SetRangeUser(float(inputDetails["plotXMin"]), float(inputDetails["plotXMax"]))
        try:
            ratioHistograms[label].GetYaxis().SetRangeUser(float(inputDetails["ratioYMin"]), float(inputDetails["ratioYMax"]))
        except KeyError:
            ratioHistograms[label].GetYaxis().SetRangeUser(0., 5.)
        plotPropertiesSet = True

    lineAt1 = ROOT.TLine(float(inputDetails["plotXMin"]), 1., float(inputDetails["plotXMax"]), 1.)
    lineAt1.SetLineColor(colorsDict[inputDetails["sources"][inputDetails["ratioDenominatorLabel"]]["color"]])
    lineAt1.SetLineWidth(commonLineWidth)
    lineAt1.Draw()
    lowerPad.cd()
    lowerPad.Update()
    lowerPad.RedrawAxis()
    frame = lowerPad.GetFrame()
    frame.Draw()

    canvas.Update()
    canvas.SaveAs("{oD}/{oP}".format(oD=inputArguments.outputDirectory, oP=inputDetails["outputPath"]))

for target in inputPlots["targets"]:
    saveComparisons(target)
