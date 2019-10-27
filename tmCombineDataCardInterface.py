from __future__ import print_function, division

import os, sys, tmGeneralUtils

class tmCombineDataCardInterface:
    def __init__(self, list_signalBinLabels, list_backgroundProcessLabels, list_signalProcessLabels, list_systematicsLabels, dict_observedNEvents, dict_expectedNEvents, dict_systematicsTypes, dict_systematics):
        self.nChannels = len(list_signalBinLabels) # Number of observables
        self.nBackgrounds = len(list_backgroundProcessLabels) # Number of background processes (each one may lead to a different nEvents in each channel)
        self.nSignals = len(list_signalProcessLabels)
        self.nUncertainties = len(list_systematicsLabels) # Number of independent sources of systematic uncertainties, aka "nuisance parameters"
        self.signalBinLabels = list_signalBinLabels
        self.backgroundProcessLabels = list_backgroundProcessLabels
        self.signalProcessLabels = list_signalProcessLabels
        self.systematicsLabels = list_systematicsLabels
        self.nProcesses = 0
        self.processIDs = {}
        runningID = 1-len(list_signalProcessLabels)
        for signalProcessLabel in list_signalProcessLabels:
            self.processIDs[signalProcessLabel] = runningID
            runningID += 1
            self.nProcesses += 1
        if not(runningID == 1): sys.exit("Logic error: check process IDs.")
        for backgroundProcessLabel in list_backgroundProcessLabels:
            self.processIDs[backgroundProcessLabel] = runningID
            runningID += 1
            self.nProcesses += 1
        self.observedNEvents = dict_observedNEvents
        self.expectedNEvents = dict_expectedNEvents
        self.systematicsTypes = dict_systematicsTypes
        self.systematics = dict_systematics
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_observedNEvents, targetList=list_signalBinLabels)):
            sys.exit("ERROR: List of signal bin labels does not match keys of signal bin observations dictionary. list_signalBinLabels: {l_sBL}, dict_observedNEvents: {d_oNE}".format(l_sBL=list_signalBinLabels, d_oNE=dict_observedNEvents))
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_expectedNEvents, targetList=list_signalBinLabels)):
            sys.exit("ERROR: List of signal bin labels does not match keys of signal bin expectations dictionary. list_signalBinLabels: {l_sBL}, dict_expectedNEvents: {d_eNE}".format(l_sBL=list_signalBinLabels, d_eNE=dict_expectedNEvents))
        for signalBinLabel in list_signalBinLabels:
            if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_expectedNEvents[signalBinLabel], targetList=(list_backgroundProcessLabels + list_signalProcessLabels))):
                sys.exit("ERROR: List of signal bin labels does not match keys of signal bin expectations dictionary. list_backgroundProcessLabels: {l_bPL}, list_signalProcessLabels: {l_sPL}, dict_expectedNEvents[signalBinLabel]: {d_eNE}".format(l_bPL=list_backgroundProcessLabels, l_sPL=list_signalProcessLabels, d_eNE=dict_expectedNEvents[signalBinLabel]))
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematicsTypes, targetList=list_systematicsLabels)):
            sys.exit("ERROR: List of systematics labels does not match keys of systematics types dictionary. list_systematicsLabels: {l_sL}, dict_systematicsTypes: {d_sT}".format(l_sL=list_systematicsLabels, d_sT=dict_systematicsTypes))
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematics, targetList=list_systematicsLabels)):
            sys.exit("ERROR: List of systematics labels does not match keys of systematics dictionary. list_systematicsLabels: {l_sL}, dict_systematics: {d_s}".format(l_sL=list_systematicsLabels, d_s=dict_systematics))
        for systematicName in (dict_systematics.keys()):
            if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematics[systematicName], targetList=list_signalBinLabels)):
                sys.exit("ERROR: List of signal bin labels does not match keys of systematics dictionary for the systematic \"{s}\". list_signalBinLabels: {l_sBL}, dict_systematics: {d_s}".format(s=systematicName, l_sBL=list_signalBinLabels, d_s=dict_systematics[systematicName]))
            for signalBinLabel in list_signalBinLabels:
                if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematics[systematicName][signalBinLabel], targetList=(list_backgroundProcessLabels + list_signalProcessLabels))):
                    sys.exit("ERROR: List of signal bin labels does not match keys of systematics dictionary. list_backgroundProcessLabels: {l_bPL}, list_signalProcessLabels: {l_sPL}, systematicsInThisSignalBin: {s}".format(l_bPL=list_backgroundProcessLabels, l_sPL=list_signalProcessLabels, s=dict_systematics[systematicName][signalBinLabel]))

    def generateHeaderSection(self):
        yield("# Auto-generated by combine datacard interface")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="imax {nC}".format(nC=self.nChannels)) + " number of channels")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="jmax {nB}".format(nB=self.nBackgrounds)) + " number of backgrounds")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="kmax {nU}".format(nU=self.nUncertainties)) + " number of nuisance parameters (sources of systematic uncertainties)")

    def generateObservationsSection(self):
        signalLabelWidth = 4 + max(len(label) for label in self.signalBinLabels)

        titleLine = tmGeneralUtils.alignFixedWidthStringLeft(width=15, inputString="bin")
        for signalBinLabel in self.signalBinLabels:
            titleLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=signalBinLabel)
        yield(titleLine)

        observationsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=15, inputString="observation")
        for signalBinLabel in self.signalBinLabels:
            observationsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=str(self.observedNEvents[signalBinLabel]))
        yield(observationsLine)

    def generateExpectationsSection(self):
        systematicsNamesColumnWidth = 4 + max(len(label) for label in self.systematicsLabels)
        systematicsTypesColumnWidth = 4 + max(len(sType) for sType in self.systematicsTypes.values())
        signalLabelWidth = 4 + max(len(label) for label in self.signalBinLabels)

        titleLine = tmGeneralUtils.alignFixedWidthStringLeft(width=(systematicsNamesColumnWidth+systematicsTypesColumnWidth), inputString="bin")
        for signalBinLabel in self.signalBinLabels:
            for copyIndex in range(0, len(self.backgroundProcessLabels)*len(self.signalProcessLabels)):
                titleLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=signalBinLabel)
        yield(titleLine)

        processLabelsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=(systematicsNamesColumnWidth+systematicsTypesColumnWidth), inputString="process")
        for signalBinLabel in self.signalBinLabels:
            for processLabel in self.signalProcessLabels:
                processLabelsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=processLabel)
            for processLabel in self.backgroundProcessLabels:
                processLabelsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=processLabel)
        yield(processLabelsLine)

        processIDsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=(systematicsNamesColumnWidth+systematicsTypesColumnWidth), inputString="process")
        for signalBinLabel in self.signalBinLabels:
            for processLabel in self.signalProcessLabels:
                processIDsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=str(self.processIDs[processLabel]))
            for processLabel in self.backgroundProcessLabels:
                processIDsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=str(self.processIDs[processLabel]))
        yield(processIDsLine)

        ratesLine = tmGeneralUtils.alignFixedWidthStringLeft(width=(systematicsNamesColumnWidth+systematicsTypesColumnWidth), inputString="rate")
        for signalBinLabel in self.signalBinLabels:
            for processLabel in self.signalProcessLabels:
                ratesLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.expectedNEvents[signalBinLabel][processLabel])
            for processLabel in self.backgroundProcessLabels:
                ratesLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.expectedNEvents[signalBinLabel][processLabel])
        yield(ratesLine)

    def generateSystematicsSection(self):
        systematicsNamesColumnWidth = 4 + max(len(label) for label in self.systematicsLabels)
        systematicsTypesColumnWidth = 4 + max(len(sType) for sType in self.systematicsTypes.values())
        signalLabelWidth = 4 + max(len(label) for label in self.signalBinLabels)
        for systematicsLabel in self.systematicsLabels:
            systematicsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=systematicsNamesColumnWidth, inputString=systematicsLabel)
            systematicsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=systematicsTypesColumnWidth, inputString=self.systematicsTypes[systematicsLabel])
            for signalBinLabel in self.signalBinLabels:
                for processLabel in self.signalProcessLabels:
                    systematicsLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.systematics[systematicsLabel][signalBinLabel][processLabel])
                for processLabel in self.backgroundProcessLabels:
                    systematicsLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.systematics[systematicsLabel][signalBinLabel][processLabel])
            yield(systematicsLine)

    def writeToFile(self, outputFilePath):
        if os.path.isfile(outputFilePath):
            print("File: {name} already exists. Recreating...".format(name=outputFilePath))
            os.system("rm -f {out}".format(out=outputFilePath))
        outputFile = open(outputFilePath, "w")
        for line in self.generateHeaderSection():
            outputFile.write(line.rstrip() + "\n")
        outputFile.write("------------\n")
        for line in self.generateObservationsSection():
            outputFile.write(line.rstrip() + "\n")
        outputFile.write("------------\n")
        for line in self.generateExpectationsSection():
            outputFile.write(line.rstrip() + "\n")
        outputFile.write("------------\n")
        for line in self.generateSystematicsSection():
            outputFile.write(line.rstrip() + "\n")
        outputFile.close()
