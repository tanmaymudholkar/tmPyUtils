from __future__ import print_function, division

import os, sys, subprocess, time, pdb

class tmMultiProcessLauncher:
    def __init__(self, logOutputFolder=None, monitorUpdateTimeSeconds=10, printDebug=False):
        self.logOutputFolder = ""
        if not(logOutputFolder is None): self.logOutputFolder = logOutputFolder
        self.monitorUpdateTimeSeconds = monitorUpdateTimeSeconds
        self.processes_list = []

    def killAll(self):
        for process in self.processes_list:
            processHandle = process["processHandle"]
            processHandle.kill()
            (self.processes_list).remove(process)

    def spawn(self, shellCommands=None, logFileName=None, printDebug=False):
        if ((shellCommands is None) or (logFileName is None)
            or (shellCommands == "") or (logFileName == "")
            or (shellCommands == [])): sys.exit("ERROR in tmProcessLauncher: both shellCommands to launch and logFileName must be specified. Currently, shellCommands={sC}, logFileName={lFN}".format(sC=shellCommands, lFN=logFileName))
        if printDebug: print("spawn called with shellCommands: {sC}, logFileName: {lFN}".format(sC=shellCommands, lFN=logFileName))
        if printDebug: print("About to spawn: {c}".format(c=shellCommands))
        logFilesList = [process["logFileName"] for process in self.processes_list]
        if logFileName in logFilesList:
            self.killAll()
            sys.exit("ERROR: duplicate log file name: {lFN}".format(lFN=logFileName))
        outputFileHandle = open("{lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=logFileName), 'w')
        formattedShellCommand = shellCommands
        if isinstance(shellCommands, list):
            formattedShellCommand = " && ".join(shellCommands)
        processHandle = subprocess.Popen("{fSC}".format(fSC=formattedShellCommand), stdout=outputFileHandle, stderr=subprocess.STDOUT, shell=True)
        self.processes_list.append({"logFileName": logFileName,
                                    "processHandle": processHandle})

    def monitorToCompletion(self, printDebug=False):
        print("Starting to monitor {n} processes:".format(n=len(self.processes_list)))
        oneOrMoreProcessesActive = True
        while oneOrMoreProcessesActive:
            time.sleep(self.monitorUpdateTimeSeconds)
            print("\n"*5)
            oneOrMoreProcessesActive = False
            processesToRemove = []
            for process in self.processes_list:
                oneOrMoreProcessesActive = True
                logFileName = process["logFileName"]
                if printDebug: print("Checking process with log: {lFN}".format(lFN=logFileName))
                processHandle = process["processHandle"]
                if ((processHandle is None) or not((processHandle.poll() is None))): # Process has terminated
                    print("Process finished: {lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=logFileName))
                    print("Last 20 lines of output:")
                    os.system("tail -20 {lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=logFileName))
                    processesToRemove.append(process)
                else: # process still hasn't terminated
                    print("Output of {lOF}/{lFN}:".format(lOF=self.logOutputFolder, lFN=logFileName))
                    os.system("tail -2 {lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=logFileName))
                print("\n"*2)
            for process in processesToRemove:
                (self.processes_list).remove(process)    
        print("All processes finished!")

def tmMultiProcessLauncherTest():
    logOutputFolder = raw_input("Enter absolute or relative path to output logs folder: ")
    returnCode = os.system("set -x && mkdir -p {oLF} && set +x".format(oLF=logOutputFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to check if folder {oLF} exists or create it.".format(oLF=logOutputFolder))
    
    multiProcessLauncher = tmMultiProcessLauncher(logOutputFolder=logOutputFolder, printDebug=True)
    # multiProcessLauncher.spawn(shellCommands="echo sleeping 25 && sleep 25 && echo slept 25", logFileName="sleeper_25.log", printDebug=True)
    # multiProcessLauncher.spawn(shellCommands="echo sleeping 59 && sleep 59 && echo slept 59", logFileName="sleeper_59.log", printDebug=True)
    # multiProcessLauncher.spawn(shellCommands="echo test sleeping 59 && sleep 59 && echo slept 59", logFileName="sleeper_59.log", printDebug=True) # should break due to duplicate log

    multiProcessLauncher.spawn(shellCommands="echo sleeping 30 && sleep 30 && echo slept 30", logFileName="sleeper_30.log", printDebug=True)
    multiProcessLauncher.spawn(shellCommands="echo sleeping 60 && sleep 60 && echo slept 60", logFileName="sleeper_60.log", printDebug=True)
    multiProcessLauncher.spawn(shellCommands="echo sleeping 65 && sleep 65 && echo slept 65", logFileName="sleeper_65.log", printDebug=True)
    multiProcessLauncher.monitorToCompletion(printDebug=True)

    print("Testing with new processes:")
    multiProcessLauncher.spawn(shellCommands=["echo sleeping 5 plus 6", "sleep 5", "echo slept 5", "sleep 6", "echo slept 6"], logFileName="sleeper_5and6.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 64 && sleep 64 && echo slept 64", logFileName="sleeper_64.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 41 && sleep 41 && echo slept 41", logFileName="sleeper_41.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 42 && sleep 42 && echo slept 42", logFileName="sleeper_42.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 55 && sleep 55 && echo slept 55", logFileName="sleeper_55.log")
    multiProcessLauncher.monitorToCompletion()

if __name__ == "__main__":
    tmMultiProcessLauncherTest()
