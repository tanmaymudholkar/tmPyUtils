#!/usr/bin/env python

from __future__ import print_function, division

import os, sys, subprocess, argparse, re
import tmJDLInterface

inputArgumentsParser = argparse.ArgumentParser(description='Submit matrix test jobs to condor.')
inputArgumentsParser.add_argument('--identifier', required=True, help="Identifier string for submission.", type=str)
inputArguments = inputArgumentsParser.parse_args()

current_working_directory = os.getcwd()
subprocess.check_call("mkdir -p condor_files", shell=True, executable="/bin/bash")

# Step 1: Create CMSSW tarball
print("Creating CMSSW tarball...")
CMSSWBase = os.getenv("CMSSW_BASE")
SCRAMArch = os.getenv("SCRAM_ARCH")
if (CMSSWBase == ""): sys.exit("ERROR: CMSSW_BASE not set.")
# print("CMSSWFolderName: {CFN}".format(CFN=CMSSWFolderName))
print("CMSSW_BASE: {CB}".format(CB=CMSSWBase))
CMSSWFolderName = CMSSWBase.split("/")[-1]
print("Packaging CMSSW...")
subprocess.check_call("set -x && cd {CB}/.. && tar --exclude-vcs -zcf CMSSWBundle_{identifier}.tar.gz -C {CFN}/.. {CFN} && mv -v CMSSWBundle_{identifier}.tar.gz {cwd}/condor_files/CMSSWBundle_{identifier}.tar.gz && cd {cwd} && set +x".format(identifier=inputArguments.identifier, CB=CMSSWBase, CFN=CMSSWFolderName, cwd=current_working_directory), shell=True, executable="/bin/bash")
print("Packaged CMSSW.")

# Step 2: Create script
print("Creating script...")
print("Creating test script:")
scriptFileHandle = open("condor_files/runMatrixScript.sh", "w")
scriptFileHandle.write("#!/bin/bash\n")
scriptFileHandle.write("\n")
scriptFileHandle.write("echo \"Sourcing CMSSW environment...\"\n")
scriptFileHandle.write("source /cvmfs/cms.cern.ch/cmsset_default.sh\n")
scriptFileHandle.write("tar -xf CMSSWBundle_{identifier}.tar.gz && rm -f CMSSWBundle_{identifier}.tar.gz\n".format(identifier=inputArguments.identifier))
scriptFileHandle.write("export SCRAM_ARCH={SA}\n".format(SA=SCRAMArch))
scriptFileHandle.write("cd {CFN}/src && scramv1 b ProjectRename && eval `scramv1 runtime -sh` && scram b clean && scram b && cd ../..\n".format(CFN=CMSSWFolderName))
scriptFileHandle.write("\n")
scriptFileHandle.write("runTheMatrix.py -l ${1} -i all --ibeos\n")
scriptFileHandle.write("mv -v ${{1}}* {cwd}/\n".format(cwd=current_working_directory))
scriptFileHandle.write("rm -r {CFN}\n".format(CFN=CMSSWFolderName))
scriptFileHandle.close()
subprocess.check_call("set -x && chmod +x condor_files/runMatrixScript.sh && set +x", shell=True, executable="/bin/bash")
print("Created executable test script.")

# Step 3: Get list of workflows to run
limitedWorkflowDetails = subprocess.check_output("runTheMatrix.py --showMatrix -l limited", stderr=subprocess.STDOUT, universal_newlines=True, shell=True, executable="/bin/bash")
followingXWereSelectedRegEx = re.compile("the\sfollowing\s+([0-9]+)\s+were\sselected")
expectedNWorkflowsCheck = -1
numberNamePairRegEx = re.compile("^([0-9]+\.[0-9]+)\s+([^\s]+)$")
workflowNumberNamePairs = []
for lineRaw in limitedWorkflowDetails.split("\n"):
    line = lineRaw.rstrip()
    if (expectedNWorkflowsCheck < 0):
        followingXWereSelectedRegExMatch = followingXWereSelectedRegEx.search(line)
        if not(followingXWereSelectedRegExMatch is None):
            expectedNWorkflowsCheck = int(0.5 + float(followingXWereSelectedRegExMatch.group(1)))
            print("Found line containing number of selected workflows. Expected number: {n}".format(n=expectedNWorkflowsCheck))
    numberNamePairRegExMatch = numberNamePairRegEx.match(line)
    if not(numberNamePairRegExMatch is None):
        wfNumber = numberNamePairRegExMatch.group(1)
        wfName = numberNamePairRegExMatch.group(2)
        print("Found (number, name) pair for selected workflow: ({wfNum}, {wfName})".format(wfNum=wfNumber, wfName=wfName))
        workflowNumberNamePairs.append(tuple([wfNumber, wfName]))

# Sanity check
if (len(workflowNumberNamePairs) != expectedNWorkflowsCheck): sys.exit("ERROR: expected {n} workflows, found {m}!".format(n=expectedNWorkflowsCheck, m=len(workflowNumberNamePairs)))

print("Submitting jobs for {n} workflows...".format(n=len(workflowNumberNamePairs)))
for workflowNumberNamePair in workflowNumberNamePairs:
    workflowNumber = workflowNumberNamePair[0]
    workflowID = workflowNumber.replace(".", "pt")
    workflowName = workflowNumberNamePair[1]
    # Step 4: Create jdl for each workflow
    print("Creating JDL for workflow {wid}:".format(wid=workflowID))
    jdlInterface = tmJDLInterface.tmJDLInterface(processName="runMatrix_{wid}".format(wid=workflowID), scriptPath="runMatrixScript.sh", outputDirectoryRelativePath="condor_files")
    filesToTransfer = ["{cwd}/condor_files/CMSSWBundle_{identifier}.tar.gz".format(cwd=current_working_directory, identifier=inputArguments.identifier)]
    jdlInterface.addFilesToTransferFromList(filesToTransfer)
    jdlInterface.addScriptArgument(workflowNumber)
    hostname = os.getenv("HOSTNAME")
    if ("lxplus" in hostname):
        jdlInterface.setFlavor("longlunch")
    jdlInterface.writeToFile()
    print("Wrote JDL for workflow {wid}.".format(wid=workflowID))

    # Step 5: Submit jdl
    subprocess.check_call("set -x && cd {cwd}/condor_files && condor_submit runMatrix_{wid}.jdl && cd - && set +x".format(cwd=current_working_directory, wid=workflowID), shell=True, executable="/bin/bash")
