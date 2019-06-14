from __future__ import print_function, division

import subprocess, os, sys, csv

def get_lumi(runNumber=-1, printDebug=False):
    userName = os.getenv("USER")
    if (printDebug): print("Username: {u}".format(u=userName))
    if (runNumber < 0): sys.exit("ERROR: runNumber needs to be a valid CMS run. Currently, runNumber = {r}".format(r=runNumber))
    if (printDebug): print("Checking that brilcalc exists...")
    brilcalc_check = subprocess.call("set -x && type brilcalc && set +x", shell=True)
    if (brilcalc_check != 0): sys.exit("ERROR: brilcalc executable not found. Please check that your environment variable ${PATH} contains the location of the brilcalc executable, usually: ${HOME}/.local/bin")
    if (printDebug): print("Running brilcalc on chosen run...")
    brilcalc_execute = subprocess.call(("set -x && brilcalc lumi --byls -r {r} -o /tmp/{u}/lumi_tmp.txt && set +x").format(r=runNumber, u=userName), shell=True)
    if (brilcalc_execute != 0): sys.exit("ERROR: brilcalc command failed. Exit code: {c}".format(c=brilcalc_execute))
    lumilist_fileObject = open("/tmp/{u}/lumi_tmp.txt".format(u=userName), 'r')

    # There is no way to specify to the csv module that lines beginning with "#" are comments to be ignored.
    # The lambda function maps a line to False if it begins with a "#" character and True otherwise.
    # The filter function adds all uncommented lines to one list.
    # The DictReader parses all those uncommented lines into a dictionary.
    lumilist_csvreader = csv.DictReader(filter(lambda line: (line[0] != "#"), lumilist_fileObject), fieldnames=["run_fill","ls1_ls2","time","beamstatus","E_GeV","delivered","recorded","avgpu","source"], delimiter=",", strict=True)
    outputDict={}
    for datapoint in lumilist_csvreader:
        if (printDebug): print("Read in datapoint from file: " + str(datapoint))
        ls1_ls2_raw_split = (datapoint["ls1_ls2"]).split(":")
        if not(len(ls1_ls2_raw_split) == 2): sys.exit("ERROR: expected lumisection info in format \"LS1:LS2\"; found: {f}".format(f=datapoint["ls1_ls2"]))
        ls1 = int(ls1_ls2_raw_split[0])
        ls2 = int(ls1_ls2_raw_split[1])
        if not(ls1 == ls2): sys.exit("Unexpected format for the lumisection numbers.")
        outputDict[ls1] = {}
        outputDict[ls1]["lumi"] = float(datapoint["recorded"])
        outputDict[ls1]["PU"] = float(datapoint["avgpu"])
        if (printDebug): print("Adding these values from LS {ls} to output dictionary: {o}".format(ls=ls1, o=str(outputDict[ls1])))
    lumilist_fileObject.close()
    if (printDebug): print("Removing temp file...")
    subprocess.call("set -x && rm -v /tmp/{u}/lumi_tmp.txt && set +x".format(u=userName), shell=True)
    return outputDict
