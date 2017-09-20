#!/usr/bin/env python

from __future__ import print_function, division

import os, sys, math, argparse, json

parser=argparse.ArgumentParser(description = "Wrapper around dasgoclient that writes a list, sorted by lumisection number, of paths to datafiles for a given run to a file.")
parser.add_argument('--dataset', action='store', help='Name of dataset', type=str, required=True)
parser.add_argument('--runNumber', action='store', help='Run number', type=int, required=True)
parser.add_argument('--outputFile', action='store', help='Name of output file to which to write the list of root files', type=str, required=True)
inputArguments = parser.parse_args()

pathToClient = "/afs/cern.ch/user/t/tmudholk/public/research/dasgoclient/dasgoclient_linux"
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
    datafilesWithFirstLumisectionDict[min(datafilesWithLumisectionsList[i][0])] = datafilesWithLumisectionsList[i][1]

datafilesString = ""
for sortedLumiNumber in sorted(datafilesWithFirstLumisectionDict.keys()):
    datafilesString += datafilesWithFirstLumisectionDict[sortedLumiNumber] + "\n"

outputFile = open(inputArguments.outputFile, 'w')
outputFile.write(datafilesString)
outputFile.close()
