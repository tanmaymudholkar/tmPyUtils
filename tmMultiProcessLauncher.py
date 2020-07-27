from __future__ import print_function, division

import os, sys, subprocess, time, signal, tmGeneralUtils, pdb

class tmMultiProcessLauncher:
    def __init__(self, logOutputFolder=None, monitorUpdateTimeSeconds=10, enableStrictErrorDetection=True, printDebug=False):
        self.logOutputFolder = ""
        if not(logOutputFolder is None): self.logOutputFolder = logOutputFolder
        self.monitorUpdateTimeSeconds = monitorUpdateTimeSeconds
        self.enableStrictErrorDetection = enableStrictErrorDetection
        self.processes_list = []
        self.monitoring_process_handle = None
        self.tail_command = "tail -f"
        # Check if "multitail" exists
        multitail_version_command_exit_status = subprocess.call("multitail -V", shell=True, executable="/bin/bash")
        if (multitail_version_command_exit_status == 0): self.tail_command = "multitail"
        else: print("WARNNING: multitail not found, using usual tail -f.")

    def killAll(self):
        if not(self.monitoring_process_handle is None): self.monitoring_process_handle.send_signal(signal.SIGINT)
        for process in self.processes_list:
            processHandle = process["processHandle"]
            if (not(processHandle is None) and (processHandle.poll() is None)): processHandle.kill()

    def spawn(self, shellCommands=None, optionalEnvSetup=None, logFileName=None, printDebug=False):
        if ((shellCommands is None) or (logFileName is None)
            or (shellCommands == "") or (logFileName == "")
            or (shellCommands == [])): sys.exit("ERROR in tmProcessLauncher: both shellCommands to launch and logFileName must be specified. Currently, shellCommands={sC}, logFileName={lFN}".format(sC=shellCommands, lFN=logFileName))
        logFilesList = [process["logFileName"] for process in self.processes_list]
        if logFileName in logFilesList:
            self.killAll()
            sys.exit("ERROR: duplicate log file name: {lFN}".format(lFN=logFileName))
        outputFileHandle = open("{lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=logFileName), 'w')
        formattedShellCommand = "set -x && "
        if not(optionalEnvSetup is None): formattedShellCommand = "{oES} && echo \"env setup done.\" && set -x && ".format(oES=optionalEnvSetup)
        if isinstance(shellCommands, list):
            formattedShellCommand += " && ".join(shellCommands)
        else:
            formattedShellCommand += shellCommands
        formattedShellCommand += " && set +x"
        if printDebug: print("Spawning process with command: {fSC}".format(fSC=formattedShellCommand))
        processHandle = subprocess.Popen(formattedShellCommand, stdout=outputFileHandle, stderr=outputFileHandle, shell=True, executable="/bin/bash")
        self.processes_list.append({"logFileName": logFileName,
                                    "processHandle": processHandle})

    def generateTailCommand(self, printDebug=False):
        tailCommand = self.tail_command
        for process in self.processes_list:
            if (self.tail_command == "multitail"):
                tailCommand += " {lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=process["logFileName"])
            else:
                tailCommand += " -f {lOF}/{lFN}".format(lOF=self.logOutputFolder, lFN=process["logFileName"])
        if printDebug: print("Generated tail command: {tC}".format(tC=tailCommand))
        return tailCommand

    def monitorToCompletion(self, printDebug=False):
        print("Starting to monitor {n} processes:".format(n=len(self.processes_list)))
        oneOrMoreProcessesActive = True
        self.monitoring_process_handle = subprocess.Popen(self.generateTailCommand(printDebug=printDebug), shell=True, executable="/bin/bash")
        returnStatuses = {}
        while oneOrMoreProcessesActive:
            time.sleep(self.monitorUpdateTimeSeconds)
            # print("\n"*5)
            oneOrMoreProcessesActive = False
            processesToRemove = []
            for process in self.processes_list:
                oneOrMoreProcessesActive = True
                logFileName = process["logFileName"]
                processHandle = process["processHandle"]
                if ((processHandle is None) or not((processHandle.poll() is None))): # Process has terminated
                    processesToRemove.append(process)
                    returnStatuses[logFileName] = processHandle.returncode
                    if (self.enableStrictErrorDetection):
                        if (returnStatuses[logFileName] != 0):
                            self.killAll()
                            time.sleep(self.monitorUpdateTimeSeconds) # seems to be required between killAll and next line, maybe to clear buffer or something?
                            sys.exit("ERROR in process with log: {lOF}/{lFN}. Return code: {r}".format(lOF=self.logOutputFolder, lFN=logFileName, r=returnStatuses[logFileName]))
            if (len(processesToRemove) > 0):
                for process in processesToRemove:
                    (self.processes_list).remove(process)
                if (self.tail_command == "multitail"): # Restart the monitoring process with only the remaining processes
                    self.monitoring_process_handle.send_signal(signal.SIGINT)
                    if (len(self.processes_list) > 0): self.monitoring_process_handle = subprocess.Popen(self.generateTailCommand(printDebug=printDebug), shell=True, executable="/bin/bash")
        print("All processes finished!")
        print("Return statuses:")
        tmGeneralUtils.prettyPrintDictionary(inputDict=returnStatuses)
        time.sleep(self.monitorUpdateTimeSeconds)

if __name__ == "__main__":
    print("Launching test for tmMultiProcessLauncher...")
    logOutputFolder = raw_input("Enter absolute or relative path to output logs folder: ")
    returnCode = os.system("set -x && mkdir -p {oLF} && set +x".format(oLF=logOutputFolder))
    if (returnCode != 0): sys.exit("ERROR: Unable to check if folder {oLF} exists or create it.".format(oLF=logOutputFolder))
    
    multiProcessLauncher = tmMultiProcessLauncher(logOutputFolder=logOutputFolder, printDebug=True)

    # multiProcessLauncher.spawn(shellCommands="echo exiting with error && sleep 5 && exit 1", logFileName="expected_error.log", printDebug=True) # Should break and exit
    # multiProcessLauncher.spawn(shellCommands="echo sleeping 11 && sleep 11 && echo should not display slept 11", logFileName="sleeper_11.log", printDebug=True) # sleeper_11.log should not have the last echo output
    # multiProcessLauncher.monitorToCompletion(printDebug=True)

    # multiProcessLauncher.spawn(shellCommands="echo sleeping 59 && sleep 59 && echo slept 59", logFileName="sleeper_59.log", printDebug=True)
    # multiProcessLauncher.spawn(shellCommands="echo test sleeping 59 && sleep 59 && echo slept 59", logFileName="sleeper_59.log", printDebug=True) # should break due to duplicate log
    # multiProcessLauncher.monitorToCompletion(printDebug=True)

    multiProcessLauncher.spawn(shellCommands="echo sleeping 30 && sleep 30 && echo slept 30", logFileName="sleeper_30.log", printDebug=True)
    multiProcessLauncher.spawn(shellCommands="echo sleeping 60 && sleep 60 && echo slept 60", logFileName="sleeper_60.log", printDebug=True)
    multiProcessLauncher.spawn(shellCommands="echo sleeping 65 && sleep 65 && echo slept 65", logFileName="sleeper_65.log", printDebug=True)
    multiProcessLauncher.monitorToCompletion(printDebug=True)

    multiProcessLauncher.spawn(shellCommands=["echo sleeping 5 plus 6", "sleep 5", "echo slept 5", "sleep 6", "echo slept 6"], optionalEnvSetup="echo \"test: HOME=${HOME}\"", logFileName="sleeper_5and6.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 64 && sleep 64 && echo slept 64", optionalEnvSetup="echo \"test: HOME=${HOME}\"", logFileName="sleeper_64.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 41 && sleep 41 && echo slept 41", optionalEnvSetup="echo \"test: HOME=${HOME}\"", logFileName="sleeper_41.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 42 && sleep 42 && echo slept 42", optionalEnvSetup="echo \"test: HOME=${HOME}\"", logFileName="sleeper_42.log")
    multiProcessLauncher.spawn(shellCommands="echo sleeping 55 && sleep 55 && echo slept 55", optionalEnvSetup="echo \"test: HOME=${HOME}\"", logFileName="sleeper_55.log")
    multiProcessLauncher.monitorToCompletion()
