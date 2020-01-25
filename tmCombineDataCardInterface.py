from __future__ import print_function, division

import os, sys, tmGeneralUtils

class tmCombineDataCardInterface:
    def __init__(self, list_signalBinLabels, list_backgroundProcessLabels, list_signalProcessLabels, list_systematicsLabels, dict_observedNEvents, dict_expectedNEvents, list_rateParamLabels, dict_rateParamProperties, dict_systematicsTypes, dict_systematics):
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
        self.rateParamLabels = list_rateParamLabels
        self.rateParamProperties = dict_rateParamProperties
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
        # for systematicName in (dict_systematics.keys()):
        #     if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematics[systematicName], targetList=list_signalBinLabels)):
        #         sys.exit("ERROR: List of signal bin labels does not match keys of systematics dictionary for the systematic \"{s}\". list_signalBinLabels: {l_sBL}, dict_systematics: {d_s}".format(s=systematicName, l_sBL=list_signalBinLabels, d_s=dict_systematics[systematicName]))
        #     for signalBinLabel in list_signalBinLabels:
        #         if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_systematics[systematicName][signalBinLabel], targetList=(list_backgroundProcessLabels + list_signalProcessLabels))):
        #             sys.exit("ERROR: List of signal bin labels does not match keys of systematics dictionary. list_backgroundProcessLabels: {l_bPL}, list_signalProcessLabels: {l_sPL}, systematicsInThisSignalBin: {s}".format(l_bPL=list_backgroundProcessLabels, l_sPL=list_signalProcessLabels, s=dict_systematics[systematicName][signalBinLabel]))
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_rateParamProperties, targetList=list_rateParamLabels)):
            sys.exit("ERROR: List of rate param labels does not match keys of rateParam properties dictionary. list_rateParamLabels: {l_rPL}, dict_rateParamProperties: {d_rPP}".format(l_rPL=list_rateParamLabels, d_rPP=dict_rateParamProperties))
        for rateParamLabel in list_rateParamLabels:
            if not(isinstance(dict_rateParamProperties[rateParamLabel], tuple)): sys.exit("ERROR: dict_rateParamProperties[\"{rPL}\"] is not a tuple. Its value is: {v}".format(rPL=rateParamLabel, v=dict_rateParamProperties[rateParamLabel]))
            if not((len(dict_rateParamProperties[rateParamLabel]) == 3) or (len(dict_rateParamProperties[rateParamLabel]) == 5)): sys.exit("ERROR: The tuple dict_rateParamProperties[\"{rPL}\"] needs to have either 3 elements with the syntax (bin_label, process_label, initial_value), or 5 elements with the syntax (bin_label, process_label, initial_value, min_rate_value, max_rate_value). Currently the tuple is: {v}".format(rPL=rateParamLabel, v=dict_rateParamProperties[rateParamLabel]))
            if isinstance(dict_rateParamProperties[rateParamLabel][0], list):
                for signalLabel in dict_rateParamProperties[rateParamLabel][0]:
                    if not(signalLabel in list_signalBinLabels): sys.exit("ERROR: All elements of dict_rateParamProperties[\"{rPL}\"][0] need to be in the list of signal bin labels. Currently the list of elements is: {v}".format(rPL=rateParamLabel, v=dict_rateParamProperties[rateParamLabel][0]))
            else:
                sys.exit("ERROR: dict_rateParamProperties[rateParamLabel][0] is not a list. Its value is: {v}".format(v=dict_rateParamProperties[rateParamLabel][0]))
            if isinstance(dict_rateParamProperties[rateParamLabel][1], list):
                for processLabel in dict_rateParamProperties[rateParamLabel][1]:
                    if not(processLabel in (list_backgroundProcessLabels + list_signalProcessLabels)): sys.exit("ERROR: All elements of dict_rateParamProperties[\"{rPL}\"][1] need to be in the list of signal or background process labels. Currently the list of elements is: {v}".format(rPL=rateParamLabel, v=dict_rateParamProperties[rateParamLabel][1]))
            else:
                sys.exit("ERROR: dict_rateParamProperties[rateParamLabel][1] is not a list. Its value is: {v}".format(v=dict_rateParamProperties[rateParamLabel][1]))

    def generateHeaderSection(self):
        yield("# Auto-generated by combine datacard interface")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="imax {nC}".format(nC=self.nChannels)) + " number of channels")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="jmax {nB}".format(nB=self.nBackgrounds)) + " number of backgrounds")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="kmax {nU}".format(nU=self.nUncertainties)) + " number of nuisance parameters (sources of systematic uncertainties)")

    def generateObservationsSection(self):
        signalLabelWidth = max(15, 4 + max(len(label) for label in self.signalBinLabels))

        titleLine = tmGeneralUtils.alignFixedWidthStringLeft(width=15, inputString="bin")
        for signalBinLabel in self.signalBinLabels:
            titleLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=signalBinLabel)
        yield(titleLine)

        observationsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=15, inputString="observation")
        for signalBinLabel in self.signalBinLabels:
            if isinstance(self.observedNEvents[signalBinLabel], int):
                observationsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString=str(self.observedNEvents[signalBinLabel]))
            elif isinstance(self.observedNEvents[signalBinLabel], float):
                observationsLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.observedNEvents[signalBinLabel])
        yield(observationsLine)

    def generateExpectationsSection(self):
        systematicsNamesColumnWidth = 4 + max(len(label) for label in self.systematicsLabels)
        systematicsTypesColumnWidth = 4 + max(len(sType) for sType in self.systematicsTypes.values())
        signalLabelWidth = max(15, 4 + max(len(label) for label in (self.signalBinLabels + self.backgroundProcessLabels + self.signalProcessLabels)))

        titleLine = tmGeneralUtils.alignFixedWidthStringLeft(width=(systematicsNamesColumnWidth+systematicsTypesColumnWidth), inputString="bin")
        for signalBinLabel in self.signalBinLabels:
            for copyIndex in range(0, (len(self.backgroundProcessLabels)+len(self.signalProcessLabels))):
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

    def generateRateParamsSection(self):
        rateParamNamesColumnWidth = 4 + max(len(label) for label in self.rateParamLabels)
        rateParamStringColumnWidth = 4 + len("rateParam")
        rateParamBinsColumnWidth = 4 + max(len(label) for label in self.signalBinLabels)
        rateParamProcessesColumnWidth = 4 + max(len(processLabel) for processLabel in (self.signalProcessLabels + self.backgroundProcessLabels))

        for rateParamLabel in self.rateParamLabels:
            paramProperties = self.rateParamProperties[rateParamLabel]
            rateParamsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=rateParamNamesColumnWidth, inputString=rateParamLabel)
            rateParamsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=rateParamStringColumnWidth, inputString="rateParam")
            for paramSignalBin in paramProperties[0]:
                rateParamsLineCopy1 = rateParamsLine
                rateParamsLineCopy1 += tmGeneralUtils.alignFixedWidthStringLeft(width=rateParamBinsColumnWidth, inputString=paramSignalBin)
                for paramProcessLabel in paramProperties[1]:
                    rateParamsLineCopy2 = rateParamsLineCopy1
                    rateParamsLineCopy2 += tmGeneralUtils.alignFixedWidthStringLeft(width=rateParamProcessesColumnWidth, inputString=paramProcessLabel)
                    rateParamsLineCopy2 += tmGeneralUtils.alignFixedWidthFloatLeft(width=rateParamProcessesColumnWidth, precision=3, number=paramProperties[2])
                    if (len(paramProperties) == 5):
                        rateParamsLineCopy2 += tmGeneralUtils.alignFixedWidthFloatLeft(width=rateParamProcessesColumnWidth, precision=3, number=paramProperties[3]) # initial value
                        rateParamsLineCopy2 += tmGeneralUtils.alignFixedWidthFloatLeft(width=rateParamProcessesColumnWidth, precision=3, number=paramProperties[4]) # final value
                    yield(rateParamsLineCopy2)

    def generateSystematicsSection(self):
        systematicsNamesColumnWidth = 4 + max(len(label) for label in self.systematicsLabels)
        systematicsTypesColumnWidth = 4 + max(len(sType) for sType in self.systematicsTypes.values())
        signalLabelWidth = max(15, 4 + max(len(label) for label in (self.signalBinLabels + self.backgroundProcessLabels + self.signalProcessLabels)))
        for systematicsLabel in self.systematicsLabels:
            systematicsLine = tmGeneralUtils.alignFixedWidthStringLeft(width=systematicsNamesColumnWidth, inputString=systematicsLabel)
            systematicsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=systematicsTypesColumnWidth, inputString=self.systematicsTypes[systematicsLabel])
            for signalBinLabel in self.signalBinLabels:
                for processLabel in (self.signalProcessLabels + self.backgroundProcessLabels):
                    try:
                        if isinstance(self.systematics[systematicsLabel][signalBinLabel][processLabel], dict):
                            try:
                                tmp = (tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.systematics[systematicsLabel][signalBinLabel][processLabel]["Down"])).rstrip() + "/"
                                systematicsLine += (tmp + tmGeneralUtils.alignFixedWidthFloatLeft(width=(signalLabelWidth-len(tmp)), precision=3, number=self.systematics[systematicsLabel][signalBinLabel][processLabel]["Up"]))
                            except KeyError:
                                sys.exit("ERROR: systematics[systematicsLabel][signalBinLabel][processLabel] is a dict but does not have elements named \"Up\" or \"Down\". dict contents: {c}".format(c=systematics[systematicsLabel][signalBinLabel][processLabel]))
                        else:
                            systematicsLine += tmGeneralUtils.alignFixedWidthFloatLeft(width=signalLabelWidth, precision=3, number=self.systematics[systematicsLabel][signalBinLabel][processLabel])
                    except KeyError:
                        systematicsLine += tmGeneralUtils.alignFixedWidthStringLeft(width=signalLabelWidth, inputString="-")
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
        for line in self.generateRateParamsSection():
            outputFile.write(line.rstrip() + "\n")
        outputFile.close()

def tmCombineDataCardInterfaceTest():
    outputFilePath = raw_input("Enter absolute or relative path to test output file: ")
    outputFileParentFolder = "/".join(outputFilePath.split("/")[:-1])
    returnCode = os.system("set -x && mkdir -p {oFPF} && set +x".format(oFPF=outputFileParentFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to check if folder {oFPF} exists or create it.".format(oFPF=outputFileParentFolder))

    signalBinLabels = ["signalBinTest1", "signalBinTest2"]
    observedNEvents = {
        "signalBinTest1": 10,
        "signalBinTest2": 20
    }
    backgroundProcessLabels = ["testBackground1", "testBackground2"]
    signalProcessLabels = ["testSignal1", "testSignal2"]

    expectedNEvents = {
        "signalBinTest1": {
            "testBackground1": 3.1,
            "testBackground2": 3.1,
            "testSignal1": 1.5,
            "testSignal2": 1.5
        },
        "signalBinTest2": {
            "testBackground1": 5.1,
            "testBackground2": 7.1,
            "testSignal1": 3.5,
            "testSignal2": 2.5
        }
    }

    rateParamLabels = ["rate1", "rate2"]
    rateParamProperties = {
        "rate1": (["signalBinTest1", "signalBinTest2"], ["testBackground1"], 1.0),
        "rate2": (["signalBinTest2"], ["testBackground1", "testBackground2"], 0.0, -5.0, 5.0)
    }
    systematicsLabels = ["systematic1", "reallyLongSystematicsLabel"]
    systematicsTypes = {
        "systematic1": "lnN",
        "reallyLongSystematicsLabel": "gmN 15"
    }
    systematics = {
        "systematic1": {
            "signalBinTest1": {
                "testSignal1": {
                    "Down": 0.95,
                    "Up": 1.05
                },
                "testSignal2": 1.05
            },
            "signalBinTest2": {
                "testBackground1": 0.,
                "testSignal1": 1.05,
                "testSignal2": 1.05
            }
        },
        "reallyLongSystematicsLabel": {
            "signalBinTest2": {
                "testBackground1": 0.,
                "testBackground2": {
                    "Up": 1.1,
                    "Down": 0.9
                }
            }
        }
    }

    dataCardInterface = tmCombineDataCardInterface(list_signalBinLabels=signalBinLabels, list_backgroundProcessLabels=backgroundProcessLabels, list_signalProcessLabels=signalProcessLabels, list_rateParamLabels=rateParamLabels, dict_rateParamProperties=rateParamProperties, list_systematicsLabels=systematicsLabels, dict_observedNEvents=observedNEvents, dict_expectedNEvents=expectedNEvents, dict_systematicsTypes=systematicsTypes, dict_systematics=systematics)
    dataCardInterface.writeToFile(outputFilePath="{oFP}".format(oFP=outputFilePath))

if __name__ == "__main__":
    tmCombineDataCardInterfaceTest()
