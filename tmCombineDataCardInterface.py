from __future__ import print_function, division

import os, sys, tmGeneralUtils

class tmCombineDataCardInterface:
    def __init__(self, list_signalBinLabels, dict_signalBins_observedNEvents):
        self.nChannels = len(list_signalBinLabels) # Number of observables
        self.nBackgrounds = 0 # Number of background processes (each one may lead to a different nEvents in each channel)
        self.nUncertainties = 0 # Number of independent sources of systematic uncertainties, aka "nuisance parameters"
        if not(tmGeneralUtils.check_dict_keys_against_list(targetDict=dict_signalBins_observedNEvents, targetList=list_signalBinLabels)):
            sys.exit("ERROR: List of signal bin labels does not match keys of signal bin observations dictionary. list_signalBinLabels: {l_sBL}, dict_signalBins_observedNEvents: {d_sB_oNE}".format(l_sBL=list_signalBinLabels, d_sB_oNE=dict_signalBins_observedNEvents))

        # self.listOfScriptArguments_ = []
        # self.listOfFilesToTransfer_ = []
        # self.processName_ = processName
        # self.scriptPath_ = scriptPath
        # self.outputDirectoryRelativePath_ = outputDirectoryRelativePath
        # if not(os.path.isdir(outputDirectoryRelativePath)):
        #     print("WARNING: folder \"{oDRP}\" does not exist, creating...".format(oDRP=outputDirectoryRelativePath))
        #     os.system("mkdir -p {oDRP}".format(oDRP=outputDirectoryRelativePath))
        # hostname = os.getenv("HOSTNAME")
        # self.habitat_ = ""
        # if ("lxplus" in hostname):
        #     self.habitat_ = "lxplus"
        # elif ("fnal" in hostname):
        #     self.habitat_ = "fnal"
        # else:
        #     sys.exit("ERROR: Unrecognized hostname: {h}, seems to be neither lxplus nor fnal.".format(h=hostname))
        # self.flavor_ = ""

    def generateHeaderSection(self):
        yield("# Auto-generated by combine datacard interface")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="imax {nC}".format(nC=self.nChannels)) + " number of channels")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="jmax {nB}".format(nB=self.nBackgrounds)) + " number of backgrounds")
        yield(tmGeneralUtils.alignFixedWidthStringLeft(width=10, inputString="kmax {nU}".format(nU=self.nUncertainties)) + " number of nuisance parameters (sources of systematic uncertainties)")

    def generateObservationsSection(self):
        yield("Test observations section")

    def generateExpectationsSection(self):
        yield("Test expectations section")

    def generateSystematicsSection(self):
        yield("Test systematics section")

    def writeToFile(self, outputFilePath):
        if os.path.isfile(outputFilePath):
            print("File: {name} already exists. Recreating...".format(name=outputFilePath))
            os.system("rm -f {out}".format(out=outputFilePath))
        outputFile = open(outputFilePath, "w")
        for line in self.generateHeaderSection():
            outputFile.write(line + "\n")
        outputFile.write("------------\n")
        for line in self.generateObservationsSection():
            outputFile.write(line + "\n")
        outputFile.write("------------\n")
        for line in self.generateExpectationsSection():
            outputFile.write(line + "\n")
        outputFile.write("------------\n")
        for line in self.generateSystematicsSection():
            outputFile.write(line + "\n")
        outputFile.close()

    # def addScriptArgument(self, scriptArgument):
    #     if not(isinstance(scriptArgument, basestring)):
    #         sys.exit("tmJDLInterface: method addScriptArgument only accepts raw strings as an argument.")
    #     (self.listOfScriptArguments_).append(scriptArgument)

    # def addScriptArgumentsFromList(self, listOfScriptArguments):
    #     if not(isinstance(listOfScriptArguments, list)):
    #         sys.exit("tmJDLInterface: method addScriptArgumentsFromList only accepts a list of strings as an argument.")
    #     for scriptArgument in listOfScriptArguments:
    #         self.addScriptArgument(scriptArgument)

    # def addFileToTransfer(self, fileToTransfer):
    #     if not(isinstance(fileToTransfer, basestring)):
    #         sys.exit("tmJDLInterface: method addFileToTransfer only accepts raw strings as an argument.")
    #     if not(os.path.isfile(fileToTransfer)):
    #         sys.exit("tmJDLInterface: ERROR: file {fTT} does not exist".format(fTT=fileToTransfer))
    #     (self.listOfFilesToTransfer_).append(fileToTransfer)

    # def addFilesToTransferFromList(self, listOfFilesToTransfer):
    #     if not(isinstance(listOfFilesToTransfer, list)):
    #         sys.exit("tmJDLInterface: method addFilesToTransferFromList only accepts a list of strings as an argument.")
    #     for fileToTransfer in listOfFilesToTransfer:
    #         self.addFileToTransfer(fileToTransfer)

    # def setFlavor(self, flavor):
    #     if not(isinstance(flavor, basestring)):
    #         sys.exit("tmJDLInterface: method setFlavor only accepts raw strings as an argument.")
    #     if not(self.habitat_ == "lxplus"):
    #         sys.exit("tmJDLInterface: method setFlavor only usable from lxplus.")
    #     self.flavor_ = flavor

    # def writeToFile(self):
    #     outputJDLFileName = ("{oD}/{name}.jdl".format(oD=self.outputDirectoryRelativePath_, name=self.processName_))
    #     if os.path.isfile(outputJDLFileName):
    #         print("File: {name} already exists. Recreating...".format(name=outputJDLFileName))
    #         os.system("rm -f {out}".format(out=outputJDLFileName))
    #     outputJDL = open(outputJDLFileName, "w")
    #     outputJDL.write("universe = vanilla\n")
    #     outputJDL.write("executable = {sP}\n".format(sP=self.scriptPath_))
    #     if (self.habitat_ == "fnal"): # questionable -- doesn't seem to achieve anything
    #         outputJDL.write("should_transfer_files = YES\n")
    #         outputJDL.write("whentotransferoutput = ON_EXIT\n")
    #     if (len(self.listOfFilesToTransfer_) > 0):
    #         transferString = "transfer_input_files = "
    #         for fileToTransfer in (self.listOfFilesToTransfer_):
    #             transferString += "{f},".format(f=fileToTransfer)
    #         transferString = transferString[:-1] # To remove the "," at the end
    #         outputJDL.write("{tS}\n".format(tS=transferString))
    #     outputJDL.write("output = log_{pN}.stdout\n".format(pN=self.processName_))
    #     outputJDL.write("error = log_{pN}.stderr\n".format(pN=self.processName_))
    #     outputJDL.write("log = log_{pN}.log\n".format(pN=self.processName_))
    #     outputJDL.write("notify_user = {lN}@cern.ch\n".format(lN=os.getenv("LOGNAME")))
    #     if (len(self.listOfScriptArguments_) > 0):
    #         argumentsString = "arguments = "
    #         for scriptArgument in self.listOfScriptArguments_:
    #             argumentsString += "{sA} ".format(sA = scriptArgument)
    #         argumentsString = argumentsString[:-1] # To remove the space character at the end
    #         outputJDL.write("{aS}\n".format(aS=argumentsString))
    #     if (self.habitat_ == "lxplus"):
    #         if (self.flavor_):
    #             outputJDL.write("+JobFlavour = {f}\n".format(f=self.flavor_)) # the "+" is deliberate and needed according to the documentation
    #         else:
    #             sys.exit("Flavor needs to be set for lxplus jobs.")
    #     outputJDL.write("queue 1\n")
    #     outputJDL.close()
