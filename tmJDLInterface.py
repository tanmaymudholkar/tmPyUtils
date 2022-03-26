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
        hostname = os.getenv("HOSTNAME")
        self.habitat_ = ""
        if ("lxplus" in hostname):
            self.habitat_ = "lxplus"
        elif ("fnal" in hostname):
            self.habitat_ = "fnal"
        else:
            sys.exit("ERROR: Unrecognized hostname: {h}, seems to be neither lxplus nor fnal.".format(h=hostname))
        self.flavor_ = ""
        self.explicitMemoryRequestInMB_ = -1.0

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

    def setFlavor(self, flavor):
        if not(isinstance(flavor, basestring)):
            sys.exit("tmJDLInterface: method setFlavor only accepts raw strings as an argument.")
        if not(self.habitat_ == "lxplus"):
            sys.exit("tmJDLInterface: method setFlavor only usable from lxplus.")
        self.flavor_ = flavor

    def makeExplicitMemoryRequest(self, requestedMemoryInMB):
        if not(isinstance(requestedMemoryInMB, int)):
            sys.exit("tmJDLInterface: method makeExplicitMemoryRequest only accepts ints (memory in MB) as an argument.")
        self.explicitMemoryRequestInMB_ = requestedMemoryInMB

    def writeToFile(self):
        outputJDLFileName = ("{oD}/{name}.jdl".format(oD=self.outputDirectoryRelativePath_, name=self.processName_))
        if os.path.isfile(outputJDLFileName):
            print("File: {name} already exists. Recreating...".format(name=outputJDLFileName))
            os.system("rm -f {out}".format(out=outputJDLFileName))
        outputJDL = open(outputJDLFileName, "w")
        outputJDL.write("universe = vanilla\n")
        outputJDL.write("executable = {sP}\n".format(sP=self.scriptPath_))
        if (self.habitat_ == "fnal"): # questionable -- doesn't seem to achieve anything
            outputJDL.write("should_transfer_files = YES\n")
            outputJDL.write("whentotransferoutput = ON_EXIT\n")
        if (len(self.listOfFilesToTransfer_) > 0):
            transferString = "transfer_input_files = "
            for fileToTransfer in (self.listOfFilesToTransfer_):
                transferString += "{f},".format(f=fileToTransfer)
            transferString = transferString[:-1] # To remove the "," at the end
            outputJDL.write("{tS}\n".format(tS=transferString))
        outputJDL.write("transfer_output_files = \"\"\n") # To prevent tons of useless files being copied back into the workarea
        outputJDL.write("output = log_{pN}.stdout\n".format(pN=self.processName_))
        outputJDL.write("error = log_{pN}.stderr\n".format(pN=self.processName_))
        outputJDL.write("log = log_{pN}.log\n".format(pN=self.processName_))
        outputJDL.write("notify_user = {lN}@cern.ch\n".format(lN=os.getenv("LOGNAME")))
        if (len(self.listOfScriptArguments_) > 0):
            argumentsString = "arguments = "
            for scriptArgument in self.listOfScriptArguments_:
                argumentsString += "{sA} ".format(sA = scriptArgument)
            argumentsString = argumentsString[:-1] # To remove the space character at the end
            outputJDL.write("{aS}\n".format(aS=argumentsString))
        if (self.habitat_ == "lxplus"):
            if (self.flavor_):
                # Apparently setting the flavor is not enough, some jobs exit with the message "Job removed by SYSTEM_PERIODIC_REMOVE due to wall time exceeded allowed max."
                # According to the documentation you can also set MaxRuntime manually...
                max_runtimes_dict = {
                    "espresso": 20*60, # 20 minutes
                    "microcentury": 60*60, # 1 hour
                    "longlunch": 2*60*60, # 2 hours
                    "workday": 8*60*60, # 8 hours
                    "tomorrow": 24*60*60, # 1 day
                    "testmatch": 3*24*60*60, # 3 days -- with the spelling of "flavor" and the reference to cricket, I'm beginning to think this was written by a Britisher...
                    "nextweek": 7*24*60*60 # 1 week
                }
                if (self.flavor_ in max_runtimes_dict):
                    outputJDL.write("+JobFlavour = {f}\n".format(f=self.flavor_)) # the "+" is deliberate and needed according to the documentation
                    outputJDL.write("+MaxRuntime = {f}\n".format(f=max_runtimes_dict[self.flavor_])) # the "+" is deliberate and needed according to the documentation
                else:
                    sys.exit("Flavor set to {f}, which is currently unsupported.".format(f=self.flavor_))
            else:
                sys.exit("Flavor needs to be set for lxplus jobs.")
        if (self.explicitMemoryRequestInMB_ > 0.):
            outputJDL.write("request_memory = {m}\n".format(m=self.explicitMemoryRequestInMB_))
        outputJDL.write("queue 1\n")
        outputJDL.close()

def tmJDLInterfaceTest():
    outputFolder = raw_input("Enter relative path to test output folder: ")
    print("Checking output folder:")
    returnCode = os.system("set -x && mkdir -p {oF} && set +x".format(oF=outputFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to check if folder {oF} exists or create it.".format(oF=outputFolder))

    # Step 1: create test script
    print("Creating test script:")
    scriptFileHandle = open("{oF}/tmJDLInterfaceTestScript.sh".format(oF=outputFolder), "w")
    scriptFileHandle.write("#!/bin/bash\n")
    scriptFileHandle.write("\n")
    scriptFileHandle.write("echo starting script \n")
    scriptFileHandle.write("echo sleeping ${1}\n")
    scriptFileHandle.write("sleep ${1}\n")
    scriptFileHandle.write("echo slept ${1}\n")
    scriptFileHandle.close()
    returnCode = os.system("set -x && chmod +x {oF}/tmJDLInterfaceTestScript.sh && set +x".format(oF=outputFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to check if folder {oF} exists or create it.".format(oF=outputFolder))
    print("Created executable test script.")

    # Step 2: create JDL
    print("Creating test JDL:")
    jdlInterface = tmJDLInterface(processName="tmJDLInterfaceTest", scriptPath="tmJDLInterfaceTestScript.sh", outputDirectoryRelativePath=outputFolder)
    jdlInterface.addScriptArgument("120") # script will sleep for 120 seconds and then exit
    hostname = os.getenv("HOSTNAME")
    if ("lxplus" in hostname):
        jdlInterface.setFlavor("espresso")
    jdlInterface.writeToFile()
    print("Wrote test JDL.")

    # Step 3: submit JDL
    print("Submitting JDL:")
    returnCode = os.system("set -x && cd {oF} && condor_submit tmJDLInterfaceTest.jdl && cd - && set +x".format(oF=outputFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to submit test JDL.")
    print("Submitted JDL.")

    # Step 4 (for convenience): call "condor_q" once
    print("Calling condor_q:")
    returnCode = os.system("set -x && condor_q && set +x")
    if (returnCode != 0): sys.exit("ERROR: Unable to call condor_q.")

if __name__ == "__main__":
    tmJDLInterfaceTest()
