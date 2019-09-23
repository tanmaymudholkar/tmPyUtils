from __future__ import print_function, division

import os, sys

class tmJDLInterface:
    def __init__(self, processName, scriptPath, outputDirectoryRelativePath):
        self.listOfScriptArguments_ = []
        self.listOfFilesToTransfer_ = []
        self.processName_ = processName
        self.scriptPath_ = scriptPath
        self.outputDirectoryRelativePath_ = outputDirectoryRelativePath
        if not(os.path.isdir(outputDirectoryRelativePath)):
            print("WARNING: folder \"{oDRP}\" does not exist, creating...".format(oDRP=outputDirectoryRelativePath))
            os.system("mkdir -p {oDRP}".format(oDRP=outputDirectoryRelativePath))

    def addScriptArgument(self, scriptArgument):
        if not(isinstance(scriptArgument, basestring)):
            sys.exit("tmJDLInterface: method addScriptArgument only accepts raw strings as an argument.")
        (self.listOfScriptArguments_).append(scriptArgument)

    def addScriptArgumentsFromList(self, listOfScriptArguments):
        if not(isinstance(listOfScriptArguments, list)):
            sys.exit("tmJDLInterface: method addScriptArgumentsFromList only accepts a list of strings as an argument.")
        for scriptArgument in listOfScriptArguments:
            self.addScriptArgument(scriptArgument)

    def addFileToTransfer(self, fileToTransfer):
        if not(isinstance(fileToTransfer, basestring)):
            sys.exit("tmJDLInterface: method addFileToTransfer only accepts raw strings as an argument.")
        if not(os.path.isfile(fileToTransfer)):
            sys.exit("tmJDLInterface: ERROR: file {fTT} does not exist".format(fTT=fileToTransfer))
        (self.listOfFilesToTransfer_).append(fileToTransfer)

    def addFilesToTransferFromList(self, listOfFilesToTransfer):
        if not(isinstance(listOfFilesToTransfer, list)):
            sys.exit("tmJDLInterface: method addFilesToTransferFromList only accepts a list of strings as an argument.")
        for fileToTransfer in listOfFilesToTransfer:
            self.addFileToTransfer(fileToTransfer)

    def writeToFile(self):
        outputJDLFileName = ("{oD}/{name}.jdl".format(oD=self.outputDirectoryRelativePath_, name=self.processName_))
        if os.path.isfile(outputJDLFileName):
            print("File: {name} already exists. Recreating...".format(name=outputJDLFileName))
            os.system("rm -f {out}".format(out=outputJDLFileName))
        outputJDL = open(outputJDLFileName, "w")
        outputJDL.write("universe = vanilla\n")
        outputJDL.write("Executable = {script}\n".format(script=self.scriptPath_))
        outputJDL.write("Should_Transfer_Files = YES\n")
        outputJDL.write("WhenToTransferOutput = ON_EXIT\n")
        if (len(self.listOfFilesToTransfer_) > 0):
            transferString = "Transfer_Input_Files = "
            for fileToTransfer in (self.listOfFilesToTransfer_):
                transferString += "{filename}, ".format(filename=fileToTransfer)
            transferString = transferString[:-2] # To remove the ", " at the end
            outputJDL.write("{tS}\n".format(tS=transferString))
        outputJDL.write("Output = log_{pN}.stdout\n".format(pN=self.processName_))
        outputJDL.write("Error = log_{pN}.stderr\n".format(pN=self.processName_))
        outputJDL.write("Log = log_{pN}.log\n".format(pN=self.processName_))
        outputJDL.write("notify_user = $ENV(LOGNAME)@cern.ch\n")
        outputJDL.write("x509userproxy = $ENV(X509_USER_PROXY)\n")
        if (len(self.listOfScriptArguments_) > 0):
            argumentsString = "Arguments = "
            for scriptArgument in self.listOfScriptArguments_:
                argumentsString += "{sA} ".format(sA = scriptArgument)
            argumentsString = argumentsString[:-1] # To remove the space character at the end
            outputJDL.write("{aS}\n".format(aS=argumentsString))
        outputJDL.write("Queue 1\n")
        outputJDL.close()
