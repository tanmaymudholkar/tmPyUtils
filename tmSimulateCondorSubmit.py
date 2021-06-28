#!/usr/bin/env python

from __future__ import print_function, division

import os, sys, subprocess, argparse

inputArgumentsParser = argparse.ArgumentParser(description='Locally run specified job specfified as if it were running on Condor, to help debug issues.')
inputArgumentsParser.add_argument('--pathToCondorFolder', required=True, help="Absolute path to directory from which condor_submit is meant to be called.", type=str)
inputArgumentsParser.add_argument('--targetJDLName', required=True, help="Name of JDL file for the job.", type=str)
inputArgumentsParser.add_argument('--workingDirectory', default="{cwd}/temp".format(cwd=os.getcwd()), help="Absolute path to working directory for simulated job.", type=str)
inputArguments = inputArgumentsParser.parse_args()

# Make working directory
subprocess.check_call("mkdir -p {wd}".format(wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")

# Make sure working directory is empty
if (len(os.listdir(inputArguments.workingDirectory)) > 0):
    choice = (raw_input(("WARNING: target directory {wd} is not empty. Do you want to clean it? (y: clean and continue, n: do nothing and exit) ").format(wd=inputArguments.workingDirectory))).lower()
    if (choice == 'y'): subprocess.check_call("rm -rf {wd}/*".format(wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")
    else:
        if (choice == 'n'): print("OK, exiting.")
        else: print("ERROR: unrecognized choice: {c}".format(c=choice))
        sys.exit("Terminated.")

# Step 1: Get relevant settings from the JDL file
relevant_jdl_argument_names = ["executable", "transfer_input_files", "arguments"]
jdl_arguments = {}
with open("{d}/{f}".format(d=inputArguments.pathToCondorFolder, f=inputArguments.targetJDLName)) as jdl_file_handle:
    for line in jdl_file_handle:
        line_split = line.strip().split("=")
        if (len(line_split) == 2):
            arg_name = (line_split[0]).strip()
            if (arg_name in relevant_jdl_argument_names):
                arg_value = (line_split[1]).strip()
                jdl_arguments[arg_name] = arg_value

# Step 2: Check that all relevant settings are present
for argument_name in relevant_jdl_argument_names:
    if not(argument_name in jdl_arguments):
        sys.exit("ERROR: Value for argument \"{a}\" not found in jdl file!".format(a=argument_name))
    print("Found {a} = {v}".format(a=argument_name, v=jdl_arguments[argument_name]))

# Step 3: Copy over script and all files that need to be transferred
subprocess.check_call("cp -a {d}/{s} {wd}/".format(d=inputArguments.pathToCondorFolder, s=jdl_arguments["executable"], wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")
for file_to_transfer in (jdl_arguments["transfer_input_files"]).split(","):
    subprocess.check_call("cp -a {f} {wd}/".format(f=file_to_transfer, wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")

run_command = "set -x && export _CONDOR_SCRATCH_DIR={wd} && cd {wd} && ./{s} {a} && set +x".format(wd=inputArguments.workingDirectory, s=jdl_arguments["executable"], a=jdl_arguments["arguments"])
subprocess.check_call(run_command, shell=True, executable="/bin/bash")

print("All done!")
