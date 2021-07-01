#!/usr/bin/env python

from __future__ import print_function, division

import os, sys, subprocess, argparse, time, signal

inputArgumentsParser = argparse.ArgumentParser(description='Locally run specified job specfified as if it were running on Condor, to help debug issues.')
inputArgumentsParser.add_argument('--pathToCondorFolder', required=True, help="Absolute path to directory from which condor_submit is meant to be called.", type=str)
inputArgumentsParser.add_argument('--targetJDLName', required=True, help="Name of JDL file for the job.", type=str)
inputArgumentsParser.add_argument('--workingDirectory', default="{cwd}/temp".format(cwd=os.getcwd()), help="Absolute path to working directory for simulated job.", type=str)
inputArguments = inputArgumentsParser.parse_args()

PROCESS_POLLING_INTERVAL_IN_SECONDS = 10

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
relevant_jdl_argument_names_compulsory = ["executable"]
relevant_jdl_argument_names_optional = ["transfer_input_files", "arguments", "request_memory"]
jdl_arguments = {}
with open("{d}/{f}".format(d=inputArguments.pathToCondorFolder, f=inputArguments.targetJDLName)) as jdl_file_handle:
    for line in jdl_file_handle:
        line_split = line.strip().split("=")
        if (len(line_split) == 2):
            arg_name = (line_split[0]).strip()
            if ((arg_name in relevant_jdl_argument_names_compulsory) or (arg_name in relevant_jdl_argument_names_optional)):
                arg_value = (line_split[1]).strip()
                jdl_arguments[arg_name] = arg_value

# Step 2: Check that all compulsory relevant settings are present
for argument_name in relevant_jdl_argument_names_compulsory:
    if not(argument_name in jdl_arguments):
        sys.exit("ERROR: Value for argument \"{a}\" not found in jdl file!".format(a=argument_name))
    print("Found {a} = {v}".format(a=argument_name, v=jdl_arguments[argument_name]))

# Step 3: Copy over script and all files that need to be transferred
subprocess.check_call("cp -a {d}/{s} {wd}/".format(d=inputArguments.pathToCondorFolder, s=jdl_arguments["executable"], wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")
if ("transfer_input_files" in jdl_arguments):
    for file_to_transfer in (jdl_arguments["transfer_input_files"]).split(","):
        subprocess.check_call("cp -a {f} {wd}/".format(f=file_to_transfer, wd=inputArguments.workingDirectory), shell=True, executable="/bin/bash")

# Step 4: Run the command within memory limits
run_command = ""
run_command += "set -x && "
if ("request_memory" in jdl_arguments): memory_limit = (int(0.5 + float(jdl_arguments["request_memory"])))*1000 # "request_memory" is in MB, the ps command measures memory consumed in KB
else: memory_limit = 2000*1000 # 2000 MB
run_command += "export _CONDOR_SCRATCH_DIR={wd} && cd {wd} && ./{s} ".format(wd=inputArguments.workingDirectory, s=jdl_arguments["executable"])
if ("arguments" in jdl_arguments): run_command += jdl_arguments["arguments"]
run_command += " && set +x"
process_handle = subprocess.Popen(run_command, shell=True, executable="/bin/bash")
process_pid = process_handle.pid
while True:
    time.sleep(PROCESS_POLLING_INTERVAL_IN_SECONDS)
    if ((process_handle is None) or not((process_handle.poll() is None))): # Process has terminated
        print("Process terminated.")
        break
    else:
        process_and_children_pids_raw = (str(subprocess.check_output("pstree -p {pid} | grep -o '([0-9]\+)' | grep -o '[0-9]\+'".format(pid=process_pid), shell=True, executable="/bin/bash"))).split("\n")
        process_and_children_pids_list_unfiltered = [s.strip() for s in process_and_children_pids_raw]
        process_and_children_pids_list_unmapped = filter(lambda s: s != '', process_and_children_pids_list_unfiltered)
        process_and_children_pids_list = map(lambda s: int(0.5 + float(s)), process_and_children_pids_list_unmapped)
        process_and_children_memory_consumption_raw = (str(subprocess.check_output("pstree -p {pid} | grep -o '([0-9]\+)' | grep -o '[0-9]\+' | xargs ps --no-headers -o rss -p".format(pid=process_pid), shell=True, executable="/bin/bash"))).split("\n")
        process_and_children_memory_consumption_list_unfiltered = [s.strip() for s in process_and_children_memory_consumption_raw]
        process_and_children_memory_consumption_list = filter(lambda s: s != '', process_and_children_memory_consumption_list_unfiltered)
        memory_consumption_max = max(map(lambda s: int(0.5 + float(s)), process_and_children_memory_consumption_list))
        if (memory_consumption_max > memory_limit):
            print("ERROR: memory consumption exceeded set maximum, killing process...")
            for pid in process_and_children_pids_list:
                if (pid != process_pid):
                    print("Terminating process with pid {pid}".format(pid=pid))
                    os.kill(pid, signal.SIGKILL)
            process_handle.kill()

print("All done!")
