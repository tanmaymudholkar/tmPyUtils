from __future__ import print_function, division

import os, sys, subprocess

def get_number_of_events_in_dataset(dataset_name):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"file dataset={d} | grep file.nevents\"".format(d=dataset_name), shell=True, universal_newlines=True, executable="/bin/bash"))
    total_nevents = 0
    for nevents_line in dasgoclient_output_raw.splitlines():
        nevents = int(nevents_line)
        total_nevents += nevents
    return total_nevents

def print_number_of_events_in_dataset(dataset_name):
    print("#evts in {d}: {n}".format(d=dataset_name, n=get_number_of_events_in_dataset(dataset_name)))

def get_list_of_datasets(query_string):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"dataset dataset={q}\"".format(q=query_string), shell=True, universal_newlines=True, executable="/bin/bash"))
    datasets_list = []
    for dset in dasgoclient_output_raw.splitlines():
        datasets_list.append(dset)
    return datasets_list

def print_list_of_datasets(query_string):
    for dataset in get_list_of_datasets(query_string):
        print(dataset)

def print_list_of_datasets_with_nevts(query_string):
    for dataset in get_list_of_datasets(query_string):
        print("{d}: {n}".format(d=dataset, n=get_number_of_events_in_dataset(dataset)))

def get_mcm_prepid_for_dataset(dataset_name):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"mcm dataset={d}\"".format(d=dataset_name), shell=True, universal_newlines=True, executable="/bin/bash"))
    if (len(dasgoclient_output_raw.splitlines()) != 1): sys.exit("ERROR: multiple prepIDs for pattern: {p}".format(p=dataset_name))
    return str((dasgoclient_output_raw.splitlines())[0])

def xsec_setup(shell_session_handle):
    path_xsec_cmssw = os.environ["PATH_XSEC_CMSSW"]
    xsec_scram_arch = os.environ["XSEC_SCRAM_ARCH"]
    path_xsec_scripts = os.environ["PATH_XSEC_SCRIPTS"]
    stdout_output, stderr_output = shell_session_handle.communicate("export SCRAM_ARCH={sa}".format(sa=xsec_scram_arch))
    stdout_output, stderr_output = shell_session_handle.communicate("echo SCRAM_ARCH=${SCRAM_ARCH}")
    print("stdout output of echo ${{SCRAM_ARCH}}: {o}".format(o=str(stdout_output)))
    stdout_output, stderr_output = shell_session_handle.communicate("cd {d}".format(d=path_xsec_cmssw))
    stdout_output, stderr_output = shell_session_handle.communicate("ls".format(sa=xsec_scram_arch))
    print("stdout output of ls: {o}".format(o=str(stdout_output)))

def get_xsec_info_for_dataset(dataset_name):
    cwd = os.getcwd()
    dataset_mcm_id = get_mcm_prepid_for_dataset(dataset_name)
    shell_session_handle = subprocess.Popen("env -i bash", stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, executable="/bin/bash")
    xsec_setup(shell_session_handle)
    shell_session_handle.terminate()
    returncode = shell_session_handle.poll()
    if (returncode is None): print("Something's gone wrong, shell process was supposed to have terminated...")
