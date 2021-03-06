#!/usr/bin/env python

from __future__ import print_function, division

import os, sys, math, argparse, json

parser=argparse.ArgumentParser(description = "Wrapper around dasgoclient that writes a list, sorted by lumisection number, of paths to datafiles for a given run to a file.")
parser.add_argument('--dataset', action='store', help='Name of dataset', type=str, required=True)
parser.add_argument('--runNumber', action='store', help='Run number', type=int, required=True)
parser.add_argument('--outputFile', action='store', help='Name of output file to which to write the list of root files', type=str, required=True)
parser.add_argument('--minLumi', action='store', default=0, help='Start from lumi (remember to pass option to CMSSW cfg file as well)', type=int)
parser.add_argument('--maxLumi', action='store', default=0, help='End at lumi (remember to pass option to CMSSW cfg as well)', type=int)
inputArguments = parser.parse_args()

backupPath = "/afs/cern.ch/user/t/tmudholk/public/research/dasgoclient/dasgoclient_linux"
pathToClient = ""
if (os.getenv("CMSSW_BASE") is None):
    print("WARNING: CMSSW_BASE not set, reverting to default client: " + backupPath)
    pathToClient = backupPath
else: pathToClient = "dasgoclient" # Should already be somewhere in $PATH if cms environment has been sourced

tempFileFullPath = "/tmp/tmudholk/query_result.jsn"

commandToCall = pathToClient + " -query \"" + "file, lumi dataset={dataset} run={run}".format(dataset=inputArguments.dataset, run=inputArguments.runNumber) + "\" -json > {tmpPath}".format(tmpPath=tempFileFullPath)
os.system(commandToCall)
jsonFormattedQueryResult = open(tempFileFullPath)
deserializedQueryResult = json.load(jsonFormattedQueryResult)
jsonFormattedQueryResult.close()
os.system("rm " + tempFileFullPath)

datafilesWithLumisectionsList = [[deserializedQueryResult[i]['lumi'][0]['number'], deserializedQueryResult[i]['file'][0]['name']] for i in range(len(deserializedQueryResult))]

datafilesWithFirstLumisectionDict = {}
for i in range(len(datafilesWithLumisectionsList)):
    datafilesWithFirstLumisectionDict[min(datafilesWithLumisectionsList[i][0])] = (max(datafilesWithLumisectionsList[i][0]), datafilesWithLumisectionsList[i][1])

datafilesString = ""
for sortedLumiNumber in sorted(datafilesWithFirstLumisectionDict.keys()):
    if ((inputArguments.minLumi > 0 and inputArguments.maxLumi > 0) and inputArguments.maxLumi >= inputArguments.minLumi):
        if (sortedLumiNumber > inputArguments.maxLumi): continue
        elif (datafilesWithFirstLumisectionDict[sortedLumiNumber][0] < inputArguments.minLumi): continue
    datafilesString += datafilesWithFirstLumisectionDict[sortedLumiNumber][1] + "\n"

outputFile = open(inputArguments.outputFile, 'w')
outputFile.write(datafilesString)
outputFile.close()
